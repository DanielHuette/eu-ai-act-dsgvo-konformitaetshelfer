"""Schutzmaßnahmen für den Webdienst und die Kommandozeile.

Dieses Werkzeug nimmt Freitext von außen an und gibt Rechtsauskunft. Daraus
ergeben sich vier Gefahren, und für jede steht hier eine Gegenmaßnahme:

1. **Zu große Eingaben.** Ein Text von zehn Megabyte würde die Suche und das
   Sprachmodell beschäftigen, bis nichts mehr geht. Darum feste Obergrenzen,
   geprüft *bevor* gerechnet wird.
2. **Text, der anders aussieht als er ist.** Steuerzeichen und die Zeichen zur
   Umkehr der Schreibrichtung können eine Beschreibung im Browser harmlos
   anzeigen lassen, während im Sprachmodell etwas anderes ankommt. Sie werden
   entfernt, nicht nur angezeigt.
3. **Überlast durch viele Anfragen.** Ein einzelner Rechner soll den Dienst
   nicht lahmlegen können. Dafür ein Zähler je Adresse.
4. **Schlüssel im Protokoll.** Protokolldateien werden kopiert, verschickt und
   in Fehlermeldungen eingeklebt. Ein Schlüssel darin ist ein Schlüssel in
   fremder Hand — darum wird jede Protokollzeile vorher gesäubert.

Alles hier ist absichtlich ohne Fremdpaket gebaut: eine Schutzmaßnahme, die
selbst erst nachgeladen werden muss, schützt beim ersten Start nicht.
"""

from __future__ import annotations

import os
import re
import time
import unicodedata
from collections import deque
from dataclasses import dataclass, field
from threading import Lock

# --------------------------------------------------------------- Eingabegrenzen

#: Höchstlänge einer Frage. Eine Rechtsfrage, die länger ist, ist keine Frage
#: mehr, sondern ein Schriftsatz — und gehört in das Beschreibungsfeld.
GRENZE_FRAGE = 2_000

#: Höchstlänge einer Systembeschreibung. Derselbe Wert steht im Datenmodell
#: (``Systembeschreibung.freitext``); beide Stellen müssen zusammenpassen,
#: sonst lehnt das Modell ab, was die Prüfung durchgelassen hat.
GRENZE_BESCHREIBUNG = 20_000


class Eingabefehler(ValueError):
    """Eine Eingabe, die der Dienst nicht annimmt — mit Klartext für den Nutzer.

    Eigene Klasse, damit die Schnittstelle sie von einem Programmfehler
    unterscheiden kann: diese Meldung darf nach außen, ein Programmfehler nicht.

    Der Name endet nicht auf "Error", wie es die englische Namensregel für
    Ausnahmen will: in diesem Projekt sind die Bezeichner deutsch, und
    "EingabeError" wäre keins von beidem.
    """


# ------------------------------------------------------------- Text säubern

#: Die Zeichen zur Umkehr der Schreibrichtung. Sie sind unsichtbar und drehen
#: die Anzeigerichtung des folgenden Textes um. Damit lässt sich eine Zeile
#: bauen, die im Browser "harmlos" anzeigt und im Protokoll etwas anderes
#: enthält. In einer Rechtsauskunft hat das nichts zu suchen.
_RICHTUNGSZEICHEN = frozenset(
    [chr(z) for z in range(0x202A, 0x202F)]  # U+202A bis U+202E
    + [chr(z) for z in range(0x2066, 0x206A)]  # U+2066 bis U+2069
)

#: Steuerzeichen, die erlaubt bleiben: Zeilenumbruch und Tabulator. Alles
#: andere aus der Unicode-Gruppe "Cc" wird entfernt — es trägt keinen Sinn,
#: kann aber Anzeige und Protokoll verfälschen.
_ERLAUBTE_STEUERZEICHEN = frozenset("\n\t")


