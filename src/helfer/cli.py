"""Die Kommandozeile des Konformitätshelfers.

Fünf Unterbefehle, und jeder antwortet auf eine Frage, die jemand wirklich hat:

* ``pruefen "…"``  — In welche Schublade fällt mein System, und was muss ich tun?
* ``fragen "…"``   — Was sagt das Recht zu dieser Frage, mit Fundstelle?
* ``suchen "…"``   — Wo steht das? Nur die Stellen, ohne Auslegung.
* ``dienst``       — Den Webdienst starten.
* ``stand``        — Ist alles da, womit das Werkzeug arbeiten soll?

Die Ausgabe ist für den Menschen gemacht, nicht für ein anderes Programm:
Absätze, Einrückung, Farbe. Wer die Ausgabe weiterverarbeiten will, nimmt
``--json`` — dann kommt genau das, was auch die Schnittstelle liefert.

Farbe wird abgeschaltet, wenn ``NO_COLOR`` gesetzt ist (so ist es verabredet,
siehe no-color.org), wenn ``--ohne-farbe`` angegeben wird oder wenn die
Ausgabe nicht an ein Fenster, sondern in eine Datei geht. Letzteres ist der
häufigste Fall: niemand will Steuerzeichen in seiner Protokolldatei.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import textwrap
from typing import Any

from helfer.modell import Einstufung, Rechtsakt, Risikoklasse, Rolle
from helfer.sicherheit import Eingabefehler, beschreibung_pruefen, frage_pruefen

# --------------------------------------------------------------------- Farbe


class Farben:
    """Die Steuerzeichen für Farbe — oder leere Zeichenketten, wenn ohne."""

    def __init__(self, an: bool) -> None:
        self.an = an

    def _f(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.an else text

    def fett(self, text: str) -> str:
        return self._f("1", text)

    def leise(self, text: str) -> str:
        return self._f("2", text)

    def rot(self, text: str) -> str:
        return self._f("1;31", text)

    def orange(self, text: str) -> str:
        return self._f("1;33", text)

    def blau(self, text: str) -> str:
        return self._f("1;34", text)

    def gruen(self, text: str) -> str:
        return self._f("1;32", text)

    def klasse(self, kennung: Risikoklasse, text: str) -> str:
        """Färbt nach Risikoklasse — dieselben vier Farben wie in der Oberfläche."""
        if kennung is Risikoklasse.VERBOTEN:
            return self.rot(text)
        if kennung.value.startswith("hochrisiko"):
            return self.orange(text)
        if kennung.value.startswith("gpai") or kennung is Risikoklasse.TRANSPARENZ:
            return self.blau(text)
        if kennung is Risikoklasse.MINIMAL:
            return self.gruen(text)
        return text


def farben_waehlen(ohne_farbe: bool) -> Farben:
    if ohne_farbe or os.environ.get("NO_COLOR") is not None:
        return Farben(an=False)
    return Farben(an=sys.stdout.isatty())


# ------------------------------------------------------------------ Ausgabe

BREITE = 78


def _punkte(anzahl: int) -> str:
    """ "1 Punkt", nicht "1 Punkte" — eine falsche Form liest sich wie ein Fehler."""
    return "1 Punkt" if anzahl == 1 else "%d Punkte" % anzahl


def _umbrechen(text: str, einzug: str = "  ") -> str:
    """Bricht Fließtext auf Lesebreite um. Rechtstext ohne Umbruch ist unlesbar."""
    zeilen = []
    for absatz in str(text).split("\n"):
        if not absatz.strip():
            zeilen.append("")
            continue
        zeilen.extend(
            textwrap.wrap(
                absatz,
                width=BREITE,
                initial_indent=einzug,
                subsequent_indent=einzug,
                # Kennungen wie KI-VO/art-6/abs-2 dürfen nicht am Bindestrich
                # auseinandergerissen werden — sonst kann man sie nicht mehr
                # abschreiben oder in die Suche einsetzen.
                break_on_hyphens=False,
                break_long_words=False,
            )
            or [einzug]
        )
    return "\n".join(zeilen)


def _ueberschrift(f: Farben, text: str) -> None:
    print()
    print(f.fett(text))
    print(f.leise("─" * min(len(text), BREITE)))


def einstufung_ausgeben(f: Farben, einstufung: Einstufung, mit_pflichten: bool = True) -> None:
    """Druckt eine Einstufung so, dass man sie am Bildschirm lesen kann."""
    schwerste = einstufung.schwerste
    _ueberschrift(f, "Einstufung")
    print("  " + f.klasse(schwerste, schwerste.value))
    print(_umbrechen(schwerste.klartext))
    if len(einstufung.klassen) > 1:
        print(
            _umbrechen(
                "Weitere zutreffende Klassen: "
                + ", ".join(k.value for k in einstufung.klassen if k is not schwerste)
            )
        )

    if einstufung.rollen:
        print()
        for rolle in einstufung.rollen:
            print(_umbrechen(f"Rolle {rolle.value} — {rolle.erklaerung}"))
    else:
        print()
        print(
            _umbrechen(
                "Rolle nicht angegeben. Es werden die Pflichten für "
                "Anbieter und für Betreiber genannt."
            )
        )

    _ueberschrift(f, "Warum")
    for hinweis in einstufung.hinweise:
        print(_umbrechen(f"• {hinweis.begruendung}"))
        print(
            f.leise(
                _umbrechen(
                    "Sicherheit: {} · Fundstellen: {}".format(
                        hinweis.sicherheit, ", ".join(hinweis.rechtsgrundlage) or "keine"
                    ),
                    einzug="    ",
                )
            )
        )

    if mit_pflichten and einstufung.pflichten:
        _ueberschrift(f, f"Zu tun nach der KI-Verordnung ({_punkte(len(einstufung.pflichten))})")
        for nummer, pflicht in enumerate(einstufung.pflichten, 1):
            marke = "" if pflicht.schwere.value == "pflicht" else f" [{pflicht.schwere.value}]"
            print("  %2d. %s%s" % (nummer, f.fett(pflicht.titel), marke))
            print(_umbrechen(pflicht.was_zu_tun_ist, einzug="      "))
            frist = (
                (" · gilt ab {}".format(pflicht.gilt_ab.strftime("%d.%m.%Y")))
                if pflicht.gilt_ab
                else ""
            )
            print(f.leise(_umbrechen(f"{pflicht.fundstellen_text}{frist}", einzug="      ")))

    if mit_pflichten and einstufung.datenschutz:
        _ueberschrift(
            f, f"Zu tun nach dem Datenschutzrecht ({_punkte(len(einstufung.datenschutz))})"
        )
        for nummer, pflicht in enumerate(einstufung.datenschutz, 1):
            print("  %2d. %s" % (nummer, f.fett(pflicht.titel)))
            print(_umbrechen(pflicht.was_zu_tun_ist, einzug="      "))
            print(f.leise(_umbrechen(pflicht.fundstellen_text, einzug="      ")))

    if einstufung.offene_fragen:
        _ueberschrift(f, "Damit die Auskunft genauer wird")
        for frage in einstufung.offene_fragen:
            print(_umbrechen(f"? {frage}"))


def belege_ausgeben(f: Farben, belege: Any, wortlaut: bool) -> None:
    _ueberschrift(f, f"Fundstellen ({len(belege):d})")
    for nummer, beleg in enumerate(belege, 1):
        print(
            "  %2d. %s %s"
            % (nummer, f.fett(beleg.fundstelle), f.leise(f"— {beleg.titel}" if beleg.titel else ""))
        )
        print(
            f.leise(
                _umbrechen(
                    "Kennung {} · Punktzahl {:.4f} · über {}".format(
                        beleg.kennung, beleg.punktzahl, ", ".join(beleg.wege) or "unbekannt"
                    ),
                    einzug="      ",
                )
            )
        )
        if wortlaut:
            print(_umbrechen(beleg.auszug, einzug="      "))
            print()


def _fusszeile(f: Farben) -> None:
    """Der Hinweis, der unter jede Auskunft gehört — auch auf der Kommandozeile."""
    from helfer.einstufung.pruefer import regelwerk

    werk = regelwerk()
    print()
    print(f.leise("─" * BREITE))
    print(
        _umbrechen(
            f.fett("Keine Rechtsberatung.") + " Dieses Werkzeug gibt "
            "Auskunft über den Inhalt von Rechtstexten und nennt die "
            "Fundstelle. Vor einer Entscheidung mit Geld- oder "
            "Rechtsfolgen sind die genannten Stellen selbst zu lesen.",
            einzug="",
        )
    )
    if werk.stand:
        print(f.leise("Regelsatz Stand {}".format(werk.stand.strftime("%d.%m.%Y"))))
    if werk.fristenvorbehalt:
        print(
            f.leise(
                _umbrechen(
                    "Vorbehalt zu den Fristen: " + " ".join(werk.fristenvorbehalt.split()),
                    einzug="",
                )
            )
        )


# ------------------------------------------------------------- Unterbefehle


def _rollen_lesen(werte: list[str] | None) -> tuple[Rolle, ...]:
    """Übersetzt ``--rolle betreiber`` in das Datenmodell, mit klarer Meldung."""
    if not werte:
        return ()
    gefunden: list[Rolle] = []
    erlaubt = {r.value for r in Rolle}
    for wert in werte:
        wort = wert.strip().lower()
        if wort not in erlaubt:
            raise Eingabefehler(
                "Die Rolle {!r} kennt das Werkzeug nicht. Möglich sind: {}".format(
                    wert, ", ".join(sorted(erlaubt))
                )
            )
        gefunden.append(Rolle(wort))
    return tuple(gefunden)


def _rechtsakte_lesen(werte: list[str] | None) -> tuple[Rechtsakt, ...] | None:
    if not werte:
        return None
    erlaubt = {a.value.lower(): a for a in Rechtsakt}
    gefunden: list[Rechtsakt] = []
    for wert in werte:
        akt = erlaubt.get(wert.strip().lower())
        if akt is None:
            raise Eingabefehler(
                "Den Rechtsakt {!r} kennt das Werkzeug nicht. Möglich sind: {}".format(
                    wert, ", ".join(a.value for a in Rechtsakt)
                )
            )
        gefunden.append(akt)
    return tuple(gefunden)


def befehl_pruefen(args: argparse.Namespace, f: Farben) -> int:
    from helfer.einstufung.pruefer import Pruefer, beschreibung_aus_text

    text = beschreibung_pruefen(args.beschreibung)
    if not text:
        raise Eingabefehler("Bitte eine Beschreibung angeben, in Anführungszeichen.")
    beschreibung = beschreibung_aus_text(text)
    if args.rolle:
        beschreibung = beschreibung.model_copy(update={"rollen": _rollen_lesen(args.rolle)})
    ergebnis = Pruefer().pruefen(beschreibung)

    if args.json:
        print(ergebnis.model_dump_json(indent=1))
        return 0
    einstufung_ausgeben(f, ergebnis)
    _fusszeile(f)
    return 0


def befehl_fragen(args: argparse.Namespace, f: Farben) -> int:
    from helfer.antwort.formulieren import formulieren, modell_waehlen
    from helfer.dienst.anwendung import _lernhinweis_und_faelle, neubewertung_an
    from helfer.einstufung.pruefer import Pruefer, beschreibung_aus_text
    from helfer.suche.index import als_belegstellen

    frage = frage_pruefen(args.frage)
    beschreibungstext = beschreibung_pruefen(args.beschreibung)
    wunsch = (args.modell or os.environ.get("HELFER_MODELL", "auto")).lower()
    ohne_modell = wunsch in ("ohne", "keines", "regelwerk")
    # Wer "--modell ohne" sagt, soll nicht die Meldung lesen, dass kein Modell
    # erreichbar sei: er hat es selbst abgeschaltet.
    zustand = _zustand(args, mit_sprachmodell=not ohne_modell)
    if zustand.bestand is None:
        return 2

    beschreibung = beschreibung_aus_text(beschreibungstext or frage)
    if args.rolle:
        beschreibung = beschreibung.model_copy(update={"rollen": _rollen_lesen(args.rolle)})
    ergebnis = Pruefer().pruefen(beschreibung)

    suchtext = f"{frage}\n{beschreibungstext}" if beschreibungstext else frage
    treffer = zustand.bestand.suchen(
        suchtext[:4000],
        anzahl=args.anzahl,
        nur_rechtsakte=_rechtsakte_lesen(args.rechtsakt),
        mit_neubewertung=neubewertung_an(),
    )
    belege = als_belegstellen(treffer)
    lernhinweis, faelle = _lernhinweis_und_faelle([t.einheit for t in treffer])

    modell = (
        None
        if ohne_modell
        else (zustand.sprachmodell if wunsch == "auto" else modell_waehlen(wunsch))
    )

    antwort = formulieren(
        frage,
        beschreibungstext,
        ergebnis,
        belege,
        modell=modell,
        lernhinweis=lernhinweis,
        beispielfaelle=faelle,
    )

    if args.json:
        print(antwort.model_dump_json(indent=1))
        return 0

    einstufung_ausgeben(f, ergebnis)
    _ueberschrift(f, "Die Auskunft im Zusammenhang")
    print(_umbrechen(antwort.text))
    print(
        f.leise(
            _umbrechen(
                "Ohne Sprachmodell aus dem Regelwerk zusammengestellt."
                if antwort.ohne_modell
                else f"Formuliert durch {antwort.modell}."
            )
        )
    )
    if antwort.lernhinweis:
        _ueberschrift(f, "Worauf es ankommt")
        print(_umbrechen(antwort.lernhinweis))
        if antwort.beispielfaelle:
            print(f.leise(_umbrechen("Vergleichbare Fälle: " + " · ".join(antwort.beispielfaelle))))
    belege_ausgeben(f, antwort.belege, wortlaut=args.wortlaut)
    for warnung in antwort.warnungen:
        print()
        print(_umbrechen(f.orange("Hinweis: ") + warnung, einzug=""))
    _fusszeile(f)
    return 0


def befehl_suchen(args: argparse.Namespace, f: Farben) -> int:
    from helfer.dienst.anwendung import neubewertung_an
    from helfer.suche.index import als_belegstellen

    frage = frage_pruefen(args.begriff)
    # Ohne Sprachmodell: hier wird nur gesucht, nicht formuliert.
    zustand = _zustand(args, mit_sprachmodell=False)
    if zustand.bestand is None:
        return 2
    treffer = zustand.bestand.suchen(
        frage,
        anzahl=args.anzahl,
        nur_rechtsakte=_rechtsakte_lesen(args.rechtsakt),
        mit_neubewertung=neubewertung_an(),
    )
    belege = als_belegstellen(treffer)
    if args.json:
        print(
            json.dumps([b.model_dump() for b in belege], ensure_ascii=False, indent=1, default=str)
        )
        return 0
    belege_ausgeben(f, belege, wortlaut=not args.kurz)
    return 0


def befehl_dienst(args: argparse.Namespace, f: Farben) -> int:
    from helfer.dienst.anwendung import starten

    print(f.fett("Konformitätshelfer startet …"))
    print(
        _umbrechen(
            "Die Oberfläche steht dann unter {}".format(
                f.blau(f"http://{args.adresse}:{args.port:d}/")
            ),
            einzug="",
        )
    )
    print(_umbrechen(f.leise("Beenden mit Strg+C."), einzug=""))
    print()
    starten(adresse=args.adresse, port=args.port, neuladen=args.neuladen)
    return 0


def befehl_stand(args: argparse.Namespace, f: Farben) -> int:
    """Zeigt, womit das Werkzeug arbeitet — und was fehlt.

    Dieser Befehl ist der erste, den man braucht, wenn etwas nicht geht: er
    sagt, ob Korpus, Suchbestand, Regelsatz und Modelle da sind, statt dass man
    es aus einer Fehlermeldung erraten muss.
    """
    from helfer.dienst.anwendung import BESTANDSPFAD, zustand_laden
    from helfer.einstufung.pruefer import REGELN, regelwerk
    from helfer.korpus.bauen import KORPUS

    zustand = zustand_laden()
    werk = regelwerk()

    if args.json:
        print(
            json.dumps(
                {
                    "korpus": str(KORPUS),
                    "korpus_vorhanden": KORPUS.exists(),
                    "einheiten": len(zustand.einheiten),
                    "stand_korpus": str(zustand.stand_korpus or ""),
                    "bestand_aus_datei": zustand.bestand_aus_datei,
                    "einbettungsmodell": zustand.einbettungsmodell,
                    "sprachmodell": zustand.sprachmodell_name,
                    "stand_regeln": str(werk.stand or ""),
                    "pflichten": len(werk.pflichten),
                    "warnungen": zustand.warnungen,
                },
                ensure_ascii=False,
                indent=1,
            )
        )
        return 0

    _ueberschrift(f, "Rechtstexte")
    print(_umbrechen(f"Datei: {KORPUS}"))
    print(
        _umbrechen(
            "%s · %d Rechtsstellen · Stand %s"
            % (
                f.gruen("vorhanden") if KORPUS.exists() else f.rot("fehlt"),
                len(zustand.einheiten),
                zustand.stand_korpus.strftime("%d.%m.%Y") if zustand.stand_korpus else "unbekannt",
            )
        )
    )
    nach_akt: dict[str, int] = {}
    for einheit in zustand.einheiten:
        nach_akt[einheit.rechtsakt.value] = nach_akt.get(einheit.rechtsakt.value, 0) + 1
    for name, zahl in sorted(nach_akt.items()):
        print(_umbrechen("%-12s %5d" % (name, zahl), einzug="    "))

    _ueberschrift(f, "Suchbestand")
    print(
        _umbrechen(
            f"Dateien: {BESTANDSPFAD.name}.vektoren.npy und {BESTANDSPFAD.name}.bestand.json.gz"
        )
    )
    print(_umbrechen(f"Ordner: {BESTANDSPFAD.parent}"))
    print(
        _umbrechen(
            "{} · Einbettungsmodell {}".format(
                f.gruen("aus Datei geladen")
                if zustand.bestand_aus_datei
                else f.orange("im Speicher gebaut"),
                zustand.einbettungsmodell,
            )
        )
    )

    _ueberschrift(f, "Regelsatz")
    print(_umbrechen(f"Ordner: {REGELN}"))
    print(
        _umbrechen(
            "Stand %s · %d Pflichten · %d Abschnitte Datenschutz"
            % (
                werk.stand.strftime("%d.%m.%Y") if werk.stand else "unbekannt",
                len(werk.pflichten),
                len(werk.datenschutz),
            )
        )
    )

    _ueberschrift(f, "Formulierung")
    print(_umbrechen(zustand.sprachmodell_name))

    if zustand.warnungen:
        _ueberschrift(f, "Warnungen")
        for warnung in zustand.warnungen:
            print(_umbrechen(f.orange("! ") + warnung))
    else:
        print()
        print(_umbrechen(f.gruen("Alles vorhanden."), einzug=""))
    return 0


def _zustand(args: argparse.Namespace, mit_sprachmodell: bool = True) -> Any:
    """Lädt Korpus und Suchbestand für die Befehle, die suchen.

    Beim ersten Lauf ohne abgelegten Bestand dauert das einen Moment — darum
    sagt es das vorher, statt den Nutzer rätseln zu lassen. Die Warnungen
    druckt hier niemand: sie kommen über das Protokoll, und zweimal dasselbe
    zu lesen ist schlimmer als einmal.
    """
    from helfer.dienst.anwendung import zustand_laden

    if not args.json:
        print("Lade Rechtstexte und Suchbestand …", file=sys.stderr)
    zustand = zustand_laden(mit_sprachmodell=mit_sprachmodell)
    if zustand.bestand is None:
        print(
            "Der Suchbestand konnte nicht geladen werden. Die Gründe stehen oben.", file=sys.stderr
        )
    return zustand


# --------------------------------------------------------------- Einstieg


def zerleger_bauen() -> argparse.ArgumentParser:
    zerleger = argparse.ArgumentParser(
        prog="konformitaetshelfer",
        description="Belegte Auskunft zur KI-Verordnung (EU) 2024/1689 und zur "
        "Datenschutz-Grundverordnung. Keine Rechtsberatung.",
        epilog="Beispiele:\n"
        '  konformitaetshelfer pruefen "Wir sortieren Bewerbungen mit '
        'einem Sprachmodell vor"\n'
        '  konformitaetshelfer fragen "Brauchen wir eine '
        'Folgenabschätzung?" --rolle betreiber\n'
        '  konformitaetshelfer suchen "Artikel 6 Absatz 3" --kurz\n'
        "  konformitaetshelfer dienst --port 8000\n"
        "  konformitaetshelfer stand",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )
    # argparse schreibt seinen Hilfetext auf Englisch. Der eine Satz, den der
    # Nutzer liest, wird deshalb selbst gesetzt; die Abschnittsköpfe von
    # argparse bleiben, weil sie das Fremdpaket vorgibt.
    zerleger.add_argument("-h", "--hilfe", action="help", help="diese Hilfe zeigen und beenden")

    # Diese zwei Angaben gelten für jeden Unterbefehl. Sie stehen zweimal da —
    # einmal vorn am Programm, einmal über einen gemeinsamen Elternzerleger an
    # jedem Unterbefehl —, weil argparse eine Angabe hinter dem Unterbefehl
    # sonst nicht annimmt. Niemand soll raten müssen, wo --json hingehört.
    def allgemeines(ziel: argparse.ArgumentParser) -> None:
        ziel.add_argument(
            "--ohne-farbe", action="store_true", help="keine Farbe ausgeben (wie NO_COLOR)"
        )
        ziel.add_argument(
            "--json", action="store_true", help="Ausgabe als JSON, zum Weiterverarbeiten"
        )

    allgemeines(zerleger)
    gemeinsam = argparse.ArgumentParser(add_help=False)
    allgemeines(gemeinsam)

    unter = zerleger.add_subparsers(dest="befehl", metavar="BEFEHL")

    p = unter.add_parser(
        "pruefen", parents=[gemeinsam], help="Ein System einstufen, ohne Sprachmodell"
    )
    p.add_argument("beschreibung", help="Das KI-System in eigenen Worten")
    p.add_argument(
        "--rolle",
        action="append",
        metavar="ROLLE",
        help="anbieter, betreiber, einfuehrer, haendler, "
        "produkthersteller, bevollmaechtigter — mehrfach möglich",
    )
    p.set_defaults(lauf=befehl_pruefen)

    p = unter.add_parser(
        "fragen", parents=[gemeinsam], help="Volle Auskunft: Einstufung, Pflichten, Belege"
    )
    p.add_argument("frage", help="Die Rechtsfrage")
    p.add_argument("--beschreibung", default="", help="Das KI-System in eigenen Worten")
    p.add_argument("--rolle", action="append", metavar="ROLLE")
    p.add_argument("--modell", default=None, help="anthropic, openai, ollama, auto oder ohne")
    p.add_argument("--anzahl", type=int, default=8, help="Zahl der Fundstellen")
    p.add_argument(
        "--rechtsakt",
        action="append",
        metavar="AKT",
        help="Suche auf KI-VO, DSGVO, BDSG oder Leitlinie beschränken",
    )
    p.add_argument(
        "--wortlaut", action="store_true", help="den Wortlaut der Fundstellen mitdrucken"
    )
    p.set_defaults(lauf=befehl_fragen)

    p = unter.add_parser(
        "suchen", parents=[gemeinsam], help="Nur Fundstellen suchen, ohne Auslegung"
    )
    p.add_argument("begriff", help="Suchbegriff oder Fundstelle")
    p.add_argument("--anzahl", type=int, default=8)
    p.add_argument("--rechtsakt", action="append", metavar="AKT")
    p.add_argument("--kurz", action="store_true", help="nur die Fundstellen, ohne Wortlaut")
    p.set_defaults(lauf=befehl_suchen)

    p = unter.add_parser("dienst", parents=[gemeinsam], help="Den Webdienst starten")
    p.add_argument(
        "--adresse",
        default=os.environ.get("HELFER_ADRESSE", "127.0.0.1"),
        help="Vorgabe 127.0.0.1 — nur der eigene Rechner",
    )
    p.add_argument("--port", type=int, default=int(os.environ.get("HELFER_PORT", "8000")))
    p.add_argument(
        "--neuladen",
        action="store_true",
        help="bei Änderungen am Quelltext neu laden (nur für Entwicklung)",
    )
    p.set_defaults(lauf=befehl_dienst)

    p = unter.add_parser("stand", parents=[gemeinsam], help="Zeigt, womit das Werkzeug arbeitet")
    p.set_defaults(lauf=befehl_stand)

    return zerleger


def main(argv: list[str] | None = None) -> int:
    zerleger = zerleger_bauen()
    args = zerleger.parse_args(argv)
    if not getattr(args, "lauf", None):
        zerleger.print_help()
        return 1

    # Die allgemeinen Schalter stehen zweimal: am Hauptbefehl und an jedem
    # Unterbefehl, damit beide Schreibweisen gehen. argparse setzt dabei den
    # Wert des Unterbefehls über den des Hauptbefehls - auch wenn dort nur die
    # Vorgabe steht. "helfer --json stand" verlor dadurch stillschweigend sein
    # --json. Darum wird hier nachgesehen, was wirklich auf der Zeile stand.
    zeile = list(sys.argv[1:] if argv is None else argv)
    if "--json" in zeile:
        args.json = True
    if "--ohne-farbe" in zeile:
        args.ohne_farbe = True

    f = farben_waehlen(args.ohne_farbe)
    # Warnungen aus den unteren Schichten gehen nach stderr, damit sie die
    # Ausgabe nicht verschmutzen, die jemand in eine Datei umleitet. Mit
    # Vorsatz "Hinweis:", damit man sie von der Auskunft unterscheiden kann.
    import logging

    logging.basicConfig(level=logging.WARNING, format="Hinweis: %(message)s", stream=sys.stderr)
    try:
        return int(args.lauf(args, f))
    except Eingabefehler as fehler:
        # Eine Eingabe, die nicht passt: Klartext, kein Rückverfolgungsbericht.
        print(f.rot("Eingabe nicht brauchbar: ") + str(fehler), file=sys.stderr)
        return 2
    except FileNotFoundError as fehler:
        print(f.rot("Es fehlt eine Datei: ") + str(fehler), file=sys.stderr)
        print("Erst bauen: python -m helfer.korpus.bauen", file=sys.stderr)
        return 3
    except KeyboardInterrupt:
        print()
        print("Abgebrochen.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
