"""Zerlegt einen amtlichen EUR-Lex-Volltext in zitierfähige Einheiten.

Warum ein eigener Zerleger und kein fertiges Paket: Eine Auskunft über Pflichten
muss auf *Artikel und Absatz* zeigen können, nicht auf "irgendwo in der
Verordnung". Dafür muss die Gliederung erhalten bleiben. Fertige
Textextraktoren werfen genau das weg.

Die Fassung, die EUR-Lex ausliefert, ist dafür gebaut. Sie trägt sprechende
Anker, und der Zerleger arbeitet ausschließlich über diese Anker — nicht über
Textmuster. Textmuster würden jede Erwähnung von "Artikel 99" im Fließtext für
einen Artikelanfang halten.

Was das Dokument hergibt:

==========================  ===================================================
``div#art_6``               der ganze Artikel 6
``p.oj-ti-art``             die Zeile "Artikel 6"
``div#art_6.tit_1``         die Überschrift des Artikels
``div#006.003``             Artikel 6 Absatz 3 — Nummer und Absatz in der Kennung
``div#anx_III``             Anhang III
``*#rct_60``                Erwägungsgrund 60
``div#cpt_III``             Kapitel III
``div#cpt_III.sct_2``       Kapitel III Abschnitt 2
==========================  ===================================================

Nach dem Lauf wird gegen die erwartete Anzahl geprüft. Kommt eine andere Zahl
heraus, steht das als Warnung im Ergebnis — ein halber Korpus darf nicht
unbemerkt durchgehen.
"""

from __future__ import annotations

import re
import warnings
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup, Tag, XMLParsedAsHTMLWarning

from helfer.modell import Einheit, Einheitsart, Rechtsakt

# EUR-Lex liefert XHTML mit XML-Deklaration; der HTML-Zweig von lxml liest es
# zuverlässig, die Warnung dazu ist hier gegenstandslos.
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

#: Erwartete Umfänge. Weicht der Lauf ab, stimmt etwas nicht.
ERWARTET: dict[Rechtsakt, dict[str, int]] = {
    Rechtsakt.KI_VO: {"artikel": 113, "anhang": 13, "erwaegungsgrund": 180},
    Rechtsakt.DSGVO: {"artikel": 99, "anhang": 0, "erwaegungsgrund": 173},
}

#: Ein Absatzcontainer trägt eine Kennung der Form "006.003".
_ABSATZ_ID = re.compile(r"^(\d{3})\.(\d{3})$")
#: Führende Absatzzählung im Text, etwa "(3)" oder "3." - wird abgetrennt.
_FUEHRENDE_ZAEHLUNG = re.compile(r"^\(?(\d{1,2})\)?\.?\s+")
#: Ein Buchstabenpunkt innerhalb eines Absatzes, etwa "a)" oder "(a)".
_BUCHSTABE = re.compile(r"^\(?([a-z])\)\s+")


@dataclass
class Zerlegung:
    """Was beim Zerlegen herauskam, samt Befund und Warnungen."""

    einheiten: list[Einheit] = field(default_factory=list)
    befund: dict[str, int] = field(default_factory=dict)
    warnungen: list[str] = field(default_factory=list)

    @property
    def vollstaendig(self) -> bool:
        return not any(
            w.startswith(("artikel:", "anhang:", "erwaegungsgrund:")) for w in self.warnungen
        )

    def nach_kennung(self, kennung: str) -> Einheit | None:
        return next((e for e in self.einheiten if e.kennung == kennung), None)


def _kennung(knoten: Tag | None) -> str:
    """Die id eines Knotens als Zeichenkette — immer.

    BeautifulSoup gibt für ein Attribut entweder eine Zeichenkette oder eine
    Liste zurück: bei mehrwertigen Attributen wie ``class`` eine Liste, bei
    ``id`` normalerweise eine Zeichenkette. "Normalerweise" genügt hier nicht,
    denn das ganze Zerlegen hängt an den id-Ankern des Dokuments — und ein
    Listenwert würde nicht als Fehler auffallen, sondern den Artikel
    stillschweigend übergehen. Darum geht jeder id-Zugriff durch diese Stelle.
    """
    if knoten is None:
        return ""
    wert = _kennung(knoten)
    if wert is None:
        return ""
    if isinstance(wert, str):
        return wert
    # Liste: die Teile zusammenfügen, wie der Browser es täte.
    return " ".join(str(teil) for teil in wert)


