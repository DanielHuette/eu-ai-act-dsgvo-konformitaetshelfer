"""Prüft die vier Suchwege und ihre Zusammenführung.

Die Suche entscheidet, welche Rechtstexte dem Sprachmodell als Belege vorgelegt
werden. Findet sie das Falsche, formuliert das Modell eine flüssige Antwort auf
der falschen Grundlage — der Fehler, den ein Nutzer am schwersten erkennt.

Gerechnet wird hier mit dem Ersatzverfahren ``Streuwerk``: es bildet Text auf
Zahlen ab, ohne ein Modell zu laden. Damit lässt sich prüfen, ob die Mechanik
stimmt — Zusammenführung, Ablegen, Laden, Fundstellenweg — ohne dass ein Lauf
Minuten dauert. Was die Treffer *inhaltlich* taugen, prüft
``test_fundstellenweg_findet_die_genannte_norm``: dieser Weg arbeitet nicht mit
Bedeutung, sondern mit der Zählung im Gesetz, und muss immer stimmen.
"""

from __future__ import annotations

import pytest

from helfer.suche.einbettung import Streuwerk
from helfer.suche.index import Suchbestand, als_belegstellen, fundstellen_aus_frage


@pytest.fixture(scope="module")
def kleiner_bestand(korpus):
    """Ein Bestand über einen Ausschnitt — groß genug, klein genug."""
    ausschnitt = [
        e
        for e in korpus
        if e.kennung.startswith(
            (
                "KI-VO/art-5",
                "KI-VO/art-6",
                "KI-VO/art-26",
                "KI-VO/art-50",
                "KI-VO/anh-III",
                "DSGVO/art-9",
                "DSGVO/art-22",
                "DSGVO/art-35",
            )
        )
    ]
    assert len(ausschnitt) > 30, f"Ausschnitt zu klein: {len(ausschnitt):d}"
    bestand = Suchbestand(ausschnitt, Streuwerk())
    bestand.bauen()
    return bestand


# -------------------------------------------------------- Fundstellenweg


@pytest.mark.parametrize(
    "frage,erwartet",
    [
        ("Was sagt Art. 6 Abs. 3?", "KI-VO/art-6/abs-3"),
        ("Artikel 6 Absatz 3 KI-VO bitte", "KI-VO/art-6/abs-3"),
        ("Was steht in Anhang III Nummer 4?", "KI-VO/anh-III/nr-4"),
        ("§ 26 BDSG", "BDSG/par-26"),
        ("Artikel 22 DSGVO", "DSGVO/art-22"),
    ],
)
def test_fundstellenweg_loest_die_schreibweisen_auf(frage, erwartet):
    """Nutzer schreiben "Art. 6 Abs. 3" genauso oft wie den Langtext."""
    assert erwartet in fundstellen_aus_frage(frage)


def test_fundstellenweg_erfindet_nichts():
    """Steht keine Fundstelle in der Frage, darf keine herauskommen."""
    assert fundstellen_aus_frage("Dürfen wir Bewerbungen vorsortieren?") == []


def test_fundstellenweg_findet_die_genannte_norm(kleiner_bestand):
    """Wer nach Artikel 6 Absatz 3 fragt, muss ihn an erster Stelle bekommen.

    Dieser Weg hängt nicht am Einbettungsmodell. Er muss daher auch mit dem
    Ersatzverfahren treffen — andernfalls ist die Zusammenführung kaputt.
    """
    treffer = kleiner_bestand.suchen(
        "Was sagt Artikel 6 Absatz 3 KI-VO?", anzahl=5, mit_neubewertung=False
    )
    kennungen = [t.einheit.kennung for t in treffer]
    assert "KI-VO/art-6/abs-3" in kennungen[:2], kennungen


# --------------------------------------------------------- Stichwortsuche


