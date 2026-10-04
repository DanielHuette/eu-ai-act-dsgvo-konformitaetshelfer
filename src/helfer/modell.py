"""Das Datenmodell des Konformitätshelfers.

Alles, was durch das System läuft, hat hier eine Form: der Rechtstext in seinen
Einheiten, die Beschreibung eines KI-Systems, die Einstufung, die Pflicht und
die Antwort. Die Formen sind streng, weil eine falsche Auskunft über Pflichten
teuer ist — lieber ein Fehler beim Einlesen als eine erfundene Pflicht.

Begriffe, einmal in Alltagssprache:

* **Rechtsakt** — ein Gesetz als Ganzes, etwa die KI-Verordnung.
* **Einheit** — das kleinste Stück Recht, auf das man zeigen kann: ein Absatz
  eines Artikels, ein Punkt eines Anhangs, ein Erwägungsgrund.
* **Rolle** — was jemand im Sinne des Gesetzes ist: Anbieter, Betreiber,
  Einführer, Händler.
* **Risikoklasse** — in welche Schublade ein KI-System nach der KI-Verordnung
  fällt. Die Schublade entscheidet, welche Pflichten gelten.
"""

from __future__ import annotations

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# --------------------------------------------------------------------- Rechtsakt


class Rechtsakt(StrEnum):
    """Die Gesetze, die der Helfer kennt."""

    KI_VO = "KI-VO"
    DSGVO = "DSGVO"
    BDSG = "BDSG"
    LEITLINIE = "Leitlinie"

    @property
    def langname(self) -> str:
        return {
            "KI-VO": "Verordnung (EU) 2024/1689 über künstliche Intelligenz",
            "DSGVO": "Verordnung (EU) 2016/679 (Datenschutz-Grundverordnung)",
            "BDSG": "Bundesdatenschutzgesetz",
            "Leitlinie": "Leitlinie oder Stellungnahme einer Aufsichtsbehörde",
        }[self.value]

    @property
    def verbindlich(self) -> bool:
        """Leitlinien binden Gerichte nicht - das muss die Antwort sagen."""
        return self is not Rechtsakt.LEITLINIE


class Einheitsart(StrEnum):
    ARTIKEL = "artikel"
    PARAGRAF = "paragraf"
    ANHANG = "anhang"
    ERWAEGUNGSGRUND = "erwaegungsgrund"
    LEITLINIE = "leitlinie"
    FALLBEISPIEL = "fallbeispiel"


