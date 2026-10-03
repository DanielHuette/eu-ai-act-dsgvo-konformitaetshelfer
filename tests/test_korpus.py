"""Prüft den aufbereiteten Rechtstext.

Der Korpus ist die Grundlage von allem: jede Pflicht, jede Fundstelle, jeder
Beleg in einer Antwort zeigt auf eine Einheit darin. Ist er lückenhaft oder
doppelt belegt, zitiert der Helfer falsch, ohne es zu merken.

Die Zahlen hier sind nachgemessen, nicht geschätzt: die KI-Verordnung hat 113
Artikel, 13 Anhänge und 180 Erwägungsgründe; die Datenschutz-Grundverordnung 99
Artikel und 173 Erwägungsgründe.
"""

from __future__ import annotations

import re
from collections import Counter

import pytest

from helfer.korpus.deutsche_quellen import beiwerk_abschneiden
from helfer.modell import Einheitsart, Rechtsakt

#: Was im Korpus stehen muss, damit er vollständig ist.
ERWARTET = {
    (Rechtsakt.KI_VO, Einheitsart.ARTIKEL): 113,
    (Rechtsakt.KI_VO, Einheitsart.ANHANG): 13,
    (Rechtsakt.KI_VO, Einheitsart.ERWAEGUNGSGRUND): 180,
    (Rechtsakt.DSGVO, Einheitsart.ARTIKEL): 99,
    (Rechtsakt.DSGVO, Einheitsart.ERWAEGUNGSGRUND): 173,
}


def _stammzahlen(korpus) -> Counter:
    """Zählt nur die Stammeinheiten, nicht ihre Absätze."""
    return Counter((e.rechtsakt, e.art) for e in korpus if e.absatz is None)


@pytest.mark.parametrize(
    "schluessel,anzahl", sorted(ERWARTET.items(), key=lambda p: (p[0][0].value, p[0][1].value))
)
def test_bestand_ist_vollstaendig(korpus, schluessel, anzahl):
    """Jede Zählung muss stimmen — eine fehlende Norm fällt sonst nicht auf."""
    gezaehlt = _stammzahlen(korpus)[schluessel]
    assert gezaehlt == anzahl, (
        f"{schluessel[0].value} {schluessel[1].value}: {gezaehlt:d} statt {anzahl:d}"
    )


def test_keine_doppelten_kennungen(korpus):
    """Eine Kennung muss genau eine Einheit bezeichnen.

    Sonst zeigt eine Fundstelle in der Antwort auf zwei verschiedene Texte, und
    welcher davon gemeint ist, hängt an der Reihenfolge im Speicher.
    """
    doppelt = [k for k, n in Counter(e.kennung for e in korpus).items() if n > 1]
    assert not doppelt, f"Doppelte Kennungen ({len(doppelt):d}): {sorted(doppelt)[:20]}"


def test_kennungen_haben_die_vereinbarte_form(korpus):
    """``KI-VO/art-6/abs-3`` — darauf verlassen sich Regeln und Fundstellenweg."""
    # Erlaubt sind drei Formen:
    #   Rechtsakt/Einheit            KI-VO/art-6, KI-VO/anh-III, DSGVO/erw-71
    #   dazu ein Punkt              KI-VO/art-6/abs-3, DSGVO/art-13/abs-1-a,
    #                               KI-VO/anh-III/nr-4, KI-VO/anh-X/nr-a
    #   Anwendungsfall              fall/<sprechende-kennung>
    form = re.compile(
        r"^((KI-VO|DSGVO|BDSG|Leitlinie)/"
        r"(art|anh|erw|par)-[0-9A-Za-z]+"
        r"(/(abs|nr)-([0-9]+(-[a-z]{1,2})?|[a-z]{1,2}))?"
        r"|fall/[a-z0-9\-]+)$"
    )
    verstoesse = [e.kennung for e in korpus if not form.match(e.kennung)]
    assert not verstoesse, f"Kennungen in fremder Form ({len(verstoesse):d}): {verstoesse[:15]}"


def test_kein_text_ist_leer_oder_winzig(korpus):
    """Eine Einheit ohne Inhalt wäre ein leerer Beleg in der Antwort."""
    duenn = [(e.kennung, len(e.text)) for e in korpus if len(e.text.strip()) < 25]
    assert not duenn, duenn[:15]


