#!/usr/bin/env python3
"""Baut die App-Datenbank für den Konformitätshelfer auf dem Telefon.

Aus dem Rechtsbestand (korpus.jsonl), den Regeldateien und den Anwendungsfällen
entsteht eine einzige SQLite-Datei, die als Beigabe (Asset) in die App wandert,
dazu der Einbetter als ONNX-Modell und sein Wortschatz.

Warum alles in eine Datei und nicht in einen Server: Rechtsauskunft ist eine
heikle Angelegenheit. Wer sein KI-System beschreibt, verrät dabei
Geschäftsinterna. Das darf das Gerät nicht verlassen. Also rechnet das Telefon
selbst, und dafür muss alles mitgeliefert werden.

Aufruf:
    python3 scripts/export_android.py

Ohne sentence-transformers bricht das Skript ab. Es schreibt dann KEINE
halbfertige Datenbank: eine Datenbank mit leeren Vektoren sieht heil aus und
liefert im Betrieb stillschweigend falsche Treffer. Besser kein Ergebnis als
ein unbemerkt falsches.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
import struct
import sys
import time
from datetime import date
from pathlib import Path
from typing import Any

# --------------------------------------------------------------------- Pfade

WURZEL = Path(__file__).resolve().parent.parent
KORPUS = WURZEL / "daten" / "aufbereitet" / "korpus.jsonl"
REGELN = WURZEL / "daten" / "regeln"
FAELLE = WURZEL / "daten" / "faelle"
BEIGABEN = WURZEL / "android" / "app" / "src" / "main" / "assets"
ZIEL_DB = BEIGABEN / "recht.db"
ZIEL_ONNX = BEIGABEN / "einbetter.onnx"
ZIEL_WORTSCHATZ = BEIGABEN / "tokenizer.json"
BEFUND = WURZEL / "daten" / "aufbereitet" / "android_export_befund.json"

#: Dasselbe Modell, das die Weboberfläche für den Telefonbetrieb vorsieht.
#: 384 Zahlen je Einheit sind der Kompromiss, der auf ein Telefon passt.
MODELL = "intfloat/multilingual-e5-small"
#: Die genaue Fassung des Modells, als Prüfsumme des Stands auf dem Hub.
#: Ohne diese Angabe holt jeder Bau "die neueste Fassung" — und wenn der
#: Anbieter das Modell ändert, erzeugt derselbe Quelltext eine andere
#: Datenbank. Die mitgelieferten Zahlenreihen passten dann nicht mehr zu dem
#: Modell, mit dem die App rechnet, und die Suche lieferte stillen Unsinn.
#: Zum Heraufsetzen: huggingface_hub.model_info(MODELL).sha ablesen, Export
#: neu laufen lassen, Prüfsummen im Befund vergleichen.
MODELL_FASSUNG = "614241f622f53c4eeff9890bdc4f31cfecc418b3"
DIMENSIONEN = 384

#: e5-Modelle sind mit diesen Vorsilben trainiert. Ohne sie fällt die
#: Trefferqualität messbar ab, weil Frage und Bestand im Training
#: unterschiedlich markiert waren.
VORSILBE_BESTAND = "passage: "
VORSILBE_FRAGE = "query: "

#: Mehr als das liest das Modell nicht; längere Artikel werden abgeschnitten.
#: Der Anfang eines Artikels trägt den Sinn, die Aufzählungen am Ende
#: wiederholen ihn meist.
MAX_WORTMARKEN = 512


# ------------------------------------------------------------------- Laden


#: Nur diese Namen dürfen in eine SQL-Abfrage eingesetzt werden:
#: Kleinbuchstaben und Unterstrich, nichts weiter. Siehe die Prüfung in
#: der Zeilenzählung weiter unten.
ZULAESSIGE_TABELLEN = re.compile(r"[a-z_]{3,30}")


def fundstelle(einheit: dict[str, Any]) -> str:
    """Wie die Stelle in einer Antwort zitiert wird.

    Gleich gebaut wie Einheit.fundstelle in src/helfer/modell.py. Weicht die
    Schreibweise ab, findet die Fundstellensuche der App eine genannte Stelle
    nicht mehr, weil sie auf genau diese Form trifft.
    """
    art = einheit["art"]
    if art == "fallbeispiel":
        # Ein Anwendungsfall hat keine Fundstelle im Gesetz. Zitiert wird er
        # mit seinem Titel; stünde hier die interne Kennung, läse der Nutzer
        # in der Belegliste "antragspruefung-behoerde" statt eines Satzes.
        return "Anwendungsfall: %s" % (einheit.get("titel") or einheit["nummer"])
    stamm = {
        "artikel": "Artikel %s",
        "paragraf": "§ %s",
        "anhang": "Anhang %s",
        "erwaegungsgrund": "Erwägungsgrund %s",
    }.get(art, "%s")
    teil = stamm % einheit["nummer"]
    if einheit.get("absatz"):
        # Die Anhänge der KI-Verordnung sind nach Nummern gegliedert, nicht
        # nach Absätzen - "Anhang III Nummer 4" ist die Schreibweise der
        # Verordnung selbst. Eine Auskunft, die hier "Absatz" sagt, zitiert
        # falsch, und eine falsch zitierte Fundstelle kostet das Vertrauen in
        # die ganze Auskunft.
        teil += (" Nummer %s" if art == "anhang" else " Absatz %s") % einheit["absatz"]
    return "{} {}".format(teil, einheit["rechtsakt"])


def laden_korpus() -> list[dict[str, Any]]:
    if not KORPUS.exists():
        abbruch(f"Der Rechtsbestand fehlt: {KORPUS}")
    einheiten = []
    with KORPUS.open(encoding="utf-8") as datei:
        for nummer, zeile in enumerate(datei, 1):
            zeile = zeile.strip()
            if not zeile:
                continue
            try:
                einheiten.append(json.loads(zeile))
            except json.JSONDecodeError as fehler:
                abbruch(f"korpus.jsonl Zeile {nummer:d} ist kein gültiges JSON: {fehler}")
    if not einheiten:
        abbruch("korpus.jsonl ist leer")
    return einheiten


def laden_yaml(pfad: Path) -> Any:
    try:
        import yaml
    except ImportError:
        abbruch("PyYAML fehlt. Installieren mit: pip install pyyaml")
    if not pfad.exists():
        abbruch(f"Regeldatei fehlt: {pfad}")
    with pfad.open(encoding="utf-8") as datei:
        return yaml.safe_load(datei)


def abbruch(nachricht: str) -> None:
    print(f"ABBRUCH: {nachricht}", file=sys.stderr)
    sys.exit(1)


def suchtext(einheit: dict[str, Any]) -> str:
    """Was eingebettet wird: Fundstelle, Titel, Kapitel und Text zusammen.

    Die Fundstelle gehört in den eingebetteten Text, weil Fragen sie oft
    nennen. Stünde sie nur in einer Spalte daneben, fände die Vektorsuche
    "Artikel 9" nicht. Gleich gebaut wie Bestand._suchtext im Python-Teil,
    damit beide Seiten dieselben Vektoren erzeugen.
    """
    kopf = [fundstelle(einheit)]
    if einheit.get("titel"):
        kopf.append(einheit["titel"])
    if einheit.get("kapitel"):
        kopf.append(einheit["kapitel"])
    return "{}\n{}".format(" — ".join(kopf), einheit["text"])


# ---------------------------------------------------------------- Tabellen

SCHEMA = """
PRAGMA journal_mode = DELETE;
PRAGMA page_size = 4096;

