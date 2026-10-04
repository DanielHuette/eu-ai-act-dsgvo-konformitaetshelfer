"""Prüft, wo das Programm seine Daten sucht.

Eine Stelle beantwortet diese Frage für alle: ``src/helfer/orte.py``. Der Grund
steht im gebauten Paket. Dort legt der Packer die Datenordner woanders ab als
im Quellbaum, und ein Pfad, der von der Lage der Programmdatei ausgeht, zeigt
dann ins Leere. Gemessen hiess das beim ersten Paketbau: das Programm startete,
meldete "Regeldatei fehlt" und war nutzlos — die Dateien waren da, nur an einer
anderen Stelle.

Darum wird hier dreierlei geprüft: dass ``HELFER_WURZEL`` gilt, wenn jemand die
Daten bewusst woanders hinlegt; dass ein Ordner ohne ``daten`` nicht genommen
wird; und dass aus dem Quellbaum heraus das Regelwerk wirklich gefunden wird.
"""

from __future__ import annotations

import pytest

from helfer import orte


@pytest.fixture(autouse=True)
def _frisch_fragen():
    """``wurzel()`` merkt sich ihre Antwort — für jede Prüfung neu fragen."""
    orte.wurzel.cache_clear()
    yield
    orte.wurzel.cache_clear()


def test_aus_dem_quellbaum_wird_das_regelwerk_gefunden(wurzel) -> None:
    assert orte.wurzel() == wurzel
    assert (orte.regeln() / "fragefolge-aufbau.yaml").is_file()
    assert (orte.regeln() / "fragefolge").is_dir()
    assert orte.faelle().is_dir()


def test_jeder_ordner_liegt_unter_daten() -> None:
    for ordner in (orte.regeln(), orte.faelle(), orte.aufbereitet(), orte.roh()):
        assert ordner.parent == orte.daten()
    assert orte.daten().parent == orte.wurzel()


def test_helfer_wurzel_aus_der_umgebung_gilt(tmp_path, monkeypatch) -> None:
    """Ein Betreiber, der das Regelwerk selbst pflegt, legt es woanders ab."""
    (tmp_path / "daten" / "regeln").mkdir(parents=True)
    monkeypatch.setenv("HELFER_WURZEL", str(tmp_path))
    assert orte.wurzel() == tmp_path
    assert orte.regeln() == tmp_path / "daten" / "regeln"


def test_ein_ordner_ohne_daten_wird_nicht_genommen(tmp_path, monkeypatch, wurzel) -> None:
    """Sonst zeigte eine Fehlermeldung auf einen Ordner, in dem nichts liegt."""
    monkeypatch.setenv("HELFER_WURZEL", str(tmp_path / "gibt-es-nicht"))
    assert orte.wurzel() == wurzel


def test_das_gebuendelte_paket_wird_vor_dem_quellbaum_genommen(tmp_path, monkeypatch) -> None:
    """Im Paket steht der Datenordner unter ``sys._MEIPASS``.

    Ohne diese Reihenfolge nähme ein Paket, das zufällig neben einem Quellbaum
    liegt, dessen Daten — und der Nutzer bekäme eine andere Auskunft als die,
    die mit dem Paket ausgeliefert wurde.
    """
    (tmp_path / "daten" / "regeln").mkdir(parents=True)
    monkeypatch.delenv("HELFER_WURZEL", raising=False)
    monkeypatch.setattr(orte.sys, "_MEIPASS", str(tmp_path), raising=False)
    assert orte.wurzel() == tmp_path
