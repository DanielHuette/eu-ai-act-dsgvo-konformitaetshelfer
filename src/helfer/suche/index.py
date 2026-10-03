"""Der Suchbestand: vier Wege zu einem Treffer, dann eine Neubewertung.

Warum vier Wege und nicht einer? Weil Rechtsfragen auf zwei Arten gestellt
werden, und jede Art braucht einen anderen Weg:

1. **Wer nach Sinn fragt** — "Dürfen wir Bewerbungen vorsortieren?" — braucht
   die Vektorsuche: sie findet "Einstellung oder Auswahl natürlicher Personen",
   obwohl kein Wort übereinstimmt.
2. **Wer nach Wortlaut fragt** — "Artikel 6 Absatz 3", "CE-Kennzeichnung" —
   braucht die Stichwortsuche. Eine Vektorsuche verwischt Artikelnummern, weil
   Zahlen für sie fast gleich aussehen.
3. **Wer eine Fundstelle nennt**, bekommt sie direkt: eine Kennungssuche, die
   "Art. 9 Abs. 2" in ``KI-VO/art-9/abs-2`` übersetzt. Ohne diesen Weg
   antwortet das System auf eine genaue Frage mit ungefährer Nähe.
4. **Die Wortgewichte des Modells** (nur bei bge-m3) liegen zwischen Sinn und
   Wortlaut: sie gewichten Wörter im Zusammenhang.

Die vier Trefferlisten werden mit *Reciprocal Rank Fusion* zusammengeführt.
Dieses Verfahren addiert nicht Punktzahlen — die sind zwischen den Wegen nicht
vergleichbar — sondern Rangplätze: ``1 / (k + Rang)``. Ein Treffer, den mehrere
Wege vorne haben, steigt; ein Treffer, den nur einer kennt, bleibt dabei.

Zum Schluss bewertet ein **Kreuzbewerter** (Cross-Encoder) die besten 30
Treffer neu. Er liest Frage und Fundstelle zusammen, statt beide getrennt in
Zahlen zu verwandeln, und ist dadurch deutlich genauer — aber zu langsam für
den ganzen Bestand. Darum erst Vorauswahl, dann Neubewertung.
"""

from __future__ import annotations

import gzip
import json
import logging
import math
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import numpy as np

from helfer.modell import Belegstelle, Einheit, Rechtsakt
from helfer.suche.einbettung import Einbetter, waehlen

protokoll = logging.getLogger(__name__)

#: Die Konstante der Rangfusion. 60 ist der in der Literatur gebräuchliche Wert;
#: er dämpft die Spitze, damit ein einzelner Weg die Liste nicht allein bestimmt.
RRF_K = 60

#: So viele Treffer liefert jeder Weg in die Fusion.
JE_WEG = 50

#: So viele Treffer bekommt der Kreuzbewerter zu sehen.
NEUBEWERTEN = 30

