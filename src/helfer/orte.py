"""Wo die Daten liegen — im Quellbaum und im fertigen Paket.

Im Quellbaum liegt alles unter der Projektwurzel: daten/regeln, daten/faelle,
daten/aufbereitet. Im gebündelten Paket legt der Packer dieselben Ordner
woanders ab, und ein Pfad, der von der Lage der Programmdatei ausgeht, zeigt
dann ins Leere. Gemessen hiess das beim ersten Paketbau: das Programm startete,
meldete "Regeldatei fehlt" und war nutzlos — die Dateien waren da, nur an einer
anderen Stelle.

Darum beantwortet diese eine Stelle die Frage, und alle anderen fragen hier.
Die Reihenfolge der Suche:

1. HELFER_WURZEL aus der Umgebung, falls jemand die Daten bewusst woanders
   hinlegt — etwa ein Betreiber, der das Regelwerk selbst pflegt.
2. Der Ordner, in den der Packer die Daten geschrieben hat (sys._MEIPASS).
3. Die Projektwurzel, wenn aus dem Quellbaum gearbeitet wird.
"""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from pathlib import Path


@lru_cache(maxsize=1)
def wurzel() -> Path:
    """Der Ordner, unter dem "daten" zu finden ist."""
    gewuenscht = os.environ.get("HELFER_WURZEL")
    if gewuenscht and (Path(gewuenscht) / "daten").is_dir():
        return Path(gewuenscht)

    gebuendelt = getattr(sys, "_MEIPASS", None)
    if gebuendelt and (Path(gebuendelt) / "daten").is_dir():
        return Path(gebuendelt)

    quellbaum = Path(__file__).resolve().parents[2]
    if (quellbaum / "daten").is_dir():
        return quellbaum

    # Nichts gefunden: die Projektwurzel zurückgeben, damit die Fehlermeldung
    # einen Pfad nennt, den jemand nachsehen kann.
    return quellbaum


def daten() -> Path:
    return wurzel() / "daten"


def regeln() -> Path:
    return daten() / "regeln"


def faelle() -> Path:
    return daten() / "faelle"


def aufbereitet() -> Path:
    return daten() / "aufbereitet"


def roh() -> Path:
    return daten() / "roh"