def _saeubern(text: str) -> str:
    """Macht aus EUR-Lex-Text lesbaren Fließtext.

    EUR-Lex setzt geschützte Leerzeichen zwischen "Artikel" und Zahl und
    gruppiert Absatzzählungen mit drei davon. Beides muss weg, sonst findet
    später keine Stichwortsuche "Artikel 6".
    """
    text = text.replace(" ", " ").replace("‑", "-").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _text_von(knoten: Tag) -> str:
    return _saeubern(knoten.get_text(" ", strip=True))


def _gliederung(knoten: Tag) -> tuple[str, str]:
    """Kapitel und Abschnitt, in denen ein Knoten steht - über die Anker."""
    kapitel = abschnitt = ""
    eltern = knoten.parent
    while eltern is not None and getattr(eltern, "name", None):
        kennung = _kennung(eltern)
        if re.match(r"^cpt_[IVXLC]+$", kennung) and not kapitel:
            titel = eltern.find(class_=["oj-ti-section-1", "oj-ti-section-2"])
            kapitel = _text_von(titel) if titel else kennung.replace("cpt_", "Kapitel ")
        elif re.match(r"^cpt_[IVXLC]+\.sct_\d+$", kennung) and not abschnitt:
            titel = eltern.find(class_="oj-ti-grseq-1")
            abschnitt = _text_von(titel) if titel else kennung.split(".")[-1]
        eltern = eltern.parent
    return kapitel, abschnitt


def _absaetze_eines_artikels(behaelter: Tag) -> list[tuple[str, str]]:
    """Die Absätze eines Artikels als (Absatzkennung, Text).

    Erste Wahl sind die Absatzcontainer mit Kennung "006.003". Fehlen sie -
    kurze Artikel haben manchmal nur Fließtext -, wird der Text des Artikels
    ohne Überschrift als ein Absatz geführt.
    """
    gefunden: list[tuple[str, str]] = []
    for kind in behaelter.find_all("div", recursive=False):
        treffer = _ABSATZ_ID.match(_kennung(kind))
        if not treffer:
            continue
        text = _text_von(kind)
        kennzahl = str(int(treffer.group(2)))
        zaehlung = _FUEHRENDE_ZAEHLUNG.match(text)
        if zaehlung and zaehlung.group(1) == kennzahl:
            text = text[zaehlung.end() :].strip()
        if text:
            gefunden.append((kennzahl, text))
    if gefunden:
        return gefunden

    teile = []
    for absatz in behaelter.find_all("p", class_="oj-normal"):
        text = _text_von(absatz)
        if text:
            teile.append(text)
    return [("1", "\n\n".join(teile))] if teile else []


def _buchstaben(text: str) -> list[tuple[str, str]]:
    """Zerlegt einen Absatz in seine Buchstabenpunkte, wenn er welche hat."""
    stuecke: list[tuple[str, str]] = []
    jetzt: str | None = None
    gesammelt: list[str] = []
    for zeile in re.split(r"(?=\b[a-z]\)\s)", text):
        treffer = _BUCHSTABE.match(zeile.strip())
        if treffer:
            if jetzt:
                stuecke.append((jetzt, " ".join(gesammelt).strip()))
            jetzt = treffer.group(1)
            gesammelt = [zeile.strip()[treffer.end() :]]
            continue
        if jetzt:
            gesammelt.append(zeile.strip())
    if jetzt:
        stuecke.append((jetzt, " ".join(gesammelt).strip()))
    return [(b, t) for b, t in stuecke if len(t) > 40]