#: Deutsche Füllwörter. Sie stehen in jedem Rechtstext und tragen nichts zur
#: Unterscheidung bei - in der Stichwortsuche würden sie alles gleich machen.
FUELLWOERTER = frozenset(
    [
        "aber",
        "alle",
        "allem",
        "allen",
        "aller",
        "alles",
        "als",
        "also",
        "am",
        "an",
        "ander",
        "andere",
        "anderem",
        "anderen",
        "anderer",
        "anderes",
        "auch",
        "auf",
        "aus",
        "bei",
        "beim",
        "bin",
        "bis",
        "bist",
        "da",
        "damit",
        "dann",
        "der",
        "den",
        "des",
        "dem",
        "die",
        "das",
        "dass",
        "dein",
        "deine",
        "dem",
        "den",
        "der",
        "des",
        "dessen",
        "deshalb",
        "dies",
        "diese",
        "diesem",
        "diesen",
        "dieser",
        "dieses",
        "doch",
        "dort",
        "du",
        "durch",
        "ein",
        "eine",
        "einem",
        "einen",
        "einer",
        "eines",
        "er",
        "es",
        "euer",
        "euch",
        "für",
        "gegen",
        "gewesen",
        "hab",
        "habe",
        "haben",
        "hat",
        "hatte",
        "hatten",
        "hier",
        "hin",
        "hinter",
        "ich",
        "ihr",
        "ihre",
        "ihrem",
        "ihren",
        "ihrer",
        "ihres",
        "im",
        "in",
        "indem",
        "ins",
        "ist",
        "ja",
        "jede",
        "jedem",
        "jeden",
        "jeder",
        "jedes",
        "jener",
        "jene",
        "kann",
        "kein",
        "keine",
        "keinem",
        "keinen",
        "keiner",
        "man",
        "mehr",
        "mein",
        "meine",
        "mit",
        "nach",
        "nicht",
        "nichts",
        "noch",
        "nun",
        "nur",
        "ob",
        "oder",
        "ohne",
        "saemtliche",
        "sein",
        "seine",
        "seinem",
        "seinen",
        "seiner",
        "sich",
        "sie",
        "sind",
        "so",
        "solche",
        "solchem",
        "solchen",
        "soll",
        "sollen",
        "sondern",
        "sonst",
        "ueber",
        "um",
        "und",
        "uns",
        "unser",
        "unsere",
        "unter",
        "vom",
        "von",
        "vor",
        "waehrend",
        "war",
        "waren",
        "was",
        "weil",
        "welche",
        "welchem",
        "welchen",
        "welcher",
        "welches",
        "wenn",
        "wer",
        "werde",
        "werden",
        "wie",
        "wieder",
        "will",
        "wir",
        "wird",
        "wirst",
        "wo",
        "wollen",
        "wurde",
        "wurden",
        "zu",
        "zum",
        "zur",
        "zwar",
        "zwischen",
    ]
)


# --------------------------------------------------------------- Hilfsfunktionen


def _flach(text: str) -> str:
    """Umlaute auflösen und kleinschreiben - für die Stichwortsuche."""
    text = text.lower()
    for alt, neu in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")):
        text = text.replace(alt, neu)
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()


_WORT = re.compile(r"[a-z0-9]+")


def zerlegen_in_woerter(text: str) -> list[str]:
    """Zerlegt Text in Suchwörter.

    Zusammengesetzte Wörter sind im deutschen Rechtsdeutsch die Regel
    ("Hochrisiko-KI-System"). Sie werden sowohl ganz als auch in ihren Teilen
    aufgenommen, damit eine Frage nach "Risiko" auch dort trifft.
    """
    flach = _flach(text)
    woerter: list[str] = []
    for stueck in _WORT.findall(flach):
        if len(stueck) < 2 or stueck in FUELLWOERTER:
            continue
        woerter.append(stueck)
    for stueck in re.findall(r"[a-z]+(?:-[a-z]+)+", flach):
        for teil in stueck.split("-"):
            if len(teil) > 2 and teil not in FUELLWOERTER:
                woerter.append(teil)
    return woerter


#: Erkennt Fundstellen in einer Frage: "Art. 6 Abs. 3", "Artikel 9", "§ 26 BDSG",
#: "Anhang III Nr. 4", "Erwägungsgrund 60".
_FUNDSTELLE = re.compile(
    r"(?:(?P<art>Art(?:ikel)?\.?)\s*(?P<artnr>\d{1,3})"
    r"(?:\s*(?:Abs(?:atz)?\.?)\s*(?P<absnr>\d{1,2}))?"
    r"(?:\s*(?:Buchst(?:abe)?\.?)\s*(?P<buchst>[a-z]))?"
    r"|(?P<par>§)\s*(?P<parnr>\d{1,3}[a-z]?)"
    r"|(?P<anh>Anhang)\s*(?P<anhnr>[IVXLC]+)"
    r"(?:\s*(?:Nr\.?|Nummer)\s*(?P<anhpunkt>\d{1,2}))?"
    r"|(?P<erw>Erw(?:ägungsgrund|aegungsgrund|G)?\.?)\s*(?P<erwnr>\d{1,3}))",
    re.IGNORECASE,
)


