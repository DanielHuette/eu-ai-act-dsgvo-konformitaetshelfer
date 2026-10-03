"""Gemeinsame Vorbereitung für alle Prüfungen."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL / "src"))


@pytest.fixture(scope="session")
def wurzel() -> Path:
    return WURZEL


@pytest.fixture(scope="session")
def korpus():
    """Der aufbereitete Korpus — einmal für alle Prüfungen geladen."""
    from helfer.korpus.bauen import laden

    einheiten = laden()
    if not einheiten:
        pytest.skip("Kein aufbereiteter Korpus vorhanden (python -m helfer.korpus.bauen)")
    return einheiten


@pytest.fixture(scope="session")
def kennungen(korpus) -> set[str]:
    return {e.kennung for e in korpus}


@pytest.fixture(scope="session")
def pruefer():
    from helfer.einstufung.pruefer import Pruefer

    return Pruefer()


@pytest.fixture(scope="session")
def faelle() -> list[dict]:
    """Alle Anwendungsfälle aus daten/faelle, mit Herkunftsdatei."""
    import yaml

    gesammelt: list[dict] = []
    for datei in sorted((WURZEL / "daten" / "faelle").glob("*.yaml")):
        satz = yaml.safe_load(datei.read_text(encoding="utf-8")) or {}
        for fall in satz.get("faelle", []):
            fall = dict(fall)
            fall["_datei"] = datei.name
            gesammelt.append(fall)
    if not gesammelt:
        pytest.skip("Keine Anwendungsfälle gefunden")
    return gesammelt
