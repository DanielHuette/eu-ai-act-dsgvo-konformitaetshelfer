"""Zerlegt das Bundesdatenschutzgesetz und die artikelweise geholte Verordnung.

Zwei Quellen mit je eigener Form:

**Bundesdatenschutzgesetz** von gesetze-im-internet.de. Die Seite ist sauber
gegliedert: je Paragraf ein Container ``div.jnnorm`` mit der Bezeichnung in
``.jnenbez`` ("§ 26"), der Überschrift in ``.jnentitel`` und dem Normtext in
``.jnhtml``, dessen Absätze als ``div.jurAbsatz`` vorliegen. Darüber wird
zerlegt — nicht über Textmuster. Ein Textmuster trennt sonst mitten im Satz,
wenn ein Querverweis wie "§ 63 Nummer 3 der Verwaltungsgerichtsordnung"
auftritt.

**Datenschutz-Grundverordnung**, artikelweise von dsgvo-gesetz.de. Diese Quelle
ist der Rückfall, wenn der amtliche Volltext aus dem Amtsblatt nicht erreichbar
war. Sie liefert guten Normtext, hängt aber Seitenbeiwerk an: "Passende
Erwägungsgründe", "Fehler melden", Navigationspfeile. Das wird abgeschnitten,
und die Absätze werden aus der Zählung im Text gewonnen.
"""

from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from bs4 import BeautifulSoup, Tag

from helfer.modell import Einheit, Einheitsart, Rechtsakt

BDSG_QUELLE = "https://www.gesetze-im-internet.de/bdsg_2018/BJNR209710017.html"

#: Alles ab einer dieser Zeilen ist Seitenbeiwerk und gehört nicht zum Normtext.
_BEIWERK_AB = (
    "Passende Erwägungsgründe",
    "Passende Paragraphen des BDSG",
    "Passende Paragrafen des BDSG",
    "Erwägungsgründe zu Art",
    "Fehler melden",
    "Inhaltsverzeichnis",
    "Diese Website verwendet",
    "Wir verwenden Cookies",
)

#: Navigationszeilen am Textende, etwa "← Art. 21 DSGVO".
_NAVIGATION = re.compile(
    r"(?m)^\s*(?:←|→|«|»)?\s*Art\.?\s*\d{1,3}\s*(?:DSGVO|GDPR)?\s*(?:←|→|«|»)?\s*$"
)

#: Ein Absatz beginnt mit "(1)" am Zeilen- oder Textanfang.
_ABSATZ = re.compile(r"(?m)^\s*\((\d{1,2})\)\s+")


def _saeubern(text: str) -> str:
    text = text.replace(" ", " ").replace("‑", "-").replace(" ", " ")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def beiwerk_abschneiden(text: str) -> str:
    """Schneidet Seitenbeiwerk ab, das hinter dem Normtext steht."""
    schnitt = len(text)
    for marke in _BEIWERK_AB:
        stelle = text.find(marke)
        if 0 <= stelle < schnitt:
            schnitt = stelle
    text = text[:schnitt]
    text = _NAVIGATION.sub("", text)
    # Einzelne Zeilen, die nur aus einer Zahl in Klammern bestehen, sind
    # Verweisziffern aus der Erwägungsgrundliste.
    text = re.sub(r"(?m)^\s*\(\s*\d{1,3}\s*\)\s*$", "", text)
    text = re.sub(r"(?m)^\s*(?:DSGVO|BDSG|GDPR)\s*$", "", text)
    return _saeubern(text)


def _absaetze_aus_text(text: str) -> list[tuple[str, str]]:
    """Zerlegt einen Normtext in seine Absätze anhand der Zählung "(1)"."""
    treffer = list(_ABSATZ.finditer(text))
    if not treffer:
        return []
    stuecke: list[tuple[str, str]] = []
    for nummer, start in enumerate(treffer):
        ende = treffer[nummer + 1].start() if nummer + 1 < len(treffer) else len(text)
        inhalt = _saeubern(text[start.end() : ende])
        if len(inhalt) > 25:
            stuecke.append((start.group(1), inhalt))
    return stuecke


# ----------------------------------------------------------- Bundesdatenschutz


