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


@pytest.fixture(autouse=True)
def _zweckweg_nur_in_der_langsamen_runde(request):
    """Schaltet den Zweckweg in der schnellen Prüfrunde ab.

    Der Zweckweg rechnet je Einstufung mit einem Kreuzbewerter und braucht dafür
    Sekunden. Die dreiunddreißig Einstufungsprüfungen prüfen aber den
    Entscheidungsbaum — Rollen, Merkmalsfilter, Ausnahmen, Pflichtenableitung —
    und die hängen nicht am Zweckweg; ihre Fälle greifen über die Wortlisten.
    Liefe er mit, dauerte die schnelle Runde zehn Minuten statt einer, und
    niemand ließe sie noch vor einem Vorschlag laufen.

    Die Genauigkeit des Zweckwegs wird nicht übersprungen, sondern an einer
    eigenen Stelle gemessen: ``test_genauigkeit_auf_unternehmensfragen`` ist als
    ``langsam`` markiert, läuft über alle hundert Unternehmensfragen und bekommt
    den echten Zweckweg. Prüfungen mit dieser Marke lässt diese Vorbereitung
    unangetastet.
    """
    if request.node.get_closest_marker("langsam"):
        yield
        return
    from helfer.einstufung import pruefer as pruefmodul
    from helfer.einstufung import zwecke

    # Ersetzt wird der Name IM Prüfermodul, nicht der im Zweckmodul: der Prüfer
    # hat ihn beim Einlesen übernommen, und ein Austausch an der Quelle käme
    # dort nicht mehr an.
    leer = zwecke.Zweckfinder(zeilen=[])
    leer._bewerter_versucht = True
    original = pruefmodul.gemeinsamer_zweckfinder
    pruefmodul.gemeinsamer_zweckfinder = lambda: leer  # type: ignore[assignment]
    # Ein Prüfer, der in einer früheren Prüfung schon einen Zweckweg geholt hat,
    # behält ihn - darum wird die Bindung auch an der Instanz zurückgesetzt.
    for zwischen in (request.node.funcargs or {}).values():
        if isinstance(zwischen, pruefmodul.Pruefer):
            zwischen._zweckfinder = leer
            zwischen._zweckfinder_versucht = True
    try:
        yield
    finally:
        pruefmodul.gemeinsamer_zweckfinder = original