def _anhangspunkte(behaelter: Tag) -> list[tuple[str, str]]:
    """Die numerierten Punkte eines Anhangs.

    EUR-Lex setzt jeden Punkt eines Anhangs in eine eigene Tabelle: die erste
    Zelle trägt die Zählung ("1.", "a)"), die zweite den Text. Anhang III führt
    so die acht Hochrisikobereiche - genau die Stellen, auf die eine Einstufung
    zeigen muss. Fehlen die Tabellen, wird der Fließtext nach Zählungen zerlegt.
    """
    stuecke: list[tuple[str, str]] = []
    for tabelle in behaelter.find_all("table", recursive=False):
        zeilen = tabelle.find_all("tr")
        if not zeilen:
            continue
        zellen = zeilen[0].find_all(["td", "th"])
        if len(zellen) < 2:
            continue
        zaehlung = _saeubern(zellen[0].get_text(" ", strip=True)).rstrip(".)")
        if not re.fullmatch(r"\d{1,2}|[a-z]|[ivxlc]+|[A-Z]", zaehlung):
            continue
        inhalt = _saeubern(tabelle.get_text(" ", strip=True))
        # Die Zählung steht am Anfang des Gesamttexts noch einmal - weg damit.
        inhalt = re.sub(rf"^{re.escape(zaehlung)}[.)]\s*", "", inhalt).strip()
        if len(inhalt) > 60:
            stuecke.append((zaehlung, inhalt))

    if stuecke:
        return stuecke

    text = _text_von(behaelter)
    teile = re.split(r"(?m)^\s*(\d{1,2})\.\s+", text)
    for i in range(1, len(teile) - 1, 2):
        nummer, inhalt = teile[i], _saeubern(teile[i + 1])
        if len(inhalt) > 60:
            stuecke.append((nummer, inhalt))
    return stuecke


