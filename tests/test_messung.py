"""Prüft, dass die veröffentlichten Zahlen nachgemessen und nicht geschätzt sind.

Jede Zahl in README, Oberfläche und Präsentation stammt aus
``daten/pruefung/zahlen.json``. Diese Prüfung stellt sie gegen die Dateien, aus
denen sie gezählt wurde: die Protokolle der Messung an den amtlichen Beispielen
und den aufbereiteten Rechtsbestand.

Der Grund: eine Zahl, die einmal gestimmt hat, stimmt nach der nächsten
Änderung am Regelwerk nicht mehr — und niemand sieht es ihr an. "Rund 2.700
Einheiten" ist keine Angabe, sondern ein Versäumnis; eine Angabe, die niemand
nachzählt, wird nach drei Änderungen eine.

Nicht geprüft wird hier, ob die Messung selbst richtig war. Sie beruht darauf,
dass ein Leser der 217 amtlichen Beispiele die Fragen so beantwortet, wie ein
Mitarbeiter sie über sein eigenes System beantworten würde. Das Verfahren und
jede einzelne Abweichung stehen in ``daten/pruefung/MESSUNG.md``.
"""

from __future__ import annotations

import json

import pytest

#: Der vollständige Durchgang über alle 217 amtlichen Beispiele.
DURCHGANG = ("schluss-00-71", "schluss-72-144", "schluss-145-216")


@pytest.fixture(scope="module")
def pruefordner(wurzel):
    return wurzel / "daten" / "pruefung"


@pytest.fixture(scope="module")
def zahlen(pruefordner) -> dict:
    return json.loads((pruefordner / "zahlen.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def durchgang(pruefordner) -> list[dict]:
    satz: list[dict] = []
    for name in DURCHGANG:
        satz += json.loads((pruefordner / f"{name}.json").read_text(encoding="utf-8"))
    return satz


@pytest.fixture(scope="module")
def nachmessung(pruefordner) -> dict[int, dict]:
    satz = json.loads((pruefordner / "nachmessung.json").read_text(encoding="utf-8"))
    return {e["index"]: e for e in satz}


def test_jedes_amtliche_beispiel_ist_genau_einmal_gemessen(pruefordner, durchgang, zahlen) -> None:
    """Ein übersprungenes Beispiel würde die Quote nach oben verfälschen."""
    beispiele = json.loads((pruefordner / "amtliche-beispiele.json").read_text(encoding="utf-8"))
    assert len(beispiele) == zahlen["gesamt"]
    nummern = [e["index"] for e in durchgang]
    assert sorted(nummern) == list(range(len(beispiele))), "Lücke oder Doppelung in der Messung"


def test_die_treffer_sind_gezaehlt_nicht_behauptet(durchgang, nachmessung, zahlen) -> None:
    """207 von 217 — nachgezählt aus den Protokollen der Messung.

    Die Nachmessung berichtigt einzelne Fälle, die nach einer Änderung am
    Regelwerk neu gefahren wurden; sie gilt vor dem ersten Durchgang.
    """
    stand = {e["index"]: e for e in durchgang}
    stand.update(nachmessung)
    getroffen = sum(1 for e in stand.values() if e["getroffen"])
    assert len(stand) == zahlen["gesamt"]
    assert getroffen == zahlen["getroffen"], (
        f"{getroffen} getroffen, veröffentlicht sind {zahlen['getroffen']}"
    )


def test_die_schrittzahl_ist_der_gemessene_schnitt(durchgang, zahlen) -> None:
    """5,3 Schritte im Schnitt — aus dem vollständigen Durchgang gerechnet."""
    schritte = [e["schritte"] for e in durchgang]
    assert all(s > 0 for s in schritte), "Ein Lauf ohne Schritt kann nicht gemessen worden sein"
    schnitt = round(sum(schritte) / len(schritte), 1)
    assert schnitt == zahlen["schritte_schnitt"], (
        f"gemessen {schnitt}, veröffentlicht {zahlen['schritte_schnitt']}"
    )


def test_jede_abweichung_ist_begruendet(durchgang, nachmessung, zahlen) -> None:
    """Eine unerklärte Abweichung ist ein offener Fehler, keine Messung."""
    stand = {e["index"]: e for e in durchgang}
    stand.update(nachmessung)
    ohne = [i for i, e in sorted(stand.items()) if not e["getroffen"] and not e["warum_abweichung"]]
    assert not ohne, f"Abweichungen ohne Begründung: {ohne}"
    daneben = [i for i, e in stand.items() if not e["getroffen"]]
    assert len(daneben) == zahlen["gesamt"] - zahlen["getroffen"]


def test_jeder_sollwert_ist_eine_bekannte_wertung(durchgang) -> None:
    """Ein Tippfehler im Soll würde als Abweichung des Durchlaufs erscheinen."""
    bekannt = {
        "kein_ki_system",
        "kein_hochrisiko",
        "hochrisiko",
        "hochrisiko_anhang_i",
        "ausnahme_greift",
    }
    fremd = sorted({e["soll"] for e in durchgang} - bekannt)
    assert not fremd, f"Unbekannte Soll-Wertungen: {fremd}"


def test_der_rechtsbestand_ist_so_gross_wie_veroeffentlicht(korpus, zahlen) -> None:
    """2811 Textstellen, davon 1386 aus der KI-Verordnung und 1024 aus der DSGVO."""
    assert len(korpus) == zahlen["korpus_einheiten"]
    je_akt: dict[str, int] = {}
    for einheit in korpus:
        je_akt[einheit.rechtsakt.value] = je_akt.get(einheit.rechtsakt.value, 0) + 1
    assert je_akt.get("KI-VO") == zahlen["kivo"]
    assert je_akt.get("DSGVO") == zahlen["dsgvo"]


def test_die_messung_nennt_ihre_zahlen_im_wortlaut(pruefordner, zahlen) -> None:
    """MESSUNG.md ist die Begründung der Zahl — sie muss dieselbe nennen."""
    text = (pruefordner / "MESSUNG.md").read_text(encoding="utf-8")
    assert f"{zahlen['getroffen']} von {zahlen['gesamt']}" in text
    assert f"{zahlen['zwei_wege']} von {zahlen['zwei_wege']}" in text


def test_das_readme_nennt_dieselben_zahlen(wurzel, zahlen) -> None:
    """Was vorn auf der Seite steht, muss hinten gemessen sein.

    Die Reihenfolge war hier einmal umgekehrt: eine Zahl stand im README, und
    das Regelwerk wuchs danach weiter. Wer das bemerkt, hat Glück gehabt.
    """
    text = (wurzel / "README.md").read_text(encoding="utf-8")
    fehlt: list[str] = []
    for feld in (
        "korpus_einheiten",
        "kivo",
        "dsgvo",
        "fragen",
        "punkte",
        "ausschluesse",
        "beispiele",
    ):
        if str(zahlen[feld]) not in text:
            fehlt.append(f"{feld}={zahlen[feld]}")
    if f"{zahlen['getroffen']} von {zahlen['gesamt']}" not in text:
        fehlt.append(f"getroffen={zahlen['getroffen']} von {zahlen['gesamt']}")
    if f"{zahlen['zwei_wege']} von {zahlen['zwei_wege']}" not in text:
        fehlt.append(f"zwei_wege={zahlen['zwei_wege']}")
    schnitt = str(zahlen["schritte_schnitt"])
    if schnitt not in text and schnitt.replace(".", ",") not in text:
        fehlt.append(f"schritte_schnitt={schnitt}")
    assert not fehlt, "Im README fehlen oder stehen anders: " + ", ".join(fehlt)
