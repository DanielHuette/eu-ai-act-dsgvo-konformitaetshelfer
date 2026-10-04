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


#: Gruppenüberschriften innerhalb eines Anhangs. Sie kommen in zwei Formen vor:
#: "Abschnitt A — Von Anbietern von Hochrisiko-KI-Systemen …" (Anhang VIII),
#: "Abschnitt 1" ohne weiteren Text (Anhang XI) und "1. Schengener
#: Informationssystem" (Anhang X). Alle drei setzen die Zählung darunter wieder
#: auf den Anfang, darum gehört die Gruppe in die Kennung:
#: KI-VO/anh-VIII/nr-A-1 statt dreimal KI-VO/anh-VIII/nr-1.
_GRUPPE_IM_ANHANG = re.compile(r"^(?:Abschnitt\s+([A-Z]|\d{1,2})\b|(\d{1,2})\.\s+\S)")


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
    wert = knoten.get("id")
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


def _absaetze_eines_artikels(behaelter: Tag, nummer: str = "") -> list[tuple[str, str, Tag | None]]:
    """Die Absätze eines Artikels als (Absatzkennung, Text).

    Erste Wahl sind die Absatzcontainer mit Kennung "006.003" — die erste Zahl
    ist der Artikel, die zweite der Absatz. Fehlen sie (kurze Artikel haben
    manchmal nur Fließtext), wird der Text des Artikels ohne Überschrift als
    ein Absatz geführt.

    ``nummer`` ist die Nummer des Artikels, in dem gesucht wird, und sie ist
    nicht nur Beiwerk: die Artikel 107 und 108 ändern andere Rechtsakte und
    zitieren deren Absätze im Wortlaut. Das Amtsblatt gibt diesen Zitaten die
    Kennung aus dem *fremden* Rechtsakt — in Artikel 107 steht ein Container
    mit der Kennung "005.004". Ohne Abgleich entstünde daraus ein zweiter
    "Artikel 5 Absatz 4", der den echten verdrängt oder stillschweigend
    verworfen wird. Beides ist falsch: zitierter Text gehört in den Artikel,
    der zitiert, nicht in den zitierten.
    """
    gefunden: list[tuple[str, str, Tag | None]] = []
    for kind in behaelter.find_all("div", recursive=False):
        treffer = _ABSATZ_ID.match(_kennung(kind))
        if not treffer:
            continue
        if nummer and str(int(treffer.group(1))) != str(nummer):
            # Zitat aus einem fremden Rechtsakt — bleibt Teil des Artikeltexts.
            continue
        text = _text_von(kind)
        kennzahl = str(int(treffer.group(2)))
        zaehlung = _FUEHRENDE_ZAEHLUNG.match(text)
        if zaehlung and zaehlung.group(1) == kennzahl:
            text = text[zaehlung.end() :].strip()
        if text:
            gefunden.append((kennzahl, text, kind))
    if gefunden:
        return gefunden

    teile = []
    for absatz in behaelter.find_all("p", class_="oj-normal"):
        text = _text_von(absatz)
        if text:
            teile.append(text)
    if not teile:
        return []
    # Ein Artikel ohne Absatzgliederung, der aber eine Buchstabenliste trägt:
    # Artikel 16 zählt die Anbieterpflichten so auf, a) bis l), ohne je einen
    # Absatz zu nennen. Zitiert wird er trotzdem als "Artikel 16 Buchstabe a",
    # und darauf zeigen dreizehn Pflichten im Regelwerk. Der Artikel selbst
    # ist dann der Container, aus dem die Buchstaben geholt werden.
    hat_buchstaben = any(
        re.fullmatch(r"[a-z]", _zaehlung_und_zelle(t)[0])
        for t in behaelter.find_all("table", recursive=False)
        if t.find_all("tr") and t.find_all("tr")[0].find_all(["td", "th"])
    )
    return [("1", "\n\n".join(teile), behaelter if hat_buchstaben else None)]


