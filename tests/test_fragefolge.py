"""Prüft die Fragefolge — den Teil, der die Einstufung entscheidet.

Der Helfer fragt, statt zu raten. Was er fragt, steht in
``daten/regeln/fragefolge/*.yaml`` und ``daten/regeln/fragefolge-aufbau.yaml``;
wie er daraus den Befund zieht, steht in ``src/helfer/einstufung/fragefolge.py``.
Liegt eine dieser beiden Seiten falsch, bekommt der Nutzer eine Einstufung, die
er nicht als falsch erkennen kann.

Drei Arten von Prüfungen stehen hier:

* **Die Belege.** Jede Rechtsfrage trägt die Absatznummer aus dem Entwurf der
  Leitlinien der Kommission vom 19. Mai 2026, und jeder Punkt zeigt auf eine
  Stelle, die im Rechtsbestand wirklich steht. Eine Frage ohne Fundstelle ist
  eine Behauptung.
* **Die gezählten Zahlen.** Was im Durchlauf steckt, wird gezählt und gegen
  ``daten/pruefung/zahlen.json`` gestellt — dieselbe Zahl, die in README und
  Oberfläche steht.
* **Die Wege durch den Durchlauf.** Vollständige Läufe mit den Antworten, die
  ein Mitarbeiter über sein eigenes System gäbe, einschliesslich der Fälle, an
  denen der Durchlauf schon einmal falsch gelaufen ist.
"""

from __future__ import annotations

import json
import re

import pytest

from helfer.einstufung.fragefolge import (
    BEDINGT,
    ERFASST,
    NICHT_ERFASST,
    TRIFFT_NICHT_ZU,
    Durchlauf,
    Frage,
)

#: Die Antworten für den Fall, der am meisten gemessen wurde: ein Werkzeug,
#: das Lebensläufe sichtet und eine Rangfolge der Bewerber bildet.
#:
#: Zwei Antworten darin sind "trifft nicht zu", und beide müssen es sein:
#: ``...:0:4`` fragt nach Plattformarbeitern, ``...:1:19`` nach Angeboten auf
#: Ausschreibungen. Ein Werkzeug zur Lebenslaufsichtung tut beides nicht —
#: und beide Fragen schliessen auf ein Nein aus.
LEBENSLAUFSICHTUNG: dict[str, object] = {
    "ist-es-ein-ki-system": True,
    "natuerliche-personen": True,
    "im-namen-von": False,
    "bereich:KI-VO/anh-III/nr-4": True,
    "haupt:nr-4-beschaeftigung:0": True,
    "haupt:nr-4-beschaeftigung:1": True,
    "haupt:nr-4-beschaeftigung:2": False,
    "folge:nr-4-beschaeftigung:0:0": True,
    "folge:nr-4-beschaeftigung:0:1": False,
    "folge:nr-4-beschaeftigung:0:2": False,
    "folge:nr-4-beschaeftigung:0:3": False,
    "folge:nr-4-beschaeftigung:0:4": TRIFFT_NICHT_ZU,
    "folge:nr-4-beschaeftigung:0:5": True,
    "folge:nr-4-beschaeftigung:0:6": False,
    "folge:nr-4-beschaeftigung:1:1": True,
    "folge:nr-4-beschaeftigung:1:3": True,
    "folge:nr-4-beschaeftigung:1:14": TRIFFT_NICHT_ZU,
    "folge:nr-4-beschaeftigung:1:19": TRIFFT_NICHT_ZU,
}

#: Die Frage, an der ein erzwungenes Nein einen erfassten Fall aus der
#: Einstufung geworfen hat: "Zeigt die Anzeige aktiv an, dass ein Arbeitgeber
#: Bewerber für eine konkrete offene Stelle sucht?" (Absatz 251). Ein Werkzeug,
#: das Lebensläufe sichtet, schaltet keine Anzeigen.
STELLENANZEIGE = "folge:nr-4-beschaeftigung:1:14"


@pytest.fixture(scope="module")
def durchlauf() -> Durchlauf:
    return Durchlauf.laden()