def test_kein_seitenbeiwerk_im_normtext(korpus):
    """Reste der Webseite dürfen nicht im Rechtstext stehen."""
    verraeter = (
        "Fehler melden",
        "Passende Erwägungsgründe",
        "Cookies",
        "Diese Website verwendet",
        "Inhaltsverzeichnis",
        "Zum Inhalt springen",
    )
    getroffen = [(e.kennung, w) for e in korpus for w in verraeter if w in e.text]
    assert not getroffen, getroffen[:10]


def test_jede_einheit_nennt_ihre_quelle(korpus):
    """Ohne Quelle lässt sich eine Angabe nicht nachprüfen."""
    ohne = [e.kennung for e in korpus if not e.quelle]
    assert not ohne, f"Einheiten ohne Quelle ({len(ohne):d}): {ohne[:10]}"


def test_absaetze_haengen_an_einem_vorhandenen_stamm(korpus):
    """Ein Absatz ohne seinen Artikel wäre eine Fundstelle ins Leere."""
    kennungen = {e.kennung for e in korpus}
    verwaist = [
        e.kennung
        for e in korpus
        if e.absatz is not None and e.kennung.rsplit("/", 1)[0] not in kennungen
    ]
    assert not verwaist, verwaist[:15]


def test_fundstelle_wird_zitierfaehig_gebildet(korpus):
    """Was in der Antwort steht, muss ein Jurist wiederfinden können."""
    nach_kennung = {e.kennung: e for e in korpus}
    proben = {
        "KI-VO/art-6/abs-3": "Artikel 6 Absatz 3 KI-VO",
        "KI-VO/anh-III": "Anhang III KI-VO",
        "DSGVO/art-9": "Artikel 9 DSGVO",
    }
    for kennung, erwartet in proben.items():
        einheit = nach_kennung.get(kennung)
        if einheit is None:
            pytest.skip(f"Probe {kennung} fehlt im Korpus")
        assert einheit.fundstelle == erwartet


def test_erwaegungsgrund_wird_nicht_als_artikel_zitiert(korpus):
    """Ein Erwägungsgrund ist kein Artikel — die Verwechslung wäre peinlich."""
    for einheit in korpus:
        if einheit.art is Einheitsart.ERWAEGUNGSGRUND:
            assert einheit.fundstelle.startswith("Erwägungsgrund")


def test_anhangspunkte_zaehlen_als_nummer_nicht_als_absatz(korpus):
    """Anhang III Nummer 4 — nicht "Anhang III Absatz 4"."""
    punkte = [e for e in korpus if e.art is Einheitsart.ANHANG and e.absatz]
    if not punkte:
        pytest.skip("Keine Anhangspunkte im Korpus")
    for einheit in punkte:
        assert "Nummer" in einheit.fundstelle
        assert "Absatz" not in einheit.fundstelle


def test_schluesselnormen_sind_da_und_tragen_ihren_inhalt(korpus):
    """Ohne diese Normen kann der Helfer seine Arbeit nicht tun."""
    nach_kennung = {e.kennung: e for e in korpus}
    proben = {
        "KI-VO/art-5": "verboten",
        "KI-VO/art-6": "hochrisiko",
        "KI-VO/art-50": "transparenz",
        "KI-VO/anh-III": "",
        "DSGVO/art-22": "automatisierten",
        "DSGVO/art-35": "folgenabschätzung",
    }
    for kennung, wort in proben.items():
        assert kennung in nach_kennung, f"fehlt im Korpus: {kennung}"
        if wort:
            assert wort in nach_kennung[kennung].text.lower(), kennung


# ------------------------------------------------------ Zerleger für sich


def test_beiwerk_wird_am_ersten_treffer_abgeschnitten():
    """Der Schnitt muss vor dem Beiwerk sitzen, nicht irgendwo darin."""
    text = (
        "(1) Dies ist der Normtext.\n\nPassende Erwägungsgründe\nErwägungsgrund 42\nFehler melden"
    )
    assert beiwerk_abschneiden(text) == "(1) Dies ist der Normtext."


def test_navigationszeilen_verschwinden():
    """ "← Art. 21 DSGVO" am Textende ist Navigation, nicht Normtext."""
    text = "(1) Der Normtext steht hier.\n← Art. 21 DSGVO\n"
    assert "Art. 21" not in beiwerk_abschneiden(text)


def test_normtext_ohne_beiwerk_bleibt_unangetastet():
    """Was kein Beiwerk enthält, darf nicht beschnitten werden."""
    text = "(1) Die Verarbeitung ist rechtmäßig, wenn eine Bedingung erfüllt ist."
    assert beiwerk_abschneiden(text) == text
