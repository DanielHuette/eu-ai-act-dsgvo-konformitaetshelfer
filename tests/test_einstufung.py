"""Prüft die Einstufung — der Teil, der nicht falsch sein darf.

Die Einstufung entscheidet, welche Pflichten ein Nutzer zu lesen bekommt.
Liegt sie falsch, ist die ganze Auskunft falsch, und zwar auf eine Weise, die
der Nutzer nicht erkennen kann. Darum stehen hier zwei Arten von Prüfungen:

* **Alle 44 Anwendungsfälle** aus ``daten/faelle`` werden durch den Prüfer
  geschickt und mit ihrer hinterlegten Einstufung verglichen. Diese Fälle sind
  aus dem Verordnungstext erarbeitet und mit Fundstellen begründet; sie sind
  der Maßstab, nicht eine Meinung.
* **Einzelne Rückfallprüfungen** für Fehler, die schon einmal gemacht wurden.
  Jede trägt im Namen, was schiefging. Sie sind der Grund, warum eine
  Verbesserung der Wortlisten nicht an anderer Stelle wieder etwas kaputt
  macht.
"""

from __future__ import annotations

import pytest

from helfer.einstufung.pruefer import Pruefer, beschreibung_aus_text, rollen_aus_text
from helfer.modell import Risikoklasse, Rolle, Systembeschreibung


def _einstufen(pruefer: Pruefer, text: str, rolle: str | None = None):
    beschreibung = beschreibung_aus_text(text)
    if rolle in Rolle._value2member_map_:
        beschreibung = beschreibung.model_copy(update={"rollen": (Rolle(rolle),)})
    return pruefer.pruefen(beschreibung)


# --------------------------------------------------------- alle Anwendungsfälle


def test_alle_anwendungsfaelle_treffen_ihre_einstufung(pruefer, faelle):
    """Jeder hinterlegte Fall muss seine Einstufung bekommen."""
    abweichungen = []
    for fall in faelle:
        erwartet = fall.get("einstufung")
        if not erwartet:
            continue
        einstufung = _einstufen(pruefer, fall["lage"], fall.get("rolle"))
        bekommen = [k.value for k in einstufung.klassen]
        if erwartet not in bekommen:
            abweichungen.append(
                "{} ({}): erwartet {}, bekommen {}".format(
                    fall["kennung"], fall["_datei"], erwartet, bekommen
                )
            )
    assert not abweichungen, "\n".join(abweichungen)


def test_jeder_fall_bekommt_mindestens_eine_pflicht(pruefer, faelle):
    """Auch ein System mit minimalem Risiko trägt die Pflicht zur KI-Kompetenz."""
    ohne = [
        f["kennung"] for f in faelle if not _einstufen(pruefer, f["lage"], f.get("rolle")).pflichten
    ]
    assert not ohne, f"Fälle ohne jede Pflicht: {ohne}"


def test_fundstellen_der_faelle_stehen_im_korpus(faelle, kennungen):
    """Jede Fundstelle eines Falls muss es im Korpus wirklich geben."""
    fehlend: dict[str, list[str]] = {}
    for fall in faelle:
        stellen = fall.get("rechtsgrundlagen") or fall.get("rechtsgrundlage") or []
        offen = [s for s in stellen if s not in kennungen]
        if offen:
            fehlend[fall["kennung"]] = offen
    assert not fehlend, fehlend


# ------------------------------------------------------- Rückfallprüfungen


def test_bewerbungsfilter_ist_hochrisiko_nicht_minimal(pruefer):
    """Früherer Fehler: "Bewerbungen filtern" traf "Bewerbungen vorsortieren" nicht.

    Das war der teuerste Fehler von allen: ein Hochrisikosystem wurde als
    minimal gemeldet, der Nutzer hätte keine einzige Pflicht erfahren.
    """
    einstufung = _einstufen(
        pruefer,
        "Wir setzen ein Sprachmodell ein, um eingehende Bewerbungen "
        "vorzusortieren und eine Rangfolge der Kandidaten zu erstellen.",
    )
    assert Risikoklasse.HOCHRISIKO_ANHANG_III in einstufung.klassen


def test_kreditwuerdigkeit_landet_nicht_im_bildungsbereich(pruefer):
    """Früherer Fehler: "automatisch" aus "note automatisch" traf jeden Text."""
    einstufung = _einstufen(
        pruefer,
        "Wir prüfen die Kreditwürdigkeit von Antragstellern und "
        "berechnen automatisch einen Punktwert.",
    )
    regeln = {h.regel for h in einstufung.hinweise}
    assert "a3-3-bildung" not in regeln
    assert "a3-5-grundlegende-dienste" in regeln


