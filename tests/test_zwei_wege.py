"""Prüft, dass Webseite und Programm dieselbe Einstufung rechnen.

Die Einstufung läuft an zwei Orten: in ``src/helfer/einstufung/fragefolge.py``
für das installierte Programm und in ``web/durchlauf.js`` für die Webseite. Die
Daten sind dieselben, die Ablauflogik steht zweimal da — und zwei Fassungen
derselben Logik laufen auseinander. Beim Bau dieses Durchlaufs haben Fragefolge
und Auswertung genau das getan und dreissig von 217 amtlichen Beispielen
gekostet.

``scripts/pruefe_zwei_wege.py`` würfelt Antwortmuster mit festem Startwert und
fährt beide Fassungen damit: dieselbe Frage in derselben Reihenfolge, dieselbe
Gruppe auf demselben Blatt, derselbe Befund am Ende. Dieselbe Prüfung läuft im
Prüfstand und vor jedem Paketbau.

Nebenher prüft dieser Lauf etwas, das sonst niemand prüft: dass
``web/fragefolge.json`` zum Regelwerk passt. Der Browserweg rechnet mit dieser
Datei, der Python-Weg mit den YAML-Dateien. Wer eine Regel ändert und die Datei
nicht neu erzeugt, bekommt hier zwei verschiedene Ergebnisse — und nicht erst
dann, wenn ein Nutzer im Netz eine veraltete Auskunft bekommt.
"""

from __future__ import annotations

import shutil
import subprocess
import sys

import pytest

#: So viele Muster laufen auch im Prüfstand und vor jedem Paketbau.
LAEUFE = 400


@pytest.mark.skipif(shutil.which("node") is None, reason="Node ist nicht vorhanden")
def test_beide_wege_rechnen_gleich(wurzel) -> None:
    fertig = subprocess.run(
        [sys.executable, "scripts/pruefe_zwei_wege.py", "--laeufe", str(LAEUFE)],
        cwd=str(wurzel),
        capture_output=True,
        text=True,
        timeout=600,
    )
    ausgabe = fertig.stdout + fertig.stderr
    if fertig.returncode == 2:
        pytest.skip(f"Der Browserweg liess sich hier nicht ausführen:\n{ausgabe[-600:]}")
    assert fertig.returncode == 0, ausgabe[-2000:]
    assert f"{LAEUFE} von {LAEUFE} Läufen gleich" in ausgabe, ausgabe[-600:]
