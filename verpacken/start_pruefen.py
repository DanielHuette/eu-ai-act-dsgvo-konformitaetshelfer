"""Prüft, dass das gebaute Paket wirklich startet und die Fragefolge zeigt.

Ein Paket, das sich bauen lässt, muss sich noch lange nicht starten lassen.
Beim ersten Bau fehlten die Datenordner im Paket: das Programm startete,
meldete "Regeldatei fehlt" und war nutzlos. Gefunden hat das niemand beim
Bauen — nur beim Starten. Darum startet der Prüflauf das fertige Paket und
sieht nach, ob die Oberfläche antwortet.
"""

from __future__ import annotations

import subprocess  # nosec B404
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]


def programmdatei() -> Path:
    kandidaten = [
        WURZEL / "dist" / "Konformitaetshelfer" / "Konformitaetshelfer",
        WURZEL / "dist" / "Konformitaetshelfer" / "Konformitaetshelfer.exe",
        WURZEL / "dist" / "Konformitaetshelfer.app" / "Contents" / "MacOS" / "Konformitaetshelfer",
    ]
    for k in kandidaten:
        if k.exists():
            return k
    raise SystemExit(
        "Kein gebautes Programm gefunden. Gesucht in:\n  " + "\n  ".join(str(k) for k in kandidaten)
    )


def holen(adresse: str, versuche: int = 90) -> tuple[int, bytes]:
    for _ in range(versuche):
        try:
            with urllib.request.urlopen(adresse, timeout=2) as antwort:  # nosec B310
                return antwort.status, antwort.read()
        except (urllib.error.URLError, OSError):
            time.sleep(0.4)
    return 0, b""


def main() -> int:
    programm = programmdatei()
    print("Starte", programm)
    lauf = subprocess.Popen(  # nosec B603
        [str(programm)],
        cwd=str(programm.parent),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        gefunden = 0
        for anschluss in range(8713, 8725):
            stand, inhalt = holen(f"http://127.0.0.1:{anschluss}/einstufung/", versuche=12)
            if stand != 200:
                continue
            gefunden = anschluss
            if b"Einstufung" not in inhalt:
                print("Die Startseite antwortet, zeigt aber nicht die Fragefolge.")
                return 1
            stand, daten = holen(f"http://127.0.0.1:{anschluss}/einstufung/fragefolge.json", 8)
            if stand != 200 or len(daten) < 100_000:
                print(f"Die Fragedaten fehlen oder sind zu klein: {stand}, {len(daten)} Zeichen")
                return 1
            print(
                f"Das Paket läuft auf Anschluss {anschluss}, "
                f"die Fragefolge ist da ({len(daten) // 1024} KB)."
            )
            break
        if not gefunden:
            print("Das gebaute Programm hat auf keinem Anschluss geantwortet.")
            if lauf.stdout:
                print(lauf.stdout.read()[-2000:])
            return 1
    finally:
        lauf.terminate()
        try:
            lauf.wait(timeout=10)
        except subprocess.TimeoutExpired:
            lauf.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