def test_kamera_auf_foerderband_ist_keine_rechtspflege(pruefer):
    """Früherer Fehler: der Wortstamm "gericht" traf "gerichtet"."""
    einstufung = _einstufen(
        pruefer,
        "Ein Zulieferer prüft gestanzte Blechteile mit einer Kamera auf "
        "Risse. Geprüft werden Teile, nicht Menschen; die Kamera ist "
        "auf das Band gerichtet.",
    )
    assert {h.regel for h in einstufung.hinweise} == {"m-minimal"}


def test_notbremsassistent_ist_kein_dialogsystem(pruefer):
    """Früherer Fehler: "assistent" galt als Hinweis auf ein Gespräch."""
    einstufung = _einstufen(
        pruefer,
        "Ein Zulieferer entwickelt einen Notbremsassistenten. Das System "
        "erkennt Hindernisse aus Kamera- und Radardaten und löst eine "
        "Vollbremsung aus. Das Teil wird als Fahrzeugbauteil in Verkehr "
        "gebracht und unterliegt der Fahrzeugtypgenehmigung.",
        "anbieter",
    )
    assert Risikoklasse.TRANSPARENZ not in einstufung.klassen
    assert Risikoklasse.HOCHRISIKO_ANHANG_I in einstufung.klassen


def test_handbuchuebersetzung_ist_kein_anhang_i_system(pruefer):
    """Früherer Fehler: "Maschine" allein galt als Einbau in ein Produkt."""
    einstufung = _einstufen(
        pruefer,
        "Ein Maschinenbauer übersetzt seine Bedienungshandbücher mit "
        "einem KI-System ins Englische. Die Technische Redaktion prüft "
        "und gibt frei.",
        "anbieter",
    )
    assert Risikoklasse.HOCHRISIKO_ANHANG_I not in einstufung.klassen


def test_lernplattform_im_intranet_bleibt_minimal(pruefer):
    """Früherer Fehler: das Wort "Beschäftigte" allein zog Anhang III Nummer 4."""
    einstufung = _einstufen(
        pruefer,
        "Ein Industriebetrieb bietet seinen Beschäftigten eine "
        "Lernplattform. Ein KI-System schlägt Kurse vor. Die Vorschläge "
        "sind unverbindlich und spielen bei Beurteilung und Beförderung "
        "keine Rolle.",
        "betreiber",
    )
    assert einstufung.klassen == (Risikoklasse.MINIMAL,)


def test_leistungskennzahl_fuer_beschaeftigte_ist_hochrisiko(pruefer):
    """Gegenstück: ohne kennzeichnendes Einzelwort, aber klar Anhang III Nummer 4."""
    einstufung = _einstufen(
        pruefer,
        "Das System erzeugt für jeden Beschäftigten eine Kennzahl aus "
        "Gesprächsdauer und Abschlussquote und ordnet die Beschäftigten "
        "in drei Gruppen ein. Grundlage für die variable Vergütung.",
        "betreiber",
    )
    assert Risikoklasse.HOCHRISIKO_ANHANG_III in einstufung.klassen


def test_kundenfreitext_ist_keine_verbotene_emotionserkennung(pruefer):
    """Artikel 3 Nummer 39 setzt biometrische Daten voraus — Text ist keine."""
    einstufung = _einstufen(
        pruefer,
        "Wir werten die Stimmung in Freitextantworten unserer "
        "Kundenumfrage aus, um die Zufriedenheit zu messen.",
    )
    assert Risikoklasse.VERBOTEN not in einstufung.klassen


def test_emotionen_aus_mimik_im_bewerbungsgespraech_ist_verboten(pruefer):
    """Gegenstück: Mimik und Stimme sind biometrische Träger, Artikel 5 Absatz 1 f."""
    einstufung = _einstufen(
        pruefer,
        "Ein KI-System wertet im aufgezeichneten Videointerview Mimik "
        "und Stimme aus und gibt Hinweise auf Begeisterung, Unsicherheit "
        "und Belastbarkeit des Bewerbers.",
        "betreiber",
    )
    assert Risikoklasse.VERBOTEN in einstufung.klassen