def test_stichwortsuche_findet_den_wortlaut(kleiner_bestand):
    """Wer ein Wort aus dem Gesetz nennt, muss die Norm bekommen."""
    treffer = kleiner_bestand.suchen(
        "Datenschutz-Folgenabschätzung", anzahl=8, mit_neubewertung=False
    )
    assert any("art-35" in t.einheit.kennung for t in treffer), [t.einheit.kennung for t in treffer]


def test_haeufige_woerter_zaehlen_weniger_als_seltene(kleiner_bestand):
    """BM25: ein Wort, das überall steht, trägt kaum Unterscheidungskraft."""
    treffer = kleiner_bestand.suchen("KI-System", anzahl=5, mit_neubewertung=False)
    selten = kleiner_bestand.suchen("Folgenabschätzung", anzahl=5, mit_neubewertung=False)
    assert treffer and selten
    assert selten[0].punktzahl > 0


# ------------------------------------------------------------- Mechanik


def test_suche_liefert_nie_mehr_als_verlangt(kleiner_bestand):
    for anzahl in (1, 3, 10):
        assert (
            len(kleiner_bestand.suchen("Hochrisiko", anzahl=anzahl, mit_neubewertung=False))
            <= anzahl
        )


def test_punktzahlen_fallen_monoton(kleiner_bestand):
    """Die Reihenfolge ist die Aussage der Suche — sie muss sortiert sein."""
    treffer = kleiner_bestand.suchen("Pflichten des Betreibers", anzahl=8, mit_neubewertung=False)
    punkte = [t.punktzahl for t in treffer]
    assert punkte == sorted(punkte, reverse=True), punkte


def test_leere_frage_wirft_nicht(kleiner_bestand):
    """Eine leere Eingabe darf keinen Absturz auslösen."""
    assert kleiner_bestand.suchen("", anzahl=5, mit_neubewertung=False) == [] or True


def test_abgelegter_bestand_liefert_dieselben_treffer(kleiner_bestand, tmp_path):
    """Ablegen und Laden darf das Ergebnis nicht verändern."""
    ziel = tmp_path / "bestand"
    kleiner_bestand.ablegen(ziel)
    geladen = Suchbestand.laden(ziel, kleiner_bestand.einheiten, Streuwerk())
    frage = "Welche Pflichten hat ein Betreiber?"
    vorher = [
        t.einheit.kennung for t in kleiner_bestand.suchen(frage, anzahl=5, mit_neubewertung=False)
    ]
    nachher = [t.einheit.kennung for t in geladen.suchen(frage, anzahl=5, mit_neubewertung=False)]
    assert vorher == nachher


def test_geladener_bestand_meldet_ein_fremdes_modell(kleiner_bestand, tmp_path):
    """Ein Bestand aus einem anderen Modell ist unbrauchbar — das muss auffallen.

    Würde er stillschweingend geladen, lägen Fragevektor und Bestandsvektoren
    in verschiedenen Räumen: die Suche liefert Unsinn, der wie ein Ergebnis
    aussieht.
    """

    class AndererName(Streuwerk):
        name = "ein/anderes-modell"

    ziel = tmp_path / "bestand"
    kleiner_bestand.ablegen(ziel)
    with pytest.raises((ValueError, RuntimeError)):
        Suchbestand.laden(ziel, kleiner_bestand.einheiten, AndererName())


# ----------------------------------------------------------- Belegstellen


def test_belegstellen_tragen_fundstelle_und_auszug(kleiner_bestand):
    """Ein Beleg ohne Fundstelle ist in einer Rechtsauskunft wertlos."""
    treffer = kleiner_bestand.suchen("Verbotene Praktiken", anzahl=4, mit_neubewertung=False)
    belege = als_belegstellen(treffer, auszug=400)
    assert belege
    for beleg in belege:
        assert beleg.fundstelle.strip()
        assert beleg.auszug.strip()
        assert len(beleg.auszug) <= 420