def bdsg(pfad: Path) -> list[Einheit]:
    """Zerlegt das Bundesdatenschutzgesetz in Paragrafen und Absätze."""
    if not pfad.exists():
        return []
    suppe = BeautifulSoup(pfad.read_text(encoding="utf-8", errors="ignore"), "lxml")
    for weg in suppe(["script", "style", "noscript"]):
        weg.decompose()
    stand = date.fromtimestamp(pfad.stat().st_mtime)

    einheiten: list[Einheit] = []
    teil = ""
    kapitel = ""
    for behaelter in suppe.select("div.jnnorm"):
        bezeichnung = behaelter.select_one(".jnenbez")
        titelknoten = behaelter.select_one(".jnentitel")
        inhalt: Tag | None = behaelter.select_one(".jnhtml")

        # Gliederungsüberschriften haben eine Bezeichnung wie "Teil 2" und
        # keinen Normtext - sie setzen nur den Zusammenhang.
        roh_bez = _saeubern(bezeichnung.get_text(" ", strip=True)) if bezeichnung else ""
        roh_titel = _saeubern(titelknoten.get_text(" ", strip=True)) if titelknoten else ""
        if roh_bez.startswith("Teil"):
            teil = (f"{roh_bez} {roh_titel}").strip()
            continue
        if roh_bez.startswith(("Kapitel", "Abschnitt", "Unterabschnitt")):
            kapitel = (f"{roh_bez} {roh_titel}").strip()
            continue

        nummer_treffer = re.match(r"^§\s*(\d+[a-z]?)$", roh_bez)
        if not nummer_treffer or inhalt is None:
            continue
        nummer = nummer_treffer.group(1)

        absatzknoten = inhalt.select("div.jurAbsatz")
        if absatzknoten:
            roh = "\n\n".join(_saeubern(k.get_text(" ", strip=True)) for k in absatzknoten)
        else:
            roh = _saeubern(inhalt.get_text("\n"))
        roh = _saeubern(roh)
        if len(roh) < 40:
            continue

        einheiten.append(
            Einheit(
                kennung=f"BDSG/par-{nummer}",
                rechtsakt=Rechtsakt.BDSG,
                art=Einheitsart.PARAGRAF,
                nummer=nummer,
                absatz=None,
                titel=roh_titel,
                kapitel=teil,
                abschnitt=kapitel,
                text=roh,
                quelle=BDSG_QUELLE,
                stand=stand,
            )
        )

        for kennung, text in _absaetze_aus_text(roh):
            einheiten.append(
                Einheit(
                    kennung=f"BDSG/par-{nummer}/abs-{kennung}",
                    rechtsakt=Rechtsakt.BDSG,
                    art=Einheitsart.PARAGRAF,
                    nummer=nummer,
                    absatz=kennung,
                    titel=roh_titel,
                    kapitel=teil,
                    abschnitt=kapitel,
                    text=text,
                    quelle=BDSG_QUELLE,
                    stand=stand,
                )
            )
    return einheiten


# ------------------------------------------------- artikelweise Verordnung


def artikeldateien(ordner: Path, rechtsakt: Rechtsakt) -> list[Einheit]:
    """Liest die artikelweise geholten JSON-Dateien, säubert und zerlegt sie."""
    einheiten: list[Einheit] = []
    if not ordner.exists():
        return einheiten

    for datei in sorted(ordner.rglob("*.json")):
        if datei.name.startswith("_") or datei.name == "inhaltsverzeichnis.json":
            continue
        try:
            satz = json.loads(datei.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        text = beiwerk_abschneiden(satz.get("text", ""))
        if len(text) < 40:
            continue

        einheit_art = satz.get("einheit", "artikel")
        art = {
            "artikel": Einheitsart.ARTIKEL,
            "anhang": Einheitsart.ANHANG,
            "erwaegungsgrund": Einheitsart.ERWAEGUNGSGRUND,
        }.get(einheit_art, Einheitsart.ARTIKEL)
        stamm = {"artikel": "art", "anhang": "anh", "erwaegungsgrund": "erw"}[einheit_art]
        nummer = str(satz["nummer"])
        stand = date.fromtimestamp(datei.stat().st_mtime)
        titel = _saeubern(satz.get("titel", ""))

        einheiten.append(
            Einheit(
                kennung=f"{rechtsakt.value}/{stamm}-{nummer}",
                rechtsakt=rechtsakt,
                art=art,
                nummer=nummer,
                absatz=None,
                titel=titel,
                kapitel=_saeubern(satz.get("kapitel", "")),
                abschnitt=_saeubern(satz.get("abschnitt", "")),
                text=text,
                quelle=satz.get("quelle", ""),
                stand=stand,
            )
        )

        if art is not Einheitsart.ARTIKEL:
            continue

        # Die neuere Beschaffung legt die Absätze mitsamt Buchstabenpunkten
        # strukturiert ab. Dann wird die Gliederung übernommen statt geraten.
        gegliedert = satz.get("absaetze") or []
        if gegliedert:
            for absatz in gegliedert:
                kennung = str(absatz.get("nummer", "")).strip()
                absatztext = _saeubern(absatz.get("text", ""))
                if not kennung or len(absatztext) < 25:
                    continue
                einheiten.append(
                    Einheit(
                        kennung=f"{rechtsakt.value}/art-{nummer}/abs-{kennung}",
                        rechtsakt=rechtsakt,
                        art=Einheitsart.ARTIKEL,
                        nummer=nummer,
                        absatz=kennung,
                        titel=titel,
                        kapitel=_saeubern(satz.get("kapitel", "")),
                        abschnitt=_saeubern(satz.get("abschnitt", "")),
                        text=absatztext,
                        quelle=satz.get("quelle", ""),
                        stand=stand,
                    )
                )
                for punkt in absatz.get("buchstaben", []):
                    buchstabe = str(punkt.get("buchstabe", "")).strip()
                    inhalt = _saeubern(punkt.get("text", ""))
                    if not buchstabe or len(inhalt) < 25:
                        continue
                    einheiten.append(
                        Einheit(
                            kennung=f"{rechtsakt.value}/art-{nummer}/abs-{kennung}-{buchstabe}",
                            rechtsakt=rechtsakt,
                            art=Einheitsart.ARTIKEL,
                            nummer=nummer,
                            absatz=f"{kennung} Buchstabe {buchstabe}",
                            titel=titel,
                            text=inhalt,
                            quelle=satz.get("quelle", ""),
                            stand=stand,
                        )
                    )
            continue

        # Ältere Dateien tragen nur Fließtext - dann die Zählung im Text nutzen.
        for kennung, absatztext in _absaetze_aus_text(text):
            einheiten.append(
                Einheit(
                    kennung=f"{rechtsakt.value}/art-{nummer}/abs-{kennung}",
                    rechtsakt=rechtsakt,
                    art=Einheitsart.ARTIKEL,
                    nummer=nummer,
                    absatz=kennung,
                    titel=titel,
                    text=absatztext,
                    quelle=satz.get("quelle", ""),
                    stand=stand,
                )
            )
    return einheiten