def zerlegen(
    html: str,
    rechtsakt: Rechtsakt,
    quelle: str = "",
    stand: date | None = None,
) -> Zerlegung:
    """Zerlegt einen EUR-Lex-Volltext in zitierfähige Einheiten.

    Je Artikel entsteht eine Einheit mit dem vollen Text und je Absatz eine
    eigene. Buchstabenpunkte eines Absatzes werden zusätzlich einzeln geführt,
    weil Verbote und Hochrisikobereiche genau dort stehen — etwa Artikel 5
    Absatz 1 Buchstabe f.
    """
    ergebnis = Zerlegung()
    suppe = BeautifulSoup(html, "lxml")
    for weg in suppe(["script", "style", "noscript"]):
        weg.decompose()

    # ------------------------------------------------------------- Artikel
    for behaelter in suppe.find_all("div", id=re.compile(r"^art_\d+$")):
        nummer = _kennung(behaelter).removeprefix("art_")
        titelknoten = behaelter.find(class_="eli-title") or behaelter.find(class_="oj-sti-art")
        titel = _text_von(titelknoten) if titelknoten else ""
        kapitel, abschnitt = _gliederung(behaelter)
        absaetze = _absaetze_eines_artikels(behaelter)
        if not absaetze:
            continue

        volltext = "\n\n".join(f"({kennung}) {text}" for kennung, text in absaetze)
        ergebnis.einheiten.append(
            Einheit(
                kennung=f"{rechtsakt.value}/art-{nummer}",
                rechtsakt=rechtsakt,
                art=Einheitsart.ARTIKEL,
                nummer=nummer,
                absatz=None,
                titel=titel,
                kapitel=kapitel,
                abschnitt=abschnitt,
                text=volltext,
                quelle=quelle,
                stand=stand,
            )
        )

        for kennung, text in absaetze:
            if len(text) < 25:
                continue
            ergebnis.einheiten.append(
                Einheit(
                    kennung=f"{rechtsakt.value}/art-{nummer}/abs-{kennung}",
                    rechtsakt=rechtsakt,
                    art=Einheitsart.ARTIKEL,
                    nummer=nummer,
                    absatz=kennung,
                    titel=titel,
                    kapitel=kapitel,
                    abschnitt=abschnitt,
                    text=text,
                    quelle=quelle,
                    stand=stand,
                )
            )
            for buchstabe, inhalt in _buchstaben(text):
                ergebnis.einheiten.append(
                    Einheit(
                        kennung=f"{rechtsakt.value}/art-{nummer}/abs-{kennung}-{buchstabe}",
                        rechtsakt=rechtsakt,
                        art=Einheitsart.ARTIKEL,
                        nummer=nummer,
                        absatz=f"{kennung} Buchstabe {buchstabe}",
                        titel=titel,
                        kapitel=kapitel,
                        abschnitt=abschnitt,
                        text=inhalt,
                        quelle=quelle,
                        stand=stand,
                    )
                )

    # ------------------------------------------------------------- Anhänge
    for behaelter in suppe.find_all("div", id=re.compile(r"^anx_[IVXLC]+$")):
        nummer = _kennung(behaelter).removeprefix("anx_")
        kopfzeilen = behaelter.find_all(class_="oj-doc-ti", limit=2)
        titel = _text_von(kopfzeilen[1]) if len(kopfzeilen) > 1 else ""
        text = _text_von(behaelter)
        if len(text) < 60:
            continue
        ergebnis.einheiten.append(
            Einheit(
                kennung=f"{rechtsakt.value}/anh-{nummer}",
                rechtsakt=rechtsakt,
                art=Einheitsart.ANHANG,
                nummer=nummer,
                absatz=None,
                titel=titel,
                text=text,
                quelle=quelle,
                stand=stand,
            )
        )
        for punkt, inhalt in _anhangspunkte(behaelter):
            ergebnis.einheiten.append(
                Einheit(
                    kennung=f"{rechtsakt.value}/anh-{nummer}/nr-{punkt}",
                    rechtsakt=rechtsakt,
                    art=Einheitsart.ANHANG,
                    nummer=nummer,
                    absatz=punkt,
                    titel=titel,
                    text=inhalt,
                    quelle=quelle,
                    stand=stand,
                )
            )

    # ------------------------------------------------- Erwägungsgründe
    for knoten in suppe.find_all(id=re.compile(r"^rct_\d+$")):
        nummer = _kennung(knoten).removeprefix("rct_")
        text = _text_von(knoten)
        zaehlung = re.match(rf"^\({re.escape(nummer)}\)\s*", text)
        if zaehlung:
            text = text[zaehlung.end() :].strip()
        if len(text) < 40:
            continue
        ergebnis.einheiten.append(
            Einheit(
                kennung=f"{rechtsakt.value}/erw-{nummer}",
                rechtsakt=rechtsakt,
                art=Einheitsart.ERWAEGUNGSGRUND,
                nummer=nummer,
                absatz=None,
                titel=f"Erwägungsgrund {nummer}",
                text=text,
                quelle=quelle,
                stand=stand,
            )
        )

    # -------------------------------------------------------------- Befund
    doppelt = 0
    gesehen: set[str] = set()
    sauber: list[Einheit] = []
    for einheit in ergebnis.einheiten:
        if einheit.kennung in gesehen:
            doppelt += 1
            continue
        gesehen.add(einheit.kennung)
        sauber.append(einheit)
    ergebnis.einheiten = sauber
    if doppelt:
        ergebnis.warnungen.append(f"{doppelt:d} doppelte Kennungen übergangen")

    ergebnis.befund = {
        "einheiten": len(ergebnis.einheiten),
        "artikel": sum(
            1 for e in ergebnis.einheiten if e.art is Einheitsart.ARTIKEL and e.absatz is None
        ),
        "absaetze": sum(
            1 for e in ergebnis.einheiten if e.art is Einheitsart.ARTIKEL and e.absatz is not None
        ),
        "anhang": sum(
            1 for e in ergebnis.einheiten if e.art is Einheitsart.ANHANG and e.absatz is None
        ),
        "anhangspunkte": sum(
            1 for e in ergebnis.einheiten if e.art is Einheitsart.ANHANG and e.absatz is not None
        ),
        "erwaegungsgrund": sum(
            1 for e in ergebnis.einheiten if e.art is Einheitsart.ERWAEGUNGSGRUND
        ),
    }
    for art, soll in ERWARTET.get(rechtsakt, {}).items():
        ist = ergebnis.befund.get(art, 0)
        if soll and ist != soll:
            ergebnis.warnungen.append(f"{art}: {ist:d} gefunden, erwartet {soll:d}")
    return ergebnis


def aus_datei(pfad: Path, rechtsakt: Rechtsakt, quelle: str = "") -> Zerlegung:
    """Zerlegt eine gespeicherte EUR-Lex-Seite."""
    html = pfad.read_text(encoding="utf-8", errors="ignore")
    stand = date.fromtimestamp(pfad.stat().st_mtime)
    return zerlegen(html, rechtsakt, quelle=quelle, stand=stand)
