"""Der Bedeutungsweg der Einstufung — welche Stelle des Gesetzes trägt den Fall?

Das Problem, das dieses Modul löst
----------------------------------
Die Einstufung lief zuerst allein über Wortlisten: steht "Bewerbung" oder
"Lebenslauf" im Text, greift Anhang III Nummer 4 Buchstabe a. Auf der eigenen
Fallsammlung traf das 44 von 44 Fällen — auf zwanzig Beschreibungen, wie
Unternehmen sie wirklich einreichen, nur 14. Die sechs Fehlgriffe waren alle
derselbe: nichts erkannt, also "minimal". Eine Wortliste kann nur treffen, was
jemand vorher aufgeschrieben hat; Sprache kann mehr Formen als eine Liste.

Was nicht funktioniert hat
--------------------------
Der naheliegende Weg — die Beschreibung mit dem Gesetzestext vergleichen —
versagt messbar. Anhang III formuliert 23 seiner 25 Punkte mit derselben Formel
("KI-Systeme, die bestimmungsgemäß … verwendet werden sollen"). Wer Beschreibung
gegen Gesetzestext stellt, misst überwiegend diese gemeinsame Formel. Gemessen:
ein richtiger Treffer lag bei 0,0017, ein falscher bei 0,1009 — die Reihenfolge
stimmte, die Höhe nicht. Eine Schwelle ist darauf nicht zu setzen.

Zweitens zieht die Frage selbst den Wert herunter. "Wir sind ein Softwarehaus
und verkaufen eine Recruiting-Software. Die KI liest Lebensläufe und schlägt
dem Personaler die drei besten Kandidaten vor. Was müssen wir beachten?" —
zwei von drei Sätzen sagen über den Zweck nichts.

Was funktioniert
----------------
Zwei Änderungen, beide gemessen:

1. **Zweck gegen Zweck.** Neben jeder Fundstelle steht in
   ``daten/regeln/kivo_zweckkatalog.yaml`` derselbe Zweck in der Sprache, in der
   ein Unternehmen ihn beschreibt. Verglichen wird mit diesen Sätzen, nicht mit
   dem Gesetzestext.
2. **Satzweise.** Jeder Satz der Beschreibung wird einzeln verglichen, es gilt
   der beste Wert. Der Satz, der den Zweck nennt, trägt dann das Ergebnis, und
   die Rückfrage am Ende verwässert ihn nicht.

Damit liegen richtige Treffer bei 0,90 bis 0,999 und Nichttreffer unter 0,05 —
dazwischen ist Platz für eine Schwelle.

Was dieses Modul nicht tut
--------------------------
Es stuft nicht ein. Es sagt, WELCHE Stelle zu prüfen ist, nicht WAS gilt. Die
Einstufung kommt weiter aus dem Regelwerk: Rolle, Merkmale und Ausnahmen prüft
der Prüfer, und jede Fundstelle, die hier herauskommt, muss im Korpus auf
echten amtlichen Text zeigen. Das Modell findet, das Regelwerk entscheidet.

Kosten
------
Zwei Stufen, damit der Kreuzbewerter nicht über alle 83 Zwecksätze läuft: erst
wählt die Sinn-Nähe des Einbetters aus den Fundstellen eine Vorauswahl, dann
bewertet der Kreuzbewerter nur diese. Die Zwecksätze werden einmal eingebettet
und als Datei abgelegt. Fehlt eines der Modelle, liefert das Modul eine leere
Liste — die Wortlisten des Prüfers bleiben dann allein zuständig, und das steht
im Protokoll.
"""

from __future__ import annotations

import gzip
import json
import logging
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import yaml

protokoll = logging.getLogger(__name__)

#: Ab diesem Wert des Kreuzbewerters gilt eine Fundstelle als betroffen.
#: Gemessen an zwanzig Unternehmensbeschreibungen: richtige Treffer lagen bei
#: 0,75 bis 0,999, Nichttreffer unter 0,05. Die Schwelle liegt in dieser Lücke
#: und damit nicht am Rand einer der beiden Gruppen.
SCHWELLE = 0.50