@pytest.fixture(scope="module")
def zahlen(wurzel) -> dict:
    return json.loads((wurzel / "daten" / "pruefung" / "zahlen.json").read_text(encoding="utf-8"))


def alle_fragen(d: Durchlauf) -> list[Frage]:
    """Jede Frage, die der Durchlauf überhaupt stellen kann."""
    fragen: list[Frage] = [*d.vorfragen, *d.hinweise, *d.filterfragen, *d.bereichsfragen]
    fragen += list(d.anhang_i_gattungen) + list(d.anhang_i_fragen.values())
    if d.anhang_i_tor is not None:
        fragen.append(d.anhang_i_tor)
    if d.profilingfrage is not None:
        fragen.append(d.profilingfrage)
    for punkt in d.punkte:
        fragen.append(punkt.hauptfrage)
        fragen += list(punkt.folgefragen)
    return fragen


def fahren(d: Durchlauf, antworten: dict[str, object]) -> tuple[dict[str, object], int]:
    """Fährt den Durchlauf von vorn und beantwortet jede Frage.

    Was in ``antworten`` steht, wird so beantwortet; alles andere mit Nein.
    Zurück kommen die gegebenen Antworten und die Zahl der Schritte — ein
    Schritt ist ein Blatt, nicht eine Frage.
    """
    gegeben: dict[str, object] = {}
    schritte = 0
    while True:
        gruppe = d.naechste_gruppe(gegeben)
        if not gruppe:
            return gegeben, schritte
        schritte += 1
        assert schritte <= 40, "Der Durchlauf kommt nicht zum Ende"
        for frage in gruppe:
            gegeben[frage.kennung] = antworten.get(frage.kennung, False)


# ------------------------------------------------------------------ Belege


def test_die_fragen_nennen_ihre_quelle(durchlauf) -> None:
    """Ohne Quellenangabe wäre nicht nachprüfbar, woher eine Frage kommt."""
    assert durchlauf.quellen, "Der Durchlauf nennt keine Quelle"
    for quelle in durchlauf.quellen:
        assert "19.05.2026" in quelle, quelle


def test_jede_rechtsfrage_traegt_ihre_absatznummer(durchlauf) -> None:
    """Jede Frage, die entscheidet, zeigt auf einen Absatz der Leitlinien.

    Ausgenommen sind die acht Bereichsfragen und die Hauptfrage eines Punktes:
    die sortieren nur. Was der Bereich rechtlich bedeutet, steht in seinen
    Folgefragen, und die tragen ihren Beleg.
    """
    sortieren = {f.kennung for f in durchlauf.bereichsfragen}
    sortieren |= {p.hauptfrage.kennung for p in durchlauf.punkte}
    ohne = [f.kennung for f in alle_fragen(durchlauf) if not f.beleg and f.kennung not in sortieren]
    assert not ohne, f"Fragen ohne Beleg ({len(ohne):d}): {ohne[:10]}"


def test_jeder_ausschluss_und_jedes_beispiel_traegt_seinen_beleg(durchlauf) -> None:
    """Ein Ausschluss ohne Fundstelle ist eine Behauptung über das Gesetz."""
    ohne: list[str] = []
    for punkt in durchlauf.punkte:
        for feld in ("erfasst", "nicht_erfasst", "beispiele"):
            for eintrag in getattr(punkt, feld):
                if not eintrag.get("beleg"):
                    ohne.append(f"{punkt.fundstelle}/{feld}: {eintrag.get('text', '')[:50]}")
    assert not ohne, "\n".join(ohne[:10])


def test_belege_sind_absatznummern_der_leitlinien(durchlauf) -> None:
    """Form des Belegs: die Absatzzählung der Leitlinien, etwa ``(245)``."""
    muster = re.compile(r"\(\d{1,4}\)")
    falsch = [
        (f.kennung, f.beleg)
        for f in alle_fragen(durchlauf)
        if f.beleg and not muster.search(f.beleg)
    ]
    # Zugelassen ist daneben die Form "(nach 293)" für eine Aufzählung, die im
    # amtlichen Text hinter einem Absatz steht und selbst keine Zählung trägt.
    falsch = [p for p in falsch if not re.search(r"\(nach \d{1,4}\)", p[1])]
    assert not falsch, falsch[:8]


