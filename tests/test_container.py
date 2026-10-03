"""Prüft das Containerabbild — wird übersprungen, wo kein Docker ist.

Was hier geprüft wird, lässt sich mit keinem anderen Mittel prüfen:

* Der Dienst läuft **ohne Netz**. Das ist der Kern des Versprechens: das
  Rechtswissen liegt im Abbild, nichts wird nachgeladen, keine Frage verlässt
  den Rechner.
* Er läuft **ohne Verwalterrechte**. Ein Fehler im Dienst wirkt dann nicht auf
  das ganze System.
* Die Rechtstexte sind **mitgeliefert**, nicht erst zu holen.

Gebaut wird mit ``MIT_SUCHMODELL=0``: ohne das Einbettungsmodell ist das Abbild
rund 400 Megabyte statt 8 Gigabyte und in einer Minute gebaut. Geprüft wird
damit die Mechanik, nicht die Suchgüte — die prüft ``test_suche.py``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
MARKE = "helfer-pruefung:ohne-modell"

docker = shutil.which("docker")
pytestmark = [
    pytest.mark.skipif(not docker, reason="Docker ist nicht vorhanden"),
    pytest.mark.container,
]


def _laufen(*argumente: str, zeit: int = 900) -> subprocess.CompletedProcess:
    return subprocess.run([docker, *argumente], capture_output=True, text=True, timeout=zeit)


@pytest.fixture(scope="module")
def abbild() -> str:
    """Baut das Abbild einmal für alle Prüfungen dieses Moduls."""
    befehl = ["build", "--build-arg", "MIT_SUCHMODELL=0", "-t", MARKE, str(WURZEL)]
    # Im abgeschirmten Bauraum geht das Netz nur über den Vermittler.
    for name in ("HTTPS_PROXY", "HTTP_PROXY", "PIP_INDEX_URL"):
        if os.environ.get(name):
            befehl[1:1] = ["--build-arg", f"{name}={os.environ[name]}"]
    if os.environ.get("HTTPS_PROXY"):
        befehl[1:1] = ["--network=host"]
    fertig = _laufen(*befehl)
    if fertig.returncode != 0:
        pytest.skip(f"Abbild lässt sich hier nicht bauen:\n{fertig.stderr[-900:]}")
    return MARKE


@pytest.fixture(scope="module")
def behaelter(abbild) -> str:
    """Startet den Dienst ohne Netz und wartet, bis er antwortet."""
    name = f"helfer-pruefung-{uuid.uuid4().hex[:8]}"
    fertig = _laufen("run", "-d", "--name", name, "--network=none", abbild)
    if fertig.returncode != 0:
        pytest.skip(f"Behälter startet nicht: {fertig.stderr[-400:]}")
    try:
        for _ in range(40):
            if (
                _innen(
                    name,
                    "import urllib.request;"
                    "urllib.request.urlopen("
                    "'http://127.0.0.1:8000/gesundheit', timeout=5)",
                ).returncode
                == 0
            ):
                break
            time.sleep(2)
        else:
            protokoll = _laufen("logs", name).stdout[-900:]
            pytest.fail(f"Dienst im Behälter antwortet nicht:\n{protokoll}")
        yield name
    finally:
        _laufen("rm", "-f", name, zeit=60)


def _innen(name: str, programm: str) -> subprocess.CompletedProcess:
    return _laufen("exec", name, "python", "-c", programm, zeit=120)


def _abfragen(name: str, pfad: str, daten: dict | None = None) -> dict:
    """Fragt einen Pfad von innerhalb des Behälters ab."""
    programm = (
        "import json, urllib.request\n"
        f"daten = {daten!r}\n"
        f"ziel = 'http://127.0.0.1:8000{pfad}'\n"
        "if daten is None:\n"
        "    anfrage = urllib.request.Request(ziel)\n"
        "else:\n"
        "    anfrage = urllib.request.Request(\n"
        "        ziel, data=json.dumps(daten).encode(),\n"
        "        headers={'Content-Type': 'application/json'})\n"
        "with urllib.request.urlopen(anfrage, timeout=60) as a:\n"
        "    print(a.read().decode())\n"
    )
    fertig = _innen(name, programm)
    assert fertig.returncode == 0, fertig.stderr[-600:]
    return json.loads(fertig.stdout)


# ------------------------------------------------------------------ Rechte


def test_dienst_laeuft_ohne_verwalterrechte(behaelter):
    """Kein root: ein Fehler im Dienst darf nicht das System treffen."""
    fertig = _laufen("exec", behaelter, "id", "-u")
    assert fertig.stdout.strip() == "10001", fertig.stdout


def test_quelltext_gehoert_nicht_dem_dienstnutzer_zum_schreiben(behaelter):
    """Der Dienst soll seinen eigenen Quelltext nicht ändern können."""
    for ort in ("/app/src", "/app/daten", "/app/src/helfer/cli.py"):
        fertig = _innen(
            behaelter, f"import os,sys;sys.exit(0 if not os.access({ort!r}, os.W_OK) else 1)"
        )
        assert fertig.returncode == 0, f"für den Dienstnutzer schreibbar: {ort}"


def test_dienst_kann_den_eigenen_quelltext_nicht_ueberschreiben(behaelter):
    """Gegenprobe mit einem echten Schreibversuch, nicht nur mit den Rechten."""
    fertig = _innen(
        behaelter,
        "import sys\n"
        "try:\n"
        "    open('/app/src/helfer/cli.py', 'a').write('# ')\n"
        "    sys.exit(1)\n"
        "except OSError:\n"
        "    sys.exit(0)\n",
    )
    assert fertig.returncode == 0, "Der Dienst konnte seinen Quelltext ändern"


# -------------------------------------------------------------- ohne Netz


def test_dienst_antwortet_ohne_netz(behaelter):
    """Der Behälter läuft mit --network=none. Er muss trotzdem arbeiten."""
    satz = _abfragen(behaelter, "/gesundheit")
    assert satz["korpus_geladen"] is True
    assert satz["einheiten"] > 2000


def test_kein_netz_vorhanden(behaelter):
    """Gegenprobe: dass das Netz wirklich fehlt, nicht nur ungenutzt ist."""
    fertig = _innen(
        behaelter,
        "import socket,sys\n"
        "try:\n"
        "    socket.create_connection(('1.1.1.1', 53), timeout=4)\n"
        "    sys.exit(1)\n"
        "except OSError:\n"
        "    sys.exit(0)\n",
    )
    assert fertig.returncode == 0, "Der Behälter hat Netz — Prüfung wertlos"


def test_rechtstexte_liegen_im_abbild(behaelter):
    satz = _abfragen(behaelter, "/gesundheit")
    assert satz["einheiten"] > 2000
    assert satz["stand_korpus"]


# ------------------------------------------------------------- Arbeitsweise


def test_einstufung_im_behaelter(behaelter):
    satz = _abfragen(
        behaelter,
        "/api/einstufung",
        {
            "beschreibung": "Wir setzen ein Sprachmodell ein, um Bewerbungen "
            "vorzusortieren und eine Rangfolge zu erstellen.",
            "rollen": ["betreiber"],
        },
    )
    assert "hochrisiko_anhang_iii" in satz["einstufung"]["klassen"]
    assert satz["einstufung"]["pflichten"]


def test_oberflaeche_im_behaelter(behaelter):
    fertig = _innen(
        behaelter,
        "import urllib.request\n"
        "with urllib.request.urlopen("
        "'http://127.0.0.1:8000/', timeout=30) as a:\n"
        "    print(len(a.read().decode()))\n",
    )
    assert fertig.returncode == 0
    assert int(fertig.stdout.strip()) > 5_000


def test_kommandozeile_im_behaelter(behaelter):
    fertig = _laufen(
        "exec",
        behaelter,
        "python",
        "-m",
        "helfer.cli",
        "--json",
        "pruefen",
        "Wir sortieren Bewerbungen vor.",
        zeit=180,
    )
    assert fertig.returncode == 0, fertig.stderr[-500:]
    satz = json.loads(fertig.stdout)
    assert satz["klassen"]


def test_eingeschraenkter_zustand_wird_gemeldet(behaelter):
    """Ohne Suchmodell ist der Dienst schlechter — das muss er sagen."""
    satz = _abfragen(behaelter, "/gesundheit")
    if satz["einbettungsmodell"].startswith("streuwerk"):
        assert satz["zustand"] == "eingeschraenkt"
        assert satz["warnungen"]
