"""Baut aus den Rohquellen den Korpus — eine Datei, die alles trägt.

Der Korpus ist eine JSONL-Datei: eine Zeile je Einheit. Diese Form ist mit
Absicht einfach gewählt — sie ist im Git lesbar, lässt sich zeilenweise prüfen,
und die Android-App kann sie ohne Python einlesen.

Quellen und ihre Rolle:

* ``eurlex/*.html``  — amtlicher Volltext aus dem Amtsblatt. Erste Wahl.
* ``dsgvo/**.json``  — artikelweise Fassung, Rückfall und Gegenprobe.
* ``kivo/**.json``   — artikelweise Fassung, Rückfall und Gegenprobe.
* ``bdsg.html``      — Bundesdatenschutzgesetz von gesetze-im-internet.de.
* ``faelle/*.yaml``  — die Anwendungsfälle mit Lernhinweis.

Aufruf:
    python -m helfer.korpus.bauen            # baut daten/aufbereitet/korpus.jsonl
    python -m helfer.korpus.bauen --pruefen   # prüft nur, schreibt nichts
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from collections import Counter
from datetime import date
from pathlib import Path

import yaml
from bs4 import XMLParsedAsHTMLWarning

from helfer.korpus.deutsche_quellen import artikeldateien, bdsg
from helfer.korpus.eurlex import aus_datei as eurlex_zerlegen
from helfer.modell import Einheit, Einheitsart, Rechtsakt

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

WURZEL = Path(__file__).resolve().parents[3]
ROH = WURZEL / "daten" / "roh"
AUFBEREITET = WURZEL / "daten" / "aufbereitet"
KORPUS = AUFBEREITET / "korpus.jsonl"
BEFUND = AUFBEREITET / "korpus_befund.json"

QUELLEN_EURLEX = {
    "ki-vo-de.html": (
        Rechtsakt.KI_VO,
        "https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:32024R1689",
    ),
    "dsgvo-de.html": (
        Rechtsakt.DSGVO,
        "https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:32016R0679",
    ),
}


def _saeubern(text: str) -> str:
    text = text.replace(" ", " ").replace("‑", "-")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ----------------------------------------------------------------- Einzelquellen


def aus_faellen(ordner: Path) -> list[Einheit]:
    """Liest die Anwendungsfälle ein - sie sind Teil des durchsuchbaren Bestands."""
    einheiten: list[Einheit] = []
    if not ordner.exists():
        return einheiten
    for datei in sorted(ordner.glob("*.yaml")):
        try:
            inhalt = yaml.safe_load(datei.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        for fall in inhalt.get("faelle", []):
            kennung = fall.get("kennung")
            if not kennung:
                continue
            teile = [
                "Anwendungsfall: {}".format(fall.get("titel", "")),
                "Ausgangslage: {}".format(fall.get("lage", "")),
                "Rolle: {}".format(fall.get("rolle", "")),
                "Einstufung: {}".format(fall.get("einstufung", "")),
                "Begründung: {}".format(fall.get("begruendung", "")),
            ]
            if fall.get("pflichten"):
                # Die Pflichten stehen je Fall als Zeilen oder als kleine
                # Sätze mit eigenen Feldern - beides wird zu Text.
                punkte = []
                for punkt in fall["pflichten"]:
                    if isinstance(punkt, str):
                        punkte.append(punkt)
                    elif isinstance(punkt, dict):
                        punkte.append(
                            " ".join(
                                str(wert)
                                for schluessel, wert in punkt.items()
                                if schluessel != "rechtsgrundlage" and wert
                            )
                        )
                teile.append("Zu tun: " + "; ".join(p for p in punkte if p))
            if fall.get("lernhinweis"):
                teile.append("Worauf es ankommt: {}".format(fall["lernhinweis"]))
            if fall.get("stolperstein"):
                teile.append("Häufiger Fehler: {}".format(fall["stolperstein"]))
            einheiten.append(
                Einheit(
                    kennung=f"fall/{kennung}",
                    rechtsakt=Rechtsakt.LEITLINIE,
                    art=Einheitsart.FALLBEISPIEL,
                    nummer=kennung,
                    absatz=None,
                    titel=fall.get("titel", kennung),
                    text=_saeubern("\n\n".join(t for t in teile if t.split(": ", 1)[-1])),
                    quelle=str(datei.relative_to(WURZEL)),
                    verweise=tuple(fall.get("rechtsgrundlage", [])),
                )
            )
    return einheiten


# ------------------------------------------------------------------------ Lauf


def sammeln() -> tuple[list[Einheit], dict]:
    einheiten: list[Einheit] = []
    befund: dict = {"quellen": {}, "warnungen": []}

    for name, (rechtsakt, adresse) in QUELLEN_EURLEX.items():
        pfad = ROH / "eurlex" / name
        if not pfad.exists() or pfad.stat().st_size < 100_000:
            befund["warnungen"].append(
                f"amtlicher Volltext fehlt: {name} - es wird die artikelweise Fassung genutzt"
            )
            continue
        zerlegung = eurlex_zerlegen(pfad, rechtsakt, quelle=adresse)
        einheiten.extend(zerlegung.einheiten)
        befund["quellen"][name] = zerlegung.befund
        befund["warnungen"].extend(f"{name}: {w}" for w in zerlegung.warnungen)

    vorhanden = {e.kennung for e in einheiten}

    # Artikelweise Fassungen füllen nur, was der amtliche Text nicht hergab.
    for ordner, rechtsakt in ((ROH / "kivo", Rechtsakt.KI_VO), (ROH / "dsgvo", Rechtsakt.DSGVO)):
        ergaenzt = [e for e in artikeldateien(ordner, rechtsakt) if e.kennung not in vorhanden]
        einheiten.extend(ergaenzt)
        vorhanden.update(e.kennung for e in ergaenzt)
        if ergaenzt:
            befund["quellen"][ordner.name + " (Rückfall)"] = {"ergänzt": len(ergaenzt)}

    bdsg_einheiten = bdsg(ROH / "bdsg.html")
    einheiten.extend(bdsg_einheiten)
    befund["quellen"]["bdsg.html"] = {"einheiten": len(bdsg_einheiten)}

    faelle = aus_faellen(WURZEL / "daten" / "faelle")
    einheiten.extend(faelle)
    befund["quellen"]["faelle"] = {"fallbeispiele": len(faelle)}

    zaehler = Counter(f"{e.rechtsakt.value}/{e.art.value}" for e in einheiten)
    befund["bestand"] = dict(sorted(zaehler.items()))
    befund["einheiten"] = len(einheiten)
    befund["zeichen"] = sum(len(e.text) for e in einheiten)
    befund["gebaut"] = date.today().isoformat()
    return einheiten, befund


def schreiben(einheiten: list[Einheit], befund: dict) -> None:
    AUFBEREITET.mkdir(parents=True, exist_ok=True)
    with KORPUS.open("w", encoding="utf-8") as datei:
        for einheit in sorted(einheiten, key=lambda e: e.kennung):
            datei.write(einheit.model_dump_json() + "\n")
    BEFUND.write_text(json.dumps(befund, ensure_ascii=False, indent=1), encoding="utf-8")


def laden() -> list[Einheit]:
    """Liest den gebauten Korpus ein."""
    if not KORPUS.exists():
        raise FileNotFoundError("Korpus fehlt. Erst bauen: python -m helfer.korpus.bauen")
    return [
        Einheit.model_validate_json(zeile)
        for zeile in KORPUS.read_text(encoding="utf-8").splitlines()
        if zeile.strip()
    ]


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(description="Baut den Rechtskorpus.")
    zerleger.add_argument(
        "--pruefen", action="store_true", help="nur prüfen und berichten, nichts schreiben"
    )
    args = zerleger.parse_args(argv)

    einheiten, befund = sammeln()
    print("Einheiten: %d, Zeichen: %d" % (befund["einheiten"], befund["zeichen"]))
    for name, zahlen in befund["quellen"].items():
        print("  %-28s %s" % (name, zahlen))
    print("Bestand nach Rechtsakt und Art:")
    for name, zahl in befund["bestand"].items():
        print("  %-34s %5d" % (name, zahl))
    for warnung in befund["warnungen"]:
        print(f"  WARNUNG: {warnung}")

    if args.pruefen:
        return 0
    schreiben(einheiten, befund)
    print(f"geschrieben: {KORPUS} ({KORPUS.stat().st_size / 1048576:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
