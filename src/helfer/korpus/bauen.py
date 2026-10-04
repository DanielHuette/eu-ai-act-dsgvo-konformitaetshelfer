"""Baut aus den Rohquellen den Korpus — eine Datei, die alles trägt.

Der Korpus ist eine JSONL-Datei: eine Zeile je Einheit. Diese Form ist mit
Absicht einfach gewählt — sie ist im Git lesbar, lässt sich zeilenweise prüfen,
und jedes Werkzeug kann sie zeilenweise ohne Python einlesen.

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

from helfer import orte
from helfer.korpus.deutsche_quellen import artikeldateien, bdsg
from helfer.korpus.eurlex import aus_datei as eurlex_zerlegen
from helfer.modell import Einheit, Einheitsart, Rechtsakt

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

WURZEL = orte.wurzel()
ROH = orte.roh()
AUFBEREITET = orte.aufbereitet()
KORPUS = AUFBEREITET / "korpus.jsonl"
BEFUND = AUFBEREITET / "korpus_befund.json"

#: Die amtlichen Volltexte, geholt von scripts/holen_amtsblatt.py aus Cellar,
#: dem Dokumentenspeicher des Amtes für Veröffentlichungen. Als Quelle genannt
#: wird die Fundstelle im Amtsblatt, nicht die Abrufadresse: wer die Angabe
#: prüfen will, schlägt im Amtsblatt nach, nicht in einem Dienst.
QUELLEN_AMTSBLATT = {
    "kivo_amtsblatt_de.xhtml": (
        Rechtsakt.KI_VO,
        "Verordnung (EU) 2024/1689, ABl. L vom 12.7.2024",
        1_000_000,
    ),
    "dsgvo_amtsblatt_de.xhtml": (
        Rechtsakt.DSGVO,
        "Verordnung (EU) 2016/679, ABl. L 119 vom 4.5.2016, S. 1",
        700_000,
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

    for name, (rechtsakt, adresse, mindestens) in QUELLEN_AMTSBLATT.items():
        pfad = ROH / name
        if not pfad.exists() or pfad.stat().st_size < mindestens:
            befund["warnungen"].append(
                f"AMTLICHER VOLLTEXT FEHLT: {name} — es wird die artikelweise "
                "Fassung aus zweiter Quelle genutzt. Sie ist unvollständig: "
                "beim Vergleich am 04.10.2026 wichen 51 Prozent der Einheiten "
                "ab, Artikel 13 DSGVO hatte 909 statt 3374 Zeichen. "
                "Erst holen: python scripts/holen_amtsblatt.py"
            )
            continue
        zerlegung = eurlex_zerlegen(pfad, rechtsakt, quelle=adresse)
        einheiten.extend(zerlegung.einheiten)
        befund["quellen"][name] = zerlegung.befund
        befund["warnungen"].extend(f"{name}: {w}" for w in zerlegung.warnungen)

    vorhanden = {e.kennung for e in einheiten}

    # Die artikelweise Fassung aus zweiter Quelle springt nur ein, wenn der
    # amtliche Volltext für diesen Rechtsakt ganz fehlt. Sie als Lückenfüller
    # danebenzulegen war falsch: sie zählt die Begriffsbestimmungen als
    # "Absatz 14", der amtliche Text als "Nummer 14" — derselbe Inhalt landete
    # zweimal im Bestand unter zwei Kennungen, und die Suche lieferte ihn
    # doppelt. Entweder amtlich oder Rückfall, nicht beides gemischt.
    amtlich = {e.rechtsakt for e in einheiten}
    for ordner, rechtsakt in ((ROH / "kivo", Rechtsakt.KI_VO), (ROH / "dsgvo", Rechtsakt.DSGVO)):
        if rechtsakt in amtlich:
            continue
        ergaenzt = [e for e in artikeldateien(ordner, rechtsakt) if e.kennung not in vorhanden]
        einheiten.extend(ergaenzt)
        vorhanden.update(e.kennung for e in ergaenzt)
        if ergaenzt:
            befund["quellen"][ordner.name + " (Rückfall)"] = {"ergänzt": len(ergaenzt)}

    bdsg_einheiten = bdsg(ROH / "bdsg.html")
    einheiten.extend(bdsg_einheiten)
    befund["quellen"]["bdsg.html"] = {"einheiten": len(bdsg_einheiten)}

    faelle = aus_faellen(orte.faelle())
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