class Einheit(BaseModel):
    """Ein Stück Recht, auf das eine Antwort zeigen kann.

    `kennung` ist der Schlüssel durch das ganze System hindurch und sieht so
    aus: ``KI-VO/art-6/abs-2``, ``DSGVO/art-35/abs-1``, ``KI-VO/anh-III/nr-5-a``,
    ``BDSG/par-26``, ``fall/bewerbungsfilter``.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    kennung: str = Field(min_length=3, max_length=120)
    rechtsakt: Rechtsakt
    art: Einheitsart
    nummer: str = Field(description="Artikel-, Paragraf- oder Anhangsnummer als Text")
    absatz: str | None = Field(default=None, description="Absatz, Buchstabe, Ziffer")
    titel: str = ""
    kapitel: str = ""
    abschnitt: str = ""
    text: str = Field(min_length=1)
    gilt_ab: date | None = Field(default=None, description="Ab wann diese Einheit anwendbar ist")
    quelle: str = Field(default="", description="Adresse, von der der Text stammt")
    stand: date | None = Field(default=None, description="Wann der Text geholt wurde")
    verweise: tuple[str, ...] = Field(default=(), description="Kennungen verwandter Einheiten")

    @field_validator("kennung")
    @classmethod
    def kennung_sauber(cls, wert: str) -> str:
        if " " in wert:
            raise ValueError(f"Kennung darf kein Leerzeichen enthalten: {wert!r}")
        if wert.count("/") < 1:
            raise ValueError(f"Kennung braucht die Form Rechtsakt/Einheit: {wert!r}")
        return wert

    @property
    def fundstelle(self) -> str:
        """Wie die Stelle in einer Antwort zitiert wird.

        Die Verordnung zählt in Anhängen nach *Nummern*, nicht nach Absätzen —
        "Anhang III Nummer 4", nicht "Anhang III Absatz 4". Ein Fallbeispiel ist
        keine Fundstelle im Gesetz und wird mit seinem Titel genannt, nicht mit
        seiner internen Kennung.
        """
        if self.art is Einheitsart.FALLBEISPIEL:
            return f"Anwendungsfall: {self.titel or self.nummer}"
        if self.art is Einheitsart.LEITLINIE:
            return self.titel or self.nummer

        stamm = {
            Einheitsart.ARTIKEL: "Artikel %s",
            Einheitsart.PARAGRAF: "§ %s",
            Einheitsart.ANHANG: "Anhang %s",
            Einheitsart.ERWAEGUNGSGRUND: "Erwägungsgrund %s",
        }.get(self.art, "%s")
        teil = stamm % self.nummer
        if self.absatz:
            # Definitionsartikel zählen in Nummern, nicht in Absätzen:
            # "Artikel 3 Nummer 39 KI-VO", nicht "Absatz 39".
            zaehlwort = (
                "Nummer"
                if self.art is Einheitsart.ANHANG or self.absatz.startswith("Nummer ")
                else "Absatz"
            )
            if self.absatz.startswith("Nummer "):
                return "%s %s %s" % (teil, self.absatz, self.rechtsakt.value)
            teil += f" {zaehlwort} {self.absatz}"
        if self.art is Einheitsart.ERWAEGUNGSGRUND:
            return f"{teil} der {self.rechtsakt.value}"
        return f"{teil} {self.rechtsakt.value}"


# ------------------------------------------------------------------ Einstufung


class Rolle(StrEnum):
    """Wer jemand im Sinne der KI-Verordnung ist. Entscheidet die Pflichten."""

    ANBIETER = "anbieter"
    BETREIBER = "betreiber"
    EINFUEHRER = "einfuehrer"
    HAENDLER = "haendler"
    PRODUKTHERSTELLER = "produkthersteller"
    BEVOLLMAECHTIGTER = "bevollmaechtigter"
    BETROFFENE_PERSON = "betroffene_person"

    @property
    def erklaerung(self) -> str:
        return {
            "anbieter": "entwickelt ein KI-System oder lässt es entwickeln und bringt es "
            "unter eigenem Namen auf den Markt oder nimmt es in Betrieb",
            "betreiber": "verwendet ein KI-System unter eigener Verantwortung, "
            "nicht im privaten Bereich",
            "einfuehrer": "bringt ein KI-System aus einem Drittland in die Union",
            "haendler": "gibt ein KI-System in der Lieferkette weiter, ohne Anbieter "
            "oder Einführer zu sein",
            "produkthersteller": "baut ein KI-System als Sicherheitsbauteil in ein eigenes "
            "Produkt ein und bringt es unter eigenem Namen heraus",
            "bevollmaechtigter": "handelt in der Union für einen Anbieter aus einem Drittland",
            "betroffene_person": "ist von einem KI-System betroffen, ohne es zu betreiben",
        }[self.value]


class Risikoklasse(StrEnum):
    """Die Schubladen der KI-Verordnung, von oben nach unten."""

    VERBOTEN = "verboten"
    HOCHRISIKO_ANHANG_I = "hochrisiko_anhang_i"
    HOCHRISIKO_ANHANG_III = "hochrisiko_anhang_iii"
    HOCHRISIKO_AUSNAHME = "hochrisiko_ausnahme"
    TRANSPARENZ = "transparenz"
    GPAI_SYSTEMISCH = "gpai_systemisch"
    GPAI = "gpai"
    MINIMAL = "minimal"
    UNKLAR = "unklar"

    @property
    def klartext(self) -> str:
        return {
            "verboten": "verbotene Praktik — das System darf so nicht betrieben werden",
            "hochrisiko_anhang_i": "hohes Risiko über das Produktsicherheitsrecht (Anhang I)",
            "hochrisiko_anhang_iii": "hohes Risiko über den Einsatzbereich (Anhang III)",
            "hochrisiko_ausnahme": "fällt unter Anhang III, greift aber eine Ausnahme "
            "nach Artikel 6 Absatz 3 — mit Registrierungspflicht",
            "transparenz": "Transparenzpflichten nach Artikel 50",
            "gpai_systemisch": "KI-Modell mit allgemeinem Verwendungszweck und systemischem Risiko",
            "gpai": "KI-Modell mit allgemeinem Verwendungszweck",
            "minimal": "keine besonderen Pflichten außer KI-Kompetenz nach Artikel 4",
            "unklar": "die Angaben reichen für eine Einstufung nicht aus",
        }[self.value]

    @property
    def rang(self) -> int:
        """Je kleiner, desto schwerer. Wird gebraucht, wenn mehrere Klassen passen."""
        return {
            "verboten": 0,
            "hochrisiko_anhang_i": 1,
            "hochrisiko_anhang_iii": 2,
            "hochrisiko_ausnahme": 3,
            "gpai_systemisch": 4,
            "gpai": 5,
            "transparenz": 6,
            "minimal": 7,
            "unklar": 8,
        }[self.value]


class Schwere(StrEnum):
    PFLICHT = "pflicht"
    EMPFEHLUNG = "empfehlung"
    HINWEIS = "hinweis"


class Pflicht(BaseModel):
    """Eine einzelne Pflicht mit Fundstelle, Frist und einem Satz zum Tun."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kennung: str
    titel: str
    was_zu_tun_ist: str = Field(description="In Alltagssprache, als Handlungsanweisung")
    rechtsgrundlage: tuple[str, ...] = Field(min_length=1, description="Kennungen der Einheiten")
    auch_genannt: tuple[str, ...] = Field(
        default=(),
        description="Normen, auf die der Handlungstext verweist, ohne die "
        "Pflicht selbst zu begründen — etwa Artikel 72 KI-VO, auf "
        "den Artikel 26 Absatz 5 für die Information des Anbieters "
        "weiterleitet. Sie werden mitbelegt, damit in der Antwort "
        "keine Fundstelle ohne Beleg steht.",
    )
    fundstellen_text: str = Field(description="Wie zitiert wird, etwa 'Artikel 9 KI-VO'")
    rollen: tuple[Rolle, ...] = Field(min_length=1)
    klassen: tuple[Risikoklasse, ...] = Field(min_length=1)
    schwere: Schwere = Schwere.PFLICHT
    gilt_ab: date | None = None
    nachweis: str = Field(default="", description="Womit man die Erfüllung belegt")
    bei_verstoss: str = Field(default="", description="Was bei Verstoß droht")
    vorbehalt: str = Field(
        default="",
        description="Steht hier etwas, hängt die Pflicht an einem Merkmal, zu dem "
        "die Beschreibung schweigt. Dann wird sie mit diesem Vorbehalt "
        "genannt statt stillschweigend weggelassen.",
    )