def test_jeder_punkt_zeigt_auf_eine_stelle_im_rechtsbestand(durchlauf, kennungen) -> None:
    """Die Fundstelle eines Punktes muss im Korpus nachlesbar sein.

    Ausgenommen sind die Tore der Bereiche: sie öffnen einen Bereich und tragen
    den Fall nicht selbst, darum dürfen sie eine eigene Kennung führen.
    """
    fehlen = sorted(
        {
            p.fundstelle
            for p in durchlauf.punkte
            if not p.ist_bereichstor and p.fundstelle not in kennungen
        }
    )
    assert not fehlen, f"Fundstellen ohne Text im Korpus: {fehlen}"


def test_die_buchstaben_des_anhangs_iii_sind_eigene_punkte(durchlauf) -> None:
    """Nummer 4 Buchstabe a trifft die Einstellung, Buchstabe b die Arbeitsbedingungen.

    Zwei verschiedene Sachverhalte unter einer Überschrift. Ein Durchlauf, der
    nur die Nummer kennt, kann einen Fall nicht auf die Stelle zurückführen,
    die ihn trägt.
    """
    mit_buchstabe = {
        p.fundstelle for p in durchlauf.punkte if re.search(r"/nr-\d+-[a-z]$", p.fundstelle)
    }
    assert "KI-VO/anh-III/nr-4-a" in mit_buchstabe
    assert "KI-VO/anh-III/nr-4-b" in mit_buchstabe
    assert len(mit_buchstabe) >= 20, sorted(mit_buchstabe)


def test_keine_frage_laesst_den_nutzer_seine_antworten_zaehlen(durchlauf) -> None:
    """ "Haben Sie alle sechs vorstehenden Fragen mit Nein beantwortet?"

    Das weiss der Durchlauf selbst. Sie zu stellen hiesse, dem Nutzer eine
    Fehlerquelle zu geben, die der Rechner nicht hat.
    """
    selbst = [
        f.kennung for f in alle_fragen(durchlauf) if f.text.lower().startswith("haben sie alle")
    ]
    assert not selbst, selbst


def test_keine_frage_ist_leer(durchlauf) -> None:
    leer = [f.kennung for f in alle_fragen(durchlauf) if len(f.text.split()) < 3]
    assert not leer, leer[:10]


# ------------------------------------------------------------------ Zahlen


def test_der_durchlauf_zaehlt_wie_veroeffentlicht(durchlauf, zahlen) -> None:
    """Was in README und Oberfläche steht, wird hier nachgezählt.

    Grundsatz: keine Zahl, die nicht gemessen ist. Ändert sich das Regelwerk
    mit Absicht, ändern sich diese Zahlen mit — in ``zahlen.json`` und damit
    überall, wo sie stehen.
    """
    gezaehlt = durchlauf.zahlen()
    for feld in ("fragen", "punkte", "ausschluesse", "beispiele", "vorfragen"):
        assert gezaehlt[feld] == zahlen[feld], f"{feld}: {gezaehlt[feld]} statt {zahlen[feld]}"
    assert len(durchlauf.bereichsfragen) == zahlen["bereichsfragen"]
    assert len(durchlauf.anhang_i_gattungen) == zahlen["anhang_i_gattungen"]


def test_jede_frage_ist_genau_einmal_zu_beantworten(durchlauf) -> None:
    """Zwei Fragen mit derselben Kennung wären eine Antwort auf beide.

    Anhang III Nummer 2 hat vier Punkte unter derselben Fundstelle. Trüge die
    Kennung nur die Fundstelle, beantwortete eine Antwort vier Fragen.
    """
    alle = [f.kennung for f in alle_fragen(durchlauf)]
    doppelt = sorted({k for k in alle if alle.count(k) > 1})
    assert not doppelt, doppelt


