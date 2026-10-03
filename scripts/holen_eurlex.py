"""Holt die amtlichen Volltexte aus EUR-Lex.

EUR-Lex antwortet nur dann mit dem Volltext, wenn die Anfrage einen
vollstaendigen Browser-Kopf traegt - mit unvollstaendigem Kopf kommt HTTP 202
und ein leerer Koerper zurueck. Diese Kopfzeilen sind deshalb kein Beiwerk,
sondern Voraussetzung. Gebraucht werden nur vier Dokumente: ein Volltext
enthaelt alle Artikel, Anhaenge und Erwaegungsgruende.

Aufruf:
    python scripts/holen_eurlex.py

Ergebnis: daten/roh/eurlex/<kennung>.html
Protokoll: daten/roh/eurlex/_holen.log
"""

from __future__ import annotations

import time
import urllib.error
import urllib.request
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "daten" / "roh" / "eurlex"

#: Ohne diese Kopfzeilen liefert EUR-Lex einen leeren Koerper.
KOPF = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "de-DE,de;q=0.9,en-US;q=0.8,en;q=0.7",
    "Accept-Encoding": "identity",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
}

MINDESTGROESSE = 100_000
VERSUCHE = 6
PAUSE = 25

DOKUMENTE = {
    "ki-vo-de": ("DE", "32024R1689"),
    "dsgvo-de": ("DE", "32016R0679"),
    "ki-vo-en": ("EN", "32024R1689"),
    "dsgvo-en": ("EN", "32016R0679"),
}

protokoll: list[str] = []


def _nur_https(adresse: str) -> str:
    """Lässt nur https-Adressen durch — und gibt sie unverändert zurück.

    ``urllib.request.urlopen`` nimmt auch ``file://`` und ``ftp://``. Die
    Adressen hier stehen fest im Quelltext, aber geprüft wird trotzdem: eine
    Zeichenkette, die in einen Netzaufruf geht, gehört geprüft, bevor sie
    hineingeht — und die Prüfung bleibt richtig, wenn die Adressen später
    einmal aus einer Datei kommen.
    """
    if not adresse.startswith("https://"):
        raise ValueError(f"Nur https ist erlaubt, bekommen: {adresse!r}")
    return adresse


def sagen(text: str) -> None:
    protokoll.append(text)
    (ZIEL / "_holen.log").write_text("\n".join(protokoll) + "\n", encoding="utf-8")
    print(text, flush=True)


def adresse(sprache: str, celex: str) -> str:
    return f"https://eur-lex.europa.eu/legal-content/{sprache}/TXT/HTML/?uri=CELEX:{celex}"


def holen(ziel: Path, sprache: str, celex: str) -> bool:
    for versuch in range(VERSUCHE):
        try:
            req = urllib.request.Request(_nur_https(adresse)(sprache, celex), headers=KOPF)
            with urllib.request.urlopen(
                req,  # nosec B310
                timeout=180,
            ) as antwort:
                daten = antwort.read()
            if len(daten) >= MINDESTGROESSE:
                ziel.write_bytes(daten)
                sagen(f"{ziel.stem}: {len(daten):d} Bytes (Versuch {versuch + 1:d})")
                return True
            sagen(
                f"{ziel.stem}: Versuch {versuch + 1:d} gab nur "
                f"{len(daten):d} Bytes - EUR-Lex bremst, warte"
            )
        except urllib.error.URLError as fehler:
            sagen(f"{ziel.stem}: Versuch {versuch + 1:d} {type(fehler).__name__}")
        except Exception as fehler:
            sagen(f"{ziel.stem}: Versuch {versuch + 1:d} {type(fehler).__name__}")
        time.sleep(PAUSE)
    sagen(f"{ziel.stem}: NICHT GEHOLT")
    return False


def main() -> int:
    ZIEL.mkdir(parents=True, exist_ok=True)
    sagen("HOLEN EUR-LEX - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    fehlend = []
    for kennung, (sprache, celex) in DOKUMENTE.items():
        ziel = ZIEL / (f"{kennung}.html")
        if ziel.exists() and ziel.stat().st_size >= MINDESTGROESSE:
            sagen(f"{kennung}: liegt schon vor ({ziel.stat().st_size:d} Bytes)")
            continue
        if not holen(ziel, sprache, celex):
            fehlend.append(kennung)
        time.sleep(PAUSE)
    if fehlend:
        sagen("FEHLEND: {}".format(", ".join(fehlend)))
    sagen("FERTIG")
    return 1 if fehlend else 0


if __name__ == "__main__":
    raise SystemExit(main())