def _begriffsbestimmungen(behaelter: Tag) -> list[tuple[str, str]]:
    """Die nummerierten Begriffe eines Definitionsartikels.

    Artikel 4 der Datenschutz-Grundverordnung und Artikel 3 der KI-Verordnung
    haben keine Absätze, sondern durchnummerierte Begriffe — 26 beziehungsweise
    68 Stück, jeder in einer eigenen Tabelle mit der Zählung in der ersten
    Zelle. Ohne diese Zerlegung wäre der ganze Artikel eine Einheit von 19.000
    Zeichen, und eine Antwort könnte nicht auf "Artikel 3 Nummer 39" zeigen —
    die Definition des Emotionserkennungssystems, an der das Verbot nach
    Artikel 5 Absatz 1 Buchstabe f hängt. Ebenso Artikel 4 Nummer 14 DSGVO,
    die biometrischen Daten.
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
        if not re.fullmatch(r"\d{1,3}", zaehlung):
            continue
        inhalt = _saeubern(tabelle.get_text(" ", strip=True))
        inhalt = re.sub(rf"^{re.escape(zaehlung)}[.)]\s*", "", inhalt).strip()
        if len(inhalt) > 30:
            stuecke.append((zaehlung, inhalt))
    return stuecke


def _zaehlung_und_zelle(tabelle: Tag) -> tuple[str, Tag | None]:
    """Zählung und Textzelle eines Aufzählungspunkts.

    EUR-Lex setzt jeden Punkt in eine eigene Tabelle. Die Zählung steht aber
    nicht immer in der ersten Zelle: eingerückte Aufzählungen haben davor eine
    oder mehrere leere Zellen, die die Einrückung tragen. Anhang I ist so
    gebaut — dort steht die Zählung in der zweiten Zelle. Wer blind die erste
    liest, findet nichts und verliert den ganzen Anhang: 24 Rechtsakte, auf die
    Artikel 6 Absatz 1 für das hohe Risiko über das Produktsicherheitsrecht
    verweist. Darum werden führende leere Zellen übersprungen.
    """
    zeilen = tabelle.find_all("tr")
    if not zeilen:
        return "", None
    zellen = zeilen[0].find_all(["td", "th"])
    for i, zelle in enumerate(zellen[:-1]):
        zaehlung = _saeubern(zelle.get_text(" ", strip=True))
        if zaehlung:
            return zaehlung.rstrip(".)"), zellen[i + 1]
    return "", None


def _buchstaben(behaelter: Tag) -> list[tuple[str, str]]:
    """Die Buchstabenpunkte eines Absatzes — aus der Gliederung, nicht aus dem Text.

    EUR-Lex setzt jeden Aufzählungspunkt in eine eigene Tabelle, die unmittelbar
    im Absatzcontainer steht: erste Zelle die Zählung ("a)"), zweite der Text.

    Über den Fließtext zu gehen war der Fehler, und zwar gleich dreifach:

    * Artikel 5 Absatz 1 Buchstabe c enthält eine *verschachtelte* Aufzählung
      "i)", "ii)". Im Fließtext sieht "i)" wie der Buchstabe i aus — und es gibt
      in demselben Absatz auch einen echten Buchstaben i. Zwei verschiedene
      Texte unter einer Kennung, einer davon ging verloren.
    * Artikel 43 hat in Absatz 1 die Punkte a) und b) und in Absatz 3 wieder
      a) bis d). Im Text eines ganzen Artikels gesucht, kollidieren sie.
    * Artikel 3 hat gar keine Absätze, sondern 68 Begriffsbestimmungen —
      Buchstaben im Fließtext stammen dort aus den Definitionen selbst.

    Die Gliederung kennt diese Unterschiede. Der Text nicht.
    """
    stuecke: list[tuple[str, str]] = []
    unterabsatz = 1
    for tabelle in behaelter.find_all("table", recursive=False):
        zaehlung, _zelle = _zaehlung_und_zelle(tabelle)
        if not re.fullmatch(r"[a-z]", zaehlung):
            continue
        inhalt = _saeubern(tabelle.get_text(" ", strip=True))
        inhalt = re.sub(rf"^{re.escape(zaehlung)}[.)]\s*", "", inhalt).strip()
        if len(inhalt) <= 40:
            continue
        # Fängt die Zählung wieder von vorn an, steht eine zweite Aufzählung im
        # selben Absatz — im Amtsblatt sind das zwei Unterabsätze. Artikel 43
        # Absatz 1 hat so zweimal a) und b). Ohne die Unterscheidung trägt der
        # zweite Punkt die Kennung des ersten, und einer von beiden fällt weg.
        if any(z == zaehlung for z, _ in stuecke):
            unterabsatz += 1
        marke = zaehlung if unterabsatz == 1 else f"ua{unterabsatz:d}-{zaehlung}"
        stuecke.append((marke, inhalt))
    return stuecke


def _unterpunkte_im_anhang(zelle: Tag, marke: str) -> list[tuple[str, str]]:
    """Die Buchstabenpunkte innerhalb eines numerierten Anhangspunkts.

    Anhang III nennt acht Bereiche, aber die Einstufung hängt nicht am Bereich,
    sondern am einzelnen Buchstaben darunter: Nummer 4 Buchstabe a trifft die
    Einstellung, Buchstabe b die Arbeitsbedingungen - zwei verschiedene
    Sachverhalte unter einer Überschrift. Wer nur die Nummer kennt, kann einen
    Fall nicht auf die Stelle zurückführen, die ihn trägt. EUR-Lex legt die
    Punkte als Tabellen unmittelbar in die Textzelle der Nummer.
    """
    stuecke: list[tuple[str, str]] = []
    for tabelle in zelle.find_all("table", recursive=False):
        zaehlung, textzelle = _zaehlung_und_zelle(tabelle)
        if textzelle is None or not re.fullmatch(r"[a-z]|[ivxlc]+", zaehlung):
            continue
        inhalt = _saeubern(tabelle.get_text(" ", strip=True))
        inhalt = re.sub(rf"^{re.escape(zaehlung)}[.)]\s*", "", inhalt).strip()
        if len(inhalt) <= 40:
            continue
        stuecke.append((f"{marke}-{zaehlung}", inhalt))
        stuecke.extend(_unterpunkte_im_anhang(textzelle, f"{marke}-{zaehlung}"))
    return stuecke


def _anhangspunkte(behaelter: Tag) -> list[tuple[str, str]]:
    """Die numerierten Punkte eines Anhangs.

    EUR-Lex setzt jeden Punkt eines Anhangs in eine eigene Tabelle: die erste
    Zelle trägt die Zählung ("1.", "a)"), die zweite den Text. Anhang III führt
    so die acht Hochrisikobereiche - genau die Stellen, auf die eine Einstufung
    zeigen muss. Fehlen die Tabellen, wird der Fließtext nach Zählungen zerlegt.
    """
    stuecke: list[tuple[str, str]] = []
    abschnitt = ""
    # Durchlaufen wird in Dokumentreihenfolge, nicht nur über die Tabellen:
    # ein Anhang kann in Abschnitte zerfallen, deren Zählung jeweils wieder bei
    # 1 beginnt. Anhang VIII hat drei davon — Angaben des Anbieters, des
    # Bevollmächtigten und des Betreibers —, Anhang X ebenfalls. Ohne den
    # Abschnitt in der Kennung trägt jede Nummer dreimal denselben Namen, und
    # zwei Drittel des Anhangs gehen beim Entdoppeln verloren.
    for kind in behaelter.find_all(["p", "table"], recursive=False):
        if kind.name == "p":
            klassen: list[str] = list(kind.get("class") or [])
            if any(str(k).startswith("oj-ti-grseq") for k in klassen):
                kopf = _saeubern(kind.get_text(" ", strip=True))
                treffer = _GRUPPE_IM_ANHANG.match(kopf)
                # Nur ein erkannter Abschnittskopf setzt den Abschnitt neu. Ein
                # Anhang kann der Abschnittszeile eine zweite Überschrift
                # nachstellen - Anhang XI hat unter "Abschnitt 1" noch "Von
                # allen Anbietern von KI-Modellen ...". Würde die den Abschnitt
                # loeschen, traegt Abschnitt 2 wieder die Kennungen von
                # Abschnitt 1, und einer der beiden fiele beim Entdoppeln weg.
                if treffer:
                    abschnitt = treffer.group(1) or treffer.group(2)
            continue

        tabelle = kind
        zaehlung, textzelle = _zaehlung_und_zelle(tabelle)
        if textzelle is None or not re.fullmatch(r"\d{1,2}|[a-z]|[ivxlc]+|[A-Z]", zaehlung):
            continue
        inhalt = _saeubern(tabelle.get_text(" ", strip=True))
        # Die Zählung steht am Anfang des Gesamttexts noch einmal - weg damit.
        inhalt = re.sub(rf"^{re.escape(zaehlung)}[.)]\s*", "", inhalt).strip()
        marke = f"{abschnitt}-{zaehlung}" if abschnitt else zaehlung
        if len(inhalt) > 60:
            stuecke.append((marke, inhalt))
        stuecke.extend(_unterpunkte_im_anhang(textzelle, marke))

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
        begriffe = _begriffsbestimmungen(behaelter)
        if begriffe:
            # Definitionsartikel: Nummern statt Absätze.
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
                    text=_text_von(behaelter),
                    quelle=quelle,
                    stand=stand,
                )
            )
            for zahl, inhalt in begriffe:
                ergebnis.einheiten.append(
                    Einheit(
                        kennung=f"{rechtsakt.value}/art-{nummer}/nr-{zahl}",
                        rechtsakt=rechtsakt,
                        art=Einheitsart.ARTIKEL,
                        nummer=nummer,
                        absatz=f"Nummer {zahl}",
                        titel=titel,
                        kapitel=kapitel,
                        abschnitt=abschnitt,
                        text=inhalt,
                        quelle=quelle,
                        stand=stand,
                    )
                )
            ergebnis.befund["begriffe"] = ergebnis.befund.get("begriffe", 0) + len(begriffe)
            continue

        absaetze = _absaetze_eines_artikels(behaelter, nummer)
        if not absaetze:
            continue

        volltext = "\n\n".join(f"({kennung}) {text}" for kennung, text, _ in absaetze)
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

        for kennung, text, container in absaetze:
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
            for buchstabe, inhalt in _buchstaben(container) if container else []:
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
    # Doppelte Kennungen: die zweite wird übergangen. Die Warnung nennt sie
    # beim Namen und sagt, ob der übergangene Text derselbe war — denn nur dann
    # ist das Übergehen harmlos. Steht ein anderer Text dahinter, geht Inhalt
    # verloren, und das muss auffallen statt in einer Zahl zu verschwinden.
    gesehen: dict[str, str] = {}
    sauber: list[Einheit] = []
    gleich: list[str] = []
    verschieden: list[str] = []
    for einheit in ergebnis.einheiten:
        vorher = gesehen.get(einheit.kennung)
        if vorher is not None:
            (gleich if vorher == einheit.text else verschieden).append(einheit.kennung)
            continue
        gesehen[einheit.kennung] = einheit.text
        sauber.append(einheit)
    ergebnis.einheiten = sauber
    if gleich:
        ergebnis.warnungen.append(
            "%d wortgleiche Dubletten übergangen: %s"
            % (len(gleich), ", ".join(sorted(set(gleich))[:6]))
        )
    if verschieden:
        ergebnis.warnungen.append(
            "ACHTUNG: %d Kennungen doppelt MIT ABWEICHENDEM TEXT — hier geht "
            "Inhalt verloren: %s" % (len(verschieden), ", ".join(sorted(set(verschieden))[:10]))
        )

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
