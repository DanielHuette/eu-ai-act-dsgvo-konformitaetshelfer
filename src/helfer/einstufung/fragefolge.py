"""Der Durchlauf, der entscheidet — die Fragen eines Juristen, als Programm.

WARUM DIESES MODUL DEN KERN BILDET
Der Helfer hat die Antworten auf Fragen vorher geraten, statt sie zu stellen.
Gemessen kam er damit auf 98 von 100 — aber genaues Raten ist schlechter als
Fragen. Ein Jurist fragt fünf bis acht Dinge ab und hat danach Gewissheit, und
der Nutzer sieht, woran die Einstufung hängt. Genau das tut dieses Modul.

Weil die Antworten vom Nutzer kommen, ist das Ergebnis nicht wahrscheinlich,
sondern richtig — soweit seine Angaben stimmen. Der Helfer behauptet nichts
über die Anlage, die er nicht kennt; er fragt danach und rechnet damit.

WOHER DIE FRAGEN STAMMEN
Aus dem Entwurf der Leitlinien der Europäischen Kommission vom 19. Mai 2026 zur
Einstufung von Hochrisiko-KI-Systemen: 148 Seiten amtliche Auslegung zu Anhang
III, 13 Seiten zu Anhang I, 6 Seiten allgemeine Grundsätze. Jede Frage, jeder
Ausschluss und jedes Beispiel in daten/regeln/fragefolge/ trägt die
Absatznummer der Fundstelle. Nichts darin ist von mir ausgedacht.

Das ist der Unterschied zur vorigen Fassung: dort stammten die Zwecksätze aus
meiner eigenen Formulierung. Jede Lücke darin war eine Lücke, die niemand sehen
konnte. Hier steht an jeder Zeile, wo sie herkommt.

WAS DER FREITEXT NOCH TUT
Er füllt die Antworten vor und wird als Vorschlag angezeigt, den der Nutzer
bestätigt oder berichtigt. Er entscheidet nichts mehr.

STAND DER QUELLE
Die Leitlinien sind ein Entwurf. Die öffentliche Anhörung lief bis zum
23. Juni 2026; eine endgültige Fassung lag bei Abschluss dieser Arbeit nicht
vor. Das sagt der Helfer in jeder Auskunft mit, die sich darauf stützt.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from helfer import orte

protokoll = logging.getLogger(__name__)

#: Was eine Antwort auslösen kann.
ERFASST = "erfasst"
NICHT_ERFASST = "nicht_erfasst"
WEITER = "weiter"
ENDE = "ende"

#: Erfüllt bis auf eine Bedingung, die der Nutzer nicht wissen kann.
#:
#: Anhang III Nummer 2 verlangt nach Absatz (190) der Leitlinien, dass der
#: Betreiber förmlich als kritische Einrichtung benannt ist — und Absatz (191)
#: stellt fest, dass der Anbieter das nicht erfahren muss. Ein Nein auf eine
#: solche Frage wäre eine falsche Auskunft. Darum dieser dritte Befund.
BEDINGT = "bedingt"

#: Die dritte Antwort neben Ja und Nein.
#:
#: Eine Fragefolge, die nur Ja und Nein zulässt, zwingt zu falschen Antworten.
#: Zu Anhang III Nummer 4 Buchstabe a gehört die Frage, ob eine Stellenanzeige
#: aktiv eine konkrete offene Stelle anzeigt. Für ein Werkzeug, das Lebensläufe
#: sichtet, gibt es darauf kein Ja und kein Nein — es schaltet keine Anzeigen.
#: Gemessen fiel ein solcher Fall durch das Nein aus der Einstufung heraus,
#: obwohl er nach dem amtlichen Text klar erfasst ist.
#:
#: Ein Jurist fragt an dieser Stelle nicht weiter. Darum gibt es diese dritte
#: Antwort: sie lässt die Frage stehen, ohne zu entscheiden. Ein Ausschluss
#: greift nur auf eine ausdrückliche Antwort, nie auf ein Offenlassen.
TRIFFT_NICHT_ZU = "trifft_nicht_zu"


def ordner() -> Path:
    return orte.regeln()


@dataclass(frozen=True)
class Frage:
    """Eine Frage, die ein Laie mit Ja oder Nein beantworten kann."""

    kennung: str
    text: str
    beleg: str
    stufe: str
    fundstelle: str = ""
    titel: str = ""
    bei_ja: str = WEITER
    bei_nein: str = WEITER
    wirkung: str = ""


@dataclass(frozen=True)
class Punkt:
    """Eine Stelle des Gesetzes mit ihrer Fragefolge und ihren Beispielen."""

    fundstelle: str
    bereich: str
    titel: str
    hauptfrage: Frage
    folgefragen: tuple[Frage, ...]
    erfasst: tuple[dict[str, str], ...]
    nicht_erfasst: tuple[dict[str, str], ...]
    beispiele: tuple[dict[str, str], ...]
    ist_bereichstor: bool = False


@dataclass(frozen=True)
class Befund:
    """Das Ergebnis eines Durchlaufs."""

    klasse: str
    getroffene_punkte: tuple[Punkt, ...]
    filter_greift: bool
    filter_grund: str
    belege: tuple[str, ...]
    offene_punkte: tuple[str, ...]
    endtext: str = ""

    @property
    def fundstellen(self) -> tuple[str, ...]:
        return tuple(p.fundstelle for p in self.getroffene_punkte)


#: Fragen, die den Nutzer nach seinen eigenen vorherigen Antworten fragen
#: ("Haben Sie alle sechs vorstehenden Fragen mit Nein beantwortet?"). Die
#: Antwort darauf weiss der Durchlauf selbst. Sie zu stellen hiesse, dem Nutzer
#: das Mitzählen aufzuladen und ihm eine Fehlerquelle zu geben, die der Rechner
#: nicht hat.
_RUECKFRAGE_AN_SICH_SELBST = ("haben sie alle",)


def _ist_selbstrueckfrage(frage: dict[str, Any]) -> bool:
    text = str(frage.get("frage") or "").strip().lower()
    return any(text.startswith(m) for m in _RUECKFRAGE_AN_SICH_SELBST)


def _geordnet(folgefragen: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Erst der Tatbestand, dann die Ausnahme — und die Ausnahme immer ganz.

    Der Punkt trägt, wenn eine Tatbestandsfrage mit Ja beantwortet ist UND
    danach keine Ausnahme greift. Der frühere Weg brach bei der ersten
    entscheidenden Antwort ab und übersprang damit die Ausnahmen: wer "Geht es
    um Kredite?" mit Ja beantwortete, war erfasst, bevor "Betrifft es nur
    Wertpapierkredite?" ihn herausnehmen konnte. Beides nachgemessen an den
    amtlichen Beispielen der Leitlinien.
    """

    def rang(f: dict[str, Any]) -> int:
        # 0 = Tatbestandsfrage (ein Ja trägt den Punkt), 1 = Ausnahmefrage.
        return 1 if NICHT_ERFASST in (f.get("bei_ja"), f.get("bei_nein")) else 0

    return sorted((f for f in folgefragen if not _ist_selbstrueckfrage(f)), key=rang)