def test_muedigkeitserkennung_bei_fahrern_ist_nicht_verboten(pruefer):
    """Artikel 5 Absatz 1 Buchstabe f nimmt Sicherheitsgründe aus."""
    einstufung = _einstufen(
        pruefer,
        "Eine Kamera im Führerhaus erkennt Müdigkeit des Fahrers und "
        "warnt ihn aus Sicherheitsgründen vor dem Einschlafen.",
        "betreiber",
    )
    assert Risikoklasse.VERBOTEN not in einstufung.klassen


def test_ausnahme_wird_nicht_von_allein_angenommen(pruefer):
    """Artikel 6 Absatz 3 greift nur bei erkannter enger Aufgabe ohne Einfluss."""
    einstufung = _einstufen(
        pruefer,
        "Wir bewerten Bewerbungen und lehnen unter einem Schwellenwert automatisch ab.",
        "betreiber",
    )
    assert Risikoklasse.HOCHRISIKO_AUSNAHME not in einstufung.klassen
    assert Risikoklasse.HOCHRISIKO_ANHANG_III in einstufung.klassen


def test_ausnahme_und_anhang_iii_stehen_nie_zusammen(pruefer, faelle):
    """Beide Klassen zugleich wäre ein Widerspruch in der Auskunft."""
    for fall in faelle:
        klassen = set(_einstufen(pruefer, fall["lage"], fall.get("rolle")).klassen)
        assert not (
            {Risikoklasse.HOCHRISIKO_AUSNAHME, Risikoklasse.HOCHRISIKO_ANHANG_III} <= klassen
        ), fall["kennung"]


# -------------------------------------------------------- Merkmalsfilter


def test_bewerbungsfilter_bekommt_keine_biometriepflichten(pruefer):
    """Artikel 26 Absatz 10 setzt Biometrie und Strafverfolgung voraus."""
    einstufung = _einstufen(
        pruefer, "Wir sortieren Bewerbungen mit einem Sprachmodell vor.", "betreiber"
    )
    kennungen = {p.kennung for p in einstufung.pflichten}
    assert "p-betr-hr-nachtraegliche-biometrie-genehmigung" not in kennungen
    assert "p-verbot-echtzeit-biometrie-genehmigung" not in kennungen


def test_zutrittskontrolle_bekommt_keine_strafverfolgungspflicht(pruefer):
    """Biometrie allein genügt nicht: Artikel 26 Absatz 10 verlangt mehr."""
    einstufung = _einstufen(
        pruefer,
        "Gesichtserkennung zur Zutrittskontrolle am Werkstor für unsere Beschäftigten.",
        "betreiber",
    )
    kennungen = {p.kennung for p in einstufung.pflichten}
    assert "p-betr-hr-nachtraegliche-biometrie-genehmigung" not in kennungen


def test_merkmalsgebundene_pflicht_wird_mit_vorbehalt_genannt(pruefer):
    """Was offen bleibt, wird genannt — mit Vorbehalt, nicht weggelassen."""
    einstufung = _einstufen(
        pruefer, "Wir sortieren Bewerbungen mit einem Sprachmodell vor.", "betreiber"
    )
    mit_vorbehalt = [p for p in einstufung.pflichten if p.vorbehalt]
    assert mit_vorbehalt, "Keine Pflicht trägt einen Vorbehalt"
    for pflicht in mit_vorbehalt:
        assert len(pflicht.vorbehalt) > 30


# ------------------------------------------------------------ Grundsätze


def test_leere_beschreibung_liefert_offene_fragen_statt_einer_zahl(pruefer):
    """Ohne Angaben darf keine Einstufung behauptet werden."""
    einstufung = pruefer.pruefen(Systembeschreibung())
    assert einstufung.offene_fragen


def test_ohne_rollenangabe_werden_beide_sichten_geliefert(pruefer):
    """Wer nichts sagt, bekommt Anbieter- und Betreiberpflichten."""
    einstufung = _einstufen(pruefer, "Wir sortieren Bewerbungen vor.")
    rollen = {r for p in einstufung.pflichten for r in p.rollen}
    assert {Rolle.ANBIETER, Rolle.BETREIBER} <= rollen


