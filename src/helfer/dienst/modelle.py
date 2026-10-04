"""Die Formen, in denen Anfragen hereinkommen und Antworten hinausgehen.

Warum eigene Formen, wenn es ``helfer.modell`` schon gibt? Weil die beiden
unterschiedliche Aufgaben haben: ``helfer.modell`` beschreibt das Recht und
soll streng sein. Hier wird beschrieben, was ein Browser schickt — und der
schickt leere Felder, Zeichenketten statt Wahrheitswerten und manchmal Unsinn.
Diese Schicht fängt das ab, säubert es und übersetzt es in die strengen Formen.

Die Antwortformen tragen die Fachbegriffe *und* ihre Erklärung in Alltagssprache
mit. Die Oberfläche soll nicht wissen müssen, was ``hochrisiko_anhang_iii``
bedeutet — das steht in derselben Antwort daneben.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from helfer.modell import (
    Antwort,
    Belegstelle,
    Einstufung,
    Rechtsakt,
    Risikoklasse,
    Rolle,
)
from helfer.sicherheit import GRENZE_BESCHREIBUNG, GRENZE_FRAGE

# ------------------------------------------------------------------- Anfragen


class FrageAnfrage(BaseModel):
    """Die volle Auskunft: Frage, optional Beschreibung, optional Modellwunsch."""

    model_config = ConfigDict(extra="forbid")

    frage: str = Field(
        min_length=1, max_length=GRENZE_FRAGE, description="Die Rechtsfrage in eigenen Worten"
    )
    beschreibung: str = Field(
        default="", max_length=GRENZE_BESCHREIBUNG, description="Das KI-System in eigenen Worten"
    )
    modell: str | None = Field(
        default=None,
        description="Welcher Antwortgeber formulieren soll: anthropic, openai, "
        "auto — oder 'ohne' für eine Antwort rein aus dem "
        "Regelwerk",
    )
    nur_rechtsakte: tuple[Rechtsakt, ...] | None = Field(
        default=None, description="Die Suche auf diese Gesetze beschränken"
    )
    anzahl_belege: int = Field(
        default=8, ge=1, le=20, description="Wie viele Fundstellen die Antwort nennt"
    )


class EinstufungAnfrage(BaseModel):
    """Nur die Einstufung — ohne Sprachmodell, deshalb schnell und wiederholbar.

    Die Merkmale kommen als Abbildung Name auf Wahrheitswert herein, weil der
    Fragebogen in der Oberfläche wachsen soll, ohne dass hier etwas zu ändern
    ist. Namen, die das Datenmodell nicht kennt, werden übergangen und in der
    Antwort genannt — stilles Verwerfen wäre schlimmer als eine Meldung.
    """

    model_config = ConfigDict(extra="forbid")

    beschreibung: str = Field(default="", max_length=GRENZE_BESCHREIBUNG)
    rollen: tuple[Rolle, ...] = ()
    merkmale: dict[str, bool | int | float | str | None] = Field(default_factory=dict)


class SucheAnfrage(BaseModel):
    """Nur die Suche — für den Fall, dass jemand selbst nachlesen will."""

    model_config = ConfigDict(extra="forbid")

    frage: str = Field(min_length=1, max_length=GRENZE_FRAGE)
    anzahl: int = Field(default=8, ge=1, le=30)
    nur_rechtsakte: tuple[Rechtsakt, ...] | None = None


# ------------------------------------------------------------------ Antworten


class Klartext(BaseModel):
    """Ein Fachbegriff und seine Erklärung — damit die Oberfläche nichts übersetzt."""

    model_config = ConfigDict(frozen=True)

    kennung: str
    klartext: str


class EinstufungAntwort(BaseModel):
    """Die Einstufung samt Erklärungen und der Zeit, die sie gebraucht hat."""

    model_config = ConfigDict(extra="forbid")

    einstufung: Einstufung
    schwerste_klasse: Risikoklasse
    schwerste_klartext: str
    klassen_klartext: tuple[Klartext, ...]
    rollen_klartext: tuple[Klartext, ...]
    nicht_erkannte_merkmale: tuple[str, ...] = ()
    stand_regeln: date | None = None
    fristenvorbehalt: str = ""
    dauer_ms: int = 0


class SucheAntwort(BaseModel):
    model_config = ConfigDict(extra="forbid")

    frage: str
    belege: tuple[Belegstelle, ...]
    einbettungsmodell: str
    dauer_ms: int = 0
    warnungen: tuple[str, ...] = ()


class FrageAntwort(BaseModel):
    """Die volle Auskunft, wie die Oberfläche sie zeigt."""

    model_config = ConfigDict(extra="forbid")

    antwort: Antwort
    schwerste_klasse: Risikoklasse | None = None
    schwerste_klartext: str = ""
    klassen_klartext: tuple[Klartext, ...] = ()
    rollen_klartext: tuple[Klartext, ...] = ()
    stand_regeln: date | None = None
    stand_korpus: date | None = None
    fristenvorbehalt: str = ""
    dauer_ms: int = 0


class Gesundheit(BaseModel):
    """Der Zustand des Dienstes — das, was ein Prüfprogramm abfragt."""

    model_config = ConfigDict(extra="forbid")

    zustand: Literal["bereit", "eingeschraenkt", "nicht_bereit"]
    korpus_geladen: bool
    bestand_geladen: bool
    einheiten: int
    einbettungsmodell: str
    sprachmodell: str
    stand_korpus: date | None = None
    stand_regeln: date | None = None
    bestand_aus_datei: bool = False
    neubewertung: bool = Field(
        default=False,
        description="Ob der Kreuzbewerter die Fundstellen neu sortiert — "
        "genauer, aber ohne Grafikkarte sehr langsam",
    )
    startdauer_ms: int = 0
    laufzeit_sekunden: int = 0
    warnungen: tuple[str, ...] = ()


class Fehlerantwort(BaseModel):
    """Eine Fehlermeldung, die nach außen darf: Klartext, keine Innereien."""

    model_config = ConfigDict(extra="forbid")

    fehler: str
    hinweis: str = ""


# ------------------------------------------------------------------ Fragebogen


class Fragebogenpunkt(BaseModel):
    """Eine Frage des Prüfers, aufbereitet für eine Oberfläche."""

    model_config = ConfigDict(frozen=True)

    kennung: str = Field(description="Name des Feldes in der Systembeschreibung")
    frage: str = Field(description="Die Frage in Alltagssprache")
    art: Literal["ja_nein", "text", "zahl", "auswahl"]
    hilfe: str = Field(default="", description="Warum die Frage gestellt wird")
    wofuer: str = Field(default="", description="Welche Prüfung davon abhängt")
    optionen: tuple[Klartext, ...] = ()


class Fragebogen(BaseModel):
    model_config = ConfigDict(extra="forbid")

    punkte: tuple[Fragebogenpunkt, ...]
    hinweis: str


class Fristenstufe(BaseModel):
    model_config = ConfigDict(frozen=True)

    datum: date
    was: str
    schon_in_kraft: bool


class Fristen(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fundstelle: str
    rechtsgrundlage: tuple[str, ...]
    stufen: tuple[Fristenstufe, ...]
    vorbehalt: str
    stand_regeln: date | None = None
    hinweis_zum_stand: str = ""


# -------------------------------------------------- Der Fragebogen selbst

#: Die Fragen, die der Prüfer stellt — in der Reihenfolge, in der die
#: Verordnung prüft. Jede Kennung ist ein Feld der ``Systembeschreibung``;
#: steht hier eine Kennung, die es dort nicht gibt, fällt das beim Start auf
#: (siehe ``fragebogen_pruefen``), nicht erst beim Nutzer.
FRAGEBOGEN: tuple[Fragebogenpunkt, ...] = (
    Fragebogenpunkt(
        kennung="rollen",
        art="auswahl",
        frage="Welche Rolle haben Sie bei diesem System?",
        hilfe="Anbieter entwickelt das System oder lässt es entwickeln und "
        "bringt es unter eigenem Namen heraus. Betreiber nutzt ein "
        "System unter eigener Verantwortung. Die Pflichten "
        "unterscheiden sich stark.",
        wofuer="Entscheidet, welcher Pflichtenkatalog gilt.",
        optionen=tuple(
            Klartext(kennung=r.value, klartext=r.erklaerung)
            for r in (
                Rolle.ANBIETER,
                Rolle.BETREIBER,
                Rolle.EINFUEHRER,
                Rolle.HAENDLER,
                Rolle.PRODUKTHERSTELLER,
                Rolle.BEVOLLMAECHTIGTER,
            )
        ),
    ),
    Fragebogenpunkt(
        kennung="zweck",
        art="text",
        frage="Wozu dient das System? Was soll es leisten?",
        hilfe="Der Zweck entscheidet über die Einstufung, nicht die Technik. "
        "Dasselbe Sprachmodell ist harmlos als Rechtschreibhilfe und "
        "hochriskant in der Bewerbungsauswahl.",
        wofuer="Anhang III, Einsatzbereiche mit hohem Risiko.",
    ),
    Fragebogenpunkt(
        kennung="einsatzbereich",
        art="text",
        frage="In welchem Bereich wird es eingesetzt?",
        hilfe="Zum Beispiel: Personalwesen, Kreditvergabe, Bildung, Medizin, "
        "Kundendienst, öffentliche Verwaltung.",
        wofuer="Anhang III nennt acht Bereiche ausdrücklich.",
    ),
    Fragebogenpunkt(
        kennung="nutzergruppe",
        art="text",
        frage="Wer ist von den Ergebnissen betroffen?",
        hilfe="Beschäftigte, Bewerber, Kunden, Schüler, Patienten, "
        "Antragsteller — oder nur das eigene Haus.",
        wofuer="Betroffenenrechte und die Folgenabschätzung.",
    ),
    Fragebogenpunkt(
        kennung="trifft_entscheidungen_ueber_menschen",
        art="ja_nein",
        frage="Wirkt das Ergebnis auf einzelne Menschen — wird darüber "
        "entschieden, bewertet oder eingeordnet?",
        hilfe="Auch eine Vorsortierung ist eine Wirkung: wer aussortiert wird, kommt nicht weiter.",
        wofuer="Anhang III und die Gegenausnahme zu Artikel 6 Absatz 3.",
    ),
    Fragebogenpunkt(
        kennung="menschliche_kontrolle",
        art="ja_nein",
        frage="Prüft ein Mensch das Ergebnis, bevor es wirkt — und kann er es ändern?",
        hilfe="Entscheidend ist, ob der Mensch wirklich eingreifen kann und "
        "nicht nur bestätigt, was das System vorgeschlagen hat.",
        wofuer="Die Ausnahme nach Artikel 6 Absatz 3 und die Aufsicht nach Artikel 14.",
    ),
    Fragebogenpunkt(
        kennung="verarbeitet_personenbezogene_daten",
        art="ja_nein",
        frage="Verarbeitet das System Angaben, über die sich ein Mensch bestimmen lässt?",
        hilfe="Name, Anschrift, Personalnummer, Stimme, Bild, aber auch eine "
        "Kennung, über die man zum Menschen zurückkommt.",
        wofuer="Ob zusätzlich das Datenschutzrecht greift.",
    ),
    Fragebogenpunkt(
        kennung="besondere_datenkategorien",
        art="ja_nein",
        frage="Sind darunter Angaben zu Gesundheit, Herkunft, Religion, "
        "Gewerkschaft, Sexualleben oder biometrische Daten?",
        hilfe="Diese Angaben sind nach Artikel 9 der "
        "Datenschutz-Grundverordnung besonders geschützt.",
        wofuer="Artikel 9 der Datenschutz-Grundverordnung, Folgenabschätzung.",
    ),
    Fragebogenpunkt(
        kennung="beschaeftigtendaten",
        art="ja_nein",
        frage="Geht es um Daten von Beschäftigten oder Bewerbern?",
        hilfe="Dann gilt neben der Verordnung auch § 26 des "
        "Bundesdatenschutzgesetzes und meist die Mitbestimmung.",
        wofuer="§ 26 Bundesdatenschutzgesetz, Betriebsrat.",
    ),
    Fragebogenpunkt(
        kennung="biometrie",
        art="ja_nein",
        frage="Erkennt das System Menschen an körperlichen Merkmalen — "
        "Gesicht, Stimme, Fingerabdruck, Gang?",
        hilfe="Hier liegen mehrere Verbote nach Artikel 5 und ein Bereich des Anhangs III.",
        wofuer="Artikel 5 und Anhang III Nummer 1.",
    ),
    Fragebogenpunkt(
        kennung="emotionserkennung",
        art="ja_nein",
        frage="Soll das System Gefühle oder Stimmungen von Menschen erkennen?",
        hilfe="Auch wenn es Stimmungsbarometer, Belastungsanzeige oder "
        "Zufriedenheitsmessung heißt.",
        wofuer="Verbot am Arbeitsplatz und in der Bildung, Artikel 5 Absatz 1 Buchstabe f.",
    ),
    Fragebogenpunkt(
        kennung="erzeugt_inhalte",
        art="ja_nein",
        frage="Erzeugt das System Texte, Bilder, Ton oder Video?",
        hilfe="Erzeugte Inhalte müssen maschinenlesbar gekennzeichnet werden.",
        wofuer="Transparenzpflichten nach Artikel 50.",
    ),
    Fragebogenpunkt(
        kennung="interagiert_mit_menschen",
        art="ja_nein",
        frage="Sprechen oder schreiben Menschen unmittelbar mit dem System?",
        hilfe="Ein Chatfenster, eine Telefonstimme, ein Hilfsassistent.",
        wofuer="Hinweispflicht nach Artikel 50 Absatz 1.",
    ),
    Fragebogenpunkt(
        kennung="eingebaut_in_produkt",
        art="ja_nein",
        frage="Ist das System in ein Produkt eingebaut, das eine Sicherheitsfunktion hat?",
        hilfe="Maschine, Aufzug, Medizingerät, Fahrzeug, Spielzeug — alles, "
        "was eine CE-Kennzeichnung braucht.",
        wofuer="Hohes Risiko über Anhang I, Artikel 6 Absatz 1.",
    ),
    Fragebogenpunkt(
        kennung="ist_basismodell",
        art="ja_nein",
        frage="Entwickeln Sie selbst ein Modell mit allgemeinem Verwendungszweck?",
        hilfe="Ein Modell, das viele verschiedene Aufgaben erfüllen kann und "
        "in andere Systeme eingebaut wird.",
        wofuer="Artikel 51 und folgende.",
    ),
    Fragebogenpunkt(
        kennung="rechenaufwand_flop",
        art="zahl",
        frage="Wie hoch war der Rechenaufwand beim Training in Gleitkommaoperationen?",
        hilfe="Ab 10 hoch 25 wird ein systemisches Risiko vermutet. Die Zahl "
        "darf als 1e25 geschrieben werden.",
        wofuer="Artikel 51 Absatz 2.",
    ),
    Fragebogenpunkt(
        kennung="oeffentliche_stelle",
        art="ja_nein",
        frage="Sind Sie eine Behörde oder eine öffentliche Stelle?",
        hilfe="Dann kommen die Grundrechte-Folgenabschätzung und die Registrierung hinzu.",
        wofuer="Artikel 27 und Artikel 49 Absatz 3.",
    ),
    Fragebogenpunkt(
        kennung="drittlandtransfer",
        art="ja_nein",
        frage="Werden Daten außerhalb der Europäischen Union verarbeitet?",
        hilfe="Auch dann, wenn nur der Rechner des Anbieters dort steht.",
        wofuer="Kapitel V der Datenschutz-Grundverordnung.",
    ),
    Fragebogenpunkt(
        kennung="anzahl_beschaeftigte",
        art="zahl",
        frage="Wie viele Menschen beschäftigt Ihr Haus?",
        hilfe="Kleine und mittlere Unternehmen haben bei den Nachweisen Erleichterungen.",
        wofuer="Artikel 11 Absatz 1 und Artikel 63.",
    ),
    Fragebogenpunkt(
        kennung="markt",
        art="text",
        frage="Wo wird das System angeboten oder genutzt?",
        hilfe="Die Verordnung gilt auch für Anbieter außerhalb der Union, "
        "wenn das Ergebnis in der Union verwendet wird.",
        wofuer="Artikel 2, Anwendungsbereich.",
    ),
)

FRAGEBOGEN_HINWEIS = (
    "Keine Frage muss beantwortet werden. Jede Antwort macht die Einstufung "
    "belastbarer; was fehlt, erscheint am Ende als offene Frage."
)


def fragebogen_pruefen() -> list[str]:
    """Prüft, dass jede Fragebogen-Kennung ein Feld der Beschreibung ist.

    Wird beim Start aufgerufen. Ein Tippfehler in einer Kennung würde sonst
    dazu führen, dass eine Antwort des Nutzers stillschweigend verfällt — und
    die Einstufung wäre falsch, ohne dass es jemand merkt.
    """
    from helfer.modell import Systembeschreibung

    felder = set(Systembeschreibung.model_fields)
    return [p.kennung for p in FRAGEBOGEN if p.kennung not in felder]
