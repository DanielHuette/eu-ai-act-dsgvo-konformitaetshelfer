"""Macht aus den Fragefolge-Dateien eine einzige JSON-Datei für den Browser.

Warum das so gebaut ist: die Einstufung muss auf der Webseite und im
installierten Programm dasselbe ergeben. Zwei getrennte Fassungen desselben
Regelwerks laufen auseinander — genau dieser Fehler hat beim Bau des
Durchlaufs dreissig von 217 amtlichen Beispielen gekostet, weil Fragelogik und
Auswertung nicht deckungsgleich waren.

Darum gibt es EINE Datenquelle: daten/regeln/fragefolge/*.yaml samt
fragefolge-aufbau.yaml. Dieses Werkzeug schreibt sie in eine Datei, die der
Browser lädt. Die Prüfung vergleicht am Ende beide Wege Antwort für Antwort an
denselben amtlichen Beispielen.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helfer.einstufung.fragefolge import Durchlauf


def ausgeben(d: Durchlauf) -> dict:
    def frage(f) -> dict:
        return {
            "kennung": f.kennung,
            "text": f.text,
            "beleg": f.beleg,
            "stufe": f.stufe,
            "fundstelle": f.fundstelle,
            "titel": f.titel,
            "bei_ja": f.bei_ja,
            "bei_nein": f.bei_nein,
            "wirkung": f.wirkung,
        }

    return {
        "stand": d.aufbau.get("stand", ""),
        "quellen": list(d.quellen),
        "aufbau": d.aufbau,
        "vorfragen": [frage(f) for f in d.vorfragen],
        "bereichsfragen": [frage(f) for f in d.bereichsfragen],
        "hinweise": [frage(f) for f in d.hinweise],
        "punkte": [
            {
                "fundstelle": p.fundstelle,
                "bereich": p.bereich,
                "titel": p.titel,
                "ist_bereichstor": p.ist_bereichstor,
                "hauptfrage": frage(p.hauptfrage),
                "folgefragen": [frage(f) for f in p.folgefragen],
                "erfasst": [dict(x) for x in p.erfasst],
                "nicht_erfasst": [dict(x) for x in p.nicht_erfasst],
                "beispiele": [dict(x) for x in p.beispiele],
            }
            for p in d.punkte
        ],
        "filterfragen": [frage(f) for f in d.filterfragen],
        "profilingfrage": frage(d.profilingfrage) if d.profilingfrage else None,
        "anhang_i": {
            "tor": frage(d.anhang_i_tor) if d.anhang_i_tor else None,
            "gattungen": [frage(f) for f in d.anhang_i_gattungen],
            "fragen": {k: frage(f) for k, f in d.anhang_i_fragen.items()},
            "bedingungen": [dict(b) for b in d.anhang_i_bedingungen],
        },
        "zahlen": d.zahlen(),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--ziel", default="daten/aufbereitet/fragefolge.json")
    a = p.parse_args(argv)
    d = Durchlauf.laden()
    inhalt = ausgeben(d)
    ziel = Path(a.ziel)
    ziel.parent.mkdir(parents=True, exist_ok=True)
    ziel.write_text(json.dumps(inhalt, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(
        "%s geschrieben — %d Punkte, %d Fragen, %d Beispiele, %.0f KB"
        % (
            ziel,
            len(inhalt["punkte"]),
            inhalt["zahlen"]["fragen"],
            inhalt["zahlen"]["beispiele"],
            ziel.stat().st_size / 1024,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