-- Der Rechtsbestand. nummer ist die laufende Nummer und gleichzeitig die
-- rowid; die Vektoren liegen in derselben Reihenfolge, damit ein Treffer der
-- Vektorsuche ohne Umweg auf seine Einheit zeigt.
CREATE TABLE einheit (
    nummer    INTEGER PRIMARY KEY,
    kennung   TEXT NOT NULL UNIQUE,
    rechtsakt TEXT NOT NULL,
    art       TEXT NOT NULL,
    nummer_im_akt TEXT NOT NULL,
    absatz    TEXT,
    titel     TEXT NOT NULL DEFAULT '',
    text      TEXT NOT NULL,
    fundstelle TEXT NOT NULL,
    gilt_ab   TEXT,
    quelle    TEXT NOT NULL DEFAULT ''
);
CREATE INDEX einheit_nach_akt ON einheit(rechtsakt, art);

-- Stichwortsuche. content='einheit' heisst: der Text wird nicht ein zweites
-- Mal gespeichert, sondern nur sein Index. Das halbiert die Datei.
-- remove_diacritics 2 ist die heutige Fassung der Regel; sie fasst auch
-- Zeichen mit mehreren Akzenten richtig an, Fassung 1 lässt die liegen.
-- Umlaute werden damit zu a, o, u - die App fragt deshalb jede Frage in
-- beiden Schreibweisen ab, mit Umlaut und mit ae/oe/ue.
CREATE VIRTUAL TABLE einheit_fts USING fts5(
    titel, text,
    content='einheit', content_rowid='nummer',
    tokenize='unicode61 remove_diacritics 2'
);

-- Die Vektoren. werte ist eine Folge von 384 float32-Zahlen, kleines Ende
-- zuerst, bereits auf Länge 1 gebracht. Dadurch ist das Skalarprodukt in der
-- App schon das Kosinusmass - eine Wurzel weniger je Vergleich, und bei 1972
-- Einheiten je Frage zählt das auf einem Telefon.
CREATE TABLE vektor (
    kennung TEXT NOT NULL PRIMARY KEY REFERENCES einheit(kennung),
    werte   BLOB NOT NULL
);

-- Die 57 Pflichten. rollen, klassen und rechtsgrundlage sind Listen und
-- liegen als JSON; eine eigene Verknüpfungstabelle brächte hier nichts,
-- weil immer die ganze Pflicht gelesen wird.
CREATE TABLE pflicht (
    kennung        TEXT NOT NULL PRIMARY KEY,
    titel          TEXT NOT NULL,
    was_zu_tun_ist TEXT NOT NULL,
    rechtsgrundlage TEXT NOT NULL,
    fundstellen_text TEXT NOT NULL,
    rollen         TEXT NOT NULL,
    klassen        TEXT NOT NULL,
    schwere        TEXT NOT NULL,
    gilt_ab        TEXT,
    nachweis       TEXT NOT NULL DEFAULT '',
    bei_verstoss   TEXT NOT NULL DEFAULT ''
);

