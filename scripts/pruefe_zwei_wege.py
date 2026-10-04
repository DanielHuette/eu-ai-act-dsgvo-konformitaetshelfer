"""Prüft, dass der Durchlauf in Python und im Browser dasselbe tut.

Die Einstufung läuft an zwei Orten: in src/helfer/einstufung/fragefolge.py für
das installierte Programm und in web/durchlauf.js für die Webseite. Die Daten
sind dieselben, die Ablauflogik steht zweimal da — und zwei Fassungen derselben
Logik laufen auseinander. Beim Bau dieses Durchlaufs haben Fragefolge und
Auswertung genau das getan und dreissig von 217 amtlichen Beispielen gekostet.

Darum fährt dieses Werkzeug beide Fassungen mit denselben Antworten und
vergleicht Schritt für Schritt: dieselbe Frage in derselben Reihenfolge,
dieselbe Gruppe auf demselben Blatt, derselbe Befund am Ende. Weicht etwas ab,
schlägt der Prüflauf fehl und nennt die erste Stelle.

Die Antwortmuster werden gewürfelt, mit festem Startwert — so ist jeder Lauf
derselbe und trotzdem breit genug, um die Wege wirklich abzudecken.
"""

from __future__ import annotations

import argparse
import json
import random
import subprocess  # nosec B404
import sys
import tempfile
from pathlib import Path

WURZEL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WURZEL / "src"))

from helfer.einstufung.fragefolge import TRIFFT_NICHT_ZU, Durchlauf  # noqa: E402

JS_TREIBER = """
import {{Durchlauf}} from "{js}";
import {{readFileSync}} from "fs";
const daten = JSON.parse(readFileSync("{json}", "utf8"));
const muster = JSON.parse(readFileSync("{muster}", "utf8"));
const aus = [];
for (const m of muster) {{
  const d = new Durchlauf(daten);
  const a = {{}};
  const spur = [];
  let schutz = 0;
  while (schutz++ < 400) {{
    const g = d.naechsteGruppe(a);
    if (!g.length) break;
    spur.push(g.map((f) => f.kennung));
    for (const f of g) a[f.kennung] = m[f.kennung] === undefined ? false : m[f.kennung];
  }}
  const e = d.ergebnis(a);
  aus.push({{spur, klasse: e.klasse,
             fundstellen: e.getroffene_punkte.map((p) => p.fundstelle),
             filter: e.filter_greift}});
}}
process.stdout.write(JSON.stringify(aus));
"""


def wuerfeln(d: Durchlauf, zufall: random.Random) -> dict[str, object]:
    """Ein Antwortmuster für alle Fragen, die es gibt."""
    alle = [f.kennung for f in d.vorfragen]
    alle += [f.kennung for f in d.bereichsfragen]
    alle += [p.hauptfrage.kennung for p in d.punkte]
    alle += [f.kennung for p in d.punkte for f in p.folgefragen]
    alle += [f.kennung for f in d.filterfragen]
    if d.profilingfrage:
        alle.append(d.profilingfrage.kennung)
    if d.anhang_i_tor:
        alle.append(d.anhang_i_tor.kennung)
    alle += [f.kennung for f in d.anhang_i_gattungen]
    alle += [f.kennung for f in d.anhang_i_fragen.values()]
    muster: dict[str, object] = {}
    for k in alle:
        w = zufall.random()
        muster[k] = True if w < 0.35 else (False if w < 0.85 else TRIFFT_NICHT_ZU)
    # Ohne KI-System endet der Durchlauf sofort — das ist ein Fall, aber nicht
    # jeder Lauf soll so ausgehen.
    if d.vorfragen:
        muster[d.vorfragen[0].kennung] = zufall.random() > 0.08
    return muster


def python_lauf(d: Durchlauf, muster: dict[str, object]) -> dict:
    a: dict[str, object] = {}
    spur: list[list[str]] = []
    schutz = 0
    while schutz < 400:
        schutz += 1
        g = d.naechste_gruppe(a)
        if not g:
            break
        spur.append([f.kennung for f in g])
        for f in g:
            a[f.kennung] = muster.get(f.kennung, False)
    e = d.ergebnis(a)
    return {
        "spur": spur,
        "klasse": e.klasse,
        "fundstellen": list(e.fundstellen),
        "filter": e.filter_greift,
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--laeufe", type=int, default=200)
    p.add_argument("--startwert", type=int, default=20261004)
    a = p.parse_args(argv)

    d = Durchlauf.laden()
    zufall = random.Random(a.startwert)  # nosec B311
    muster = [wuerfeln(d, zufall) for _ in range(a.laeufe)]

    mit = tempfile.TemporaryDirectory()
    ordner = Path(mit.name)
    (ordner / "muster.json").write_text(json.dumps(muster), encoding="utf-8")
    treiber = ordner / "treiber.mjs"
    treiber.write_text(
        JS_TREIBER.format(
            js=(WURZEL / "web" / "durchlauf.js").as_uri(),
            json=WURZEL / "web" / "fragefolge.json",
            muster=ordner / "muster.json",
        ),
        encoding="utf-8",
    )
    lauf = subprocess.run(  # nosec B603 B607
        ["node", str(treiber)], capture_output=True, text=True, cwd=str(WURZEL)
    )
    if lauf.returncode != 0:
        print("Der Browserweg liess sich nicht ausführen:\n" + lauf.stderr[-2000:])
        return 2
    js = json.loads(lauf.stdout)

    fehler = 0
    for i, m in enumerate(muster):
        py = python_lauf(d, m)
        if py == js[i]:
            continue
        fehler += 1
        if fehler <= 3:
            print(f"\n--- Lauf {i}: Python und Browser weichen ab ---")
            if py["spur"] != js[i]["spur"]:
                for s, (x, y) in enumerate(zip(py["spur"], js[i]["spur"], strict=False)):
                    if x != y:
                        print(f"  Schritt {s + 1} unterschiedlich:")
                        print(f"    Python : {x[:6]}")
                        print(f"    Browser: {y[:6]}")
                        break
                else:
                    print(f"  Schrittzahl: Python {len(py['spur'])}, Browser {len(js[i]['spur'])}")
                    k = min(len(py["spur"]), len(js[i]["spur"]))
                    laenger = py if len(py["spur"]) > k else js[i]
                    print(f"    zusätzlicher Schritt: {laenger['spur'][k][:6]}")
            for feld in ("klasse", "fundstellen", "filter"):
                if py[feld] != js[i][feld]:
                    print(f"  {feld}: Python {py[feld]!r}, Browser {js[i][feld]!r}")

    print(f"\n{a.laeufe - fehler} von {a.laeufe} Läufen gleich.")
    return 1 if fehler else 0


if __name__ == "__main__":
    raise SystemExit(main())
