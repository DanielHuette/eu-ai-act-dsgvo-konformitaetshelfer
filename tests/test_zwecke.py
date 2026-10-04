"""Prüfungen für den Zweckweg — den zweiten Eingang in das Regelwerk.

Geprüft wird in zwei Schichten. Die Form des Katalogs läuft immer: dass jede
Fundstelle auf echten amtlichen Text zeigt, dass jede Regel im Regelwerk
existiert und dass die Zwecksätze die gemessene Satzform einhalten. Die
Genauigkeit selbst braucht die Modelle und ist darum als ``langsam`` markiert —
sie gehört in den nächtlichen Lauf, nicht in jeden Vorschlag.

Der Grund für die Formprüfungen: der Zweckweg steht und fällt mit der Form der
Sätze. Gemessen traf ein Zwecksatz als Infinitiv 0,036, als Aussagesatz in der
dritten Person 0,546 und in der ersten Person 0,988. Wer einen Zweck in der
falschen Form ergänzt, senkt den Wert um den Faktor zwanzig — und merkt es
nicht, weil nichts bricht. Darum prüft eine Zeile hier die Form.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from helfer.einstufung.pruefer import regelwerk
from helfer.einstufung.zwecke import (
    GEGEN_STARK,
    SCHWELLE,
    SCHWELLEN_JE_KLASSE,
    Zweckfinder,
    katalog_lesen,
    katalogpfad,
    saetze,
)
from helfer.korpus.bauen import laden
from helfer.modell import Risikoklasse

ZEILEN = katalog_lesen()
KORPUS = {e.kennung for e in laden()}


def _regelkennungen() -> set[str]:
    """Alle Kennungen, die das Regelwerk vergibt — über alle Stufen."""
    werk = regelwerk().risikoklassen
    kennungen: set[str] = set()
    for regel in werk.get("verbote", []):
        kennungen.add(regel["kennung"])
    for schluessel in ("hochrisiko_anhang_i", "hochrisiko_ausnahme", "gpai", "minimal"):
        teil = werk.get(schluessel) or {}
        if teil.get("kennung"):
            kennungen.add(teil["kennung"])
    for bereich in (werk.get("hochrisiko_anhang_iii") or {}).get("bereiche", []):
        kennungen.add(bereich["kennung"])
    for fall in (werk.get("transparenz") or {}).get("faelle", []):
        kennungen.add(fall["kennung"])
    return kennungen


# --------------------------------------------------------------- Form


def test_katalog_ist_nicht_leer() -> None:
    assert len(ZEILEN) >= 100, "Der Zweckkatalog ist zu dünn, um zu tragen"


def test_jede_fundstelle_zeigt_auf_amtlichen_text() -> None:
    """Eine Fundstelle, die es nicht gibt, ist eine erfundene Begründung.

    Der Zweckweg schreibt seine Fundstelle in die Rechtsgrundlage der Auskunft.
    Zeigt sie ins Leere, steht in der Antwort eine Stelle, die der Nutzer nicht
    nachlesen kann — schlimmer als keine Angabe.
    """
    fehlend = sorted({z.fundstelle for z in ZEILEN if z.fundstelle not in KORPUS})
    assert not fehlend, f"Fundstellen ohne Text im Korpus: {fehlend}"


def test_jede_regel_steht_im_regelwerk() -> None:
    """Der Zweckweg ist ein zweiter Eingang, kein zweites Regelwerk.

    Zeigt ein Eintrag auf eine Regel, die es nicht gibt, so löst er nichts aus
    und fällt still weg. Das ist der Fehler, der am längsten unentdeckt bleibt.
    """
    bekannt = _regelkennungen()
    fremd = sorted({z.regel for z in ZEILEN if z.regel not in bekannt})
    assert not fremd, f"Regelkennungen, die das Regelwerk nicht kennt: {fremd}"


def test_jede_klasse_ist_eine_echte_risikoklasse() -> None:
    gueltig = {k.value for k in Risikoklasse}
    fremd = sorted({z.klasse for z in ZEILEN if z.klasse not in gueltig})
    assert not fremd, f"Unbekannte Klassen im Katalog: {fremd}"


def test_zwecksaetze_stehen_in_der_ersten_person() -> None:
    """Die gemessene Satzform: Aussagesatz, erste Person Plural, Punkt am Ende.

    Gemessen gegen dieselben drei Beschreibungen: Infinitiv 0,036 bis 0,447,
    dritte Person 0,037 bis 0,546, erste Person 0,986 bis 0,989. Die Schwelle
    liegt bei 0,50 — die beiden anderen Formen tragen also nicht.
    """
    muster = re.compile(r"^(Wir|Unser(e|es)?)\b.*[.!]$")
    falsch = [z.text for z in ZEILEN if not muster.match(z.text)]
    assert not falsch, "Zwecksätze nicht in der gemessenen Form:\n" + "\n".join(falsch[:10])


def test_zwecksaetze_sind_saetze_und_keine_stichwortlisten() -> None:
    kurz = [z.text for z in ZEILEN if len(z.text.split()) < 4]
    assert not kurz, f"Zu kurz, um ein Zweck zu sein: {kurz}"


def test_keine_doppelten_zwecksaetze() -> None:
    """Derselbe Satz an zwei Fundstellen macht die Begründung beliebig."""
    gesehen: dict[str, str] = {}
    doppelt: list[str] = []
    for z in ZEILEN:
        if z.gegenzweck:
            # Ein Gegenzweck darf mehrfach stehen: dieselbe Entlastung kann für
            # mehrere Regeln gelten, etwa das Besprechungsprotokoll gegen
            # Anhang III Nummer 1 und Nummer 4.
            continue
        if z.text in gesehen and gesehen[z.text] != z.fundstelle:
            doppelt.append(f"{z.text!r} bei {gesehen[z.text]} und {z.fundstelle}")
        gesehen[z.text] = z.fundstelle
    assert not doppelt, "\n".join(doppelt)


def test_jeder_eintrag_nennt_mindestens_einen_zweck() -> None:
    rohdaten = yaml.safe_load(katalogpfad().read_text(encoding="utf-8"))
    ohne = [e["fundstelle"] for e in rohdaten["eintraege"] if not e.get("zwecke")]
    assert not ohne, f"Einträge ohne Zweck: {ohne}"


def test_katalog_nennt_seinen_stand() -> None:
    rohdaten = yaml.safe_load(katalogpfad().read_text(encoding="utf-8"))
    assert rohdaten.get("stand"), "Ohne Standsangabe ist der Katalog nicht datierbar"


def test_verbote_haben_die_hoehere_schwelle() -> None:
    """Ein falsches Verbot stellt ein Geschäft ein — das braucht mehr Beleg.

    Gemessen: eine Lernplattform, die Aufsätze benotet, traf den Satz zur
    Emotionserkennung bei Schülern mit 0,6297; die App, die die Stimmung von
    Mitarbeitern misst, traf ihren Satz mit 0,9974. Die Schwelle liegt
    dazwischen und nicht am Rand einer der beiden Gruppen.
    """
    assert SCHWELLEN_JE_KLASSE["verboten"] > SCHWELLE
    assert 0.63 < SCHWELLEN_JE_KLASSE["verboten"] < 0.99


def test_starker_gegenzweck_liegt_ueber_der_schwelle() -> None:
    assert GEGEN_STARK > SCHWELLE


# ------------------------------------------------------- Satzzerlegung


def test_rueckfrage_faellt_weg() -> None:
    teile = saetze("Die KI liest Lebensläufe. Was müssen wir beachten?")
    assert not any("beachten" in s for s in teile)


def test_verkaeuferworspann_wird_abgeleitet() -> None:
    """Der Zweck steckt im Relativsatz; ohne Ableitung fehlt der Treffer.

    Gemessen: 0,35 mit Vorspann, 0,75 ohne ihn, bei einer Schwelle von 0,50.
    """
    teile = saetze("Wir verkaufen eine Software, die Gesichter mit einer Liste abgleicht.")
    assert any(s.startswith("Wir Gesichter mit einer Liste") for s in teile)


def test_systemsatz_wird_abgeleitet() -> None:
    teile = saetze("Sie verteilt die Nachtschichten danach, wer wie oft krank war.")
    assert any(s.startswith("Wir verteilt die Nachtschichten") for s in teile)


def test_ein_mensch_als_subjekt_wird_nicht_zu_wir() -> None:
    """Die Gegenprobe zur Ableitung — und die wichtigere Hälfte.

    "Eine Kollegin liest alles gegen" darf nicht zu "Wir lesen alles gegen"
    werden: dort handelt ein Mensch, und genau dieser Unterschied entlastet
    nach Artikel 6 Absatz 3. Eine Ableitung, die Menschen zu Systemen macht,
    nimmt dem Nutzer die Entlastung weg.
    """
    teile = saetze("Eine Kollegin liest alles gegen, bevor es online geht.")
    assert all(not s.startswith("Wir liest") for s in teile)


def test_beschreibung_ohne_aussage_bleibt_erhalten() -> None:
    """Wer nur fragt, soll gemessen werden — ungenau ist besser als gar nicht."""
    teile = saetze("Was müssen wir beachten?")
    assert teile == ["Was müssen wir beachten?"]


def test_ohne_modelle_bleibt_der_zweckweg_leer() -> None:
    """Der Container ohne Netz und das Telefon müssen weiter einstufen können."""
    finder = Zweckfinder(zeilen=ZEILEN)
    finder._bewerter_versucht = True
    finder._bewerter = None
    assert finder.finden("Wir sichten Bewerbungen und sortieren sie vor.") == []


# ---------------------------------------------------------- Genauigkeit


def _unternehmensfragen() -> list[dict[str, str]]:
    pfad = Path(__file__).resolve().parents[1] / "daten" / "pruefung" / "unternehmensfragen.yaml"
    return list(yaml.safe_load(pfad.read_text(encoding="utf-8"))["fragen"])


def test_unternehmensfragen_sind_vollstaendig_und_gemischt() -> None:
    """Die Sammlung selbst wird geprüft, nicht nur das Ergebnis darauf.

    Ohne genug "minimal" wäre die Quote wertlos: ein Prüfer, der alles für
    Hochrisiko erklärt, träfe eine Sammlung ohne harmlose Fälle fast perfekt
    und wäre im Betrieb unbrauchbar.
    """
    fragen = _unternehmensfragen()
    assert len(fragen) >= 100
    harmlos = [f for f in fragen if f["einstufung"] == "minimal"]
    assert len(harmlos) >= 25, "Zu wenige harmlose Fälle — die Quote sagt dann nichts"
    gueltig = {k.value for k in Risikoklasse}
    assert all(f["einstufung"] in gueltig for f in fragen)
    assert all(f.get("stelle") for f in fragen), "Jedes Soll braucht seine Fundstelle"


@pytest.mark.langsam
def test_genauigkeit_auf_unternehmensfragen() -> None:
    """Die eigentliche Messung — braucht Einbetter und Kreuzbewerter.

    Die Grenze liegt bei 95 von 100 und nicht bei 100: zwei Fälle sind offen
    benannt, und eine Grenze, die beim ersten neuen Zwecksatz bricht, wird
    hochgesetzt statt behoben. Fällt die Quote unter 95, ist etwas
    zurückgefallen.
    """
    from helfer.einstufung.pruefer import Pruefer, beschreibung_aus_text
    from helfer.modell import Rolle

    pruefer = Pruefer()
    if pruefer.zweckfinder() is None or pruefer.zweckfinder()._bewerter_holen() is None:
        pytest.skip("Ohne Kreuzbewerter ist die Genauigkeit nicht messbar")

    richtig = 0
    falsch: list[str] = []
    for fall in _unternehmensfragen():
        beschreibung = beschreibung_aus_text(fall["frage"]).model_copy(
            update={"rollen": (Rolle(fall["rolle"]),)}
        )
        ist = [k.value for k in pruefer.pruefen(beschreibung).klassen]
        if fall["einstufung"] in ist:
            richtig += 1
        else:
            falsch.append(f"soll={fall['einstufung']} ist={','.join(ist)}: {fall['frage'][:70]}")
    assert richtig >= 95, f"Nur {richtig} von 100 richtig:\n" + "\n".join(falsch)