def fundstellen_aus_frage(frage: str) -> list[str]:
    """Übersetzt genannte Fundstellen in Korpus-Kennungen.

    Welcher Rechtsakt gemeint ist, verrät meist die Frage selbst. Fehlt der
    Hinweis, werden beide Kennungen geliefert und die Suche entscheidet.
    """
    flach = frage.lower()
    if "bdsg" in flach or "bundesdatenschutz" in flach:
        akte = [Rechtsakt.BDSG]
    elif any(w in flach for w in ("dsgvo", "datenschutz-grundverordnung", "gdpr")):
        akte = [Rechtsakt.DSGVO]
    elif any(
        w in flach
        for w in (
            "ki-vo",
            "ki-verordnung",
            "ai act",
            "ai-act",
            "kuenstliche intelligenz",
            "künstliche intelligenz",
        )
    ):
        akte = [Rechtsakt.KI_VO]
    else:
        akte = [Rechtsakt.KI_VO, Rechtsakt.DSGVO]

    kennungen: list[str] = []
    for treffer in _FUNDSTELLE.finditer(frage):
        teile = treffer.groupdict()
        if teile.get("artnr"):
            for akt in akte:
                stamm = "{}/art-{}".format(akt.value, teile["artnr"])
                if teile.get("absnr"):
                    stamm += "/abs-{}".format(teile["absnr"])
                    if teile.get("buchst"):
                        stamm += "-{}".format(teile["buchst"].lower())
                kennungen.append(stamm)
        elif teile.get("parnr"):
            kennungen.append("BDSG/par-{}".format(teile["parnr"]))
        elif teile.get("anhnr"):
            stamm = "KI-VO/anh-{}".format(teile["anhnr"].upper())
            if teile.get("anhpunkt"):
                stamm += "/nr-{}".format(teile["anhpunkt"])
            kennungen.append(stamm)
        elif teile.get("erwnr"):
            for akt in akte:
                kennungen.append("{}/erw-{}".format(akt.value, teile["erwnr"]))
    return kennungen


# -------------------------------------------------------------------- BM25


@dataclass
class Stichwortbestand:
    """Stichwortsuche nach BM25 — ohne Fremdpaket, damit nichts nachzuladen ist.

    BM25 gewichtet ein Wort danach, wie selten es im Bestand ist und wie oft es
    in einer Fundstelle vorkommt, und rechnet die Länge der Fundstelle heraus.
    Ohne diese Längenkorrektur gewinnen immer die langen Artikel.
    """

    k1: float = 1.5
    b: float = 0.75
    _haeufigkeit: list[dict[str, int]] = field(default_factory=list)
    _laengen: list[int] = field(default_factory=list)
    _wortstellen: dict[str, list[int]] = field(default_factory=dict)
    _durchschnitt: float = 0.0
    _anzahl: int = 0

    def bauen(self, texte: list[str]) -> None:
        self._haeufigkeit = []
        self._laengen = []
        stellen: dict[str, list[int]] = defaultdict(list)
        for nummer, text in enumerate(texte):
            woerter = zerlegen_in_woerter(text)
            zaehler: dict[str, int] = {}
            for wort in woerter:
                zaehler[wort] = zaehler.get(wort, 0) + 1
            self._haeufigkeit.append(zaehler)
            self._laengen.append(len(woerter))
            for wort in zaehler:
                stellen[wort].append(nummer)
        self._wortstellen = dict(stellen)
        self._anzahl = len(texte)
        self._durchschnitt = (sum(self._laengen) / self._anzahl) if self._anzahl else 0.0

    def suchen(self, frage: str, anzahl: int = JE_WEG) -> list[tuple[int, float]]:
        woerter = zerlegen_in_woerter(frage)
        if not woerter or not self._anzahl:
            return []
        punkte: dict[int, float] = defaultdict(float)
        for wort in set(woerter):
            stellen = self._wortstellen.get(wort)
            if not stellen:
                continue
            # Je seltener das Wort, desto schwerer wiegt ein Treffer.
            gewicht = math.log(1 + (self._anzahl - len(stellen) + 0.5) / (len(stellen) + 0.5))
            for nummer in stellen:
                haeufig = self._haeufigkeit[nummer][wort]
                laenge = self._laengen[nummer] or 1
                punkte[nummer] += gewicht * (
                    haeufig
                    * (self.k1 + 1)
                    / (haeufig + self.k1 * (1 - self.b + self.b * laenge / self._durchschnitt))
                )
        return sorted(punkte.items(), key=lambda x: -x[1])[:anzahl]