#: Eine eigene, höhere Schwelle für die verbotenen Praktiken.
#:
#: Die Folgen der Klassen sind nicht gleich schwer. "Verboten" heißt: das
#: System darf so nicht betrieben werden, und wer sich darauf verlässt, stellt
#: ein Geschäft ein. Diese Aussage braucht mehr als eine knappe Mehrheit der
#: Ähnlichkeit. Gemessen: eine Lernplattform, die Aufsätze benotet, traf den
#: Satz "Wir erkennen die Gefühle von Schülern" mit 0,6297 - verboten wäre das
#: falsch; die App, die die Stimmung von Mitarbeitern misst, traf ihren Satz
#: mit 0,9974 - verboten ist das richtig. Dazwischen liegt viel Platz.
#:
#: In der anderen Richtung gilt das Gegenteil: ein übersehenes hohes Risiko
#: kostet den Nutzer die Vorbereitung auf Pflichten, die er erfüllen muss.
#: Darum bleibt es dort bei der niedrigeren Schwelle.
SCHWELLEN_JE_KLASSE = {"verboten": 0.85}

#: So viele Fundstellen gehen je SATZ in den Kreuzbewerter.
#:
#: Die Vorauswahl trifft (Satz, Zwecksatz)-Paare, nicht Fundstellen allein.
#: Vorher ging jeder Satz der Beschreibung gegen jede gewählte Zeile - bei drei
#: Sätzen und zwölf Fundstellen über hundert Paare, von denen die meisten
#: offensichtlich nicht zusammenpassen ("Wir sind ein Softwarehaus" gegen
#: "Wir steuern ein Stromnetz"). Der Kreuzbewerter kostet je Paar Rechenzeit,
#: also wird je Satz nur das geprüft, was für DIESEN Satz überhaupt in Frage
#: kommt. Der Einbetter taugt für diese Auswahl: gemessen stand bei 15 von 20
#: Beschreibungen die richtige Stelle schon bei ihm auf Platz eins. Entscheiden
#: kann er nicht - seine Werte lagen für falsche Stellen bis 0,745 und für
#: richtige bei 0,673 -, aber auswählen kann er.
VORAUSWAHL = 5

#: Ab diesem Wert wirkt ein Gegenzweck über seine eigene Regel hinaus.
#:
#: Ein Gegenzweck beschreibt einen Zweck, den die Verordnung NICHT erfasst: die
#: Sichtprüfung in der Fertigung, die Suche nach Vertragsfristen, das Protokoll
#: einer Besprechung. Trifft ein solcher Satz die Beschreibung deutlich besser
#: als der Zweck einer Regel, so ist das die bessere Lesart - und zwar für jede
#: Regel, nicht nur für die, bei der der Satz zufällig steht. Gemessen: ein
#: Besprechungsprotokoll aus einer Tonaufnahme traf den Gegenzweck mit 1,0000
#: und den Satz "Wir lesen aus Gesicht, Stimme oder Tonfall ab, wie jemand sich
#: fühlt" mit 0,6751 - und wurde als Biometrie nach Anhang III Nummer 1
#: ausgegeben, weil der Gegenzweck bei Nummer 4 stand.
#:
#: Unterhalb dieses Werts bleibt der Gegenzweck auf seine Regel beschränkt: ein
#: knapper Treffer ist keine andere Lesart, sondern nur ein knapper Treffer.
GEGEN_STARK = 0.90

#: Höchstens so viele Fundstellen je Regel dürfen die Vorauswahl belegen.
#:
#: Ohne diese Grenze füllt eine Regel mit vielen Fundstellen die Vorauswahl
#: allein: Anhang I nennt 17 Produktgattungen, deren Zwecksätze alle gleich
#: gebaut sind ("Wir bauen KI in ein Spielzeug ein", "… in ein Medizinprodukt
#: ein"). Die Sinn-Nähe greift dann genau das gemeinsame Satzgerüst - derselbe
#: Fehler, der den Vergleich mit dem Gesetzestext unbrauchbar machte, nur eine
#: Stufe früher. Gemessen fiel so Anhang III Nummer 4 Buchstabe b aus der
#: Vorauswahl, obwohl die Beschreibung von Schichtzuteilung sprach, und sieben
#: der zwölf Plätze gingen an Anhang I. Je Regel zählt ohnehin nur die beste
#: Fundstelle, denn die Regel ist dieselbe.
JE_REGEL = 2

