"""Die Einstufung — und warum hier kein Sprachmodell mitredet.

Ein Sprachmodell formuliert gut und rät gern. Bei der Frage, ob ein KI-System
unter Anhang III fällt, ist Raten teuer: wer ein Hochrisikosystem für harmlos
hält, verfehlt ein Dutzend Pflichten und riskiert nach Artikel 99 bis zu
15 Millionen Euro. Darum trennt dieses Werkzeug zwei Dinge streng:

* **Die Einstufung** entsteht hier, aus den Regeldateien unter ``daten/regeln``.
  Sie ist ein Entscheidungsbaum: nachlesbar, wiederholbar, mit Artikelverweis an
  jeder Verzweigung. Dieselbe Beschreibung ergibt immer dieselbe Einstufung.
* **Die Formulierung** macht später ein Sprachmodell — und darf das Ergebnis
  nicht ändern. Es bekommt die Einstufung als feststehende Tatsache vorgelegt.

Der Prüfer arbeitet in der Reihenfolge, die die Verordnung vorgibt:

1. Verbotene Praktiken nach Artikel 5. Wer hier landet, braucht keine
   Pflichtenliste, sondern muss aufhören.
2. Hohes Risiko über das Produktsicherheitsrecht, Artikel 6 Absatz 1.
3. Hohes Risiko über den Einsatzbereich, Artikel 6 Absatz 2 mit Anhang III.
4. Die Ausnahme nach Artikel 6 Absatz 3 — mit der Gegenausnahme Profiling.
5. Transparenzpflichten nach Artikel 50.
6. Modelle mit allgemeinem Verwendungszweck, Artikel 51 und folgende.
7. Alles übrige: Artikel 4, KI-Kompetenz.

Was der Prüfer nicht weiß, behauptet er nicht. Fehlende Angaben werden zu
offenen Fragen, und die Sicherheit einer Einstufung wird mitgeliefert:
``sicher``, ``wahrscheinlich`` oder ``zu_pruefen``.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any, ClassVar

import yaml

from helfer.einstufung.zwecke import Zweckfinder, Zwecktreffer
from helfer.einstufung.zwecke import zweckfinder as gemeinsamer_zweckfinder
from helfer.modell import (
    Einstufung,
    Pflicht,
    Risikohinweis,
    Risikoklasse,
    Rolle,
    Schwere,
    Systembeschreibung,
)

protokoll = logging.getLogger(__name__)

WURZEL = Path(__file__).resolve().parents[3]
REGELN = WURZEL / "daten" / "regeln"


# --------------------------------------------------------------- Regeln laden


@dataclass
class Regelwerk:
    """Die Regeldateien, einmal gelesen."""

    risikoklassen: dict[str, Any] = field(default_factory=dict)
    pflichten: list[dict[str, Any]] = field(default_factory=list)
    datenschutz: list[dict[str, Any]] = field(default_factory=list)
    stand: date | None = None

    # Die Werte kommen aus YAML und sind für mypy darum "irgendetwas". Die
    # Umwandlung steht hier an der Grenze: ab hier arbeitet der Quelltext mit
    # festen Typen, und eine Regeldatei mit einem falschen Feldtyp fällt an
    # dieser Stelle auf, nicht erst irgendwo in der Auskunft.

    @property
    def fristen(self) -> list[dict[str, Any]]:
        stufen = (self.risikoklassen.get("fristen") or {}).get("stufen", [])
        return list(stufen) if isinstance(stufen, list) else []

    @property
    def fristenvorbehalt(self) -> str:
        return str((self.risikoklassen.get("fristen") or {}).get("vorbehalt", ""))

    @property
    def standhinweis(self) -> str:
        return str(self.risikoklassen.get("hinweis_zum_stand", ""))


def _lesen(pfad: Path) -> dict[str, Any]:
    if not pfad.exists():
        protokoll.warning("Regeldatei fehlt: %s", pfad)
        return {}
    try:
        return yaml.safe_load(pfad.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as fehler:
        raise RuntimeError(f"Regeldatei {pfad.name} ist fehlerhaft: {fehler}") from fehler


@lru_cache(maxsize=1)
def regelwerk() -> Regelwerk:
    risiko = _lesen(REGELN / "kivo_risikoklassen.yaml")
    pflichtdatei = _lesen(REGELN / "kivo_pflichten.yaml")
    datenschutzdatei = _lesen(REGELN / "dsgvo_pruefpfad.yaml")
    stand = risiko.get("stand")
    return Regelwerk(
        risikoklassen=risiko,
        pflichten=pflichtdatei.get("pflichten", []),
        datenschutz=(datenschutzdatei.get("abschnitte") or datenschutzdatei.get("pruefpfad") or []),
        stand=stand if isinstance(stand, date) else None,
    )


# ------------------------------------------------------- Beschreibung lesen

#: Wörter, die eine Angabe bejahen, wenn sie in der Beschreibung auftauchen.
#: Der Freitext wird nur als *Hinweis* gelesen, nie als Beweis: er setzt ein
#: Merkmal auf "wahrscheinlich", nicht auf "sicher".
_STICHWORTFELDER = {
    "biometrie": [
        "biometri",
        "gesichtserkennung",
        "fingerabdruck",
        "iris",
        "stimmerkennung",
        "gangerkennung",
    ],
    # Vorsicht bei der Wortwahl: Anbieter nennen Emotionserkennung selten so.
    # Im Angebot heißt sie Stimmungsbarometer, Belastungsanzeige oder
    # Zufriedenheitsmessung. Darum werden die Umschreibungen mitgeführt. Dass
    # daraus nicht jede Kundenumfrage ein Verbot wird, sichert die zweite
    # Bedingung der Regel: der Einsatz muss am Arbeitsplatz oder in der
    # Bildung stattfinden.
    "emotionserkennung": [
        "emotionserkennung",
        "emotion erkenn",
        "emotion ableit",
        "emotionen",
        "gefuehl",
        "gefühl",
        "stimmung",
        "sentiment",
        "belastung erkenn",
        "belastungsanzeige",
        "belastbarkeit",
        "begeisterung",
        "unsicherheit",
        "nervositaet",
        "nervosität",
        "aufregung",
        "motivation erkenn",
        "zufriedenheit mess",
        "gemuetszustand",
        "gemütszustand",
        "gemuetslage",
        "gemütslage",
        "stresserkennung",
        "stress erkenn",
        "muedigkeitserkennung",
        "muedigkeit",
        "müdigkeit",
        "aufmerksamkeit mess",
        "wachheit",
        "sekundenschlaf",
        "mimik auswert",
        "mimik und stimme",
        "innere einstellung",
        "hinweise auf begeisterung",
    ],
    "erzeugt_inhalte": [
        "erzeugt bilder",
        "erzeugt text",
        "generativ",
        "bildgenerierung",
        "bildgenerator",
        "bilddienst",
        "texterzeugung",
        "synthetische",
        "erstellt inhalte",
        "erzeugt video",
        "erzeugt audio",
        "bild erzeug",
        "text erzeug",
        "ansagen erzeug",
        "sprachsynthese",
        "kuenstlich erzeugt",
        "künstlich erzeugt",
        "darstellen lassen",
    ],
    # "Assistent" allein taugt nicht: ein Notbremsassistent spricht mit
    # niemandem. Darum nur die Zusammensetzungen, die wirklich Dialog meinen.
    "interagiert_mit_menschen": [
        "chatbot",
        "sprachassistent",
        "chatassistent",
        "digitaler assistent",
        "dialog",
        "kundendienst",
        "chat mit kunden",
        "telefonbot",
        "spricht mit kunden",
        "beantwortet fragen von kunden",
    ],
    # Veröffentlichte, von einer KI erzeugte Bilder, Töne oder Videos. Ob sie
    # unter Artikel 50 Absatz 4 fallen, hängt daran, ob sie einen bestehenden
    # Ort, eine Person oder ein Ereignis vortäuschen - das kann der Helfer nicht
    # entscheiden, aber er muss den Fall nennen. Nur Bild, Ton und Video: bei
    # Text greift Absatz 4 erst für Themen von öffentlichem Interesse.
    "veroeffentlicht_erzeugte_medien": [
        "bilder erzeug shop",
        "bilder erzeug veroeffentlich",
        "bilder darstellen lassen",
        "produktbilder erzeug",
        "produktfotos erzeug",
        "bilder ki erzeug shop",
        "erzeugte bilder stellt",
        "ergebnisse in seinen shop",
        "bilder in gestalteten raeumen",
        "bilder in gestalteten räumen",
        "video erzeug veroeffentlich",
        "werbespots erzeug",
    ],
    "erzeugt_deepfakes": [
        "deepfake",
        "gesicht tausch",
        "gesicht ersetz",
        "gesicht setzen",
        "statist",
        "stimme klon",
        "stimmklon",
        "geklont",
        "stimme nachbild",
        "person imitier",
        "stimme nachgeahm",
    ],
    "trifft_entscheidungen_ueber_menschen": [
        "entscheidet ueber",
        "entscheidet über",
        "bewertet personen",
        "bewertet bewerber",
        "bewertet mitarbeiter",
        "lehnt ab",
        "sortiert aus",
        "vorauswahl",
        "scoring",
        "bonitaet",
        "bonität",
    ],
    # Ein Modell mit allgemeinem Verwendungszweck im Sinne des Artikels 51 ist
    # nicht, wer irgendein Modell trainiert — es ist, wer eines *in Verkehr
    # bringt*. Ein Ingenieurbüro, das ein freies Modell auf die eigene
    # Fachsprache nachstimmt und nichts nach außen gibt, bleibt Betreiber.
    # Darum verlangt jede Wendung hier entweder den ausdrücklichen Begriff
    # oder das Bereitstellen für andere. Wortstämme, keine gebeugten Formen:
    # "trainier" trifft "trainieren" wie "trainiert".
    "ist_basismodell": [
        "basismodell",
        "foundation model",
        "allgemeiner verwendungszweck",
        "modell von grund auf",
        "modell andere unternehmen bereit",
        "modell anderen zur verfuegung",
        "modell ueber programmierschnittstelle",
        "modell in verkehr",
        "modell veroeffentlich",
        "modell herausgeb",
        # "bieten es an" ist ein getrenntes Verb: der Stamm "biet" trifft es,
        # "anbiet" nicht.
        "sprachmodell biet",
        "modell biet",
        "modell nachgelagerte anbieter",
    ],
    "beschaeftigtendaten": [
        "mitarbeiter",
        "beschaeftigte",
        "beschäftigte",
        "bewerber",
        "personal",
        "angestellte",
    ],
    "oeffentliche_stelle": [
        "behoerde",
        "behörde",
        "amt",
        "ministerium",
        "oeffentliche stelle",
        "öffentliche stelle",
        "kommune",
    ],
    "verarbeitet_personenbezogene_daten": [
        "personenbezogen",
        "kundendaten",
        "mitarbeiterdaten",
        "name",
        "adresse",
        "e-mail",
        "patientendaten",
        "bewerberdaten",
    ],
    # "Maschine" oder "Fahrzeug" allein sagt nichts über einen Einbau: der
    # Maschinenbauer, der Handbücher übersetzt, nennt seine Maschine auch.
    "eingebaut_in_produkt": [
        "sicherheitsbauteil",
        "eingebaut in",
        "bestandteil des produkts",
        "medizinprodukt",
        "fahrzeugbauteil",
        "typgenehmigung",
        "als bauteil",
        "notbremsassistent",
        "fahrerassistenz",
        "steuerung der maschine",
        "in die maschine",
        "in das fahrzeug",
    ],
    "soziale_bewertung": [
        "social scoring",
        "sozialbewertung",
        "sozialpunkte",
        "vertrauenswuerdigkeit",
        "vertrauenswürdigkeit",
        "vertrauenswert",
        "kundenbewertung verhalten",
        "verhaltensscore",
        "verhaltenspunkte",
        "buergerbewertung",
        "bürgerbewertung",
        "zuverlaessigkeitsbewertung",
        "zuverlässigkeitsbewertung",
        "zuverlaessigkeitspunkte",
        "punktwert kunde",
        "kundenwert verhalten",
    ],
    "gesichtsbilder_ungezielt_gesammelt": [
        "gesichter aus dem internet",
        "gesichtsbilder sammeln",
        "scrapen",
        "scraping",
        "gesichtsdatenbank",
        "profilbilder",
        "profilbilder herunterlad",
        "bilder aus sozialen netzwerken",
        "massenhaft bilder",
        "massenhaft profilbilder",
        "ungezielt gesichter",
        "ueberwachungsaufnahmen einspeisen",
    ],
    "biometrische_echtzeit_fernidentifizierung": [
        "echtzeit",
        "live-gesichtserkennung",
        "fernidentifizierung",
    ],
    # Vorsicht: "Platz" allein taugt nicht als Stichwort, sonst trifft es
    # "Arbeitsplatz". Darum stehen hier nur Wortgruppen und eindeutige Orte.
    "oeffentlich_zugaenglicher_raum": [
        "oeffentlicher raum",
        "öffentlicher raum",
        "oeffentlich zugaenglich",
        "öffentlich zugänglich",
        "oeffentliche plaetz",
        "öffentliche plätz",
        "oeffentlichen plaetz",
        "öffentlichen plätz",
        "oeffentlicher platz",
        "öffentlicher platz",
        "marktplatz",
        "bahnhof",
        "bahnsteig",
        "flughafen",
        "innenstadt",
        "einkaufszentrum",
        "fussgaengerzone",
        "fußgängerzone",
        "stadion",
        "haltestelle",
        "u-bahn",
        "s-bahn",
        "strassenverkehr",
        "oeffentliche strasse",
        "öffentliche straße",
        "park",
        "schulhof",
        "veranstaltungsort",
        "konzert",
        "messegelaende",
        "messegelände",
        "sportveranstaltung",
        "fussgaengerweg",
    ],
    "zweck_strafverfolgung": ["strafverfolgung", "polizei", "ermittlung", "fahndung", "straftat"],
    "bereich_arbeit_oder_bildung": [
        "arbeitsplatz",
        "buero",
        "büro",
        "betrieb",
        "schule",
        "hochschule",
        "universitaet",
        "universität",
        "unterricht",
        "pruefung",
        "prüfung",
        "ausbildung",
        "callcenter",
        "kundendienst",
        "mitarbeiter",
        "beschaeftigte",
        "beschäftigte",
        "angestellte",
        "personal",
        "belegschaft",
        "team",
        "schicht",
        "azubi",
        "auszubildende",
        "klassenzimmer",
        "seminar",
        "lehrkraft",
        "schueler",
        "schüler",
        "studierende",
        "lernende",
        "fahrer",
        "fahrerin",
        "arbeitnehmer",
        "kollege",
        "kollegin",
        "dienstplan",
        "arbeitszeit",
        "bewerber",
        "bewerbung",
        "bewerbungsgespraech",
        "bewerbungsgespräch",
        "erstgespraech",
        "erstgespräch",
        "videointerview",
        "vorstellungsgespraech",
        "vorstellungsgespräch",
        "einstellungsverfahren",
        "auswahlverfahren",
    ],
    "leitet_geschuetzte_merkmale_ab": [
        "ethnie",
        "herkunft erkennen",
        "religion",
        "politische",
        "gewerkschaft",
        "sexuelle orientierung",
        "hautfarbe",
    ],
    "nutzt_schwaeche_aus": [
        "kinder",
        "minderjaehrige",
        "minderjährige",
        "behinderung",
        "schulden",
        "notlage",
        "armut",
    ],
    "straftatvorhersage_person": [
        "rueckfall",
        "rückfall",
        "straftat vorhersag",
        "taeterprofil",
        "täterprofil",
        "risikoscore person",
    ],
}


def _flach(text: str) -> str:
    text = text.lower()
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(alt, neu)
    return text


#: Träger biometrischer Daten. Emotionserkennung im Sinne von Artikel 3
#: Nummer 39 setzt biometrische Daten voraus — Stimme, Gesicht, Mimik,
#: Körpersignale. Wer Freitexte einer Kundenumfrage auswertet, betreibt keine
#: Emotionserkennung nach der Verordnung, auch wenn das Ergebnis "Stimmung"
#: heißt. Ohne diese Unterscheidung würde das Werkzeug harmlose Umfragen zur
#: Wortmarken für die vier Ausnahmefälle des Artikels 6 Absatz 3. Die
#: Verordnung beschreibt sie abstrakt — "eng umgrenzte verfahrenstechnische
#: Aufgabe". Kein Anbieter schreibt das so hin; er schreibt "liest die Angaben
#: ein und überträgt sie in feste Felder". Darum stehen hier die Wendungen, in
#: denen die vier Fälle tatsächlich auftreten.
_AUSNAHMEFAELLE: dict[str, tuple[str, ...]] = {
    "ausn-a-enge-aufgabe": (
        "feste felder",
        "festes format",
        "in ein format bringen",
        "format bringen",
        "angaben uebertragen",
        "angaben übertragen",
        "daten uebertragen",
        "strukturiert ablegen",
        "aus textdateien einliest",
        "einliest und uebertraegt",
        "umwandeln in",
        "in tabellenform",
        "felder uebertragen",
    ),
    "ausn-b-verbesserung": (
        "glaettet",
        "glättet",
        "rechtschreibung",
        "satzbau",
        "schreibhilfe",
        "formulierung vorschlag",
        "verstaendlichere formulierung",
        "verständlichere formulierung",
        "sprachlich verbessern",
        "korrekturvorschlag",
        "stil verbessern",
        "uebersetzt den fertigen",
        "nachbearbeitet den text",
    ),
    "ausn-c-muster-erkennen": (
        "abweichung meldet",
        "meldet abweichung",
        "weicht ab",
        "anders bewertet als",
        "notenverteilung",
        "muster erkennt",
        "erkennt ein muster",
        "auffaelliges muster",
        "auffälliges muster",
        "mustererkennung",
        "abweichung vom ueblichen",
        "verteilung auswerten",
        "hinweist auf abweichung",
    ),
    "ausn-d-vorbereitung": (
        "sortiert nach art",
        "nach art des schreibens",
        "posteingang sortieren",
        "in den ordner",
        "verschlagwort",
        "akten sortieren",
        "dateien sortieren",
        "vorbereitende aufgabe",
        "vorsortiert die unterlagen",
        "zuordnet zur abteilung",
        "zustaendige abteilung",
        "zuständige abteilung",
        "uebersetzen von unterlagen",
    ),
}

#: Wendungen, mit denen eine Beschreibung ausdrücklich sagt, dass das System
#: die Entscheidung *nicht* beeinflusst. Sie sind die zweite Voraussetzung des
#: Artikels 6 Absatz 3 und werden gebraucht, weil die Ausnahme sonst an jedem
#: Hochrisikosystem hängen bliebe, das nur harmlos klingt.
_KEIN_ENTSCHEIDUNGSEINFLUSS: tuple[str, ...] = (
    "bewertet nicht",
    "bewertet nichts",
    "bewertet keine",
    "ordnet nicht ein",
    "sortiert nicht",
    "aendert nichts",
    "ändert nichts",
    "spielt keine rolle",
    "spielt rolle keine",
    "keine rolle bei",
    "nicht gespeichert",
    "uebernimmt oder verwirft",
    "übernimmt oder verwirft",
    "unverbindlich",
    "entscheidet nicht",
    "trifft keine entscheidung",
    "vergibt keine dringlichkeit",
    "bewerbungen danach selbst",
    "ersetzt bewertung nicht",
    "mensch prueft",
    "mensch überprüft",
    "nicht vorgesetzten gemeldet",
    "keine rangfolge",
    "aendert system nicht",
    "ändert system nicht",
    "bewertet system nicht",
)

#: verbotenen Praktik erklären.
_BIOMETRISCHE_TRAEGER = (
    "kamera",
    "video",
    "bild",
    "gesicht",
    "mimik",
    "mikrofon",
    "stimme",
    "stimmlich",
    "tonfall",
    "sprachaufnahme",
    "telefon",
    "audio",
    "webcam",
    "sensor",
    "puls",
    "herzfrequenz",
    "hautleitwert",
    "augenbewegung",
    "blickrichtung",
    "koerperhaltung",
    "körperhaltung",
    "gestik",
    "eye-track",
)

#: Diese Wörter deuten auf die Ausnahme in Artikel 5 Absatz 1 Buchstabe f:
#: Emotionserkennung aus medizinischen Gründen oder aus Sicherheitsgründen.
_AUSNAHME_SICHERHEIT_MEDIZIN = (
    "sicherheitsgrund",
    "aus sicherheitsgruenden",
    "aus sicherheitsgründen",
    "arbeitssicherheit",
    "unfallverhuetung",
    "unfallverhütung",
    "medizinisch",
    "medizinische gruende",
    "medizinische gründe",
    "therapie",
    "diagnose",
    "muedigkeit",
    "müdigkeit",
    "sekundenschlaf",
    "fahrtauglichkeit",
)


def _enthaelt(text: str, woerter: tuple[str, ...] | list[str]) -> bool:
    """Trifft eine der Wendungen im Text?

    Eine Wendung aus mehreren Wörtern gilt als getroffen, wenn *alle* ihre
    tragenden Wörter im Text stehen — nicht nur, wenn sie zufällig unmittelbar
    nebeneinander vorkommen. "Wir entwickeln ein Sprachmodell und trainieren
    es" enthält "sprachmodell trainier" nicht als Zeichenfolge, meint aber
    genau das. Ein reiner Zeichenfolgenvergleich übersah solche Sätze, und ein
    Modell mit systemischem Risiko fiel als "minimal" durch.

    Einzelne Wörter treffen weiter als Wortstamm am Wortanfang: "trainier"
    trifft "trainieren" wie "trainiert".
    """
    for wendung in woerter:
        teile = [t for t in wendung.split() if len(t) > 3]
        if not teile:
            # Zu kurz für einen Wortstamm: dann muss es wörtlich dastehen.
            if wendung in text:
                return True
            continue
        if all(_wortstamm_trifft(t, text) for t in teile):
            return True
    return False


def _wortstamm_trifft(stamm: str, text: str) -> bool:
    """Trifft ein Wortstamm — auch als hinterer Teil eines zusammengesetzten Worts?

    Deutsch setzt zusammen: "Sprachmodell", "Basismodell", "KI-Modell",
    "Krankenversicherung", "Bewerbungsgespräch". Ein Stamm nur am Wortanfang
    zu suchen, übersieht genau die Wörter, die ein Nutzer schreibt — ein Modell
    mit systemischem Risiko fiel so als "minimal" durch, weil "modell" in
    "Sprachmodell" nicht am Anfang steht.

    Im Wortinneren wird aber erst ab fünf Zeichen gesucht. Kürzere Stämme
    stecken zu leicht zufällig in anderen Wörtern: "note" in "Notebook",
    "bild" in "Abbildung". Bei denen bleibt es beim Wortanfang.
    """
    if re.search(r"\b%s" % re.escape(stamm), text):
        return True
    return len(stamm) >= 5 and stamm in text


def merkmale_aus_freitext(beschreibung: Systembeschreibung) -> dict[str, bool]:
    """Liest Merkmale aus dem Freitext — als Hinweis, nicht als Beweis.

    Ausdrücklich gesetzte Felder gewinnen immer. Der Freitext füllt nur Lücken,
    und jedes so gewonnene Merkmal senkt die Sicherheit der Einstufung.
    """
    gefunden: dict[str, bool] = {}
    text = _flach(
        beschreibung.freitext
        + " "
        + beschreibung.zweck
        + " "
        + beschreibung.einsatzbereich
        + " "
        + beschreibung.nutzergruppe
    )
    if not text.strip():
        return gefunden
    for feld, woerter in _STICHWORTFELDER.items():
        if getattr(beschreibung, feld, None) is not None:
            continue
        if _enthaelt(text, woerter):
            gefunden[feld] = True

    # Emotionserkennung nur, wenn auch ein biometrischer Träger genannt ist.
    if gefunden.get("emotionserkennung") and not _enthaelt(text, _BIOMETRISCHE_TRAEGER):
        gefunden.pop("emotionserkennung")

    # Die Ausnahme Sicherheit oder Medizin hebt das Verbot auf. Sie wird
    # vermerkt, damit die Regel sie auswerten kann - und nicht verschwiegen.
    if _enthaelt(text, _AUSNAHME_SICHERHEIT_MEDIZIN):
        gefunden["ausnahme_sicherheit_medizin"] = True
    return gefunden


def _feld(beschreibung: Systembeschreibung, aus_text: dict[str, bool], name: str) -> bool | None:
    """Der Wert eines Merkmals: gesetzt, aus dem Text geschlossen, oder unbekannt."""
    wert = getattr(beschreibung, name, None)
    if wert is not None:
        return bool(wert)
    return aus_text.get(name)


# ------------------------------------------------------------------- Prüfer


class Pruefer:
    """Stuft eine Systembeschreibung ein und leitet die Pflichten ab."""

    def __init__(
        self, werk: Regelwerk | None = None, zweckfinder: Zweckfinder | None = None
    ) -> None:
        self.werk = werk or regelwerk()
        # Der Zweckweg ist der zweite Eingang in dieselben Regeln. Er wird erst
        # beim ersten Gebrauch gebaut, damit ein Lauf ohne Modelle - Prüfstand,
        # Telefon, Rechner ohne Netz - nicht am Laden eines Modells hängt.
        self._zweckfinder = zweckfinder
        self._zweckfinder_versucht = zweckfinder is not None

    def zweckfinder(self) -> Zweckfinder | None:
        """Der Zweckweg, einmal gebaut. ``None``, wenn er nicht verfügbar ist."""
        if not self._zweckfinder_versucht:
            self._zweckfinder_versucht = True
            try:
                self._zweckfinder = gemeinsamer_zweckfinder()
            except Exception as fehler:
                protokoll.warning(
                    "Zweckkatalog nicht lesbar (%s) — die Einstufung läuft allein "
                    "über die Stichworte des Regelwerks",
                    fehler,
                )
        return self._zweckfinder

    def _zwecke(self, beschreibung: Systembeschreibung) -> dict[str, Zwecktreffer]:
        """Zu jeder angestoßenen Regel der beste Zwecktreffer."""
        finder = self.zweckfinder()
        if finder is None:
            return {}
        text = " ".join(
            t
            for t in (
                beschreibung.freitext,
                beschreibung.zweck,
                beschreibung.einsatzbereich,
            )
            if t
        )
        gefunden: dict[str, Zwecktreffer] = {}
        for treffer in finder.finden(text):
            vorhanden = gefunden.get(treffer.regel)
            if vorhanden is None or treffer.wert > vorhanden.wert:
                gefunden[treffer.regel] = treffer
        return gefunden

    @staticmethod
    def _zweckbegruendung(treffer: Zwecktreffer) -> str:
        """Der Satz, der sagt, warum der Zweckweg diese Stelle gezogen hat.

        Er nennt die Stelle, den Satz der Beschreibung und den Wert. Ohne diese
        drei Angaben kann niemand nachvollziehen, woher die Einstufung kommt —
        und eine Einstufung, die man nicht nachvollziehen kann, ist für den
        Nutzer wertlos.
        """
        return (
            f"Der beschriebene Zweck entspricht {treffer.fundstelle} "
            f"({treffer.sicherheit}): {treffer.satz!r} trifft "
            f"{treffer.zweck!r} (Nähe {treffer.wert:.2f})."
        )

    # ------------------------------------------------------------- Verbote

    def _verbote(
        self,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        zwecke: dict[str, Zwecktreffer] | None = None,
    ) -> list[Risikohinweis]:
        zwecke = zwecke or {}
        hinweise: list[Risikohinweis] = []
        for regel in self.werk.risikoklassen.get("verbote", []):
            bedingungen = regel.get("wenn", [])
            werte = [_feld(beschreibung, aus_text, b["feld"]) for b in bedingungen]
            ueber_zweck = zwecke.get(regel["kennung"])
            if (not werte or any(w is not True for w in werte)) and ueber_zweck is None:
                continue

            # Verlangt der Tatbestand ein ausdrückliches Merkmal, so entscheidet
            # das Wort und nicht die Ähnlichkeit. Steht es nicht da, greift das
            # Verbot nicht - die Stelle bleibt über die anderen Prüfwege
            # erreichbar, dort aber mit Pflichten statt Untersagung.
            if not self._wortlaut_steht(regel, beschreibung):
                continue

            # Trägt die Regel eine Ausnahme und ist sie in der Beschreibung
            # erkennbar geltend gemacht, ist die Praktik nicht verboten. Sie
            # bleibt aber Emotionserkennung und fällt dann unter Anhang III
            # Nummer 1 - deshalb kein stilles Durchwinken, sondern ein
            # Hinweis mit anderer Klasse.
            if regel.get("ausnahme") and aus_text.get("ausnahme_sicherheit_medizin"):
                hinweise.append(
                    Risikohinweis(
                        klasse=Risikoklasse.HOCHRISIKO_ANHANG_III,
                        regel="{}-ausnahme".format(regel["kennung"]),
                        begruendung=(
                            "Die Beschreibung nennt einen medizinischen oder "
                            "sicherheitsbezogenen Zweck. Dann greift die Ausnahme zu "
                            "{}, und die Praktik ist nicht verboten. Sie bleibt aber "
                            "Emotionserkennung und fällt damit unter Anhang III "
                            "Nummer 1 Buchstabe c — mit allen Pflichten für "
                            "Hochrisiko-KI-Systeme. Der Ausnahmegrund ist zu "
                            "dokumentieren. Wortlaut der Ausnahme: {}".format(
                                regel.get("fundstelle", ""), " ".join(regel["ausnahme"].split())
                            )
                        ),
                        rechtsgrundlage=(
                            *tuple(regel.get("rechtsgrundlage", [])),
                            "KI-VO/anh-III/nr-1",
                        ),
                        sicherheit="zu_pruefen",
                    )
                )
                continue
            # Ein Verbot, das nur aus dem Freitext kommt, ist ein Verdacht.
            nur_text = any(b["feld"] in aus_text for b in bedingungen)
            begruendung = self._mit_ausnahme(regel)
            grundlage = tuple(regel.get("rechtsgrundlage", []))
            if ueber_zweck is not None:
                begruendung += " " + self._zweckbegruendung(ueber_zweck)
                if ueber_zweck.fundstelle not in grundlage:
                    grundlage = (ueber_zweck.fundstelle, *grundlage)
                nur_text = True
            hinweise.append(
                Risikohinweis(
                    klasse=Risikoklasse.VERBOTEN,
                    regel=regel["kennung"],
                    begruendung=begruendung,
                    rechtsgrundlage=grundlage,
                    sicherheit="zu_pruefen"
                    if nur_text
                    else regel.get("sicherheit", "wahrscheinlich"),
                )
            )
        return hinweise

    @staticmethod
    def _wortlaut_steht(regel: dict[str, Any], beschreibung: Systembeschreibung) -> bool:
        """Steht ein Wort da, das der Tatbestand der Regel ausdrücklich verlangt?"""
        verlangt = regel.get("verlangt_wortlaut") or []
        if not verlangt:
            return True
        text = _flach(" ".join((beschreibung.freitext, beschreibung.zweck)))
        return any(_flach(wort) in text for wort in verlangt)

    @staticmethod
    def _mit_ausnahme(regel: dict[str, Any]) -> str:
        text = " ".join((regel.get("begruendung") or "").split())
        if regel.get("ausnahme"):
            text += " Ausnahme: {}".format(" ".join(regel["ausnahme"].split()))
        return text

    # ---------------------------------------------------------- Hochrisiko

    def _anhang_i(
        self,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        zwecke: dict[str, Zwecktreffer] | None = None,
    ) -> Risikohinweis | None:
        zwecke = zwecke or {}
        regel = self.werk.risikoklassen.get("hochrisiko_anhang_i") or {}
        if not regel:
            return None
        ueber_zweck = zwecke.get(regel["kennung"])
        werte = [_feld(beschreibung, aus_text, b["feld"]) for b in regel.get("wenn", [])]
        sicher = bool(werte) and all(w is True for w in werte)

        # Die drei Bedingungen der Regel ("Produkt unter Anhang I",
        # "Konformitätsbewertung durch Dritte") kann niemand beantworten, der
        # die Verordnung nicht schon kennt - genau diese Arbeit soll der Helfer
        # abnehmen. Darum wird zweitens über die Produktgattung gegangen: nennt
        # die Beschreibung ein Medizinprodukt, ein Fahrzeugbauteil, eine
        # Maschine, so ist das der Anhang-I-Weg, auch wenn die Felder leer sind.
        if not sicher:
            text = _flach(
                " ".join((beschreibung.freitext, beschreibung.zweck, beschreibung.einsatzbereich))
            )
            produkt = any(self._stichwort_trifft(w, text) for w in regel.get("stichworte", []))
            traeger = _feld(beschreibung, aus_text, "eingebaut_in_produkt") is True
            # Der Zweckweg nennt die Produktgattung selbst - "Wir bauen ein
            # KI-Teil, das eine Maschine sicher hält". Damit ist der Einbau
            # mitgesagt, und das Merkmal muss nicht zusätzlich gesetzt sein:
            # wer die Gattung nicht kennt, kann das Feld auch nicht füllen.
            if not (produkt and traeger) and ueber_zweck is None:
                return None

        begruendung = " ".join(regel.get("begruendung", "").split())
        grundlage = tuple(regel.get("rechtsgrundlage", []))
        if ueber_zweck is not None:
            begruendung += " " + self._zweckbegruendung(ueber_zweck)
            if ueber_zweck.fundstelle not in grundlage:
                grundlage = (ueber_zweck.fundstelle, *grundlage)
            begruendung += (
                " Zu prüfen bleibt, ob für dieses Produkt eine "
                "Konformitätsbewertung durch eine dritte Stelle verlangt wird — "
                "nur dann greift Artikel 6 Absatz 1."
            )
        return Risikohinweis(
            klasse=Risikoklasse.HOCHRISIKO_ANHANG_I,
            regel=regel["kennung"],
            begruendung=begruendung,
            rechtsgrundlage=grundlage,
            sicherheit="wahrscheinlich" if sicher else "zu_pruefen",
        )

    @staticmethod
    def _stamm_trifft(wort: str, text: str) -> bool:
        """Trifft ein Wort am Wortanfang? "bewerbung" trifft "bewerbungen"."""
        wort = _flach(wort)
        return len(wort) > 3 and bool(re.search(rf"\b{re.escape(wort)}", text))

    @classmethod
    def _stichwort_trifft(cls, stichwort: str, text: str) -> bool:
        """Prüft eine Wortgruppe: *alle* tragenden Wörter müssen vorkommen.

        Die Stichworte der Regeldatei sind oft Wortgruppen wie "note
        automatisch". Würde ein einzelnes Wort daraus genügen, erfasste
        "automatisch" jede Beschreibung, in der irgendetwas automatisch läuft —
        und eine Kreditprüfung landete im Bildungsbereich. Darum gilt eine
        Wortgruppe nur als getroffen, wenn jedes ihrer Wörter im Text steht.

        Einzelne, für den Bereich kennzeichnende Wörter stehen dafür in der
        Regeldatei unter ``starke_woerter`` und treffen allein. Diese Trennung
        gehört in die Daten, nicht in die Logik: welches Wort einen Bereich
        kennzeichnet, ist eine Rechtsfrage, keine Programmierfrage.
        """
        teile = [t for t in _flach(stichwort).split() if len(t) > 3]
        if not teile:
            return False
        return all(cls._stamm_trifft(t, text) for t in teile)

    def _anhang_iii(
        self,
        beschreibung: Systembeschreibung,
        _aus_text: dict[str, bool] | None = None,
        zwecke: dict[str, Zwecktreffer] | None = None,
    ) -> list[Risikohinweis]:
        """Findet die Anhang-III-Bereiche über die Stichworte der Regeldatei.

        ``_aus_text`` wird hier nicht gebraucht - dieser Weg liest den Freitext
        selbst, weil er Wortgruppen und Wortstämme sucht, nicht fertige
        Merkmale. Der Unterstrich sagt das; das Argument bleibt, damit alle
        Prüfwege dieselbe Form haben.
        """
        zwecke = zwecke or {}
        teil = self.werk.risikoklassen.get("hochrisiko_anhang_iii") or {}
        text = _flach(
            " ".join(
                (
                    beschreibung.freitext,
                    beschreibung.zweck,
                    beschreibung.einsatzbereich,
                    beschreibung.nutzergruppe,
                )
            )
        )
        # Ausdrückliche Entlastung: "die Vorschläge sind unverbindlich",
        # "geprüft werden Teile, nicht Menschen". Dann fehlt es am Einsatz
        # *für* einen Bereich des Anhangs III, und der Bereich wird nicht
        # gezogen. Gewertet wird nur die ausdrückliche Aussage.
        entlastet = any(_flach(w) in text for w in teil.get("entlastung", []))

        hinweise: list[Risikohinweis] = []
        for bereich in teil.get("bereiche", []):
            treffer = [w for w in bereich.get("starke_woerter", []) if self._stamm_trifft(w, text)]
            treffer += [w for w in bereich.get("stichworte", []) if self._stichwort_trifft(w, text)]

            # Zweiter Weg: Trägerwort und Handlungswort zusammen. Er erfasst
            # die Fälle, die kein einzelnes kennzeichnendes Wort tragen - eine
            # Leistungskennzahl für Beschäftigte etwa nennt weder "Beförderung"
            # noch "Kündigung", ist aber genau Anhang III Nummer 4.
            paar = bereich.get("kombination") or {}
            if paar:
                traeger = [w for w in paar.get("traeger", []) if self._stamm_trifft(w, text)]
                handlung = [w for w in paar.get("handlung", []) if self._stichwort_trifft(w, text)]
                if traeger and handlung:
                    treffer += [f"{traeger[0]} + {handlung[0]}"]

            ueber_zweck = zwecke.get(bereich["kennung"])
            # Kommt ein Bereich allein über den Zweckweg und sagt die
            # Beschreibung ausdrücklich, dass nichts bewertet und nichts
            # entschieden wird, so wird er nicht gezogen. Der Zweckweg hat dann
            # nur eine Wortverwandtschaft gefunden - gemessen traf "eingehende
            # Mails nach Abteilung sortiert" den Satz "Wir sichten Bewerbungen
            # und sortieren sie vor" mit 0,75, weil beide Male sortiert wird.
            # Gegen eine ausdrückliche Verneinung wiegt das nicht. Der
            # Stichwortweg bleibt davon unberührt: wer "Bewerbungen bewertet,
            # entscheidet aber nichts" schreibt, fällt weiter unter Anhang III
            # Nummer 4, und erst Artikel 6 Absatz 3 entlastet ihn.
            if not treffer and ueber_zweck is not None and self._kein_einfluss(beschreibung):
                continue
            if (not treffer and ueber_zweck is None) or entlastet:
                continue
            umfasst = bereich.get("umfasst") or []
            if treffer:
                begruendung = (
                    "Der beschriebene Einsatz fällt in den Bereich {!r} des "
                    "Anhangs III (Stichworte: {}).".format(
                        bereich.get("titel", ""), ", ".join(treffer[:3])
                    )
                )
            else:
                begruendung = (
                    "Der beschriebene Einsatz fällt in den Bereich {!r} des Anhangs III.".format(
                        bereich.get("titel", "")
                    )
                )
            if umfasst:
                begruendung += " Der Bereich umfasst: {}.".format("; ".join(umfasst))
            if bereich.get("ausnahme"):
                begruendung += " Zu beachten: {}".format(" ".join(bereich["ausnahme"].split()))
            grundlage = tuple(bereich.get("rechtsgrundlage", []))
            if ueber_zweck is not None:
                begruendung += " " + self._zweckbegruendung(ueber_zweck)
                # Die Fundstelle des Zweckwegs steht vor der des Bereichs: sie
                # ist der Buchstabe, nicht die Nummer, und damit die Stelle,
                # die den Fall wirklich trägt.
                if ueber_zweck.fundstelle not in grundlage:
                    grundlage = (ueber_zweck.fundstelle, *grundlage)
            hinweise.append(
                Risikohinweis(
                    klasse=Risikoklasse.HOCHRISIKO_ANHANG_III,
                    regel=bereich["kennung"],
                    begruendung=begruendung,
                    rechtsgrundlage=grundlage,
                    sicherheit="zu_pruefen",
                )
            )
        return hinweise

    @classmethod
    def _kein_einfluss(cls, beschreibung: Systembeschreibung) -> bool:
        """Sagt die Beschreibung ausdrücklich, dass nicht entschieden wird?

        Geprüft wird als Wortgruppe, nicht als Zeichenfolge: "bewertet es
        nicht" und "bewertet nicht" sind dieselbe Aussage, und an solchen
        Einschüben darf die Prüfung nicht scheitern.
        """
        text = _flach(" ".join((beschreibung.freitext, beschreibung.zweck)))
        return any(cls._stichwort_trifft(w, text) for w in _KEIN_ENTSCHEIDUNGSEINFLUSS)

    @classmethod
    def _ausnahmefall_erkannt(cls, beschreibung: Systembeschreibung) -> str | None:
        """Welcher der vier Fälle des Artikels 6 Absatz 3 passt — wenn einer."""
        text = _flach(
            " ".join((beschreibung.freitext, beschreibung.zweck, beschreibung.einsatzbereich))
        )
        for kennung, marken in _AUSNAHMEFAELLE.items():
            if any(cls._stichwort_trifft(m, text) for m in marken):
                return kennung
        return None

    def _ausnahme_pruefen(
        self, beschreibung: Systembeschreibung, aus_text: dict[str, bool]
    ) -> Risikohinweis | None:
        """Prüft Artikel 6 Absatz 3 — mit der Gegenausnahme Profiling.

        Die Ausnahme wird NICHT von allein angenommen. Sie greift nur, wenn der
        Nutzer sie ausdrücklich geltend macht, denn sie verlangt eine eigene
        dokumentierte Bewertung und eine Registrierung.
        """
        teil = self.werk.risikoklassen.get("hochrisiko_ausnahme") or {}
        if not teil:
            return None
        profiling = _feld(beschreibung, aus_text, "trifft_entscheidungen_ueber_menschen")
        gegen = teil.get("gegenausnahme") or {}

        # Die Gegenausnahme hat Vorrang: wer über Menschen entscheidet, kommt
        # aus Anhang III nicht heraus - es sei denn, die Beschreibung sagt
        # ausdrücklich, dass das System die Entscheidung nicht beeinflusst.
        if profiling is True and not self._kein_einfluss(beschreibung):
            return Risikohinweis(
                klasse=Risikoklasse.HOCHRISIKO_ANHANG_III,
                regel=gegen.get("kennung", "h6-3-profiling"),
                begruendung=" ".join((gegen.get("text") or "").split()),
                rechtsgrundlage=tuple(gegen.get("rechtsgrundlage", [])),
                sicherheit="wahrscheinlich",
            )
        fall = self._ausnahmefall_erkannt(beschreibung)
        if not (fall and self._kein_einfluss(beschreibung)):
            # Weder ein erkannter Fall noch die ausdrückliche Aussage, dass
            # nicht entschieden wird: dann bleibt es bei Anhang III. Die
            # Ausnahme von allein anzunehmen wäre der gefährlichere Fehler.
            return None
        erlaeuterung = next(
            (
                " ".join(f.get("text", "").split())
                for f in teil.get("einer_der_faelle", [])
                if f.get("kennung") == fall
            ),
            "",
        )
        folge = teil.get("folgepflicht") or {}
        return Risikohinweis(
            klasse=Risikoklasse.HOCHRISIKO_AUSNAHME,
            regel=teil["kennung"],
            begruendung=(
                "Ihre Beschreibung deutet auf den Fall: {} {} Wer sich darauf "
                "beruft, trägt die Nachweislast: {}".format(
                    erlaeuterung,
                    " ".join((teil.get("voraussetzung") or "").split()),
                    " ".join((folge.get("text") or "").split()),
                )
            ),
            rechtsgrundlage=tuple(
                teil.get("rechtsgrundlage", []) + folge.get("rechtsgrundlage", [])
            ),
            sicherheit="zu_pruefen",
        )

    # --------------------------------------------------------- Transparenz

    def _transparenz(
        self,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        zwecke: dict[str, Zwecktreffer] | None = None,
    ) -> list[Risikohinweis]:
        zwecke = zwecke or {}
        teil = self.werk.risikoklassen.get("transparenz") or {}
        hinweise: list[Risikohinweis] = []
        for fall in teil.get("faelle", []):
            # Artikel 50 verteilt seine Pflichten auf zwei Adressaten:
            # Absatz 1 und 2 binden den Anbieter, Absatz 3 und 4 den Betreiber.
            # Wer ChatGPT benutzt, muss die erzeugten Texte nicht mit einem
            # Wasserzeichen versehen - das ist Sache des Modellanbieters. Die
            # Rolle steht in der Regeldatei und wird hier angewandt; ohne sie
            # bekam ein Betreiber die Pflichten des Anbieters vorgehalten.
            # Ein Fall nennt entweder eine Rolle oder mehrere. Mehrere stehen
            # da, wo die Pflicht dem Wortlaut nach eine Rolle trifft, der Fall
            # aber auch der anderen zu sagen ist.
            erlaubt = fall.get("rollen") or ([fall["rolle"]] if fall.get("rolle") else [])
            if (
                erlaubt
                and beschreibung.rollen
                and not any(Rolle(r) in beschreibung.rollen for r in erlaubt)
            ):
                continue
            werte = [_feld(beschreibung, aus_text, b["feld"]) for b in fall.get("wenn", [])]
            getroffen = bool(werte) and all(w is True for w in werte)
            # "oder_wenn": eine Alternative genügt. Artikel 50 Absatz 4 braucht
            # sie: er greift bei Deepfakes, und daneben steht die Frage, ob
            # veröffentlichte erzeugte Bilder einen echten Ort oder eine
            # erkennbare Person vortäuschen - das ist zu prüfen und nicht zu
            # entscheiden, muss dem Nutzer aber gesagt werden.
            for satz in fall.get("oder_wenn", []):
                einzeln = [_feld(beschreibung, aus_text, b["feld"]) for b in satz.get("wenn", [])]
                if einzeln and all(w is True for w in einzeln):
                    getroffen = True
                    break
            ueber_zweck = zwecke.get(fall["kennung"])
            if not getroffen and ueber_zweck is None:
                continue
            nur_text = any(b["feld"] in aus_text for b in fall.get("wenn", []))
            begruendung = "{} ({})".format(
                " ".join(fall.get("pflicht", "").split()), fall.get("fundstelle", "")
            )
            grundlage = tuple(fall.get("rechtsgrundlage", []))
            if ueber_zweck is not None:
                begruendung += " " + self._zweckbegruendung(ueber_zweck)
                if ueber_zweck.fundstelle not in grundlage:
                    grundlage = (ueber_zweck.fundstelle, *grundlage)
                nur_text = True
            hinweise.append(
                Risikohinweis(
                    klasse=Risikoklasse.TRANSPARENZ,
                    regel=fall["kennung"],
                    begruendung=begruendung,
                    rechtsgrundlage=grundlage,
                    sicherheit="zu_pruefen" if nur_text else "wahrscheinlich",
                )
            )
        return hinweise

    # ---------------------------------------------------------------- GPAI

    def _gpai(
        self,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        zwecke: dict[str, Zwecktreffer] | None = None,
    ) -> list[Risikohinweis]:
        zwecke = zwecke or {}
        teil = self.werk.risikoklassen.get("gpai") or {}
        if not teil:
            return []
        werte = [_feld(beschreibung, aus_text, b["feld"]) for b in teil.get("wenn", [])]
        ueber_zweck = zwecke.get(teil["kennung"])
        if (not werte or any(w is not True for w in werte)) and ueber_zweck is None:
            return []

        # Sagt die Beschreibung ausdrücklich, dass das Modell nicht in Verkehr
        # kommt, greift die Ausnahme des Artikels 3 Nummer 63.
        freitext = _flach(" ".join((beschreibung.freitext, beschreibung.zweck)))
        if any(_flach(w) in freitext for w in teil.get("entlastung", [])):
            return []

        # Die Artikel 51 und 53 richten sich an *Anbieter* von KI-Modellen mit
        # allgemeinem Verwendungszweck. Wer eines einkauft, ist Betreiber — und
        # zwar auch dann, wenn in seiner Beschreibung das Wort "Modellanbieter"
        # vorkommt, weil er von seinem Lieferanten spricht. Wortlisten können
        # das nicht unterscheiden; die Rolle kann es.
        if Rolle.BETREIBER in beschreibung.rollen and Rolle.ANBIETER not in beschreibung.rollen:
            return []

        begruendung = (
            "Es wird selbst ein KI-Modell mit allgemeinem Verwendungszweck "
            "bereitgestellt. Damit greifen die Pflichten für Modellanbieter."
        )
        grundlage = tuple(teil.get("rechtsgrundlage", []))
        if ueber_zweck is not None:
            begruendung += " " + self._zweckbegruendung(ueber_zweck)
            if ueber_zweck.fundstelle not in grundlage:
                grundlage = (ueber_zweck.fundstelle, *grundlage)
        hinweise = [
            Risikohinweis(
                klasse=Risikoklasse.GPAI,
                regel=teil["kennung"],
                begruendung=begruendung,
                rechtsgrundlage=grundlage,
                sicherheit="wahrscheinlich",
            )
        ]
        systemisch = teil.get("systemisches_risiko") or {}
        schwelle = float(systemisch.get("schwelle_flop", 1e25))
        if beschreibung.rechenaufwand_flop and beschreibung.rechenaufwand_flop >= schwelle:
            hinweise.append(
                Risikohinweis(
                    klasse=Risikoklasse.GPAI_SYSTEMISCH,
                    regel=systemisch.get("kennung", "g51-systemisch"),
                    begruendung=(
                        "Der angegebene Trainingsaufwand von {:.1e} "
                        "Gleitkommaoperationen erreicht die Schwelle von {:.0e}. "
                        "{}".format(
                            beschreibung.rechenaufwand_flop,
                            schwelle,
                            " ".join((systemisch.get("vermutung") or "").split()),
                        )
                    ),
                    rechtsgrundlage=tuple(systemisch.get("rechtsgrundlage", [])),
                    sicherheit="wahrscheinlich",
                )
            )
        return hinweise

    # ------------------------------------------------------------- Pflichten

    @staticmethod
    def _merkmal_steht(
        name: str, beschreibung: Systembeschreibung, aus_text: dict[str, bool]
    ) -> bool | None:
        """Was die Beschreibung zu einem Merkmal sagt — oder None, wenn nichts.

        Die ausdrückliche Angabe des Nutzers wiegt mehr als der Freitext. Sagt
        er nichts und findet sich auch im Freitext kein Hinweis, bleibt es
        offen; dann entscheidet ``bei_unbekannt`` in der Regeldatei.
        """
        gesetzt = getattr(beschreibung, name, None)
        if isinstance(gesetzt, bool):
            return gesetzt
        if name in aus_text:
            return aus_text[name]
        return None

    def _merkmalsfilter(
        self, satz: dict, beschreibung: Systembeschreibung, aus_text: dict[str, bool]
    ) -> tuple[bool, str]:
        """Entscheidet, ob eine merkmalsgebundene Pflicht genannt wird.

        Rückgabe: (nennen, Vorbehalt). Einige Pflichten hängen nicht an der
        Risikoklasse, sondern an einem Merkmal des Systems — die Genehmigung
        für biometrische Fernidentifizierung etwa trifft einen Bewerbungsfilter
        nicht. Ohne diesen Filter erscheint bei jedem Hochrisikosystem die
        gesamte Hochrisikoliste, und der Nutzer muss selbst aussortieren; genau
        das soll ihm abgenommen werden.

        Die Richtung ist bewusst vorsichtig: weggelassen wird nur, was die
        Beschreibung ausdrücklich ausschliesst, oder was so eng umgrenzt ist,
        dass ohne jeden Hinweis darauf nichts dafür spricht
        (``bei_unbekannt: weglassen``). Alles andere wird genannt, dann aber mit
        Vorbehalt, damit der Nutzer die Bedingung selbst prüfen kann.
        """
        merkmale = satz.get("nur_wenn") or []
        zwingend = satz.get("nur_wenn_alle") or []
        if not merkmale and not zwingend:
            return True, ""

        # "nur_wenn_alle" ist die engere Bindung: jedes genannte Merkmal muss
        # zutreffen. Artikel 26 Absatz 10 etwa verlangt nicht nur Biometrie,
        # sondern zusätzlich den Zweck der Strafverfolgung — sonst landet die
        # Pflicht bei jeder Zutrittskontrolle am Werkstor.
        if zwingend:
            streng = [self._merkmal_steht(m, beschreibung, aus_text) for m in zwingend]
            if any(b is not True for b in streng):
                if satz.get("bei_unbekannt", "mit_vorbehalt") == "weglassen" or any(
                    b is False for b in streng
                ):
                    return False, ""
                return True, " ".join(satz.get("vorbehalt", "").split())
            if not merkmale:
                return True, ""

        befunde = [self._merkmal_steht(m, beschreibung, aus_text) for m in merkmale]
        if any(b is True for b in befunde):
            return True, ""
        if all(b is False for b in befunde):
            return False, ""
        if satz.get("bei_unbekannt", "mit_vorbehalt") == "weglassen":
            return False, ""
        return True, " ".join(satz.get("vorbehalt", "").split()) or (
            "Diese Pflicht greift nur, wenn Ihr System das Merkmal {} aufweist. "
            "Ihre Beschreibung sagt dazu nichts — bitte selbst prüfen.".format(
                " oder ".join(m.replace("_", " ") for m in merkmale)
            )
        )

    def _pflichten(
        self,
        klassen: set[Risikoklasse],
        rollen: set[Rolle],
        beschreibung: Systembeschreibung | None = None,
        aus_text: dict[str, bool] | None = None,
    ) -> list[Pflicht]:
        """Alle Pflichten, die zu Klasse, Rolle und Merkmalen passen."""
        beschreibung = beschreibung or Systembeschreibung()
        aus_text = aus_text or {}
        gefunden: list[Pflicht] = []
        for satz in self.werk.pflichten:
            satz_klassen = {
                Risikoklasse(k)
                for k in satz.get("klassen", [])
                if k in Risikoklasse._value2member_map_
            }
            satz_rollen = {
                Rolle(r) for r in satz.get("rollen", []) if r in Rolle._value2member_map_
            }
            if satz_klassen and not (satz_klassen & klassen):
                continue
            if satz_rollen and rollen and not (satz_rollen & rollen):
                continue
            nennen, vorbehalt = self._merkmalsfilter(satz, beschreibung, aus_text)
            if not nennen:
                continue
            gilt_ab = satz.get("gilt_ab")
            gefunden.append(
                Pflicht(
                    kennung=satz["kennung"],
                    titel=satz.get("titel", satz["kennung"]),
                    was_zu_tun_ist=" ".join(satz.get("was_zu_tun_ist", "").split()),
                    rechtsgrundlage=tuple(satz.get("rechtsgrundlage", [])) or ("",),
                    auch_genannt=tuple(satz.get("auch_genannt", [])),
                    fundstellen_text=satz.get("fundstellen_text", ""),
                    rollen=tuple(satz_rollen) or tuple(rollen) or (Rolle.ANBIETER,),
                    klassen=tuple(satz_klassen) or tuple(klassen),
                    schwere=Schwere(satz.get("schwere", "pflicht"))
                    if satz.get("schwere") in Schwere._value2member_map_
                    else Schwere.PFLICHT,
                    gilt_ab=gilt_ab if isinstance(gilt_ab, date) else None,
                    nachweis=" ".join(satz.get("nachweis", "").split()),
                    bei_verstoss=" ".join(satz.get("bei_verstoss", "").split()),
                    vorbehalt=vorbehalt,
                )
            )
        # Schwerste Pflichten zuerst, dann nach Fundstelle.
        return sorted(gefunden, key=lambda p: (p.schwere.value, p.fundstellen_text))

    #: Diese Abschnitte des Datenschutzpfads gelten bei jeder Verarbeitung
    #: personenbezogener Daten. Sie kommen immer mit.
    IMMER_DATENSCHUTZ = frozenset(
        {
            "a-personenbezug",
            "b-rolle",
            "c-rechtsgrundlage",
            "d1-grundsatz-rechtmaessigkeit",
            "d2-grundsatz-zweckbindung",
            "d3-grundsatz-datenminimierung",
            "d5-grundsatz-speicherbegrenzung",
            "d6-grundsatz-integritaet-vertraulichkeit",
            "d7-grundsatz-rechenschaftspflicht",
            "e-information-der-betroffenen",
            "f-betroffenenrechte",
            "i-verzeichnis-verarbeitungstaetigkeiten",
            "k-sicherheit-der-verarbeitung",
            "o-meldung-datenschutzverletzung",
        }
    )

    #: Diese Abschnitte greifen nur unter einer Bedingung. Ohne diese Zuordnung
    #: bekäme jeder Nutzer alle 26 Abschnitte — das ist der volle Prüfpfad und
    #: damit keine Auskunft mehr, sondern eine Materialsammlung.
    BEDINGTER_DATENSCHUTZ: ClassVar[dict[str, tuple[str, ...]]] = {
        "g-automatisierte-entscheidung": ("trifft_entscheidungen_ueber_menschen",),
        "h-auftragsverarbeitung": ("zugekauft",),
        "j-datenschutz-durch-technikgestaltung": ("eigenentwicklung",),
        "l-datenschutz-folgenabschaetzung": ("hohes_risiko",),
        "m-vorherige-konsultation": ("hohes_risiko",),
        "n-datenschutzbeauftragter": ("viele_beschaeftigte",),
        "p-benachrichtigung-betroffener": ("hohes_risiko",),
        "q-drittlandsuebermittlung": ("drittlandtransfer",),
        "r-beschaeftigtendaten": ("beschaeftigtendaten",),
        "s-training-mit-personenbezogenen-daten": ("training_mit_daten",),
        "t-zusammenspiel-mit-der-ki-verordnung": ("immer_bei_ki",),
        "d4-grundsatz-richtigkeit": ("trifft_entscheidungen_ueber_menschen",),
    }

    def _bedingung_erfuellt(
        self,
        name: str,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        klassen: set[Risikoklasse],
    ) -> bool:
        """Löst die Bedingungen der bedingten Datenschutzabschnitte auf."""
        if name == "immer_bei_ki":
            return True
        if name == "hohes_risiko":
            return bool(
                klassen
                & {
                    Risikoklasse.HOCHRISIKO_ANHANG_I,
                    Risikoklasse.HOCHRISIKO_ANHANG_III,
                    Risikoklasse.HOCHRISIKO_AUSNAHME,
                    Risikoklasse.VERBOTEN,
                }
            )
        if name == "viele_beschaeftigte":
            zahl = beschreibung.anzahl_beschaeftigte
            return zahl is not None and zahl >= 20
        if name == "drittlandtransfer":
            return _feld(beschreibung, aus_text, "drittlandtransfer") is True
        if name == "beschaeftigtendaten":
            return _feld(beschreibung, aus_text, "beschaeftigtendaten") is True
        if name == "training_mit_daten":
            flach = _flach(beschreibung.freitext + " " + beschreibung.zweck)
            return any(
                w in flach
                for w in ("trainier", "feinabstimm", "fine-tun", "lernt aus", "mit unseren daten")
            )
        if name == "zugekauft":
            flach = _flach(beschreibung.freitext)
            return any(
                w in flach
                for w in (
                    "zugekauft",
                    "eingekauft",
                    "fremdes system",
                    "von einem anbieter",
                    "dienstleister",
                    "anbieter",
                    "api",
                    "schnittstelle",
                )
            )
        if name == "eigenentwicklung":
            return Rolle.ANBIETER in beschreibung.rollen
        return _feld(beschreibung, aus_text, name) is True

    def _datenschutz(
        self,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        klassen: set[Risikoklasse] | None = None,
    ) -> list[Pflicht]:
        """Der Datenschutzpfad — nur die Abschnitte, die hier greifen."""
        personenbezug = _feld(beschreibung, aus_text, "verarbeitet_personenbezogene_daten")
        if personenbezug is False:
            return []
        klassen = klassen or set()
        gefunden: list[Pflicht] = []
        for abschnitt in self.werk.datenschutz:
            kennung = abschnitt.get("kennung", "")
            bedingungen = self.BEDINGTER_DATENSCHUTZ.get(kennung)
            if bedingungen is not None:
                if not all(
                    self._bedingung_erfuellt(b, beschreibung, aus_text, klassen)
                    for b in bedingungen
                ):
                    continue
            elif kennung not in self.IMMER_DATENSCHUTZ:
                # Unbekannter Abschnitt: mitnehmen, aber nicht stillschweigend
                # verschweigen - eine neue Regeldatei soll nicht Teile verlieren.
                protokoll.debug("Datenschutzabschnitt ohne Zuordnung: %s", kennung)
            gefunden.append(
                Pflicht(
                    kennung=abschnitt.get("kennung", "ds-unbenannt"),
                    titel=abschnitt.get("titel", ""),
                    was_zu_tun_ist=" ".join(
                        (abschnitt.get("was_zu_tun_ist") or abschnitt.get("frage") or "").split()
                    ),
                    rechtsgrundlage=tuple(abschnitt.get("rechtsgrundlage", [])) or ("",),
                    auch_genannt=tuple(abschnitt.get("auch_genannt", [])),
                    fundstellen_text=abschnitt.get("fundstellen_text", ""),
                    rollen=(Rolle.ANBIETER, Rolle.BETREIBER),
                    klassen=(Risikoklasse.MINIMAL,),
                    schwere=Schwere.PFLICHT,
                    nachweis=" ".join(abschnitt.get("nachweis", "").split()),
                    bei_verstoss=" ".join(abschnitt.get("bei_verstoss", "").split()),
                )
            )
        return gefunden

    # ---------------------------------------------------------- offene Fragen

    def _offene_fragen(
        self,
        beschreibung: Systembeschreibung,
        aus_text: dict[str, bool],
        klassen: set[Risikoklasse],
    ) -> list[str]:
        fragen: list[str] = []
        if not beschreibung.rollen:
            fragen.append(
                "Sind Sie Anbieter oder Betreiber? Anbieter entwickelt das System "
                "und bringt es unter eigenem Namen heraus; Betreiber nutzt es unter "
                "eigener Verantwortung. Die Pflichten unterscheiden sich stark."
            )
        if _feld(beschreibung, aus_text, "verarbeitet_personenbezogene_daten") is None:
            fragen.append(
                "Verarbeitet das System personenbezogene Daten — also Angaben, über "
                "die sich ein Mensch bestimmen lässt? Davon hängt ab, ob zusätzlich "
                "das Datenschutzrecht greift."
            )
        if Risikoklasse.HOCHRISIKO_ANHANG_III in klassen:
            if _feld(beschreibung, aus_text, "menschliche_kontrolle") is None:
                fragen.append(
                    "Prüft ein Mensch das Ergebnis, bevor es wirkt — und kann er es "
                    "ändern? Das entscheidet über die Ausnahme nach Artikel 6 Absatz 3."
                )
            if _feld(beschreibung, aus_text, "trifft_entscheidungen_ueber_menschen") is None:
                fragen.append(
                    "Wird mit dem System ein Profil über einzelne Menschen gebildet "
                    "oder ausgewertet? Dann greift keine Ausnahme."
                )
        if Risikoklasse.GPAI in klassen and beschreibung.rechenaufwand_flop is None:
            fragen.append(
                "Wie hoch war der Rechenaufwand beim Training in "
                "Gleitkommaoperationen? Ab 10^25 wird systemisches Risiko vermutet."
            )
        if beschreibung.gefuellt() < 3:
            fragen.append(
                "Die Beschreibung ist noch dünn. Je genauer Zweck, Einsatzbereich "
                "und betroffene Personen benannt sind, desto belastbarer die Auskunft."
            )
        return fragen

    # ------------------------------------------------------------------ Lauf

    def pruefen(self, beschreibung: Systembeschreibung) -> Einstufung:
        """Die eigentliche Einstufung."""
        aus_text = merkmale_aus_freitext(beschreibung)
        # Der Zweckweg läuft einmal und wird an alle Prüfwege weitergegeben.
        # Zweimal zu rechnen wäre zweimal Rechenzeit für dasselbe Ergebnis.
        zwecke = self._zwecke(beschreibung)
        hinweise: list[Risikohinweis] = []

        verbote = self._verbote(beschreibung, aus_text, zwecke)
        hinweise.extend(verbote)

        if not verbote:
            anhang_i = self._anhang_i(beschreibung, aus_text, zwecke)
            if anhang_i:
                hinweise.append(anhang_i)
            anhang_iii = self._anhang_iii(beschreibung, aus_text, zwecke)
            hinweise.extend(anhang_iii)
            if anhang_iii:
                ausnahme = self._ausnahme_pruefen(beschreibung, aus_text)
                if ausnahme is not None:
                    if ausnahme.klasse is Risikoklasse.HOCHRISIKO_AUSNAHME:
                        # Greift die Ausnahme, tritt sie an die Stelle der
                        # Einordnung in Anhang III - sonst stünden beide
                        # Klassen gleichzeitig da und widersprächen sich.
                        hinweise = [
                            h
                            for h in hinweise
                            if h.klasse is not Risikoklasse.HOCHRISIKO_ANHANG_III
                        ]
                    hinweise.append(ausnahme)
            hinweise.extend(self._transparenz(beschreibung, aus_text, zwecke))
            hinweise.extend(self._gpai(beschreibung, aus_text, zwecke))

        klassen = {h.klasse for h in hinweise}
        if not klassen:
            minimal = self.werk.risikoklassen.get("minimal") or {}
            hinweise.append(
                Risikohinweis(
                    klasse=Risikoklasse.MINIMAL,
                    regel=minimal.get("kennung", "m-minimal"),
                    begruendung=" ".join(minimal.get("begruendung", "").split()),
                    rechtsgrundlage=tuple(minimal.get("rechtsgrundlage", [])),
                    sicherheit="wahrscheinlich",
                )
            )
            klassen = {Risikoklasse.MINIMAL}

        rollen = set(beschreibung.rollen)
        # Wer nichts sagt, bekommt beide Sichten - sonst fehlt die halbe Auskunft.
        wirkrollen = rollen or {Rolle.ANBIETER, Rolle.BETREIBER}

        return Einstufung(
            klassen=tuple(sorted(klassen, key=lambda k: k.rang)),
            hinweise=tuple(hinweise),
            rollen=tuple(sorted(rollen, key=lambda r: r.value)),
            pflichten=tuple(self._pflichten(klassen, wirkrollen, beschreibung, aus_text)),
            datenschutz=tuple(self._datenschutz(beschreibung, aus_text, klassen)),
            offene_fragen=tuple(self._offene_fragen(beschreibung, aus_text, klassen)),
            stand=self.werk.stand,
        )


def rollen_aus_text(text: str) -> tuple[Rolle, ...]:
    """Erkennt die Rolle aus der Beschreibung — konservativ.

    "Wir kaufen ein" deutet auf Betreiber, "wir entwickeln" auf Anbieter. Steht
    beides oder keines drin, wird nichts behauptet: der Prüfer fragt dann nach.
    """
    flach = _flach(text)
    anbieter = any(
        w in flach
        for w in (
            "wir entwickeln",
            "wir bauen",
            "selbst entwickelt",
            "eigenentwicklung",
            "wir programmieren",
            "unser modell",
            "wir trainieren",
            "bringen wir auf den markt",
            "unter unserem namen",
            "wir vertreiben",
            "wir bieten an",
            "bieten wir an",
            "stellen wir zur verfuegung",
            "in verkehr bringen",
            "bringen wir in verkehr",
        )
    )
    betreiber = any(
        w in flach
        for w in (
            "wir nutzen",
            "wir setzen ein",
            "wir verwenden",
            "zugekauft",
            "eingekauft",
            "wir haben gekauft",
            "fremdes system",
            "von einem anbieter",
            "wir betreiben",
            # Der Docstring versprach "wir kaufen ein" - die Liste hatte es nicht.
            # Dazu die Wendungen, in denen ein Betreiber tatsächlich schreibt:
            # "wir lassen das System ...", "setzen es ein", "ist bei uns im Einsatz".
            "wir kaufen",
            "kaufen wir",
            "wir lassen ein",
            "lassen wir ein",
            "setzen es ein",
            "setzen wir ein",
            "im einsatz",
            "wir haben eingefuehrt",
            "wir beziehen",
            "als dienst bezogen",
        )
    )
    gefunden: list[Rolle] = []
    if anbieter:
        gefunden.append(Rolle.ANBIETER)
    if betreiber:
        gefunden.append(Rolle.BETREIBER)
    return tuple(gefunden)


#: Der Trainingsaufwand, wie Menschen ihn schreiben: "10^25", "10²⁵", "1e26",
#: "10 hoch 25", "2,5 x 10^25 Gleitkommaoperationen". Artikel 51 Absatz 2 knüpft
#: die Vermutung des systemischen Risikos an 10^25 Gleitkommaoperationen — eine
#: Beschreibung, die diese Zahl nennt, muss sie auch erkannt bekommen, sonst
#: fällt ein Modell mit systemischem Risiko als "minimal" durch.
_HOCHZAHLEN = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
#: Die hochgestellten Ziffern liegen in zwei Unicode-Blöcken: ⁰ und ⁴ bis ⁹
#: stehen bei U+2070 ff., ¹ ² ³ dagegen bei U+00B9, U+00B2, U+00B3 — ein Rest
#: aus Latin-1. Wer nur den ersten Block aufzählt, erkennt 10²⁵ nicht.
_ZIFFERN = "0-9\u2070\u2074-\u2079\u00b9\u00b2\u00b3"
_RECHENAUFWAND = re.compile(
    r"(?:(\d+(?:[.,]\d+)?)\s*(?:x|\*|·|mal)\s*)?"
    r"(?:10\s*(?:\^|\*\*|hoch\s*)?|1\s*e)\s*([" + _ZIFFERN + r"]{1,3})"
    r"(?=[^0-9]|$)",
    re.IGNORECASE,
)


def rechenaufwand_aus_text(text: str) -> float | None:
    """Liest den Trainingsaufwand aus der Beschreibung — oder None.

    Gelesen wird nur, was eindeutig als Rechenaufwand gemeint ist: die Zahl
    muss in der Nähe eines Wortes stehen, das den Aufwand benennt. Sonst würde
    jede Jahreszahl oder Stückzahl als Rechenaufwand gelten.
    """
    flach = _flach(text)
    if not any(
        wort in flach
        for wort in (
            "rechenoperation",
            "gleitkommaoperation",
            "flop",
            "rechenaufwand",
            "rechenleistung",
            "trainingsaufwand",
            "operationen trainiert",
        )
    ):
        return None
    treffer = _RECHENAUFWAND.search(text)
    if not treffer:
        return None
    vorfaktor = float((treffer.group(1) or "1").replace(",", "."))
    hochzahl = int(treffer.group(2).translate(_HOCHZAHLEN))
    if not 10 <= hochzahl <= 40:
        return None
    return vorfaktor * (10.0**hochzahl)


def beschreibung_aus_text(text: str) -> Systembeschreibung:
    """Baut aus einer freien Beschreibung das Prüfobjekt."""
    text = re.sub(r"\s+", " ", text).strip()
    return Systembeschreibung(
        freitext=text[:20_000],
        rollen=rollen_aus_text(text),
        rechenaufwand_flop=rechenaufwand_aus_text(text),
    )