def text_saeubern(text: str) -> str:
    """Entfernt Steuerzeichen und Zeichen zur Schreibrichtungsumkehr.

    Zusätzlich wird die Unicode-Form vereinheitlicht (NFC). Ohne das steht
    dasselbe Wort je nach Tastatur in zwei verschiedenen Zeichenfolgen und die
    Stichwortsuche findet es nur in einer davon.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    behalten: list[str] = []
    for zeichen in text:
        if zeichen in _RICHTUNGSZEICHEN:
            continue
        gruppe = unicodedata.category(zeichen)
        if gruppe == "Cc" and zeichen not in _ERLAUBTE_STEUERZEICHEN:
            continue
        if gruppe == "Cf":  # unsichtbare Formatzeichen, etwa Breitenlos-Trenner
            continue
        behalten.append(zeichen)
    gesaeubert = "".join(behalten)
    # Mehr als zwei Leerzeilen hintereinander tragen nichts und blähen die
    # Vorlage auf, die später an das Sprachmodell geht.
    return re.sub(r"\n{3,}", "\n\n", gesaeubert).strip()


def frage_pruefen(frage: str) -> str:
    """Prüft und säubert eine Frage. Wirft ``Eingabefehler`` mit Klartext."""
    gesaeubert = text_saeubern(frage or "")
    if not gesaeubert:
        raise Eingabefehler("Bitte geben Sie eine Frage ein.")
    if len(gesaeubert) > GRENZE_FRAGE:
        raise Eingabefehler(
            "Die Frage ist zu lang: %d Zeichen, erlaubt sind höchstens %d. "
            "Bitte stellen Sie die Frage kürzer und schreiben Sie die "
            "Einzelheiten in das Feld für die Systembeschreibung." % (len(gesaeubert), GRENZE_FRAGE)
        )
    return gesaeubert


def beschreibung_pruefen(beschreibung: str | None) -> str:
    """Prüft und säubert eine Systembeschreibung. Leer ist erlaubt."""
    gesaeubert = text_saeubern(beschreibung or "")
    if len(gesaeubert) > GRENZE_BESCHREIBUNG:
        raise Eingabefehler(
            "Die Beschreibung ist zu lang: %d Zeichen, erlaubt sind höchstens %d. "
            "Bitte kürzen Sie auf das, was für die Einstufung zählt: Zweck, "
            "Einsatzbereich, betroffene Personen, Ihre Rolle."
            % (len(gesaeubert), GRENZE_BESCHREIBUNG)
        )
    return gesaeubert


# ------------------------------------------------------------ Ratenbegrenzung


@dataclass
class Anfragezaehler:
    """Begrenzt Anfragen je Adresse — ein Eimer mit Zeitstempeln im Speicher.

    Das Verfahren ist ein gleitendes Fenster: je Adresse werden die Zeitpunkte
    der letzten Anfragen behalten, alles Ältere als das Fenster fällt heraus.
    Das ist genauer als ein Zähler, der zu jeder Minute auf Null springt — dort
    könnte man an der Minutengrenze die doppelte Menge durchschieben.

    Im Speicher und nicht in einer Datenbank, weil der Dienst für einen Rechner
    gedacht ist. Bei mehreren Abläufen hinter einem Verteiler zählt jeder für
    sich; dann gehört die Begrenzung in den Verteiler davor.
    """

    grenze: int = 30
    fenster_sekunden: float = 60.0
    #: Mehr Adressen als das hält der Zähler nicht vor. Ohne diese Grenze
    #: wächst der Speicher mit jeder neuen Adresse — das ist selbst ein Angriff.
    hoechstens_adressen: int = 10_000
    _eimer: dict[str, deque[float]] = field(default_factory=dict)
    _schloss: Lock = field(default_factory=Lock)

    def pruefen(self, adresse: str) -> tuple[bool, int]:
        """Darf diese Adresse? Gibt (erlaubt, Wartezeit in Sekunden) zurück."""
        jetzt = time.monotonic()
        with self._schloss:
            if len(self._eimer) > self.hoechstens_adressen:
                # Aufräumen: alle Eimer, in denen nichts Frisches mehr liegt.
                for schluessel in [
                    k
                    for k, v in self._eimer.items()
                    if not v or jetzt - v[-1] > self.fenster_sekunden
                ]:
                    del self._eimer[schluessel]
            eimer = self._eimer.setdefault(adresse, deque())
            while eimer and jetzt - eimer[0] > self.fenster_sekunden:
                eimer.popleft()
            if len(eimer) >= self.grenze:
                warten = self.fenster_sekunden - (jetzt - eimer[0])
                return False, max(1, int(warten) + 1)
            eimer.append(jetzt)
            return True, 0

    def meldung(self, warten: int) -> str:
        """Die Meldung, die der Nutzer sieht — in Alltagssprache."""
        return (
            "Zu viele Anfragen von dieser Adresse: erlaubt sind %d Anfragen "
            "je Minute. Bitte in %d Sekunden erneut versuchen." % (self.grenze, warten)
        )

    def zuruecksetzen(self) -> None:
        """Nur für Prüfläufe: alle Eimer leeren."""
        with self._schloss:
            self._eimer.clear()


def zaehler_aus_umgebung() -> Anfragezaehler:
    """Baut den Zähler aus den Umgebungsvariablen, mit der Vorgabe 30/Minute."""
    try:
        grenze = int(os.environ.get("HELFER_ANFRAGEN_JE_MINUTE", "30"))
    except ValueError:
        grenze = 30
    return Anfragezaehler(grenze=max(1, grenze))


# -------------------------------------------------------- Protokoll säubern

#: Muster, die nach Schlüssel aussehen. Lieber einmal zu viel ersetzt als
#: einmal einen echten Schlüssel im Protokoll: ein ersetzter Text kostet
#: Lesbarkeit, ein veröffentlichter Schlüssel kostet Geld.
#: Die Reihenfolge ist wichtig: zuerst die benannten Felder, damit der
#: Feldname erhalten bleibt, erst danach die Muster für freistehende
#: Schlüssel. Umgekehrt würde der Feldname auf einen bereits ersetzten Wert
#: treffen und die Zeile zweimal bearbeitet.
_SCHLUESSELMUSTER = (
    # Benanntes Feld: key=..., token: ..., passwort = ..., schluessel: "..."
    # Die Klammerzeichen ⟨⟩ sind ausgenommen, weil der Ersatztext sie benutzt.
    re.compile(
        r"(?i)\b(api[-_ ]?key|key|token|secret|geheimnis|passwor[dt]|"
        r"schl(?:ü|ue)ssel|credential|authorization)\b"
        r"\s*[:=]\s*[\"']?[^\s\"',;)⟨⟩]{6,}"
    ),
    # Anbieterschlüssel mit erkennbarem Vorspann (Anthropic, OpenAI, GitHub, Google)
    re.compile(
        r"\b(?:sk|pk|rk|ghp|gho|ghs|ghu|github_pat|xoxb|xoxp|AIza)"
        r"[-_A-Za-z0-9]{10,}",
        re.IGNORECASE,
    ),
    # "Bearer" gefolgt von einem Wort — das Wort ist der Schlüssel
    re.compile(r"\bBearer\s+[A-Za-z0-9._\-]{8,}", re.IGNORECASE),
    # Netzadresse mit Anmeldedaten darin
    re.compile(r"\b[a-z][a-z0-9+.\-]*://[^\s/@]+:[^\s/@]+@", re.IGNORECASE),
)

#: Ab dieser Länge gilt eine Zeichenkette ohne Leerzeichen als verdächtig:
#: natürlicher Text hat Lücken, ein Schlüssel oder ein eingebettetes Bild nicht.
_LANGE_KETTE = re.compile(r"[A-Za-z0-9+/=_\-]{48,}")

#: So lang darf eine Protokollzeile werden. Alles darüber wird gekappt — ein
#: Protokoll, in dem ein einziger Eintrag die Datei füllt, ist unbrauchbar.
PROTOKOLL_HOECHSTLAENGE = 2_000


def protokollsicher(text: object) -> str:
    """Macht einen Text protokollfähig: keine Schlüssel, keine Endlos-Zeilen.

    Wird auf jeden Wert angewandt, der in eine Protokollzeile geht — auch auf
    Fehlermeldungen von Fremdpaketen, denn genau die geben gern die ganze
    Anfrage samt Kopfzeilen zurück.
    """
    roh = text if isinstance(text, str) else str(text)
    roh = roh.replace("\r", " ").replace("\n", " ⏎ ")
    for muster in _SCHLUESSELMUSTER:
        roh = muster.sub(lambda t: _ersetzen(t.group(0)), roh)
    roh = _LANGE_KETTE.sub(
        lambda t: f"⟨lange Zeichenkette, {len(t.group(0)):d} Zeichen, entfernt⟩", roh
    )
    # Steuerzeichen würden die Protokollzeile verschieben oder überschreiben.
    roh = "".join(z for z in roh if unicodedata.category(z) not in ("Cc", "Cf") or z == " ")
    if len(roh) > PROTOKOLL_HOECHSTLAENGE:
        roh = roh[:PROTOKOLL_HOECHSTLAENGE] + " …⟨gekappt⟩"
    return roh


def _ersetzen(fund: str) -> str:
    """Behält den Feldnamen, wirft den Wert weg — damit die Zeile noch lesbar ist."""
    for trenner in ("=", ":"):
        if trenner in fund:
            name, _, _wert = fund.partition(trenner)
            if len(name) < 40:
                return f"{name}{trenner} ⟨Schlüssel entfernt⟩"
    return "⟨Schlüssel entfernt⟩"


class SchluesselFilter:
    """Ein Protokollfilter, der jede Zeile durch ``protokollsicher`` schickt.

    Als Filter und nicht als Formatierer, damit er auch greift, wenn ein
    Fremdpaket seine eigene Formatierung mitbringt.
    """

    def filter(self, eintrag: object) -> bool:  # Signatur von logging.Filter
        nachricht = getattr(eintrag, "msg", None)
        if isinstance(nachricht, str):
            eintrag.msg = protokollsicher(nachricht)  # type: ignore[attr-defined]
        argumente = getattr(eintrag, "args", None)
        if isinstance(argumente, tuple):
            eintrag.args = tuple(  # type: ignore[attr-defined]
                protokollsicher(a) if isinstance(a, str) else a for a in argumente
            )
        return True


# ----------------------------------------------------------- Umgebung prüfen


def umgebung_pruefen() -> list[str]:
    """Prüft beim Start, ob der Dienst unter gefährlichen Bedingungen läuft.

    Gibt eine Liste von Warnungen zurück, statt abzubrechen: wer bewusst als
    Verwalter startet, soll es tun können — aber es darf nicht unbemerkt
    bleiben, denn ein Fehler im Dienst hätte dann Zugriff auf das ganze System.
    """
    warnungen: list[str] = []

    kennung = getattr(os, "geteuid", None)
    if kennung is not None and kennung() == 0:
        warnungen.append(
            "Der Dienst läuft mit Verwalterrechten (root). Ein Fehler im Dienst "
            "wirkt dann auf das ganze System. Im Container sorgt der Nutzer "
            "helfer (Kennung 10001) dafür, dass das nicht passiert."
        )

    for name in ("DEBUG", "HELFER_DEBUG", "FASTAPI_DEBUG"):
        wert = os.environ.get(name, "")
        if wert and wert.lower() not in ("0", "false", "nein", "off", ""):
            warnungen.append(
                f"Die Umgebungsvariable {name} ist gesetzt ({wert!r}). Im Fehlersuchbetrieb "
                "können Innereien nach außen gelangen — für den Betrieb abschalten."
            )

    # Ein Schlüssel in der Umgebung ist in Ordnung; ein Schlüssel, der schon in
    # der Prozessliste steht, nicht. Darauf wird hingewiesen, nicht geprüft —
    # prüfen hieße, die Kommandozeile zu lesen und damit selbst zu protokollieren.
    if os.environ.get("ANTHROPIC_API_KEY") and os.environ.get("OPENAI_API_KEY"):
        warnungen.append(
            "Es liegen Zugangsschlüssel für zwei Anbieter in der Umgebung. "
            "Der Dienst nimmt den ersten erreichbaren — wer ein bestimmtes "
            "Modell will, gibt HELFER_MODELL ausdrücklich an."
        )

    return warnungen