#: Längstes Textstück, das der Kreuzbewerter ansieht - in Wortstücken.
#:
#: Der Kreuzbewerter rechnet mit der Länge im Quadrat. Seine Voreinstellung ist
#: 512 Wortstücke, gebraucht werden hier höchstens 80: verglichen werden ein
#: Satz der Beschreibung und ein Zwecksatz des Katalogs, beide kurz. Gemessen
#: fiel die Zeit je Frage damit von 10 bis 35 Sekunden auf unter 3.
LAENGE = 128

#: Höchstens so viele Fundstellen stehen am Ende da. Mehr ist keine Auskunft
#: mehr, sondern eine Liste.
HOECHSTENS = 4

#: Der Verkäufervorspann: "Wir verkaufen eine Software, die …", "Unser Produkt
#: ist ein Modul, das …". Der Zweck steht dann im Relativsatz, und sein Verb
#: steht in der dritten Person, während die Zwecksätze des Katalogs in der
#: ersten stehen. Gemessen kostet das den Treffer: dieselbe Beschreibung erhielt
#: 0,35 mit Vorspann und 0,75 ohne ihn, bei einer Schwelle von 0,50. Darum wird
#: aus einem solchen Satz ein zweiter abgeleitet, der nur den Zweck trägt.
_VERKAEUFERVORSPANN = re.compile(
    r"^(?:wir|unser\w*|die|das)\b[^,]{0,90},\s+(?:die|das|der|welche[rs]?)\s+(?P<zweck>.{15,})$",
    re.IGNORECASE | re.DOTALL,
)

#: Sätze, deren Subjekt das System selbst ist: "Sie berücksichtigt
#: Qualifikation …", "Die KI liest Lebensläufe …". Auch hier steht das Verb in
#: der dritten Person. Die Liste nennt nur Wörter, die das System bezeichnen —
#: "Eine Kollegin liest alles gegen" darf nicht zu "Wir lesen alles gegen"
#: werden, denn dort handelt ein Mensch, und genau dieser Unterschied entlastet
#: nach Artikel 6 Absatz 3.
_SYSTEMSATZ = re.compile(
    r"^(?:sie|es|die\s+ki|das\s+ki[\s-]?system|das\s+system|das\s+tool|das\s+modul|"
    r"das\s+modell|das\s+programm|die\s+software|die\s+anwendung|die\s+app|"
    r"die\s+ki[\s-]?kamera|der\s+bot|der\s+chatbot|der\s+assistent|"
    r"unser(?:e|es)?\s+(?:system|tool|modul|modell|programm|software|anwendung|app|ki))"
    r"\s+(?P<zweck>.{15,})$",
    re.IGNORECASE | re.DOTALL,
)