-- Der Entscheidungsbaum, flach ausgelegt. art sagt, an welcher Stelle des
-- Baums die Regel hängt; rang bestimmt die Reihenfolge der Prüfung. Die
-- Verbote stehen vorn, weil ein Verbot jede weitere Einstufung erledigt.
CREATE TABLE risikoregel (
    kennung  TEXT NOT NULL PRIMARY KEY,
    art      TEXT NOT NULL,
    rang     INTEGER NOT NULL,
    klasse   TEXT,
    rolle    TEXT,
    titel    TEXT NOT NULL DEFAULT '',
    fundstelle TEXT NOT NULL DEFAULT '',
    rechtsgrundlage TEXT NOT NULL DEFAULT '[]',
    bedingungen TEXT NOT NULL DEFAULT '[]',
    stichworte  TEXT NOT NULL DEFAULT '[]',
    frage    TEXT NOT NULL DEFAULT '',
    begruendung TEXT NOT NULL DEFAULT '',
    sicherheit TEXT NOT NULL DEFAULT 'wahrscheinlich',
    gilt_ab  TEXT,
    zusatz   TEXT NOT NULL DEFAULT '{}'
);
CREATE INDEX risikoregel_nach_art ON risikoregel(art, rang);

-- Die 44 Anwendungsfälle. Sie sind der Lernteil der App: ein fremder Fall,
-- der dem eigenen gleicht, erklärt mehr als ein Gesetzestext.
CREATE TABLE fall (
    kennung      TEXT NOT NULL PRIMARY KEY,
    gebiet       TEXT NOT NULL DEFAULT '',
    titel        TEXT NOT NULL,
    lage         TEXT NOT NULL,
    rolle        TEXT NOT NULL,
    einstufung   TEXT NOT NULL,
    begruendung  TEXT NOT NULL,
    rechtsgrundlage TEXT NOT NULL DEFAULT '[]',
    pflichten    TEXT NOT NULL DEFAULT '[]',
    lernhinweis  TEXT NOT NULL DEFAULT '',
    stolperstein TEXT NOT NULL DEFAULT '',
    verwandte_faelle TEXT NOT NULL DEFAULT '[]'
);
CREATE INDEX fall_nach_einstufung ON fall(einstufung, rolle);

-- Der Prüfpfad der Datenschutz-Grundverordnung, 26 Abschnitte in der
-- Reihenfolge, in der sie zu prüfen sind. Ohne diese Tabelle hätte die App
-- nur die halbe Auskunft, weil der Name beide Rechtsakte verspricht.
CREATE TABLE pruefabschnitt (
    kennung  TEXT NOT NULL PRIMARY KEY,
    rang     INTEGER NOT NULL,
    titel    TEXT NOT NULL,
    frage    TEXT NOT NULL,
    rechtsgrundlage TEXT NOT NULL DEFAULT '[]',
    fundstellen_text TEXT NOT NULL DEFAULT '',
    was_zu_tun_ist TEXT NOT NULL DEFAULT '',
    nachweis TEXT NOT NULL DEFAULT '',
    bei_verstoss TEXT NOT NULL DEFAULT ''
);