def test_jede_pflicht_tragt_eine_fundstelle_aus_dem_korpus(pruefer, faelle, kennungen):
    """Keine Pflicht ohne nachprüfbare Rechtsgrundlage."""
    fehlend: set[str] = set()
    for fall in faelle:
        for pflicht in _einstufen(pruefer, fall["lage"], fall.get("rolle")).pflichten:
            fehlend |= {s for s in pflicht.rechtsgrundlage if s and s not in kennungen}
    assert not fehlend, f"Fundstellen ohne Korpuseintrag: {sorted(fehlend)}"


def test_rollenerkennung_bleibt_zurueckhaltend():
    """ "Wir kaufen ein" ist Betreiber, "wir entwickeln" Anbieter, sonst nichts."""
    assert rollen_aus_text("Wir entwickeln ein KI-System und bringen es in Verkehr.") == (
        Rolle.ANBIETER,
    )
    assert rollen_aus_text("Wir kaufen ein KI-System ein und setzen es ein.") == (Rolle.BETREIBER,)
    assert rollen_aus_text("Guten Tag, eine Frage zur Verordnung.") == ()


@pytest.mark.parametrize("klasse", [k for k in Risikoklasse if k is not Risikoklasse.UNKLAR])
def test_jede_risikoklasse_hat_mindestens_eine_pflicht(pruefer, klasse):
    """Eine Klasse ohne Pflichten wäre eine Lücke in der Matrix.

    ``UNKLAR`` ist ausgenommen: das ist kein Rechtszustand, sondern die
    Aussage "aus dieser Beschreibung lässt sich nichts einstufen". Dort muss
    der Helfer nachfragen statt Pflichten aufzuzählen — das prüft
    ``test_leere_beschreibung_liefert_offene_fragen_statt_einer_zahl``.
    """
    pflichten = pruefer._pflichten({klasse}, {Rolle.ANBIETER, Rolle.BETREIBER})
    assert pflichten, f"Klasse ohne Pflichten: {klasse.value}"


def test_unklar_fuehrt_zu_keiner_pflichtenliste(pruefer):
    """Gegenstück: bei UNKLAR darf nichts behauptet werden."""
    assert pruefer._pflichten({Risikoklasse.UNKLAR}, {Rolle.ANBIETER}) == []


# ------------------------------------------------- Regelwerk gegen den Korpus


def test_jede_fundstelle_der_regeln_steht_im_korpus(pruefer, kennungen):
    """Keine Regel darf auf eine Norm zeigen, die es im Korpus nicht gibt."""
    fehlend: dict[str, list[str]] = {}
    for satz in list(pruefer.werk.pflichten) + list(pruefer.werk.datenschutz):
        stellen = list(satz.get("rechtsgrundlage", [])) + list(satz.get("auch_genannt", []))
        offen = [s for s in stellen if s and s not in kennungen]
        if offen:
            fehlend[satz["kennung"]] = offen
    assert not fehlend, fehlend


def test_jeder_verweis_im_handlungstext_ist_belegt(pruefer, korpus):
    """Was der Handlungstext als Artikel nennt, muss auch als Beleg dastehen.

    Früherer Fehler: Artikel 26 Absatz 5 KI-VO leitet für die Information des
    Anbieters auf Artikel 72 weiter. Der Pflichttext nannte Artikel 72, die
    Fundstellen nicht — die Antwort hätte eine Fundstelle genannt, zu der kein
    Beleg vorlag. Genau das meldet ``erfundene_fundstellen`` als Erfindung.

    Artikel, die die Verordnung selbst nicht enthält, bleiben ausgenommen: ein
    Verweis auf eine andere Verordnung ist kein Beleg aus diesem Korpus.
    """
    import re as _re

    kennungen = {e.kennung for e in korpus}
    luecken: dict[str, list[str]] = {}
    for datei, saetze, stamm in (
        ("kivo_pflichten", pruefer.werk.pflichten, "KI-VO"),
        ("dsgvo_pruefpfad", pruefer.werk.datenschutz, "DSGVO"),
    ):
        for satz in saetze:
            gedeckt = {
                t.split("art-")[1].split("/")[0]
                for t in (
                    list(satz.get("rechtsgrundlage", [])) + list(satz.get("auch_genannt", []))
                )
                if "art-" in t
            }
            genannt = set(_re.findall(r"Artikel (\d{1,3})", str(satz.get("was_zu_tun_ist", ""))))
            offen = [
                n for n in sorted(genannt - gedeckt, key=int) if f"{stamm}/art-{n}" in kennungen
            ]
            if offen:
                luecken["{}/{}".format(datei, satz["kennung"])] = offen
    assert not luecken, luecken