# ------------------------------------------------------------------ Bestand


@dataclass
class Treffer:
    """Ein Treffer samt der Wege, auf denen er gefunden wurde."""

    einheit: Einheit
    punktzahl: float
    wege: set[str] = field(default_factory=set)
    rangplaetze: dict[str, int] = field(default_factory=dict)


class Suchbestand:
    """Alle Suchwege über einem Korpus.

    Der Bestand wird einmal gebaut und als Datei abgelegt, damit das Programm
    beim Start nicht rechnen muss. Die Datei enthält die Vektoren, den
    Stichwortbestand und den Modellnamen — ohne den Modellnamen ließen sich
    später Fragen mit einem anderen Modell einbetten, und die Treffer wären
    stiller Unsinn.
    """

    def __init__(self, einheiten: list[Einheit], einbetter: Einbetter | None = None):
        self.einheiten = einheiten
        self.einbetter = einbetter or waehlen()
        self.vektoren: np.ndarray | None = None
        self.wortgewichte: list[dict[str, float]] | None = None
        self.stichworte = Stichwortbestand()
        self._nach_kennung = {e.kennung: nummer for nummer, e in enumerate(einheiten)}
        self.gebaut: date | None = None

    # ----------------------------------------------------------------- bauen

    def _suchtext(self, einheit: Einheit) -> str:
        """Was eingebettet wird: Fundstelle, Titel und Text zusammen.

        Die Fundstelle gehört in den Text, weil Fragen sie oft nennen. Stünde
        sie nur in den Metadaten, fände die Vektorsuche "Artikel 9" nicht.
        """
        kopf = [einheit.fundstelle]
        if einheit.titel:
            kopf.append(einheit.titel)
        if einheit.kapitel:
            kopf.append(einheit.kapitel)
        return "{}\n{}".format(" — ".join(kopf), einheit.text)

    def bauen(
        self, stapel: int = 32, zwischenlager: Path | None = None, je_teilstueck: int = 2
    ) -> None:
        """Rechnet die Vektoren — bei Bedarf mit Zwischenstand auf Platte.

        Das Einbetten von rund 2700 Rechtseinheiten dauert auf einem
        Hauptprozessor eine Stunde oder mehr. Bricht der Lauf dabei ab, war die
        ganze Rechenzeit verloren: so ist es zweimal passiert. Darum legt der
        Lauf mit ``zwischenlager`` alle ``je_teilstueck`` Stapel ein Teilstück
        ab und überspringt beim nächsten Anlauf, was schon gerechnet ist. Der
        Bestand kommt damit auch über mehrere Anläufe zustande.

        ``je_teilstueck`` ist mit Absicht klein: zwei Stapel sind 64
        Einheiten und etwa zwei Minuten Rechenzeit. Größere Teilstücke sparen
        ein paar Schreibvorgänge, kosten bei einem Abbruch aber genau so viel
        Rechenzeit, wie seit dem letzten Teilstück vergangen ist — ein
        schlechter Tausch.
        """
        texte = [self._suchtext(e) for e in self.einheiten]
        protokoll.info("Bestand bauen: %d Einheiten mit %s", len(texte), self.einbetter.name)
        if zwischenlager is not None:
            zwischenlager.mkdir(parents=True, exist_ok=True)

        # Gerechnet wird in Blöcken. Ein Block ist das, was ein Teilstück
        # enthält, und er wird über seinen Anfang benannt: so weiß der nächste
        # Anlauf an der Datei, welche Einheiten er überspringen darf. Blockweise
        # statt stapelweise, weil ein Teilstück mehrere Stapel abdeckt — wer
        # stapelweise überspringt, rechnet Teile doppelt.
        block = max(1, stapel * je_teilstueck)
        teile: list[np.ndarray] = []
        gewichte: list[dict[str, float]] = []
        gerechnet = geladen = 0

        # Ein Teilstück sind zwei Dateien: die Zahlen als .npy, die Wortgewichte
        # als gepacktes JSON. Zusammen in einer .npz ginge nur mit
        # allow_pickle - und was für den ausgelieferten Bestand gilt, gilt hier
        # auch: eine Datei, die beim Laden Code ausführen kann, wird nicht
        # gelesen, auch wenn sie gerade aus dem eigenen Lauf stammt.
        lager = zwischenlager  # feste Bindung: innen ist der Typ dann eindeutig

        def teilstueck(anfang: int) -> tuple[Path, Path] | None:
            if lager is None:
                return None
            stamm = lager / ("teil-%06d" % anfang)
            return stamm.with_suffix(".vektoren.npy"), stamm.with_suffix(".wort.json.gz")

        for blockanfang in range(0, len(texte), block):
            paar = teilstueck(blockanfang)
            abschnitt = texte[blockanfang : blockanfang + block]

            if paar is not None and paar[0].exists() and paar[1].exists():
                zahlen, worte = paar
                dicht = np.load(zahlen)
                if len(dicht) == len(abschnitt):
                    teile.append(dicht)
                    with gzip.open(worte, "rt", encoding="utf-8") as datei:
                        gewichte.extend(json.load(datei))
                    geladen += len(dicht)
                    continue
                # Ein Teilstück falscher Länge stammt aus einem anderen Korpus
                # oder einer anderen Blockgröße. Es wird verworfen, nicht
                # verwendet - sonst stimmte die Zuordnung Vektor zu Einheit nicht.
                protokoll.warning(
                    "Teilstück %s passt nicht (%d statt %d) — wird neu gerechnet",
                    zahlen.name,
                    len(dicht),
                    len(abschnitt),
                )
                zahlen.unlink()
                worte.unlink(missing_ok=True)

            stuecke: list[np.ndarray] = []
            wort: list[dict[str, float]] = []
            for anfang in range(0, len(abschnitt), stapel):
                befund = self.einbetter.bestand(abschnitt[anfang : anfang + stapel])
                stuecke.append(befund.dicht)
                if befund.wortgewichte:
                    wort.extend(befund.wortgewichte)
            dicht = np.vstack(stuecke)
            teile.append(dicht)
            gewichte.extend(wort)
            gerechnet += len(dicht)
            if paar is not None:
                zahlen, worte = paar
                np.save(zahlen, dicht)
                with gzip.open(worte, "wt", encoding="utf-8") as datei:
                    json.dump(wort, datei, separators=(",", ":"))
                protokoll.info(
                    "  %s abgelegt — %d von %d Einheiten fertig",
                    zahlen.name,
                    geladen + gerechnet,
                    len(texte),
                )

        if geladen:
            protokoll.info(
                "%d Einheiten aus dem Zwischenlager übernommen, %d neu gerechnet",
                geladen,
                gerechnet,
            )

        self.vektoren = np.vstack(teile) if teile else np.zeros((0, 1), dtype=np.float32)
        if len(self.vektoren) != len(texte):
            raise RuntimeError(
                "Vektoren passen nicht zum Korpus: %d statt %d. Das Zwischenlager "
                "stammt aus einem anderen Lauf — mit --von-vorn neu rechnen."
                % (len(self.vektoren), len(texte))
            )
        self.wortgewichte = gewichte or None
        self.stichworte.bauen(texte)
        self.gebaut = date.today()

    # ----------------------------------------------------------------- Wege

    def _weg_vektor(self, frage: str, anzahl: int) -> list[tuple[int, float]]:
        if self.vektoren is None or not len(self.vektoren):
            return []
        reihe = self.einbetter.eine_frage(frage)
        naehe = self.vektoren @ reihe
        beste = np.argsort(-naehe)[:anzahl]
        return [(int(i), float(naehe[i])) for i in beste]

    def _weg_stichwort(self, frage: str, anzahl: int) -> list[tuple[int, float]]:
        return self.stichworte.suchen(frage, anzahl)

    def _weg_wortgewichte(self, frage: str, anzahl: int) -> list[tuple[int, float]]:
        """Nur mit bge-m3: die Wortgewichte des Modells vergleichen."""
        if not self.wortgewichte:
            return []
        befund = self.einbetter.frage([frage])
        if not befund.wortgewichte:
            return []
        fragegewichte = befund.wortgewichte[0]
        punkte: list[tuple[int, float]] = []
        for nummer, bestand in enumerate(self.wortgewichte):
            summe = sum(
                gewicht * bestand.get(marke, 0.0) for marke, gewicht in fragegewichte.items()
            )
            if summe > 0:
                punkte.append((nummer, float(summe)))
        return sorted(punkte, key=lambda x: -x[1])[:anzahl]

    def _weg_fundstelle(self, frage: str) -> list[tuple[int, float]]:
        """Genannte Fundstellen direkt holen - mit dem höchsten Rang."""
        gefunden: list[tuple[int, float]] = []
        for kennung in fundstellen_aus_frage(frage):
            nummer = self._nach_kennung.get(kennung)
            if nummer is not None:
                gefunden.append((nummer, 1.0))
                continue
            # Nennt die Frage einen Absatz, den es nicht gibt, hilft der Artikel.
            stamm = kennung.rsplit("/", 1)[0]
            nummer = self._nach_kennung.get(stamm)
            if nummer is not None:
                gefunden.append((nummer, 0.9))
        return gefunden

    # ---------------------------------------------------------------- suchen

    def suchen(
        self,
        frage: str,
        anzahl: int = 8,
        nur_rechtsakte: tuple[Rechtsakt, ...] | None = None,
        mit_neubewertung: bool = True,
    ) -> list[Treffer]:
        """Sucht über alle Wege, führt zusammen und bewertet neu."""
        wege: dict[str, list[tuple[int, float]]] = {
            "fundstelle": self._weg_fundstelle(frage),
            "vektor": self._weg_vektor(frage, JE_WEG),
            "stichwort": self._weg_stichwort(frage, JE_WEG),
            "wortgewichte": self._weg_wortgewichte(frage, JE_WEG),
        }

        # Rangfusion: Rangplätze addieren, nicht Punktzahlen.
        fusion: dict[int, float] = defaultdict(float)
        herkunft: dict[int, set[str]] = defaultdict(set)
        raenge: dict[int, dict[str, int]] = defaultdict(dict)
        for name, liste in wege.items():
            # Der Fundstellenweg ist kein Schätzwert, sondern eine Tatsache -
            # er bekommt deshalb mehr Gewicht als die drei Ähnlichkeitswege.
            gewicht = 3.0 if name == "fundstelle" else 1.0
            for rang, (nummer, _) in enumerate(liste, 1):
                fusion[nummer] += gewicht / (RRF_K + rang)
                herkunft[nummer].add(name)
                raenge[nummer][name] = rang

        kandidaten = sorted(fusion.items(), key=lambda x: -x[1])
        if nur_rechtsakte:
            erlaubt = set(nur_rechtsakte)
            kandidaten = [(n, p) for n, p in kandidaten if self.einheiten[n].rechtsakt in erlaubt]

        treffer = [
            Treffer(einheit=self.einheiten[n], punktzahl=p, wege=herkunft[n], rangplaetze=raenge[n])
            for n, p in kandidaten[: max(anzahl, NEUBEWERTEN)]
        ]

        if mit_neubewertung and len(treffer) > 1:
            treffer = neu_bewerten(frage, treffer)
        return treffer[:anzahl]

    # ------------------------------------------------------------- ablegen

    def ablegen(self, pfad: Path) -> None:
        """Legt den Bestand als Datei ab - Vektoren getrennt, weil binär."""
        if self.vektoren is None:
            # Ein Bestand ohne Vektoren ist kein Bestand. Würde er abgelegt,
            # fiele das erst beim Laden auf - und dann als Längenfehler, der
            # nichts über die Ursache sagt.
            raise RuntimeError("Der Bestand ist nicht gebaut. Erst bauen(), dann ablegen().")
        pfad.parent.mkdir(parents=True, exist_ok=True)
        np.save(pfad.with_suffix(".vektoren.npy"), self.vektoren)
        beipack = {
            "modell": self.einbetter.name,
            "dimensionen": self.einbetter.dimensionen,
            "gebaut": (self.gebaut or date.today()).isoformat(),
            "kennungen": [e.kennung for e in self.einheiten],
            "wortgewichte": self.wortgewichte,
            "stichworte": {
                "haeufigkeit": self.stichworte._haeufigkeit,
                "laengen": self.stichworte._laengen,
                "wortstellen": self.stichworte._wortstellen,
                "durchschnitt": self.stichworte._durchschnitt,
                "anzahl": self.stichworte._anzahl,
            },
        }
        # Kein pickle. Der Bestand wird mit dem Repository ausgeliefert, also
        # bekommt ihn der Nutzer von uns — aber er bekommt ihn über eine
        # Kopie, einen Abzweig, einen Spiegel. Wer eine solche Kopie ändert,
        # würde mit pickle beim Laden eigenen Code im Rechner des Nutzers
        # ausführen, ohne dass irgendeine Prüfung greift: pickle.load ruft auf,
        # was in der Datei steht. Darum JSON, gzip-gepackt (die Wortstellen
        # sind groß): JSON kennt nur Zahlen, Zeichenketten, Listen und
        # Abbildungen. Eine veränderte Datei kann dann falsche Treffer
        # verursachen — aber keinen fremden Code starten.
        with gzip.open(pfad.with_suffix(".bestand.json.gz"), "wt", encoding="utf-8") as datei:
            json.dump(beipack, datei, ensure_ascii=False, separators=(",", ":"))
        pfad.with_suffix(".bestand.json").write_text(
            json.dumps(
                {
                    "modell": self.einbetter.name,
                    "dimensionen": self.einbetter.dimensionen,
                    "einheiten": len(self.einheiten),
                    "gebaut": (self.gebaut or date.today()).isoformat(),
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )

    @classmethod
    def laden(
        cls, pfad: Path, einheiten: list[Einheit], einbetter: Einbetter | None = None
    ) -> Suchbestand:
        """Liest einen abgelegten Bestand und prüft, dass das Modell passt."""
        gepackt = pfad.with_suffix(".bestand.json.gz")
        alt = pfad.with_suffix(".bestand.pkl")
        if gepackt.exists():
            with gzip.open(gepackt, "rt", encoding="utf-8") as datei:
                beipack = json.load(datei)
        elif alt.exists():
            # Bestände aus früheren Fassungen lagen als pickle vor. Sie werden
            # nicht mehr gelesen: wer eine solche Datei lädt, vertraut ihrem
            # Inhalt mit der Ausführung von Code. Einmal neu bauen kostet eine
            # Stunde Rechenzeit, der Fehlerfall kostet den Rechner.
            raise RuntimeError(
                f"Der abgelegte Bestand {alt.name} ist im alten pickle-Format. "
                "Es wird nicht mehr gelesen, weil eine veränderte Datei beim "
                "Laden fremden Code ausführen könnte. Bestand neu bauen: "
                "python scripts/bestand_bauen.py"
            )
        else:
            raise FileNotFoundError(f"Kein abgelegter Bestand bei {pfad}")
        gewolltes_modell = beipack["modell"]
        werkzeug = einbetter or waehlen(gewolltes_modell)
        if werkzeug.name != gewolltes_modell:
            raise RuntimeError(
                f"Der Bestand wurde mit {gewolltes_modell} gebaut, geladen "
                f"ist {werkzeug.name}. Einbettungen "
                "verschiedener Modelle sind nicht vergleichbar — Bestand neu bauen."
            )

        bestand = cls(einheiten, werkzeug)
        bestand.vektoren = np.load(pfad.with_suffix(".vektoren.npy"))
        bestand.wortgewichte = beipack.get("wortgewichte")
        gespeichert = beipack["stichworte"]
        bestand.stichworte._haeufigkeit = gespeichert["haeufigkeit"]
        bestand.stichworte._laengen = gespeichert["laengen"]
        # Die Wortstellen sind {Wort: [Nummern der Einheiten]}. Schlüssel sind
        # Wörter, Werte Zahlenlisten — beides übersteht JSON unverändert.
        bestand.stichworte._wortstellen = gespeichert["wortstellen"]
        bestand.stichworte._durchschnitt = gespeichert["durchschnitt"]
        bestand.stichworte._anzahl = gespeichert["anzahl"]
        bestand.gebaut = date.fromisoformat(beipack["gebaut"])

        if len(bestand.vektoren) != len(einheiten):
            raise RuntimeError(
                "Bestand und Korpus passen nicht zusammen: %d Vektoren, %d Einheiten. "
                "Bestand neu bauen." % (len(bestand.vektoren), len(einheiten))
            )
        return bestand


# ------------------------------------------------------------- Neubewertung

_kreuzbewerter = None
_kreuzbewerter_versucht = False


def neu_bewerten(frage: str, treffer: list[Treffer]) -> list[Treffer]:
    """Bewertet die Vorauswahl mit einem Kreuzbewerter neu.

    Der Kreuzbewerter liest Frage und Fundstelle gemeinsam und beantwortet
    direkt: passt das zusammen? Das ist genauer als zwei getrennte Zahlenreihen
    zu vergleichen, aber zu langsam für tausend Einheiten — darum nur für die
    Vorauswahl. Fehlt das Modell, bleibt die Reihenfolge der Rangfusion.
    """
    global _kreuzbewerter, _kreuzbewerter_versucht
    if not _kreuzbewerter_versucht:
        _kreuzbewerter_versucht = True
        try:
            from FlagEmbedding import FlagReranker

            _kreuzbewerter = FlagReranker("BAAI/bge-reranker-v2-m3", use_fp16=True)
        except Exception as fehler:
            protokoll.info(
                "Kreuzbewerter nicht verfügbar (%s) — es gilt die Reihenfolge der Rangfusion",
                fehler,
            )
            _kreuzbewerter = None
    if _kreuzbewerter is None:
        return treffer

    paare = [[frage, f"{t.einheit.fundstelle}\n{t.einheit.text[:1800]}"] for t in treffer]
    try:
        punkte = _kreuzbewerter.compute_score(paare, normalize=True)
    except Exception as fehler:
        protokoll.warning("Neubewertung fehlgeschlagen: %s", fehler)
        return treffer
    if not isinstance(punkte, list):
        punkte = [punkte]
    for stelle, punkt in zip(treffer, punkte, strict=False):
        stelle.punktzahl = float(punkt)
        stelle.wege.add("neubewertet")
    return sorted(treffer, key=lambda t: -t.punktzahl)


def als_belegstellen(treffer: list[Treffer], auszug: int = 700) -> tuple[Belegstelle, ...]:
    """Macht aus Treffern das, was in einer Antwort erscheint."""
    return tuple(
        Belegstelle(
            kennung=t.einheit.kennung,
            fundstelle=t.einheit.fundstelle,
            rechtsakt=t.einheit.rechtsakt,
            titel=t.einheit.titel,
            auszug=t.einheit.text[:auszug],
            punktzahl=round(t.punktzahl, 4),
            wege=tuple(sorted(t.wege)),
        )
        for t in treffer
    )