def _folge(frage: Frage, antwort: Any) -> str:
    """Was eine Antwort auf diese Frage auslöst.

    Eine Antwort "trifft nicht zu" löst nichts aus. Sonst gilt der Zweig, der
    zur Antwort gehört — und zwar auf BEIDEN Seiten. Dass ein Treffer auch am
    Nein hängen kann, war der teuerste Fehler dieses Durchlaufs: Anhang III
    Nummer 1 Buchstabe a trägt über das Nein zu "Bleibt das Material aus der
    Tatortarbeit in sich geschlossen?". Wer nur die Ja-Seite liest, kann diesen
    Punkt überhaupt nicht treffen — gemessen fielen so beide amtlichen
    Gesichtserkennungsbeispiele durch.
    """
    if antwort is None or antwort == TRIFFT_NICHT_ZU:
        return WEITER
    return frage.bei_ja if antwort else frage.bei_nein


def _werten(fragen: tuple[Frage, ...], antworten: dict[str, Any]) -> str:
    """Der Befund aus einer Fragenkette — eine Logik für Wertung und Weg.

    Es wird NICHT bei der ersten entscheidenden Antwort abgebrochen. Genau das
    hatte Fragefolge und Auswertung auseinanderlaufen lassen: der Weg hörte nach
    dem ersten Ja auf zu fragen, die Auswertung wartete weiter auf Antworten,
    die nie kamen, und der Punkt blieb für immer offen. Ein Punkt, der nie
    schliesst, ist für den Nutzer dasselbe wie ein Punkt, der nicht trifft —
    nur dass er es nicht erfährt.

    Reihenfolge der Wirkung: eine ausdrücklich bejahte Ausnahme schlägt den
    Tatbestand. So steht es im amtlichen Text, und so wiegt es auch für den
    Nutzer: wer unter eine Ausnahme fällt, soll das erfahren.
    """
    schliesst_aus = False
    traegt = False
    offen = False
    for f in fragen:
        antwort = antworten.get(f.kennung)
        if antwort is None:
            offen = True
            continue
        folge = _folge(f, antwort)
        if folge == NICHT_ERFASST:
            schliesst_aus = True
        elif folge == ERFASST:
            traegt = True
    if schliesst_aus:
        return NICHT_ERFASST
    if traegt:
        return ERFASST
    return WEITER if offen else NICHT_ERFASST