# ---------------------------------------------------- Wege durch die Folge


def test_ohne_ki_system_endet_der_durchlauf_sofort(durchlauf) -> None:
    """Artikel 3 Nummer 1: ist es kein KI-System, gilt die Verordnung nicht."""
    antworten = {durchlauf.vorfragen[0].kennung: False}
    assert durchlauf.naechste(antworten) is None
    befund = durchlauf.ergebnis(antworten)
    assert befund.klasse == "kein_ki_system"
    assert befund.endtext, "Der Nutzer erfährt nicht, was das für ihn bedeutet"


def test_die_bereichsauswahl_ist_ein_schritt_nicht_acht(durchlauf) -> None:
    """Ein Jurist fragt "In welchem Bereich arbeiten Sie?" einmal, nicht achtmal."""
    antworten: dict[str, object] = {
        "ist-es-ein-ki-system": True,
        "natuerliche-personen": True,
        "im-namen-von": False,
    }
    if durchlauf.anhang_i_tor is not None:
        antworten[durchlauf.anhang_i_tor.kennung] = False
    gruppe = durchlauf.naechste_gruppe(antworten)
    assert {f.kennung for f in gruppe} == {f.kennung for f in durchlauf.bereichsfragen}


def test_lebenslaufsichtung_ist_hochrisiko_nach_nummer_4_buchstabe_a(durchlauf) -> None:
    """Der Fall, an dem der Durchlauf am häufigsten gemessen wurde."""
    antworten, schritte = fahren(durchlauf, LEBENSLAUFSICHTUNG)
    befund = durchlauf.ergebnis(antworten)
    assert befund.klasse == "hochrisiko_anhang_iii", befund.klasse
    assert "KI-VO/anh-III/nr-4-a" in befund.fundstellen, befund.fundstellen
    assert schritte <= 10, f"{schritte} Schritte — ein Jurist fragt fünf bis acht Dinge ab"


def test_trifft_nicht_zu_wirft_den_fall_nicht_aus_der_einstufung(durchlauf) -> None:
    """Die dritte Antwort, und warum sie keine Bequemlichkeit ist.

    Ein Werkzeug, das Lebensläufe sichtet, schaltet keine Stellenanzeigen. Auf
    die Frage, ob eine Anzeige eine konkrete offene Stelle anzeigt, gibt es
    dort weder Ja noch Nein — und ein Nein schliesst nach Absatz 251 aus.
    Gemessen fiel der Fall dadurch aus der Einstufung heraus, obwohl er nach
    dem amtlichen Text klar erfasst ist.
    """
    mit_offen, _ = fahren(durchlauf, LEBENSLAUFSICHTUNG)
    assert durchlauf.ergebnis(mit_offen).klasse == "hochrisiko_anhang_iii"

    erzwungen = dict(LEBENSLAUFSICHTUNG, **{STELLENANZEIGE: False})
    mit_nein, _ = fahren(durchlauf, erzwungen)
    assert durchlauf.ergebnis(mit_nein).klasse == "kein_hohes_risiko", (
        "Das erzwungene Nein schliesst nicht mehr aus — dann prüft diese Stelle nichts"
    )


def test_ein_offengelassener_ausschluss_greift_nicht(durchlauf) -> None:
    """Dieselbe Regel eine Ebene tiefer, an der Wertung selbst."""
    punkt = next(p for p in durchlauf.punkte if p.fundstelle == "KI-VO/anh-III/nr-4-a")
    ausschluss = next(f for f in punkt.folgefragen if f.bei_ja == NICHT_ERFASST)
    traeger = next(f for f in punkt.folgefragen if f.bei_ja == ERFASST)

    # Ausgangslage: der Tatbestand ist bejaht, und keine Ausnahme greift. Wo ein
    # Nein ausschliesst, bleibt die Frage offen — genau dafür ist sie da.
    grund: dict[str, object] = {}
    for frage in punkt.folgefragen:
        grund[frage.kennung] = TRIFFT_NICHT_ZU if frage.bei_nein == NICHT_ERFASST else False
    grund[punkt.hauptfrage.kennung] = True
    grund[traeger.kennung] = True

    grund[ausschluss.kennung] = TRIFFT_NICHT_ZU
    assert durchlauf.punktbefund(punkt, grund) == ERFASST
    grund[ausschluss.kennung] = True
    assert durchlauf.punktbefund(punkt, grund) == NICHT_ERFASST


