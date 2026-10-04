"""Werkzeug für den Prüfstand: den Durchlauf schrittweise mit Antworten füttern.

Wird gebraucht, um die amtlichen Beispiele der Leitlinien gegen den Durchlauf
zu messen. Ein Leser des Beispielfalls beantwortet die Fragen so, wie ein
Mitarbeiter sie über sein eigenes System beantworten würde; dieses Werkzeug
gibt dafür immer die nächsten offenen Fragen heraus und nimmt die Antworten
entgegen.

  python scripts/fragen_beantworten.py --antworten a.json
      gibt die nächsten offenen Fragen als JSON aus

Zugelassene Antworten in der JSON-Datei: true, false und "trifft_nicht_zu".
Die dritte lässt die Frage stehen, ohne zu entscheiden — für Fragen, die auf
das eigene System nicht passen. Ein Ausschluss greift nur auf true oder false.

  python scripts/fragen_beantworten.py --antworten a.json --ergebnis
      gibt den Befund aus, wenn keine Frage mehr offen ist
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from helfer.einstufung.fragefolge import TRIFFT_NICHT_ZU, Durchlauf


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--antworten", required=True, help="JSON-Datei mit den bisherigen Antworten")
    p.add_argument("--ergebnis", action="store_true", help="Befund ausgeben")
    a = p.parse_args(argv)

    pfad = Path(a.antworten)
    antworten = json.loads(pfad.read_text(encoding="utf-8")) if pfad.exists() else {}
    # Drei Antworten sind zugelassen: true, false und "trifft_nicht_zu".
    gesaeubert: dict[str, object] = {}
    for k, v in antworten.items():
        if v is None:
            continue
        if isinstance(v, str) and v.strip().lower() in (TRIFFT_NICHT_ZU, "trifft nicht zu", "?"):
            gesaeubert[k] = TRIFFT_NICHT_ZU
        else:
            gesaeubert[k] = bool(v)
    antworten = gesaeubert

    d = Durchlauf.laden()
    if a.ergebnis:
        e = d.ergebnis(antworten)
        print(
            json.dumps(
                {
                    "klasse": e.klasse,
                    "fundstellen": list(e.fundstellen),
                    "filter_greift": e.filter_greift,
                    "filter_grund": e.filter_grund,
                    "offene_punkte": list(e.offene_punkte),
                    "endtext": e.endtext,
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        return 0

    gruppe = d.naechste_gruppe(antworten)
    print(
        json.dumps(
            {
                "fertig": not gruppe,
                "fragen": [
                    {
                        "kennung": f.kennung,
                        "frage": f.text,
                        "stufe": f.stufe,
                        "fundstelle": f.fundstelle,
                        "beleg": f.beleg,
                    }
                    for f in gruppe
                ],
                "zugelassene_antworten": [True, False, TRIFFT_NICHT_ZU],
            },
            ensure_ascii=False,
            indent=1,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