def _frage(
    roh: dict[str, Any], kennung: str, stufe: str, fundstelle: str = "", titel: str = ""
) -> Frage:
    return Frage(
        kennung=kennung,
        text=" ".join(str(roh.get("frage") or roh.get("hauptfrage") or "").split()),
        beleg=str(roh.get("beleg") or ""),
        stufe=stufe,
        fundstelle=fundstelle,
        titel=titel,
        bei_ja=str(roh.get("bei_ja") or WEITER),
        bei_nein=str(roh.get("bei_nein") or WEITER),
        wirkung=" ".join(str(roh.get("wirkung") or "").split()),
    )


@dataclass
class Durchlauf:
    """Stellt die nächste Frage und zieht am Ende den Schluss."""

    aufbau: dict[str, Any] = field(default_factory=dict)
    vorfragen: tuple[Frage, ...] = ()
    hinweise: tuple[Frage, ...] = ()
    punkte: tuple[Punkt, ...] = ()
    filterfragen: tuple[Frage, ...] = ()
    profilingfrage: Frage | None = None
    anhang_i_tor: Frage | None = None
    anhang_i_gattungen: tuple[Frage, ...] = ()
    anhang_i_bedingungen: tuple[dict[str, Any], ...] = ()
    anhang_i_fragen: dict[str, Frage] = field(default_factory=dict)
    bereichsfragen: tuple[Frage, ...] = ()
    quellen: tuple[str, ...] = ()

    # ------------------------------------------------------------- Laden
    @classmethod
    def laden(cls, wo: Path | None = None) -> Durchlauf:
        wo = wo or ordner()
        aufbau = yaml.safe_load((wo / "fragefolge-aufbau.yaml").read_text(encoding="utf-8"))
        teile = {}
        for datei in sorted((wo / "fragefolge").glob("*.yaml")):
            teile[datei.stem] = yaml.safe_load(datei.read_text(encoding="utf-8"))

        vf = teile["vorfragen-und-filter"]
        nach_kennung = {f["kennung"]: f for f in vf.get("vorfragen", [])}
        tore: list[Frage] = []
        hinweise: list[Frage] = []
        for eintrag in aufbau.get("vorfragen", []):
            roh = nach_kennung.get(eintrag["kennung"])
            if roh is None:
                protokoll.warning("Vorfrage %s fehlt in den Daten", eintrag["kennung"])
                continue
            f = _frage(roh, eintrag["kennung"], "vorfrage")
            (tore if eintrag.get("art") == "tor" else hinweise).append(f)

        tore_je_bereich = aufbau.get("tore_je_bereich") or {}
        reihenfolge = [b["fundstelle"] for b in aufbau.get("bereiche", [])]
        titel_je_bereich = {b["fundstelle"]: b["titel"] for b in aufbau.get("bereiche", [])}

        punkte: list[Punkt] = []
        for name, inhalt in teile.items():
            for lauf, roh in enumerate(inhalt.get("punkte") or []):
                fs = str(roh.get("fundstelle") or "")
                bereich = next((b for b in reihenfolge if fs.startswith(b)), "")
                if not bereich:
                    protokoll.warning("Punkt %s gehört zu keinem Bereich", fs)
                    continue
                punkte.append(
                    Punkt(
                        fundstelle=fs,
                        bereich=bereich,
                        titel=titel_je_bereich.get(bereich, ""),
                        # Die Kennung trägt Datei UND Laufnummer, nicht nur die
                        # Fundstelle. Anhang III Nummer 2 hat vier Punkte unter
                        # derselben Fundstelle — Bereich, Schutzaufgabe, benannte
                        # Einrichtung, Kernenergie. Mit der Fundstelle allein
                        # fielen ihre Kennungen zusammen, und eine Antwort
                        # beantwortete vier verschiedene Fragen auf einmal.
                        hauptfrage=_frage(
                            roh, f"haupt:{name}:{lauf}", "punkt", fs, inhalt.get("titel", "")
                        ),
                        folgefragen=tuple(
                            _frage(
                                f, f"folge:{name}:{lauf}:{i}", "punkt", fs, inhalt.get("titel", "")
                            )
                            for i, f in enumerate(_geordnet(roh.get("folgefragen") or []))
                        ),
                        erfasst=tuple(roh.get("erfasst") or []),
                        nicht_erfasst=tuple(roh.get("nicht_erfasst") or []),
                        beispiele=tuple(roh.get("beispiele") or []),
                        ist_bereichstor=tore_je_bereich.get(bereich) == fs,
                    )
                )
        # In der Reihenfolge der Bereiche, Tore ihres Bereichs zuerst.
        punkte.sort(
            key=lambda p: (
                reihenfolge.index(p.bereich) if p.bereich in reihenfolge else 99,
                0 if p.ist_bereichstor else 1,
                p.fundstelle,
            )
        )

        filt = vf.get("filter") or {}
        filterfragen = tuple(
            _frage(b, f"filter:{b.get('kennung')}", "filter") for b in filt.get("bedingungen") or []
        )
        prof = filt.get("gegenausnahme_profiling") or {}
        profilingfrage = _frage(prof, "filter:profiling", "filter") if prof else None

        # --- Anhang I: eigener Weg, drei Bedingungen zusammen ---
        ai = teile.get("anhang-i-produkte") or {}
        aufbau_ai = aufbau.get("anhang_i") or {}
        nicht_fragen = set(aufbau_ai.get("nicht_fragen") or [])
        ai_fragen = {
            f["kennung"]: _frage(f, f"anhang-i:{f['kennung']}", "anhang_i", "KI-VO/anh-I")
            for f in ai.get("fragen") or []
            if f.get("kennung") not in nicht_fragen
        }
        ai_tor_kennung = aufbau_ai.get("tor") or ""
        ai_tor = ai_fragen.pop(ai_tor_kennung, None)
        ai_gattungen = tuple(
            _frage(
                g,
                f"anhang-i-gattung:{g.get('kennung')}",
                "anhang_i",
                "KI-VO/anh-I",
                str(g.get("alltagsname") or ""),
            )
            for g in ai.get("produktgattungen") or []
            if g.get("frage")
        )

        # Acht Sätze, die nur sortieren: in welchem Bereich arbeitet der Nutzer?
        # Ohne sie standen 31 Rechtsfragen auf einem Blatt.
        bereichsfragen = tuple(
            Frage(
                kennung="bereich:" + b["fundstelle"],
                text=" ".join(str(b.get("frage") or "").split()),
                beleg="",
                stufe="bereich",
                fundstelle=b["fundstelle"],
                titel=str(b.get("titel") or ""),
            )
            for b in aufbau.get("bereiche", [])
            if b.get("frage")
        )

        quellen = tuple(sorted({str(i.get("quelle")) for i in teile.values() if i.get("quelle")}))
        return cls(
            aufbau=aufbau,
            vorfragen=tuple(tore),
            hinweise=tuple(hinweise),
            punkte=tuple(punkte),
            filterfragen=filterfragen,
            profilingfrage=profilingfrage,
            anhang_i_tor=ai_tor,
            anhang_i_gattungen=ai_gattungen,
            anhang_i_bedingungen=tuple(aufbau_ai.get("bedingungen") or []),
            anhang_i_fragen=ai_fragen,
            bereichsfragen=bereichsfragen,
            quellen=quellen,
        )

    # --------------------------------------------------------- Der Weg
    def _vorfrage_eintrag(self, kennung: str) -> dict[str, Any]:
        eintraege: list[dict[str, Any]] = self.aufbau.get("vorfragen", [])
        for e in eintraege:
            if e.get("kennung") == kennung:
                return e
        return {}

    def _punkt_gesperrt(self, punkt: Punkt, antworten: dict[str, Any]) -> bool:
        """Hat eine Vorfrage diesen Punkt bereits ausgeschlossen?"""
        for f in self.vorfragen:
            eintrag = self._vorfrage_eintrag(f.kennung)
            betroffen = eintrag.get("wirkt_auf") or []
            if punkt.fundstelle not in betroffen:
                continue
            antwort = antworten.get(f.kennung)
            if antwort is False and not eintrag.get("nur_als_zusatz"):
                return True
        return False

    def _bereich_abgewaehlt(self, punkt: Punkt, antworten: dict[str, Any]) -> bool:
        """Hat der Nutzer diesen Bereich schon im ersten Schritt verneint?"""
        return antworten.get("bereich:" + punkt.bereich) is False

    def _bereich_gesperrt(self, punkt: Punkt, antworten: dict[str, Any]) -> bool:
        """Hat das Tor des Bereichs diesen Punkt ausgeschlossen?

        Sagt der Nutzer, sein System habe mit Beschäftigung nichts zu tun, sind
        die Buchstaben darunter nicht offen, sondern erledigt. Sie als offen zu
        führen hiesse, dem Nutzer Fragen nachzutragen, die er beantwortet hat.
        """
        tor = (self.aufbau.get("tore_je_bereich") or {}).get(punkt.bereich)
        if not tor or tor == punkt.fundstelle:
            return False
        torpunkt = next((p for p in self.punkte if p.fundstelle == tor), None)
        if torpunkt is None:
            return False
        return antworten.get(torpunkt.hauptfrage.kennung) is False

    def punktbefund(self, punkt: Punkt, antworten: dict[str, Any]) -> str:
        """Wie der Punkt nach den bisherigen Antworten steht."""
        if (
            self._punkt_gesperrt(punkt, antworten)
            or self._bereich_gesperrt(punkt, antworten)
            or self._bereich_abgewaehlt(punkt, antworten)
        ):
            return NICHT_ERFASST
        # Gehört der Punkt zu einem Verbund, trägt er nicht allein. Dann
        # entscheidet der Bereich als Ganzes, und die Wertung des einzelnen
        # Punkts würde den Bereich zu früh schliessen oder zu früh öffnen.
        if self._verbund(punkt.bereich) is not None:
            return NICHT_ERFASST
        haupt = antworten.get(punkt.hauptfrage.kennung)
        if haupt is None:
            return WEITER
        if haupt is False:
            return NICHT_ERFASST
        # Ein Bereichstor öffnet seinen Bereich, es trägt den Fall nicht selbst.
        # Die Tore der Nummern 6 und 7 fragen breit nach dem Gebiet
        # ("Verarbeitet Ihr System Gesicht, Fingerabdruck oder Gangbild?") und
        # kennen die Ausnahmen der Buchstaben darunter nicht. Gemessen stufte
        # das eine Grenzkamera, die nur Alter und Geschlecht ableitet, als
        # hochriskant ein, obwohl Nummer 1 Buchstabe b genau das ausnimmt.
        if punkt.ist_bereichstor:
            return NICHT_ERFASST
        return _werten(punkt.folgefragen, antworten)

    def _gruppe_entfaellt(self, gruppe: dict[str, Any], antworten: dict[str, Any]) -> bool:
        """Ist eine Bedingungsgruppe des Anhangs I gegenstandslos geworden?

        Artikel 6 Absatz 1 Buchstabe a verlangt: Sicherheitsbauteil eines
        Produkts ODER selbst ein solches Produkt. Wer das Produkt selbst
        liefert, muss nicht auch noch Sicherheitsbauteil sein.
        """
        for k in gruppe.get("entfaellt_wenn") or []:
            frage = self.anhang_i_fragen.get(k)
            if frage is not None and antworten.get(frage.kennung) is True:
                return True
        return False

    def anhang_i_befund(self, antworten: dict[str, Any]) -> str:
        """Steht das System nach Artikel 6 Absatz 1 fest?

        Drei Bedingungen müssen zusammenkommen. Jede Gruppe gilt als erfüllt,
        wenn eine ihrer Fragen mit Ja beantwortet ist; ein Ausschluss in der
        Gruppe hebt sie wieder auf. Ist eine Gruppe verneint, ist der Weg zu
        Ende — dann hilft es nicht, dass die anderen zutreffen.
        """
        if self.anhang_i_tor is None:
            return NICHT_ERFASST
        tor = antworten.get(self.anhang_i_tor.kennung)
        if tor is None:
            return WEITER
        if tor is False:
            return NICHT_ERFASST
        if not any(antworten.get(g.kennung) for g in self.anhang_i_gattungen):
            if any(g.kennung not in antworten for g in self.anhang_i_gattungen):
                return WEITER
            return NICHT_ERFASST
        for gruppe in self.anhang_i_bedingungen:
            if self._gruppe_entfaellt(gruppe, antworten):
                continue
            kennungen = [
                self.anhang_i_fragen[k].kennung
                for k in gruppe.get("eine_genuegt") or []
                if k in self.anhang_i_fragen
            ]
            if any(k not in antworten for k in kennungen):
                return WEITER
            if not any(antworten.get(k) for k in kennungen):
                return NICHT_ERFASST
            for k in gruppe.get("ausschluss") or []:
                frage = self.anhang_i_fragen.get(k)
                if frage is None:
                    continue
                if frage.kennung not in antworten:
                    return WEITER
                if antworten[frage.kennung]:
                    return NICHT_ERFASST
        return ERFASST

    def _naechste_anhang_i(self, antworten: dict[str, Any]) -> Frage | None:
        if self.anhang_i_tor is None:
            return None
        if self.anhang_i_tor.kennung not in antworten:
            return self.anhang_i_tor
        if antworten[self.anhang_i_tor.kennung] is False:
            return None
        for g in self.anhang_i_gattungen:
            if g.kennung not in antworten:
                return g
        if not any(antworten.get(g.kennung) for g in self.anhang_i_gattungen):
            return None
        for gruppe in self.anhang_i_bedingungen:
            if self._gruppe_entfaellt(gruppe, antworten):
                continue
            kennungen = [k for k in gruppe.get("eine_genuegt") or [] if k in self.anhang_i_fragen]
            # Alle Fragen der Gruppe, nicht nur bis zum ersten Ja: die
            # Auswertung verlangt sie alle, und ein Weg, der früher aufhört,
            # lässt den Befund für immer auf "offen" stehen. Gemessen konnte
            # Anhang I dadurch überhaupt nicht treffen.
            for k in kennungen:
                frage = self.anhang_i_fragen[k]
                if frage.kennung not in antworten:
                    return frage
            if not any(antworten.get(self.anhang_i_fragen[k].kennung) for k in kennungen):
                return None
            for k in gruppe.get("ausschluss") or []:
                ausnahme = self.anhang_i_fragen.get(k)
                if ausnahme is not None and ausnahme.kennung not in antworten:
                    return ausnahme
        return None

    def _verbund(self, bereich: str) -> dict[str, Any] | None:
        verbunde: list[dict[str, Any]] = self.aufbau.get("verbunde") or []
        for v in verbunde:
            if v.get("bereich") == bereich:
                return v
        return None

    def _verbundpunkt_erfuellt(self, punkt: Punkt, antworten: dict[str, Any]) -> str:
        """Ein Punkt eines Verbundes: erfüllt, nicht erfüllt oder noch offen."""
        haupt = antworten.get(punkt.hauptfrage.kennung)
        if haupt is None:
            return WEITER
        if haupt is False:
            return NICHT_ERFASST
        # Ein Punkt des Verbundes hat oft keine Frage, die allein trägt — er
        # nennt nur die Merkmale des Bereichs. Erfüllt ist er darum, wenn die
        # Hauptfrage bejaht ist, keine Ausnahme greift und, wo der Punkt
        # Merkmale aufzählt, eines davon zutrifft.
        aufzaehlung = [f for f in punkt.folgefragen if _folge(f, True) == WEITER]
        offen = any(f.kennung not in antworten for f in punkt.folgefragen)
        for f in punkt.folgefragen:
            if _folge(f, antworten.get(f.kennung)) == NICHT_ERFASST:
                return NICHT_ERFASST
        if aufzaehlung and not any(antworten.get(f.kennung) is True for f in aufzaehlung):
            return WEITER if offen else NICHT_ERFASST
        return WEITER if offen else ERFASST

    def verbundbefund(self, bereich: str, antworten: dict[str, Any]) -> str:
        """Der Bereich als Ganzes — alle seine Punkte müssen tragen."""
        v = self._verbund(bereich)
        if v is None:
            return NICHT_ERFASST
        marke = str(v.get("sonderfall_hauptfrage_enthaelt") or "")
        if antworten.get("bereich:" + bereich) is False:
            return NICHT_ERFASST
        punkte = [p for p in self.punkte if p.bereich == bereich]
        regel = [p for p in punkte if marke not in p.hauptfrage.text]
        if not regel:
            return NICHT_ERFASST
        offen_erlaubt = v.get("darf_offen_bleiben") or {}
        marke_offen = str(offen_erlaubt.get("hauptfrage_enthaelt") or "")
        befunde = []
        bedingt = False
        for punkt in regel:
            befund = self._verbundpunkt_erfuellt(punkt, antworten)
            # Eine Bedingung, die der Nutzer nicht wissen kann, darf offen
            # bleiben. Sie dann als verneint zu werten, wäre eine falsche
            # Auskunft; der Befund lautet stattdessen "bedingt".
            if (
                marke_offen
                and marke_offen in punkt.hauptfrage.text
                and befund == NICHT_ERFASST
                and antworten.get(punkt.hauptfrage.kennung) is not False
            ):
                bedingt = True
                continue
            befunde.append(befund)
        if NICHT_ERFASST in befunde:
            return NICHT_ERFASST
        if WEITER in befunde:
            return WEITER
        return BEDINGT if bedingt else ERFASST

    def naechste(self, antworten: dict[str, Any]) -> Frage | None:
        """Die nächste zu stellende Frage — oder None, wenn alles feststeht."""
        # 1. Vorfragen, die ein Tor sind.
        for f in self.vorfragen:
            if f.kennung not in antworten:
                return f
            eintrag = self._vorfrage_eintrag(f.kennung)
            if antworten[f.kennung] is False and eintrag.get("bei_nein") == ENDE:
                return None

        # 1b. Anhang I vor Anhang III — Artikel 6 Absatz 1 steht vor Absatz 2.
        frage = self._naechste_anhang_i(antworten)
        if frage is not None:
            return frage

        # 1c. In welchem Bereich arbeitet der Nutzer? Erst danach die
        # Rechtsfragen des gewählten Bereichs.
        for f in self.bereichsfragen:
            if f.kennung not in antworten:
                return f

        # 2. Bereich für Bereich, Punkt für Punkt.
        uebersprungene_bereiche: set[str] = set()
        for punkt in self.punkte:
            if punkt.bereich in uebersprungene_bereiche:
                continue
            # Dieselben drei Sperren wie in punktbefund. Stünden sie nur dort,
            # fragte der Weg nach etwas, das die Wertung längst verworfen hat —
            # oder er schwiege zu etwas, das sie noch braucht. Genau diese
            # Ungleichheit hat den Durchlauf schon einmal auseinanderlaufen
            # lassen; der Abgleich in scripts/pruefe_zwei_wege.py hat sie
            # zwischen Python und Browser wieder zutage gefördert.
            if (
                self._punkt_gesperrt(punkt, antworten)
                or self._bereich_gesperrt(punkt, antworten)
                or self._bereich_abgewaehlt(punkt, antworten)
            ):
                continue
            if punkt.hauptfrage.kennung not in antworten:
                return punkt.hauptfrage
            if antworten[punkt.hauptfrage.kennung] is False:
                if punkt.ist_bereichstor:
                    uebersprungene_bereiche.add(punkt.bereich)
                continue
            # Alle Folgefragen des geöffneten Punkts, keine ausgelassen. Wer
            # unterwegs abbricht, lässt die Auswertung auf Antworten warten,
            # die nicht kommen. Die Bedienoberfläche zeigt sie auf einem Blatt,
            # darum kostet das den Nutzer keinen zusätzlichen Schritt.
            for f in punkt.folgefragen:
                if f.kennung not in antworten:
                    return f

        # 3. Nur wenn ein Punkt trägt, lohnt der Filter des Artikels 6 Absatz 3.
        traegt = any(self.punktbefund(p, antworten) == ERFASST for p in self.punkte) or any(
            self.verbundbefund(str(v.get("bereich")), antworten) == ERFASST
            for v in self.aufbau.get("verbunde") or []
        )
        if traegt:
            for f in self.filterfragen:
                if f.kennung not in antworten:
                    return f
            # Greift eine der vier Bedingungen, entscheidet noch das Profiling.
            if (
                any(antworten.get(f.kennung) for f in self.filterfragen)
                and self.profilingfrage
                and self.profilingfrage.kennung not in antworten
            ):
                return self.profilingfrage
        return None

    def naechste_gruppe(self, antworten: dict[str, Any]) -> tuple[Frage, ...]:
        """Alle Fragen, die zusammen auf ein Blatt gehören.

        Ein Jurist fragt in fünf bis acht Schritten, nicht in vierzig. Er
        bündelt aber, was zusammengehört: "In welchem Bereich arbeiten Sie?"
        ist eine Frage mit acht Kästchen, nicht acht Fragen. Und wenn er den
        Bereich kennt, legt er alle Fragen dazu auf einmal vor.

        Darum bildet jeder dieser Blöcke einen Schritt:
        Vorfragen, Bereichsauswahl, die Produktgattungen des Anhangs I, die
        Fragen eines Punktes, der Filter des Artikels 6 Absatz 3. Gemessen
        sinkt die Lebenslauf-Sichtung damit von 37 Schritten auf acht, ohne
        dass eine Frage wegfällt.
        """
        erste = self.naechste(antworten)
        if erste is None:
            return ()

        offen = lambda fs: tuple(f for f in fs if f.kennung not in antworten)  # noqa: E731

        # Vorfragen auf ein Blatt.
        if erste.stufe == "vorfrage":
            return offen(self.vorfragen)
        if erste.stufe == "bereich":
            return offen(self.bereichsfragen)

        # Anhang I: Tor allein, dann alle Gattungen, dann die Bedingungen.
        if erste.stufe == "anhang_i":
            if self.anhang_i_tor is not None and erste.kennung == self.anhang_i_tor.kennung:
                return (erste,)
            if erste.kennung.startswith("anhang-i-gattung:"):
                return offen(self.anhang_i_gattungen)
            return offen(tuple(self.anhang_i_fragen.values()))

        # Der Filter auf ein Blatt; die Profilingfrage erst danach, weil sie
        # nur nach einer bejahten Bedingung überhaupt zählt.
        if erste.stufe == "filter":
            if self.profilingfrage and erste.kennung == self.profilingfrage.kennung:
                return (erste,)
            return offen(self.filterfragen)

        # Bereichsauswahl: alle noch offenen Hauptfragen auf ein Blatt.
        if erste.kennung.startswith("haupt:"):
            gruppe: list[Frage] = []
            gesperrt: set[str] = set()
            for punkt in self.punkte:
                if punkt.bereich in gesperrt:
                    continue
                if (
                    self._punkt_gesperrt(punkt, antworten)
                    or self._bereich_gesperrt(punkt, antworten)
                    or self._bereich_abgewaehlt(punkt, antworten)
                ):
                    continue
                if punkt.hauptfrage.kennung in antworten:
                    if antworten[punkt.hauptfrage.kennung] is False and punkt.ist_bereichstor:
                        gesperrt.add(punkt.bereich)
                    continue
                gruppe.append(punkt.hauptfrage)
            return tuple(gruppe)

        # Die Fragen eines Punktes auf ein Blatt.
        gefunden = next((p for p in self.punkte if p.fundstelle == erste.fundstelle), None)
        if gefunden is None:
            return (erste,)
        # Bei mehreren Punkten unter derselben Fundstelle nur den, zu dem die
        # Frage gehört — Anhang III Nummer 2 hat vier davon.
        for kandidat in self.punkte:
            if any(f.kennung == erste.kennung for f in kandidat.folgefragen):
                gefunden = kandidat
                break
        return offen(gefunden.folgefragen)

    def ergebnis(self, antworten: dict[str, Any]) -> Befund:
        """Der Schluss aus den Antworten."""
        ki = self.vorfragen[0].kennung if self.vorfragen else ""
        if antworten.get(ki) is False:
            eintrag = self._vorfrage_eintrag(ki)
            return Befund(
                klasse="kein_ki_system",
                getroffene_punkte=(),
                filter_greift=False,
                filter_grund="",
                belege=(self.vorfragen[0].beleg,),
                offene_punkte=(),
                endtext=" ".join(str(eintrag.get("endtext") or "").split()),
            )

        if self.anhang_i_befund(antworten) == ERFASST:
            gattung = next((g for g in self.anhang_i_gattungen if antworten.get(g.kennung)), None)
            return Befund(
                klasse="hochrisiko_anhang_i",
                getroffene_punkte=(),
                filter_greift=False,
                filter_grund="",
                belege=tuple(f.beleg for f in (self.anhang_i_tor, gattung) if f and f.beleg),
                offene_punkte=(),
                endtext=(
                    "Hohes Risiko über das Produktsicherheitsrecht: "
                    + (gattung.titel if gattung else "Produkt nach Anhang I")
                    + ". Der Filter des Artikels 6 Absatz 3 gilt hier nicht — er "
                    "betrifft nur Anhang III."
                ),
            )

        getroffen = [p for p in self.punkte if self.punktbefund(p, antworten) == ERFASST]
        offen = [p.fundstelle for p in self.punkte if self.punktbefund(p, antworten) == WEITER]
        for v in self.aufbau.get("verbunde") or []:
            bereich = str(v.get("bereich"))
            befund = self.verbundbefund(bereich, antworten)
            if befund == ERFASST:
                getroffen += [p for p in self.punkte if p.bereich == bereich][:1]
            elif befund == BEDINGT:
                erster = [p for p in self.punkte if p.bereich == bereich][:1]
                offen_erlaubt = v.get("darf_offen_bleiben") or {}
                return Befund(
                    klasse="hochrisiko_bedingt",
                    getroffene_punkte=tuple(erster),
                    filter_greift=False,
                    filter_grund="",
                    belege=(str(offen_erlaubt.get("beleg") or ""),),
                    offene_punkte=tuple(offen),
                    endtext=" ".join(str(offen_erlaubt.get("wenn_offen") or "").split()),
                )
            elif befund == WEITER:
                offen.append(bereich)
        if not getroffen:
            return Befund(
                klasse="kein_hohes_risiko",
                getroffene_punkte=(),
                filter_greift=False,
                filter_grund="",
                belege=(),
                offene_punkte=tuple(offen),
            )

        bedingung = next((f for f in self.filterfragen if antworten.get(f.kennung) is True), None)
        profiling = antworten.get(self.profilingfrage.kennung) if self.profilingfrage else None
        # Reihenfolge nach dem amtlichen Text: erst eine der vier Bedingungen,
        # dann das Profiling. Nimmt das System Profiling vor, bleibt es
        # hochriskant, gleich wie gründlich ein Mensch nachprüft.
        if bedingung is not None and profiling is False:
            return Befund(
                klasse="hochrisiko_ausnahme",
                getroffene_punkte=tuple(getroffen),
                filter_greift=True,
                filter_grund=bedingung.text,
                belege=tuple(f.beleg for f in (bedingung, self.profilingfrage) if f),
                offene_punkte=tuple(offen),
            )
        return Befund(
            klasse="hochrisiko_anhang_iii",
            getroffene_punkte=tuple(getroffen),
            filter_greift=False,
            filter_grund="",
            belege=tuple(p.hauptfrage.beleg for p in getroffen),
            offene_punkte=tuple(offen),
        )

    # ------------------------------------------------------------- Zahlen
    def zahlen(self) -> dict[str, int]:
        """Was im Durchlauf steckt — gezählt, nicht geschätzt."""
        return {
            "vorfragen": len(self.vorfragen),
            "hinweise": len(self.hinweise),
            "punkte": len(self.punkte),
            "fragen": len(self.vorfragen)
            + sum(1 + len(p.folgefragen) for p in self.punkte)
            + len(self.filterfragen)
            + (1 if self.profilingfrage else 0)
            + (1 if self.anhang_i_tor else 0)
            + len(self.anhang_i_gattungen)
            + len(self.anhang_i_fragen)
            + len(self.bereichsfragen),
            "ausschluesse": sum(len(p.nicht_erfasst) for p in self.punkte),
            "beispiele": sum(len(p.beispiele) for p in self.punkte),
        }