def test_ohne_bereich_kein_hohes_risiko(durchlauf) -> None:
    """Wer alle acht Bereiche verneint, fällt nicht unter Anhang III."""
    antworten, _ = fahren(durchlauf, {"ist-es-ein-ki-system": True, "natuerliche-personen": True})
    befund = durchlauf.ergebnis(antworten)
    assert befund.klasse == "kein_hohes_risiko", befund.klasse
    assert not befund.getroffene_punkte


def test_der_filter_wird_erst_nach_einem_getragenen_punkt_gefragt(durchlauf) -> None:
    """Artikel 6 Absatz 3 nimmt nur aus, was zuvor unter Anhang III fällt.

    Darum kommt die Frage nach der Ausnahme nie an die Reihe, solange keine
    Stelle trägt. Sie vorher zu stellen hiesse, über eine Ausnahme von nichts
    zu reden.
    """
    ohne_bereich, _ = fahren(
        durchlauf, {"ist-es-ein-ki-system": True, "natuerliche-personen": True}
    )
    assert not any(k.startswith("filter:") for k in ohne_bereich)

    mit_bereich, _ = fahren(durchlauf, LEBENSLAUFSICHTUNG)
    assert [k for k in mit_bereich if k.startswith("filter:")], "Der Filter wurde nie gefragt"


def test_die_ausnahme_greift_nur_ohne_profiling(durchlauf) -> None:
    """Nimmt das System Profiling vor, bleibt es hochriskant.

    So steht es im amtlichen Text, und so wiegt es für den Nutzer: eine
    gründliche menschliche Nachprüfung hilft ihm dann nicht.
    """
    bedingung = durchlauf.filterfragen[0].kennung
    profiling = durchlauf.profilingfrage.kennung

    mit_ausnahme, _ = fahren(durchlauf, dict(LEBENSLAUFSICHTUNG, **{bedingung: True}))
    befund = durchlauf.ergebnis(mit_ausnahme)
    assert befund.klasse == "hochrisiko_ausnahme", befund.klasse
    assert befund.filter_greift
    assert befund.filter_grund, "Der Nutzer erfährt nicht, welche Bedingung ihn entlastet"

    mit_profiling, _ = fahren(
        durchlauf, dict(LEBENSLAUFSICHTUNG, **{bedingung: True, profiling: True})
    )
    assert durchlauf.ergebnis(mit_profiling).klasse == "hochrisiko_anhang_iii"


def test_ausnahme_und_anhang_iii_stehen_nie_zusammen(durchlauf) -> None:
    """Beide Klassen zugleich wären ein Widerspruch in der Auskunft."""
    bedingung = durchlauf.filterfragen[0].kennung
    antworten, _ = fahren(durchlauf, dict(LEBENSLAUFSICHTUNG, **{bedingung: True}))
    klasse = durchlauf.ergebnis(antworten).klasse
    assert klasse in {"hochrisiko_ausnahme", "hochrisiko_anhang_iii"}
    assert klasse != "hochrisiko_anhang_iii" or not antworten.get(bedingung)


def test_anhang_i_geht_dem_anhang_iii_vor(durchlauf) -> None:
    """Artikel 6 Absatz 1 steht vor Absatz 2 — und der Filter gilt dort nicht.

    Drei Bedingungen müssen zusammenkommen: ein geregeltes Produkt, die Rolle
    im Produkt und die Beteiligung einer dritten Stelle vor dem Verkauf.
    """
    antworten, _ = fahren(
        durchlauf,
        {
            "ist-es-ein-ki-system": True,
            "natuerliche-personen": False,
            "im-namen-von": False,
            "anhang-i:produkt-faellt-unter-anhang-i": True,
            "anhang-i-gattung:maschinen": True,
            "anhang-i:ki-system-ist-selbst-das-produkt": True,
            "anhang-i:dritte-stelle-verlangt": True,
        },
    )
    befund = durchlauf.ergebnis(antworten)
    assert befund.klasse == "hochrisiko_anhang_i", befund.klasse
    assert "Anhang III" in befund.endtext, "Dass der Filter hier nicht gilt, muss dastehen"
    assert not any(k.startswith("filter:") for k in antworten)