-- Was die App über ihren eigenen Datenstand wissen muss. Sie zeigt den Stand
-- in jeder Auskunft an, weil eine Rechtsauskunft ohne Datum wertlos ist.
CREATE TABLE meta (
    schluessel TEXT NOT NULL PRIMARY KEY,
    wert       TEXT NOT NULL
);
"""


def als_json(wert: Any) -> str:
    """Listen und verschachtelte Angaben wandern als JSON in eine Spalte."""
    return json.dumps(wert if wert is not None else [], ensure_ascii=False, default=str)


def als_text(wert: Any) -> str:
    """YAML-Blöcke enden oft mit Zeilenumbruch; der stört in der Anzeige."""
    if wert is None:
        return ""
    return str(wert).strip()


# ----------------------------------------------------------------- Schreiben


def schreiben_einheiten(db: sqlite3.Connection, einheiten: list[dict[str, Any]]) -> None:
    db.executemany(
        "INSERT INTO einheit (nummer, kennung, rechtsakt, art, nummer_im_akt, absatz,"
        " titel, text, fundstelle, gilt_ab, quelle) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                nummer,
                e["kennung"],
                e["rechtsakt"],
                e["art"],
                str(e["nummer"]),
                e.get("absatz"),
                e.get("titel") or "",
                e["text"],
                fundstelle(e),
                e.get("gilt_ab"),
                e.get("quelle") or "",
            )
            for nummer, e in enumerate(einheiten, 1)
        ],
    )
    db.execute(
        "INSERT INTO einheit_fts(rowid, titel, text) SELECT nummer, titel, text FROM einheit"
    )


def schreiben_pflichten(db: sqlite3.Connection) -> int:
    daten = laden_yaml(REGELN / "kivo_pflichten.yaml")
    zeilen = []
    for p in daten["pflichten"]:
        zeilen.append(
            (
                p["kennung"],
                als_text(p["titel"]),
                als_text(p["was_zu_tun_ist"]),
                als_json(p.get("rechtsgrundlage")),
                als_text(p.get("fundstellen_text")),
                als_json(p.get("rollen")),
                als_json(p.get("klassen")),
                p.get("schwere") or "pflicht",
                str(p["gilt_ab"]) if p.get("gilt_ab") else None,
                als_text(p.get("nachweis")),
                als_text(p.get("bei_verstoss")),
            )
        )
    db.executemany(
        "INSERT INTO pflicht (kennung, titel, was_zu_tun_ist, rechtsgrundlage,"
        " fundstellen_text, rollen, klassen, schwere, gilt_ab, nachweis, bei_verstoss)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        zeilen,
    )
    return len(zeilen)


def schreiben_regeln(db: sqlite3.Connection) -> tuple[int, dict[str, str]]:
    """Legt den Entscheidungsbaum flach aus - eine Zeile je Regel.

    Die Reihenfolge im Feld rang ist die Prüfreihenfolge: Verbot vor
    Hochrisiko vor Transparenz vor Basismodell vor minimal. Sie steckt in den
    Daten und nicht im Programm, damit eine Rechtsänderung diese Datei
    ändert und nicht den Quelltext der App.
    """
    daten = laden_yaml(REGELN / "kivo_risikoklassen.yaml")
    zeilen: list[tuple[Any, ...]] = []
    rang = 0

    def hinzu(art: str, kennung: str, **werte: Any) -> None:
        nonlocal rang
        rang += 1
        zeilen.append(
            (
                kennung,
                art,
                rang,
                werte.get("klasse"),
                werte.get("rolle"),
                als_text(werte.get("titel")),
                als_text(werte.get("fundstelle")),
                als_json(werte.get("rechtsgrundlage")),
                als_json(werte.get("bedingungen")),
                als_json(werte.get("stichworte")),
                als_text(werte.get("frage")),
                als_text(werte.get("begruendung")),
                werte.get("sicherheit") or "wahrscheinlich",
                str(werte["gilt_ab"]) if werte.get("gilt_ab") else None,
                json.dumps(werte.get("zusatz") or {}, ensure_ascii=False, default=str),
            )
        )

    # Stufe 1 - Verbote nach Artikel 5. Sie kommen zuerst, weil ein Verbot
    # jede weitere Einstufung gegenstandslos macht.
    for v in daten.get("verbote", []):
        hinzu(
            "verbot",
            v["kennung"],
            klasse=v.get("klasse", "verboten"),
            titel=v.get("titel"),
            fundstelle=v.get("fundstelle"),
            rechtsgrundlage=v.get("rechtsgrundlage"),
            bedingungen=v.get("wenn"),
            stichworte=v.get("stichworte"),
            frage=v.get("frage"),
            begruendung=v.get("begruendung"),
            sicherheit=v.get("sicherheit"),
            zusatz={k: v[k] for k in ("ausnahme", "oder_wenn") if k in v},
        )

    # Stufe 2 - Hochrisiko über ein Produkt nach Anhang I.
    ai = daten["hochrisiko_anhang_i"]
    hinzu(
        "hochrisiko_anhang_i",
        ai["kennung"],
        klasse=ai.get("klasse"),
        titel=ai.get("titel"),
        fundstelle=ai.get("fundstelle"),
        rechtsgrundlage=ai.get("rechtsgrundlage"),
        bedingungen=ai.get("wenn"),
        stichworte=ai.get("stichworte"),
        frage=ai.get("frage"),
        begruendung=ai.get("begruendung"),
        gilt_ab=ai.get("gilt_ab"),
        sicherheit="wahrscheinlich",
    )

    # Stufe 2 - Hochrisiko über einen Bereich nach Anhang III. Hier gibt es
    # keine Ja/Nein-Felder, sondern acht Bereiche mit je einer Frage.
    aiii = daten["hochrisiko_anhang_iii"]
    for b in aiii.get("bereiche", []):
        hinzu(
            "hochrisiko_anhang_iii",
            b["kennung"],
            klasse="hochrisiko_anhang_iii",
            titel=b.get("titel"),
            fundstelle=b.get("fundstelle"),
            rechtsgrundlage=b.get("rechtsgrundlage"),
            stichworte=b.get("stichworte"),
            frage=b.get("frage"),
            gilt_ab=aiii.get("gilt_ab"),
            sicherheit="zu_pruefen",
            zusatz={
                "nummer": b.get("nummer"),
                "umfasst": b.get("umfasst", []),
                "ausnahme": b.get("ausnahme", ""),
            },
        )

    # Die Ausnahme nach Artikel 6 Absatz 3 samt Gegenausnahme und Folgepflicht.
    aus = daten["hochrisiko_ausnahme"]
    hinzu(
        "hochrisiko_ausnahme",
        aus["kennung"],
        klasse=aus.get("klasse"),
        fundstelle=aus.get("fundstelle"),
        rechtsgrundlage=aus.get("rechtsgrundlage"),
        begruendung=aus.get("voraussetzung"),
        sicherheit="zu_pruefen",
        zusatz={
            "einer_der_faelle": aus.get("einer_der_faelle", []),
            "gegenausnahme": aus.get("gegenausnahme", {}),
            "folgepflicht": aus.get("folgepflicht", {}),
        },
    )

    # Stufe 3 - Transparenzpflichten nach Artikel 50.
    tr = daten["transparenz"]
    for f in tr.get("faelle", []):
        hinzu(
            "transparenz",
            f["kennung"],
            klasse=f.get("klasse", "transparenz"),
            rolle=f.get("rolle"),
            fundstelle=f.get("fundstelle"),
            rechtsgrundlage=f.get("rechtsgrundlage"),
            bedingungen=f.get("wenn"),
            stichworte=f.get("stichworte"),
            begruendung=f.get("pflicht"),
            gilt_ab=tr.get("gilt_ab"),
            sicherheit="wahrscheinlich",
        )

    # Stufe 4 - Modelle mit allgemeinem Verwendungszweck.
    g = daten["gpai"]
    hinzu(
        "gpai",
        g["kennung"],
        klasse=g.get("klasse"),
        fundstelle=g.get("fundstelle"),
        rechtsgrundlage=g.get("rechtsgrundlage"),
        bedingungen=g.get("wenn"),
        stichworte=g.get("stichworte"),
        frage=g.get("frage"),
        gilt_ab=g.get("gilt_ab"),
        sicherheit="wahrscheinlich",
        zusatz={"altmodelle": g.get("altmodelle", {})},
    )
    sysr = g["systemisches_risiko"]
    hinzu(
        "gpai_systemisch",
        sysr["kennung"],
        klasse=sysr.get("klasse"),
        fundstelle=sysr.get("fundstelle"),
        rechtsgrundlage=sysr.get("rechtsgrundlage"),
        begruendung=sysr.get("vermutung"),
        sicherheit="zu_pruefen",
        zusatz={"schwelle_flop": sysr.get("schwelle_flop")},
    )

    # Stufe 5 - alles Übrige.
    mi = daten["minimal"]
    hinzu(
        "minimal",
        mi["kennung"],
        klasse=mi.get("klasse"),
        fundstelle=mi.get("fundstelle"),
        rechtsgrundlage=mi.get("rechtsgrundlage"),
        begruendung=mi.get("begruendung"),
        sicherheit="wahrscheinlich",
    )

    # Kein Einstufungsschritt, aber für die Rolle entscheidend: wer als
    # Betreiber anfängt, kann nach Artikel 25 zum Anbieter werden.
    rw = daten["rollenwechsel"]
    hinzu(
        "rollenwechsel",
        rw["kennung"],
        fundstelle=rw.get("fundstelle"),
        rechtsgrundlage=rw.get("rechtsgrundlage"),
        begruendung=rw.get("folge"),
        zusatz={"wird_anbieter_wenn": rw.get("wer_betreiber_ist_wird_anbieter_wenn", [])},
    )

    hinzu(
        "fristen",
        "fristen-art-113",
        fundstelle=daten["fristen"].get("fundstelle"),
        rechtsgrundlage=daten["fristen"].get("rechtsgrundlage"),
        begruendung=daten["fristen"].get("vorbehalt"),
        zusatz={"stufen": daten["fristen"].get("stufen", [])},
    )
    hinzu(
        "sanktionen",
        "sanktionen-art-99",
        fundstelle=daten["sanktionen"].get("fundstelle"),
        rechtsgrundlage=daten["sanktionen"].get("rechtsgrundlage"),
        zusatz={
            "stufen": daten["sanktionen"].get("stufen", []),
            "klein_und_mittel": daten["sanktionen"].get("klein_und_mittel", ""),
        },
    )

    db.executemany(
        "INSERT INTO risikoregel (kennung, art, rang, klasse, rolle, titel, fundstelle,"
        " rechtsgrundlage, bedingungen, stichworte, frage, begruendung, sicherheit,"
        " gilt_ab, zusatz) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        zeilen,
    )
    stand = {
        "regelstand": str(daten.get("stand", "")),
        "regelvorbehalt": als_text(daten.get("hinweis_zum_stand")),
    }
    return len(zeilen), stand


def schreiben_faelle(db: sqlite3.Connection) -> int:
    zeilen = []
    for datei in sorted(FAELLE.glob("*.yaml")):
        daten = laden_yaml(datei)
        gebiet = als_text(daten.get("gebiet"))
        for f in daten.get("faelle", []):
            zeilen.append(
                (
                    f["kennung"],
                    gebiet,
                    als_text(f["titel"]),
                    als_text(f["lage"]),
                    f.get("rolle") or "",
                    f.get("einstufung") or "",
                    als_text(f.get("begruendung")),
                    als_json(f.get("rechtsgrundlage")),
                    als_json(f.get("pflichten")),
                    als_text(f.get("lernhinweis")),
                    als_text(f.get("stolperstein")),
                    als_json(f.get("verwandte_faelle")),
                )
            )
    if not zeilen:
        abbruch(f"keine Anwendungsfälle in {FAELLE} gefunden")
    db.executemany(
        "INSERT INTO fall (kennung, gebiet, titel, lage, rolle, einstufung, begruendung,"
        " rechtsgrundlage, pflichten, lernhinweis, stolperstein, verwandte_faelle)"
        " VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        zeilen,
    )
    return len(zeilen)


def schreiben_pruefpfad(db: sqlite3.Connection) -> tuple[int, str]:
    daten = laden_yaml(REGELN / "dsgvo_pruefpfad.yaml")
    zeilen = []
    for rang, a in enumerate(daten["abschnitte"], 1):
        zeilen.append(
            (
                a["kennung"],
                rang,
                als_text(a["titel"]),
                als_text(a.get("frage")),
                als_json(a.get("rechtsgrundlage")),
                als_text(a.get("fundstellen_text")),
                als_text(a.get("was_zu_tun_ist")),
                als_text(a.get("nachweis")),
                als_text(a.get("bei_verstoss")),
            )
        )
    db.executemany(
        "INSERT INTO pruefabschnitt (kennung, rang, titel, frage, rechtsgrundlage,"
        " fundstellen_text, was_zu_tun_ist, nachweis, bei_verstoss)"
        " VALUES (?,?,?,?,?,?,?,?,?)",
        zeilen,
    )
    return len(zeilen), str(daten.get("stand", ""))


# ------------------------------------------------------------------ Vektoren


def rechnen_vektoren(texte: list[str], stapel: int) -> Any:
    """Bettet den ganzen Bestand ein. Bricht ab, wenn das Modell fehlt."""
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except ImportError as fehler:
        abbruch(
            f"sentence-transformers fehlt ({fehler}). Ohne das Modell gibt es keine "
            "Vektoren, und ohne Vektoren findet die App nur über Stichworte.\n"
            "Installieren mit: pip install 'sentence-transformers>=3.0' torch\n"
            "Es wird KEINE Datenbank mit Platzhaltern geschrieben."
        )
    print(f"  Modell laden: {MODELL}", flush=True)
    modell = SentenceTransformer(MODELL)
    # Der Name der Abfrage hat sich zwischen den Fassungen von
    # sentence-transformers geändert; beide Wege führen zur gleichen Zahl.
    messen = (
        getattr(modell, "get_embedding_dimension", None) or modell.get_sentence_embedding_dimension
    )
    tatsaechlich = int(messen())
    if tatsaechlich != DIMENSIONEN:
        abbruch(
            f"Das Modell liefert {tatsaechlich:d} Zahlen, erwartet sind "
            f"{DIMENSIONEN:d}. Falsches Modell?"
        )
    print(f"  {len(texte):d} Einheiten einbetten", flush=True)
    reihen = modell.encode(
        [VORSILBE_BESTAND + t for t in texte],
        batch_size=stapel,
        normalize_embeddings=True,
        show_progress_bar=False,
        convert_to_numpy=True,
    )
    return np.asarray(reihen, dtype=np.float32)


def schreiben_vektoren(db: sqlite3.Connection, kennungen: list[str], reihen: Any) -> None:
    db.executemany(
        "INSERT INTO vektor (kennung, werte) VALUES (?, ?)",
        [
            (kennung, sqlite3.Binary(struct.pack(f"<{DIMENSIONEN:d}f", *reihe)))
            for kennung, reihe in zip(kennungen, reihen, strict=True)
        ],
    )


# --------------------------------------------------------------------- ONNX


def ausgeben_onnx() -> dict[str, Any]:
    """Legt den Einbetter als ONNX-Modell neben die Datenbank.

    Mittelwertbildung und Längennormierung stecken mit im Graphen. Damit gibt
    die App Wortmarken hinein und bekommt 384 fertige Zahlen heraus; sie muss
    nichts nachrechnen, was sie falsch machen könnte.

    Danach wird das Modell auf 8-Bit-Gewichte verkleinert: 470 MB wären für
    eine Telefon-App nicht zu vertreten, 118 MB sind es. Was das kostet,
    steht gemessen im Befund.
    """
    befund: dict[str, Any] = {"ausgefuehrt": False}
    try:
        import numpy as np
        import onnxruntime as ort
        import torch
        from onnxruntime.quantization import QuantType, quantize_dynamic
        from transformers import AutoModel, AutoTokenizer
    except ImportError as fehler:
        # Kein Abbruch: die Datenbank ist dann trotzdem brauchbar, nur muss
        # der ONNX-Schritt in der Bauanlage nachgeholt werden.
        print(f"  ONNX übersprungen, Paket fehlt: {fehler}", file=sys.stderr)
        befund["uebersprungen_weil"] = str(fehler)
        return befund

    class Einbettungsgraph(torch.nn.Module):
        """Modellkern, Mittelwert über die Wortmarken, Länge auf 1."""

        def __init__(self, kern: Any) -> None:
            super().__init__()
            self.kern = kern

        def forward(self, input_ids: Any, attention_mask: Any) -> Any:
            aus = self.kern(input_ids=input_ids, attention_mask=attention_mask)
            zustand = aus.last_hidden_state
            maske = attention_mask.unsqueeze(-1).to(zustand.dtype)
            summe = (zustand * maske).sum(1)
            anzahl = maske.sum(1).clamp(min=1e-9)
            return torch.nn.functional.normalize(summe / anzahl, p=2.0, dim=1)

    print("  ONNX bauen", flush=True)
    wortschatz = AutoTokenizer.from_pretrained(MODELL, revision=MODELL_FASSUNG)
    graph = Einbettungsgraph(
        AutoModel.from_pretrained(MODELL, revision=MODELL_FASSUNG).eval()
    ).eval()

    probe = [
        "passage: Eine Probe für den Bau des Graphen.",
        "query: Eine zweite Probe mit anderer Länge.",
    ]
    marken = wortschatz(
        probe, padding=True, truncation=True, max_length=MAX_WORTMARKEN, return_tensors="pt"
    )
    with torch.no_grad():
        erwartet = graph(marken["input_ids"], marken["attention_mask"]).numpy()

    roh = ZIEL_ONNX.with_suffix(".fp32.onnx")
    torch.onnx.export(
        graph,
        (marken["input_ids"], marken["attention_mask"]),
        str(roh),
        input_names=["input_ids", "attention_mask"],
        output_names=["einbettung"],
        dynamic_axes={
            "input_ids": {0: "stapel", 1: "laenge"},
            "attention_mask": {0: "stapel", 1: "laenge"},
            "einbettung": {0: "stapel"},
        },
        opset_version=17,
        do_constant_folding=True,
        dynamo=False,
    )
    quantize_dynamic(str(roh), str(ZIEL_ONNX), weight_type=QuantType.QInt8)
    roh.unlink()

    sitzung = ort.InferenceSession(str(ZIEL_ONNX), providers=["CPUExecutionProvider"])
    bekommen = sitzung.run(
        None,
        {
            "input_ids": marken["input_ids"].numpy().astype(np.int64),
            "attention_mask": marken["attention_mask"].numpy().astype(np.int64),
        },
    )[0]
    aehnlichkeit = float((bekommen * erwartet).sum(1).min())

    wortschatz.save_pretrained(BEIGABEN)
    for unnoetig in ("tokenizer_config.json", "special_tokens_map.json", "sentencepiece.bpe.model"):
        (BEIGABEN / unnoetig).unlink(missing_ok=True)
    if not ZIEL_WORTSCHATZ.exists():
        abbruch(
            "tokenizer.json wurde nicht geschrieben - die App kann dann nicht "
            "zerlegen und die Vektorsuche fällt aus"
        )

    befund.update(
        {
            "ausgefuehrt": True,
            "onnx_mb": round(ZIEL_ONNX.stat().st_size / 1e6, 1),
            "wortschatz_mb": round(ZIEL_WORTSCHATZ.stat().st_size / 1e6, 1),
            "aehnlichkeit_8bit_zu_32bit": round(aehnlichkeit, 4),
            "hinweis": (
                "Die Einheiten im Bestand sind mit dem 32-Bit-Modell gerechnet, "
                "die App rechnet Fragen mit dem 8-Bit-Modell. Die gemessene "
                "Ähnlichkeit sagt, wie weit beide auseinanderliegen."
            ),
        }
    )
    return befund


# ------------------------------------------------------------------- Prüfen


def pruefen(db: sqlite3.Connection, einheiten: int) -> dict[str, Any]:
    """Sieht nach, ob die gebaute Datenbank wirklich trägt.

    Nicht die Zeilen zählen, die geschrieben wurden, sondern die, die
    drinstehen - dazwischen liegt der Unterschied zwischen einer Annahme und
    einer Messung.
    """
    ergebnis: dict[str, Any] = {"zeilen": {}, "proben": {}, "fehler": []}
    for tabelle in (
        "einheit",
        "vektor",
        "pflicht",
        "risikoregel",
        "fall",
        "pruefabschnitt",
        "meta",
    ):
        # Der Tabellenname kommt aus der Aufzählung dieser Schleife, nicht von
        # außen. Trotzdem wird er geprüft, bevor er in die Abfrage geht: eine
        # Zeichenkette, die in SQL eingesetzt wird, gehört geprüft - gleich, wie
        # sicher die Herkunft gerade aussieht. Die Prüfung kostet nichts und
        # bleibt richtig, wenn jemand die Aufzählung später aus einer Datei liest.
        if not ZULAESSIGE_TABELLEN.fullmatch(tabelle):
            raise ValueError(f"Unerwarteter Tabellenname: {tabelle!r}")
        ergebnis["zeilen"][tabelle] = db.execute(
            f"SELECT count(*) FROM {tabelle}"  # noqa: S608  # nosec B608
        ).fetchone()[0]

    if ergebnis["zeilen"]["einheit"] != einheiten:
        ergebnis["fehler"].append(
            "einheit: %d statt %d Zeilen" % (ergebnis["zeilen"]["einheit"], einheiten)
        )
    if ergebnis["zeilen"]["vektor"] != einheiten:
        ergebnis["fehler"].append(
            "vektor: %d statt %d Zeilen" % (ergebnis["zeilen"]["vektor"], einheiten)
        )

    # Jede Vektorzeile muss genau 384 float32 lang sein. Eine kurze Zeile
    # würde die App beim Lesen aus dem Tritt bringen.
    falsche_laenge = db.execute(
        "SELECT count(*) FROM vektor WHERE length(werte) <> ?", (DIMENSIONEN * 4,)
    ).fetchone()[0]
    if falsche_laenge:
        ergebnis["fehler"].append(
            f"{falsche_laenge:d} Vektoren haben nicht {DIMENSIONEN * 4:d} Byte"
        )

    # Stichwortsuche: drei Fragen, die in diesem Bestand treffen müssen.
    for frage in ("Hochrisiko", "Bewerbungen", "Einwilligung"):
        treffer = db.execute(
            "SELECT count(*) FROM einheit_fts WHERE einheit_fts MATCH ?", (frage,)
        ).fetchone()[0]
        ergebnis["proben"]["fts:" + frage] = treffer
        if treffer == 0:
            ergebnis["fehler"].append(f"Stichwortsuche nach '{frage}' findet nichts")

    # Umlautprobe: so ist der Tokenizer eingestellt, und genau darauf baut
    # die Suche in der App auf.
    ohne_umlaut = db.execute(
        "SELECT count(*) FROM einheit_fts WHERE einheit_fts MATCH ?", ("beschaftigte",)
    ).fetchone()[0]
    ergebnis["proben"]["fts:beschaftigte (ohne Umlaut)"] = ohne_umlaut
    if ohne_umlaut == 0:
        ergebnis["fehler"].append(
            "Umlautfaltung greift nicht: 'beschaftigte' findet 'Beschäftigte' nicht"
        )

    # Eine Fundstelle, die der Entscheidungsbaum zitiert, muss im Bestand sein.
    fehlende: list[str] = []
    for (roh,) in db.execute("SELECT rechtsgrundlage FROM risikoregel"):
        for kennung in json.loads(roh):
            da = db.execute("SELECT 1 FROM einheit WHERE kennung = ?", (kennung,)).fetchone()
            if not da:
                fehlende.append(kennung)
    ergebnis["proben"]["rechtsgrundlagen_ohne_fundstelle"] = sorted(set(fehlende))

    # Eine Einstufung muss am Ende Pflichten finden, sonst ist die Antwort leer.
    for klasse in ("hochrisiko_anhang_iii", "transparenz", "gpai", "minimal"):
        anzahl = db.execute(
            "SELECT count(*) FROM pflicht WHERE klassen LIKE ?", (f"%{klasse}%",)
        ).fetchone()[0]
        ergebnis["proben"]["pflichten:" + klasse] = anzahl
        if anzahl == 0:
            ergebnis["fehler"].append(f"keine Pflicht für Klasse {klasse}")
    return ergebnis


# --------------------------------------------------------------------- Haupt


def haupt() -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument(
        "--stapel", type=int, default=16, help="Wie viele Einheiten das Modell auf einmal einbettet"
    )
    zerleger.add_argument(
        "--ohne-onnx",
        action="store_true",
        help="Nur die Datenbank bauen; den Einbetter liefert die Bauanlage",
    )
    argumente = zerleger.parse_args()

    begonnen = time.time()
    BEIGABEN.mkdir(parents=True, exist_ok=True)

    print("Rechtsbestand lesen", flush=True)
    einheiten = laden_korpus()
    pruefsumme = hashlib.sha256(KORPUS.read_bytes()).hexdigest()
    print(f"  {len(einheiten):d} Einheiten, Prüfsumme {pruefsumme[:16]}", flush=True)

    print("Vektoren rechnen", flush=True)
    reihen = rechnen_vektoren([suchtext(e) for e in einheiten], argumente.stapel)

    # Erst jetzt wird geschrieben. Bricht etwas vorher ab, bleibt die alte
    # Datenbank unversehrt liegen statt halb überschrieben.
    print(f"Datenbank bauen: {ZIEL_DB}", flush=True)
    ZIEL_DB.unlink(missing_ok=True)
    db = sqlite3.connect(ZIEL_DB)
    try:
        db.executescript(SCHEMA)
        schreiben_einheiten(db, einheiten)
        schreiben_vektoren(db, [e["kennung"] for e in einheiten], reihen)
        anzahl_pflichten = schreiben_pflichten(db)
        anzahl_regeln, regelstand = schreiben_regeln(db)
        anzahl_faelle = schreiben_faelle(db)
        anzahl_abschnitte, dsgvo_stand = schreiben_pruefpfad(db)

        db.executemany(
            "INSERT INTO meta (schluessel, wert) VALUES (?, ?)",
            [
                ("modell", MODELL),
                ("dimensionen", str(DIMENSIONEN)),
                ("gebaut", date.today().isoformat()),
                ("korpus_pruefsumme", pruefsumme),
                ("vorsilbe_frage", VORSILBE_FRAGE),
                ("vorsilbe_bestand", VORSILBE_BESTAND),
                ("max_wortmarken", str(MAX_WORTMARKEN)),
                ("einheiten", str(len(einheiten))),
                ("regelstand", regelstand["regelstand"]),
                ("regelvorbehalt", regelstand["regelvorbehalt"]),
                ("dsgvo_stand", dsgvo_stand),
                ("datenstand", max(e.get("stand") or "" for e in einheiten)),
            ],
        )
        db.commit()
        db.execute("VACUUM")
        db.commit()
        befund_db = pruefen(db, len(einheiten))
    finally:
        db.close()

    befund_onnx = {"ausgefuehrt": False, "uebersprungen_weil": "mit --ohne-onnx abgewählt"}
    if not argumente.ohne_onnx:
        print("Einbetter ausgeben", flush=True)
        befund_onnx = ausgeben_onnx()

    befund = {
        "gebaut": date.today().isoformat(),
        "dauer_sekunden": round(time.time() - begonnen, 1),
        "modell": MODELL,
        "dimensionen": DIMENSIONEN,
        "korpus_pruefsumme": pruefsumme,
        "dateien": {
            "recht.db_mb": round(ZIEL_DB.stat().st_size / 1e6, 2),
            "einbetter.onnx_mb": befund_onnx.get("onnx_mb"),
            "tokenizer.json_mb": befund_onnx.get("wortschatz_mb"),
        },
        "zeilen": befund_db["zeilen"],
        "proben": befund_db["proben"],
        "onnx": befund_onnx,
        "fehler": befund_db["fehler"],
        "pflichten": anzahl_pflichten,
        "regeln": anzahl_regeln,
        "faelle": anzahl_faelle,
        "pruefabschnitte": anzahl_abschnitte,
    }
    BEFUND.write_text(json.dumps(befund, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print(f"\nBefund: {BEFUND}")
    for tabelle, anzahl in befund_db["zeilen"].items():
        print("  %-16s %6d Zeilen" % (tabelle, anzahl))
    print("  recht.db         {:6.2f} MB".format(befund["dateien"]["recht.db_mb"]))
    if befund_onnx.get("ausgefuehrt"):
        print(
            "  einbetter.onnx   {:6.1f} MB  Ähnlichkeit 8 zu 32 Bit: {:.4f}".format(
                befund_onnx["onnx_mb"], befund_onnx["aehnlichkeit_8bit_zu_32bit"]
            )
        )
    if befund_db["fehler"]:
        print("\nFEHLER:", file=sys.stderr)
        for fehler in befund_db["fehler"]:
            print(f"  - {fehler}", file=sys.stderr)
        return 1
    print("\nAlles geprüft, keine Beanstandung.")
    return 0


if __name__ == "__main__":
    sys.exit(haupt())