class Risikohinweis(BaseModel):
    """Eine Begründung, warum eine Klasse gezogen wurde."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    klasse: Risikoklasse
    regel: str = Field(description="Kennung der Regel, die gegriffen hat")
    begruendung: str
    rechtsgrundlage: tuple[str, ...]
    sicherheit: Literal["sicher", "wahrscheinlich", "zu_pruefen"] = "wahrscheinlich"


# --------------------------------------------------------------- Beschreibung


class Systembeschreibung(BaseModel):
    """Was der Nutzer über sein KI-System erzählt.

    Alle Felder sind freiwillig: der Helfer soll auch bei dünner Beschreibung
    etwas Brauchbares sagen und dann nachfragen, statt nichts zu liefern.
    """

    model_config = ConfigDict(extra="forbid")

    freitext: str = Field(
        default="", max_length=20_000, description="Die Beschreibung in eigenen Worten"
    )
    rollen: tuple[Rolle, ...] = ()
    zweck: str = ""
    einsatzbereich: str = ""
    nutzergruppe: str = ""
    verarbeitet_personenbezogene_daten: bool | None = None
    besondere_datenkategorien: bool | None = None
    trifft_entscheidungen_ueber_menschen: bool | None = None
    menschliche_kontrolle: bool | None = None
    biometrie: bool | None = None
    emotionserkennung: bool | None = None
    erzeugt_inhalte: bool | None = None
    interagiert_mit_menschen: bool | None = None
    eingebaut_in_produkt: bool | None = None
    ist_basismodell: bool | None = None
    rechenaufwand_flop: float | None = Field(
        default=None, description="Trainingsaufwand in Gleitkommaoperationen, für Artikel 51"
    )
    oeffentliche_stelle: bool | None = None
    drittlandtransfer: bool | None = None
    beschaeftigtendaten: bool | None = None
    anzahl_beschaeftigte: int | None = None
    markt: str = Field(default="EU", description="Wo das System angeboten oder genutzt wird")

    def gefuellt(self) -> int:
        """Wie viele Angaben stehen - entscheidet, ob eine Einstufung tragfähig ist."""
        werte = self.model_dump(exclude={"freitext", "markt"})
        return sum(1 for w in werte.values() if w not in (None, "", ()))


# ------------------------------------------------------------------- Antworten


class Belegstelle(BaseModel):
    """Ein Treffer aus dem Korpus, der in der Antwort erscheint."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kennung: str
    fundstelle: str
    rechtsakt: Rechtsakt
    titel: str
    auszug: str
    punktzahl: float
    wege: tuple[str, ...] = Field(default=(), description="Welche Suchwege diesen Treffer fanden")


class Einstufung(BaseModel):
    """Das Ergebnis der Prüfung: Klasse, Rollen, Pflichten, Lücken."""

    model_config = ConfigDict(extra="forbid")

    klassen: tuple[Risikoklasse, ...]
    hinweise: tuple[Risikohinweis, ...]
    rollen: tuple[Rolle, ...]
    pflichten: tuple[Pflicht, ...]
    offene_fragen: tuple[str, ...] = Field(
        default=(), description="Was noch fehlt, um sicher einzustufen"
    )
    datenschutz: tuple[Pflicht, ...] = ()
    stand: date | None = None

    @property
    def schwerste(self) -> Risikoklasse:
        return min(self.klassen, key=lambda k: k.rang) if self.klassen else Risikoklasse.UNKLAR


class Antwort(BaseModel):
    """Was der Nutzer am Ende sieht."""

    model_config = ConfigDict(extra="forbid")

    frage: str
    text: str
    belege: tuple[Belegstelle, ...]
    einstufung: Einstufung | None = None
    lernhinweis: str = Field(default="", description="Der kleine Weiterbildungseffekt")
    beispielfaelle: tuple[str, ...] = ()
    modell: str = Field(default="", description="Womit der Text formuliert wurde")
    ohne_modell: bool = Field(
        default=False, description="True, wenn rein aus Regeln und Treffern gebaut"
    )
    warnungen: tuple[str, ...] = ()
    dauer_ms: int = 0