def test_eine_verneinte_bedingung_des_anhangs_i_beendet_den_weg(durchlauf) -> None:
    """Fehlt eine der drei Bedingungen, hilft es nicht, dass die anderen tragen."""
    antworten, _ = fahren(
        durchlauf,
        {
            "ist-es-ein-ki-system": True,
            "natuerliche-personen": False,
            "im-namen-von": False,
            "anhang-i:produkt-faellt-unter-anhang-i": True,
            "anhang-i-gattung:maschinen": True,
            "anhang-i:ki-system-ist-selbst-das-produkt": True,
            # Keine dritte Stelle, keine verstärkte Kontrolle vor dem Verkauf.
        },
    )
    assert durchlauf.anhang_i_befund(antworten) == NICHT_ERFASST
    assert durchlauf.ergebnis(antworten).klasse != "hochrisiko_anhang_i"


def test_jeder_befund_ist_eine_bekannte_klasse(durchlauf) -> None:
    """Eine unbekannte Klasse wäre in der Oberfläche ein leeres Ergebnis."""
    bekannt = {
        "kein_ki_system",
        "kein_hohes_risiko",
        "hochrisiko_anhang_i",
        "hochrisiko_anhang_iii",
        "hochrisiko_ausnahme",
        "hochrisiko_bedingt",
    }
    for antworten in (
        {},
        {"ist-es-ein-ki-system": False},
        LEBENSLAUFSICHTUNG,
        dict(LEBENSLAUFSICHTUNG, **{durchlauf.filterfragen[0].kennung: True}),
    ):
        gegeben, _ = fahren(durchlauf, antworten)
        assert durchlauf.ergebnis(gegeben).klasse in bekannt


def test_eine_bedingung_die_der_nutzer_nicht_wissen_kann_bleibt_offen(durchlauf) -> None:
    """Anhang III Nummer 2 verlangt eine förmliche Benennung als kritische Einrichtung.

    Nach Absatz (191) der Leitlinien muss der Anbieter davon nichts erfahren.
    Ein Nein wäre dort eine falsche Auskunft, ein Ja eine erfundene. Der Befund
    lautet darum "bedingt", und der Nutzer bekommt den Satz dazu, was er in
    seiner Lage zu tun hat.
    """
    antworten, _ = fahren(
        durchlauf,
        {
            "ist-es-ein-ki-system": True,
            "natuerliche-personen": False,
            "im-namen-von": False,
            # Trinkwasserversorgung, mit eigener Schutzaufgabe.
            "haupt:nr-2-infrastruktur:0": True,
            "folge:nr-2-infrastruktur:0:2": True,
            "haupt:nr-2-infrastruktur:2": True,
            "folge:nr-2-infrastruktur:2:0": True,
            # Die Benennung des Betreibers kennt der Anbieter nicht.
            "haupt:nr-2-infrastruktur:1": TRIFFT_NICHT_ZU,
            "folge:nr-2-infrastruktur:1:0": TRIFFT_NICHT_ZU,
            "bereich:KI-VO/anh-III/nr-2": True,
        },
    )
    assert durchlauf.verbundbefund("KI-VO/anh-III/nr-2", antworten) == BEDINGT
    befund = durchlauf.ergebnis(antworten)
    assert befund.klasse == "hochrisiko_bedingt", befund.klasse
    assert befund.endtext, "Der Nutzer erfährt nicht, wovon es noch abhängt"
    assert befund.belege, "Der Vorbehalt steht ohne Fundstelle da"