#: Rückfragen und Höflichkeiten. Sie nennen keinen Zweck, verwässern aber jeden
#: Vergleich, in dem sie mitlaufen - darum fallen sie vor der Messung weg.
_RUECKFRAGE = re.compile(
    r"was (muessen|müssen|gilt|kommt|ist)|fallen wir|f(ae|ä)llt das|d(ue|ü)rfen wir|"
    r"brauchen wir|betrifft uns|ist das (zul(ae|ä)ssig|erlaubt|ein problem)|gibt es da|"
    r"z(ae|ä)hlt das|etwas melden|auf uns zu|welche pflichten|wie sieht|"
    r"k(oe|ö)nnen wir das|haben wir|sind wir",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Zwecktreffer:
    """Eine Fundstelle, die den beschriebenen Zweck trägt."""

    fundstelle: str
    klasse: str
    regel: str
    wert: float
    zweck: str
    satz: str

    @property
    def sicherheit(self) -> str:
        """Wie fest der Treffer sitzt — das steht später in der Auskunft."""
        if self.wert >= 0.90:
            return "sicher"
        if self.wert >= 0.70:
            return "wahrscheinlich"
        return "zu prüfen"


def saetze(beschreibung: str) -> list[str]:
    """Zerlegt eine Beschreibung in die Sätze, die einen Zweck nennen können.

    Rückfragen fallen weg. Bleibt danach nichts übrig — jemand hat nur gefragt,
    ohne etwas zu beschreiben —, gelten wieder alle Sätze: lieber ungenau
    messen als nichts.
    """
    text = re.sub(r"\s+", " ", beschreibung).strip()
    roh = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
    if not roh:
        return []
    behalten = [s for s in roh if not (s.endswith("?") and _RUECKFRAGE.search(s))]
    behalten = behalten or roh

    # Zu jedem Satz mit Verkäufervorspann kommt der abgeleitete Zwecksatz
    # HINZU, er ersetzt den Satz nicht. Gewertet wird später der beste Wert,
    # also kann die Ableitung nur helfen und nie etwas verdecken. Dass der
    # abgeleitete Satz grammatisch hinkt ("Wir liest Lebensläufe"), ist
    # hingenommen: gemessen zählt die Person des Satzes, nicht seine Beugung -
    # mit "Wir" davor 0,86, mit richtig gebeugtem Vorspann 0,02. Eine
    # Beugung wäre ohne Wörterbuch nicht verlässlich, und ein Wörterbuch
    # brächte eine Abhängigkeit für einen Gewinn, den die Messung nicht zeigt.
    ergebnis = list(behalten)
    for satz in behalten:
        for muster in (_VERKAEUFERVORSPANN, _SYSTEMSATZ):
            treffer = muster.match(satz)
            if treffer is None:
                continue
            abgeleitet = "Wir " + treffer.group("zweck").strip()
            if abgeleitet not in ergebnis:
                ergebnis.append(abgeleitet)
            break
    return ergebnis


def _wortlaut_steht(zeile: Zweckzeile, beschreibung: str) -> bool:
    """Steht ein Wort da, das der Tatbestand ausdrücklich verlangt?

    Manche Stellen verlangen ein Merkmal, das kein Bedeutungsvergleich ersetzen
    kann. Artikel 5 Absatz 1 Buchstabe d verbietet die Vorhersage von Straftaten
    nur, wenn sie AUSSCHLIESSLICH auf dem Profiling beruht. Eine Rückfallprognose
    für die Polizei, die das nicht sagt, ist nicht verboten, sondern fällt unter
    Anhang III Nummer 6 Buchstabe d - hohes Risiko mit Pflichten. Der Unterschied
    ist für den Nutzer der zwischen "weitermachen mit Auflagen" und "einstellen",
    und er hängt an einem Wort. Dann entscheidet das Wort, nicht die Ähnlichkeit.
    """
    if not zeile.verlangt:
        return True
    flach = beschreibung.lower()
    return any(wort.lower() in flach for wort in zeile.verlangt)


def katalogpfad() -> Path:
    return Path(__file__).resolve().parents[3] / "daten" / "regeln" / "kivo_zweckkatalog.yaml"


@dataclass(frozen=True)
class Zweckzeile:
    """Ein Zwecksatz des Katalogs mit der Fundstelle, zu der er gehört."""

    text: str
    fundstelle: str
    klasse: str
    regel: str
    gegenzweck: bool
    verlangt: tuple[str, ...] = ()


def katalog_lesen(pfad: Path | None = None) -> list[Zweckzeile]:
    """Liest den Zweckkatalog und prüft ihn auf Vollständigkeit."""
    pfad = pfad or katalogpfad()
    rohdaten: dict[str, Any] = yaml.safe_load(pfad.read_text(encoding="utf-8"))
    zeilen: list[Zweckzeile] = []
    for eintrag in rohdaten.get("eintraege", []):
        for feld in ("fundstelle", "klasse", "regel"):
            if not eintrag.get(feld):
                raise ValueError(f"{pfad.name}: Eintrag ohne {feld}: {eintrag}")
        if not eintrag.get("zwecke"):
            raise ValueError(f"{pfad.name}: {eintrag['fundstelle']} nennt keinen Zweck")
        for gegenzweck, schluessel in ((False, "zwecke"), (True, "ausser")):
            for text in eintrag.get(schluessel) or []:
                zeilen.append(
                    Zweckzeile(
                        text=text,
                        fundstelle=eintrag["fundstelle"],
                        klasse=eintrag["klasse"],
                        regel=eintrag["regel"],
                        gegenzweck=gegenzweck,
                        verlangt=tuple(eintrag.get("verlangt") or ()),
                    )
                )
    return zeilen


@dataclass
class Zweckfinder:
    """Findet zu einer Beschreibung die Stellen des Gesetzes, die sie tragen."""

    zeilen: list[Zweckzeile] = field(default_factory=list)
    schwelle: float = SCHWELLE
    _vektoren: np.ndarray | None = None
    _einbetter: Any = None
    _bewerter: Any = None
    _bewerter_versucht: bool = False

    @classmethod
    def aus_katalog(cls, pfad: Path | None = None, schwelle: float = SCHWELLE) -> Zweckfinder:
        return cls(zeilen=katalog_lesen(pfad), schwelle=schwelle)

    # -- Vorauswahl über die Sinn-Nähe ------------------------------------
    def _vektoren_holen(self, ablage: Path | None = None) -> np.ndarray | None:
        """Die eingebetteten Zwecksätze — einmal gerechnet, dann aus der Datei.

        Ändert sich der Katalog, passt die abgelegte Datei nicht mehr. Darum
        steht die Anzahl der Sätze mit in der Datei und wird beim Laden geprüft.
        """
        if self._vektoren is not None:
            return self._vektoren
        ablage = ablage or (katalogpfad().parent / "_zwecke_vektoren.json.gz")
        if ablage.exists():
            try:
                with gzip.open(ablage, "rt", encoding="utf-8") as datei:
                    gespeichert = json.load(datei)
                if gespeichert.get("anzahl") == len(self.zeilen):
                    self._vektoren = np.asarray(gespeichert["vektoren"], dtype=np.float32)
                    return self._vektoren
                protokoll.info("Abgelegte Zweckvektoren passen nicht mehr — neu gerechnet")
            except Exception as fehler:
                protokoll.warning("Zweckvektoren nicht lesbar (%s) — neu gerechnet", fehler)
        einbetter = self._einbetter_holen()
        if einbetter is None:
            return None
        self._vektoren = np.asarray(
            einbetter.bestand([z.text for z in self.zeilen]).dicht, dtype=np.float32
        )
        try:
            with gzip.open(ablage, "wt", encoding="utf-8") as datei:
                json.dump(
                    {"anzahl": len(self.zeilen), "vektoren": self._vektoren.tolist()},
                    datei,
                )
        except Exception as fehler:
            protokoll.info("Zweckvektoren nicht ablegbar: %s", fehler)
        return self._vektoren

    def _einbetter_holen(self) -> Any:
        if self._einbetter is None:
            try:
                from helfer.suche.einbettung import waehlen

                self._einbetter = waehlen()
            except Exception as fehler:
                protokoll.warning("Kein Einbetter für den Zweckweg: %s", fehler)
                return None
        return self._einbetter

    def _bewerter_holen(self) -> Any:
        if not self._bewerter_versucht:
            self._bewerter_versucht = True
            try:
                from FlagEmbedding import FlagReranker

                self._bewerter = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
            except Exception as fehler:
                protokoll.info(
                    "Kreuzbewerter nicht verfügbar (%s) — der Zweckweg bleibt aus, "
                    "die Einstufung läuft allein über das Regelwerk",
                    fehler,
                )
        return self._bewerter

    # -- der eigentliche Weg ----------------------------------------------
    def finden(self, beschreibung: str) -> list[Zwecktreffer]:
        """Die Fundstellen, deren Zweck die Beschreibung trifft."""
        teile = saetze(beschreibung)
        if not teile or not self.zeilen:
            return []
        bewerter = self._bewerter_holen()
        if bewerter is None:
            return []

        auswahl = self._vorauswahl(teile)
        paare = [[teile[s], self.zeilen[i].text] for s, i in auswahl]
        protokoll.debug("Zweckweg: %d Sätze, %d Paare", len(teile), len(paare))
        if not paare:
            return []
        try:
            werte = bewerter.compute_score(
                paare, normalize=True, max_length=LAENGE, batch_size=len(paare)
            )
        except Exception as fehler:
            protokoll.warning("Zweckbewertung fehlgeschlagen: %s", fehler)
            return []
        if not isinstance(werte, list):
            werte = [werte]

        # Je Fundstelle der beste Zwecksatz, und - getrennt davon - je REGEL der
        # beste Gegenzweck. Trifft der Gegenzweck besser, beschreibt die Stelle
        # einen anderen Fall: Anhang III Nummer 5 Buchstabe b nimmt die
        # Betrugserkennung ausdrücklich aus, Artikel 5 Absatz 1 Buchstabe f die
        # Müdigkeitserkennung aus Sicherheitsgründen.
        #
        # Der Gegenzweck wirkt auf die ganze Regel, nicht nur auf die
        # Fundstelle, bei der er steht. Angestoßen wird die Regel, also muss
        # die Entlastung dort greifen. Gemessen: die Sichtprüfung in der
        # Fertigung ("prüft eine KI-Kamera, ob die Schweißnähte in Ordnung
        # sind") traf den Gegenzweck bei Anhang I Nummer 1 mit 0,9988 - und
        # wurde dann über Nummer 11, "KI in ein Medizinprodukt", mit 0,56
        # doch als Anhang I eingeordnet. Dieselbe Regel, dieselbe Entlastung.
        best: dict[str, tuple[float, Zweckzeile, str]] = {}
        gegen: dict[str, float] = {}
        gegen_stark = 0.0
        for (s, i), rohwert in zip(auswahl, werte, strict=False):
            zeile = self.zeilen[i]
            wert = float(rohwert)
            if zeile.gegenzweck:
                if wert > gegen.get(zeile.regel, -1.0):
                    gegen[zeile.regel] = wert
                if wert >= GEGEN_STARK:
                    gegen_stark = max(gegen_stark, wert)
            elif wert > best.get(zeile.fundstelle, (-1.0,))[0]:
                best[zeile.fundstelle] = (wert, zeile, teile[s])

        treffer = [
            Zwecktreffer(
                fundstelle=fundstelle,
                klasse=zeile.klasse,
                regel=zeile.regel,
                wert=round(wert, 4),
                zweck=zeile.text,
                satz=satz,
            )
            for fundstelle, (wert, zeile, satz) in best.items()
            if wert >= SCHWELLEN_JE_KLASSE.get(zeile.klasse, self.schwelle)
            and wert > max(gegen.get(zeile.regel, -1.0), gegen_stark)
            and _wortlaut_steht(zeile, beschreibung)
        ]
        return sorted(treffer, key=lambda t: -t.wert)[:HOECHSTENS]

    def _vorauswahl(self, teile: list[str]) -> list[tuple[int, int]]:
        """Welche Paare aus Satz und Zwecksatz der Kreuzbewerter ansehen muss.

        Ohne Einbetter gibt es keine Vorauswahl — dann läuft der Kreuzbewerter
        über alle Paare. Das ist langsamer, aber nicht falsch.
        """
        alle = [(s, i) for s in range(len(teile)) for i in range(len(self.zeilen))]
        vektoren = self._vektoren_holen()
        einbetter = self._einbetter_holen()
        if vektoren is None or einbetter is None:
            return alle
        try:
            fragen = np.asarray(einbetter.frage(teile).dicht, dtype=np.float32)
        except Exception as fehler:
            protokoll.warning("Vorauswahl fehlgeschlagen: %s", fehler)
            return alle
        naehe = vektoren @ fragen.T  # Zeilen x Sätze

        paare: list[tuple[int, int]] = []
        for s in range(len(teile)):
            spalte = naehe[:, s]
            reihe = sorted(range(len(self.zeilen)), key=lambda i: -float(spalte[i]))
            # Gewählt werden Fundstellen, nicht einzelne Zeilen: eine Fundstelle
            # kommt mit allen ihren Zeilen in den Kreuzbewerter, sonst fehlt
            # ausgerechnet der Gegenzweck, der sie wieder herausnimmt.
            fundstellen: list[str] = []
            je_regel: dict[str, int] = {}
            for i in reihe:
                zeile = self.zeilen[i]
                if zeile.fundstelle in fundstellen:
                    continue
                if je_regel.get(zeile.regel, 0) >= JE_REGEL:
                    continue
                fundstellen.append(zeile.fundstelle)
                je_regel[zeile.regel] = je_regel.get(zeile.regel, 0) + 1
                if len(fundstellen) >= VORAUSWAHL:
                    break
            gewaehlt = set(fundstellen)
            paare += [(s, i) for i, z in enumerate(self.zeilen) if z.fundstelle in gewaehlt]
        return paare


@lru_cache(maxsize=1)
def zweckfinder() -> Zweckfinder:
    """Der Zweckweg, einmal je Prozess.

    Die beiden Modelle wiegen zusammen rund drei Gigabyte und brauchen zum
    Laden Sekunden. Jede neue Instanz lud sie erneut: eine Prüfreihe mit
    dreiunddreißig Einstufungen lud sie dreiunddreißig Mal und lief in den
    Arbeitsspeicher, und ein Webdienst täte dasselbe je Anfrage. Der
    Zweckkatalog und die Modelle ändern sich während eines Laufs nicht, also
    gehören sie einmal geladen.
    """
    return Zweckfinder.aus_katalog()
