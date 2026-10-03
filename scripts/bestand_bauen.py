"""Baut den Suchbestand aus dem Korpus — einmalig, dann liegt er als Datei.

Das Einbetten von rund 2700 Rechtseinheiten dauert auf einem Hauptprozessor
einige Minuten. Deshalb wird es einmal gemacht und abgelegt; der Betrieb lädt
nur die Datei. Die Datei wandert mit ins Repository, damit das Werkzeug ohne
Rechenlauf startklar ist.

Aufruf:
    python scripts/bestand_bauen.py
    python scripts/bestand_bauen.py --modell intfloat/multilingual-e5-small
    python scripts/bestand_bauen.py --ersatz      # ohne Modell, nur für Tests

Protokoll: daten/aufbereitet/_bestand_lauf.log
"""

from __future__ import annotations

import argparse
import logging
import shutil
import time
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
import sys  # noqa: E402

sys.path.insert(0, str(WURZEL / "src"))

from helfer.korpus.bauen import laden  # noqa: E402
from helfer.suche.einbettung import STANDARD_MODELL, Streuwerk, waehlen  # noqa: E402
from helfer.suche.index import Suchbestand  # noqa: E402

ZIEL = WURZEL / "daten" / "aufbereitet" / "suchbestand"
PROTOKOLL = WURZEL / "daten" / "aufbereitet" / "_bestand_lauf.log"
#: Teilstücke des laufenden Rechenvorgangs. Bricht der Lauf ab, macht der
#: nächste hier weiter statt von vorn. Der Ordner wird nach dem Ablegen
#: gelöscht - er ist Baustelle, nicht Ergebnis.
ZWISCHENLAGER = WURZEL / "daten" / "aufbereitet" / "_bestand_teile"


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser()
    zerleger.add_argument("--modell", default=STANDARD_MODELL)
    zerleger.add_argument(
        "--ersatz", action="store_true", help="ohne Einbettungsmodell arbeiten (nur für Tests)"
    )
    zerleger.add_argument(
        "--von-vorn", action="store_true", help="Zwischenlager verwerfen und neu rechnen"
    )
    args = zerleger.parse_args(argv)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(PROTOKOLL, encoding="utf-8"), logging.StreamHandler()],
    )
    protokoll = logging.getLogger("bestand")

    beginn = time.time()
    einheiten = laden()
    protokoll.info("Korpus: %d Einheiten", len(einheiten))

    einbetter = Streuwerk() if args.ersatz else waehlen(args.modell)
    protokoll.info("Modell: %s mit %d Dimensionen", einbetter.name, einbetter.dimensionen)
    if isinstance(einbetter, Streuwerk) and not args.ersatz:
        protokoll.error(
            "Das gewünschte Modell fehlt — Abbruch, damit kein Bestand mit Ersatzqualität entsteht."
        )
        return 1

    if args.von_vorn and ZWISCHENLAGER.exists():
        shutil.rmtree(ZWISCHENLAGER)
        protokoll.info("Zwischenlager verworfen")

    bestand = Suchbestand(einheiten, einbetter)
    bestand.bauen(zwischenlager=ZWISCHENLAGER)
    bestand.ablegen(ZIEL)
    if ZWISCHENLAGER.exists():
        shutil.rmtree(ZWISCHENLAGER)
        protokoll.info("Zwischenlager aufgeräumt")

    dauer = time.time() - beginn
    protokoll.info("abgelegt in %s", ZIEL.parent)
    for datei in sorted(ZIEL.parent.glob("suchbestand.*")):
        protokoll.info("  %-28s %7.1f MB", datei.name, datei.stat().st_size / 1048576)
    protokoll.info("Dauer: %.0f s", dauer)

    # Gegenprobe: eine Frage, deren Antwort bekannt ist.
    probe = "Dürfen wir Bewerbungen mit einem Sprachmodell vorsortieren?"
    treffer = bestand.suchen(probe, anzahl=3, mit_neubewertung=False)
    protokoll.info("Probe %r", probe)
    for stelle in treffer:
        protokoll.info(
            "  %.4f %-34s %s",
            stelle.punktzahl,
            stelle.einheit.fundstelle,
            stelle.einheit.titel[:60],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
