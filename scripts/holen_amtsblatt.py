"""Holt die amtlichen Volltexte aus dem Amtsblatt der Europäischen Union.

Nicht über die Webseite eur-lex.europa.eu: die steht hinter einer Firewall,
die einen Aufruf ohne vollständigen Browser-Kopf mit HTTP 202 und null Bytes
beantwortet und bei Wiederholung ein Captcha ausliefert — ein Hindernis, das
sich nicht sauber umgehen lässt und auch nicht umgangen werden soll.

Stattdessen über **Cellar**, den Dokumentenspeicher des Amtes für
Veröffentlichungen. Das ist dieselbe Quelle, die auch die Webseite bedient,
nur ohne Firewall davor: man nennt die Cellar-Kennung des Rechtsakts und die
gewünschte Darstellung, und bekommt den Text, wie er im Amtsblatt steht.

Die Cellar-Kennung lässt sich aus der CELEX-Nummer auflösen; sie steht hier
fest, damit der Lauf nachvollziehbar bleibt und nicht von einer zweiten
Abfrage abhängt.

Aufruf:
    python scripts/holen_amtsblatt.py
    python scripts/holen_amtsblatt.py --neu    # auch holen, was schon daliegt
"""

from __future__ import annotations

import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "daten" / "roh"

#: Was geholt wird. Die Cellar-Kennung ist die des *Werks*; Cellar liefert
#: dazu die Fassung in der Sprache, die der Kopf "Accept-Language" nennt.
RECHTSAKTE = {
    "kivo_amtsblatt_de.xhtml": (
        "dc8116a1-3fe6-11ef-865a-01aa75ed71a1",
        "Verordnung (EU) 2024/1689 — KI-Verordnung",
        1_200_000,
    ),
    "dsgvo_amtsblatt_de.xhtml": (
        "3e485e15-11bd-11e6-ba9a-01aa75ed71a1",
        "Verordnung (EU) 2016/679 — Datenschutz-Grundverordnung",
        800_000,
    ),
}

CELLAR = "http://publications.europa.eu/resource/cellar/%s"
KOPF = {
    # Diese Darstellung ist der aufbereitete Volltext mit den id-Ankern, an
    # denen der Zerleger die Artikel, Absätze und Anhänge trennt.
    "Accept": "application/xhtml+xml",
    "Accept-Language": "deu",
}


def holen(kennung: str, ziel: Path, mindestens: int, versuche: int = 3) -> bool:
    """Holt einen Rechtsakt und legt ihn ab — nur, wenn er vollständig aussieht."""
    for versuch in range(1, versuche + 1):
        try:
            anfrage = urllib.request.Request(CELLAR % kennung, headers=KOPF)
            with urllib.request.urlopen(  # nosec B310
                anfrage, timeout=180
            ) as antwort:
                daten = antwort.read()
        except (urllib.error.URLError, OSError) as fehler:
            print(f"    Versuch {versuch:d} fehlgeschlagen: {fehler}")
            time.sleep(3 * versuch)
            continue

        # Ein zu kurzer Text ist kein Text, sondern eine Fehlerseite. Lieber
        # nichts ablegen als etwas Unvollständiges, das später als Rechtstext
        # durchgeht.
        if len(daten) < mindestens:
            print(
                f"    Versuch {versuch:d}: nur {len(daten):d} Bytes, erwartet "
                f"mindestens {mindestens:d} — wird verworfen"
            )
            time.sleep(3 * versuch)
            continue

        ziel.write_bytes(daten)
        print(f"    {len(daten) / 1024:.0f} KB abgelegt")
        return True
    return False


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument("--neu", action="store_true", help="auch holen, was schon vorliegt")
    args = zerleger.parse_args(argv)

    ZIEL.mkdir(parents=True, exist_ok=True)
    offen = 0
    for name, (kennung, bezeichnung, mindestens) in RECHTSAKTE.items():
        pfad = ZIEL / name
        print(bezeichnung)
        if pfad.exists() and not args.neu:
            print(f"    liegt schon vor ({pfad.stat().st_size / 1024:.0f} KB)")
            continue
        if not holen(kennung, pfad, mindestens):
            print("    NICHT GEHOLT")
            offen += 1

    if offen:
        print(f"\n{offen:d} Rechtsakte fehlen. Ohne sie ist der Korpus unvollständig.")
    return 1 if offen else 0


if __name__ == "__main__":
    sys.exit(main())