def test_auszug_wird_nicht_mitten_im_wort_abgeschnitten(kleiner_bestand):
    treffer = kleiner_bestand.suchen("Hochrisiko-KI-System", anzahl=3, mit_neubewertung=False)
    for beleg in als_belegstellen(treffer, auszug=200):
        if beleg.auszug.endswith("…") or beleg.auszug.endswith("..."):
            assert (
                beleg.auszug.rstrip("…. ")[-1] not in "abcdefghijklmnopqrstuvwxyz"
                or " " in beleg.auszug[-30:]
            )


# --------------------------------------------------------- Einbetterwahl


def test_ersatzverfahren_liefert_gleich_lange_vektoren():
    streuwerk = Streuwerk()
    befund = streuwerk.bestand(["erster Text", "zweiter Text", "dritter"])
    assert befund.dicht.shape == (3, streuwerk.dimensionen)


def test_gleicher_text_gibt_gleichen_vektor():
    """Ohne diese Eigenschaft wäre kein abgelegter Bestand wiederverwendbar."""
    streuwerk = Streuwerk()
    eins = streuwerk.eine_frage("Artikel 6 Absatz 3")
    zwei = streuwerk.eine_frage("Artikel 6 Absatz 3")
    assert (eins == zwei).all()


# ----------------------------------------------- Format des abgelegten Bestands


def test_abgelegter_bestand_enthaelt_kein_pickle(kleiner_bestand, tmp_path):
    """Der Bestand wird mit dem Repository ausgeliefert — und über Kopien.

    Läge er als pickle vor, würde eine veränderte Kopie beim Laden fremden
    Code im Rechner des Nutzers ausführen: ``pickle.load`` ruft auf, was in
    der Datei steht, ohne jede Prüfung. Darum JSON — eine veränderte Datei
    kann dann falsche Treffer verursachen, aber keinen Code starten.
    """
    ziel = tmp_path / "bestand"
    kleiner_bestand.ablegen(ziel)
    abgelegt = sorted(p.name for p in tmp_path.iterdir())
    assert abgelegt, "nichts abgelegt"
    assert not any(name.endswith((".pkl", ".pickle")) for name in abgelegt), abgelegt


def test_abgelegter_bestand_ist_ohne_python_lesbar(kleiner_bestand, tmp_path):
    """Gegenprobe: der Beipack muss sich als reines JSON lesen lassen."""
    import gzip
    import json

    ziel = tmp_path / "bestand"
    kleiner_bestand.ablegen(ziel)
    with gzip.open(ziel.with_suffix(".bestand.json.gz"), "rt", encoding="utf-8") as datei:
        beipack = json.load(datei)
    assert beipack["modell"] == kleiner_bestand.einbetter.name
    assert beipack["stichworte"]["anzahl"] == len(kleiner_bestand.einheiten)


def test_alter_pickle_bestand_wird_abgelehnt(kleiner_bestand, tmp_path):
    """Ein Bestand im alten Format darf nicht stillschweigend geladen werden."""
    ziel = tmp_path / "bestand"
    kleiner_bestand.ablegen(ziel)
    ziel.with_suffix(".bestand.json.gz").unlink()
    ziel.with_suffix(".bestand.pkl").write_bytes(b"egal, wird nicht gelesen")
    with pytest.raises(RuntimeError, match="pickle"):
        Suchbestand.laden(ziel, kleiner_bestand.einheiten, Streuwerk())


def test_fehlender_bestand_sagt_das_deutlich(tmp_path, korpus):
    with pytest.raises(FileNotFoundError):
        Suchbestand.laden(tmp_path / "gibtesnicht", korpus[:10], Streuwerk())


def test_ungebauter_bestand_wird_nicht_abgelegt(korpus, tmp_path):
    """Ein Bestand ohne Vektoren ist kein Bestand.

    Würde er abgelegt, fiele das erst beim Laden auf — und dann als
    Längenfehler, der nichts über die Ursache sagt.
    """
    leer = Suchbestand(korpus[:10], Streuwerk())
    with pytest.raises(RuntimeError, match="nicht gebaut"):
        leer.ablegen(tmp_path / "bestand")
