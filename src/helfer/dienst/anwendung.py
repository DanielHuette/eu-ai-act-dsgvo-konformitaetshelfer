"""Der Webdienst: eine Oberfläche, fünf Schnittstellen, nichts im Hintergrund.

Drei Entscheidungen, die den Aufbau erklären:

**Einmal laden, nicht je Anfrage.** Korpus, Suchbestand und Regelwerk werden
beim Start in den Speicher gelegt (``lifespan``). Je Anfrage zu laden hieße,
2721 Rechtseinheiten und ihre Zahlenreihen jedes Mal von der Platte zu holen —
die erste Antwort käme nach Minuten statt nach Millisekunden.

**Die Einstufung ohne Sprachmodell, die Formulierung mit.** Welche Risikoklasse
gilt, entscheidet der Prüfer aus den Regeldateien; derselbe Fall ergibt immer
dasselbe Ergebnis. Das Sprachmodell formuliert nur und bekommt die Einstufung
als feststehende Tatsache vorgelegt. Darum gibt es ``/api/einstufung`` auch
ohne Sprachmodell: das ist der Teil, auf den man sich verlassen kann.

**Keine Innereien nach außen.** Jeder Fehler wird abgefangen und als deutscher
Satz zurückgegeben. Eine Rückverfolgung (Stacktrace) nennt Dateipfade,
Paketversionen und manchmal Inhalte von Variablen — sie gehört ins Protokoll
des Betreibers, nicht in die Antwort an einen Unbekannten.

Umgebungsvariablen stehen erklärt in ``.env.example``.
"""

from __future__ import annotations

import logging
import os
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.cors import CORSMiddleware

from helfer.antwort.formulieren import formulieren, modell_waehlen
from helfer.dienst.modelle import (
    FRAGEBOGEN,
    FRAGEBOGEN_HINWEIS,
    EinstufungAnfrage,
    EinstufungAntwort,
    Fehlerantwort,
    FrageAnfrage,
    FrageAntwort,
    Fragebogen,
    Fristen,
    Fristenstufe,
    Gesundheit,
    Klartext,
    SucheAnfrage,
    SucheAntwort,
    fragebogen_pruefen,
)
from helfer.einstufung.pruefer import Pruefer, beschreibung_aus_text, regelwerk
from helfer.korpus.bauen import AUFBEREITET, KORPUS, laden
from helfer.modell import (
    Einheit,
    Einheitsart,
    Risikoklasse,
    Rolle,
    Systembeschreibung,
)
from helfer.sicherheit import (
    Eingabefehler,
    SchluesselFilter,
    beschreibung_pruefen,
    frage_pruefen,
    protokollsicher,
    umgebung_pruefen,
    zaehler_aus_umgebung,
)
from helfer.suche.einbettung import Streuwerk, waehlen
from helfer.suche.index import Suchbestand, als_belegstellen

protokoll = logging.getLogger("helfer.dienst")

#: Wo der abgelegte Suchbestand liegt. Derselbe Ordner wie der Korpus, damit
#: Korpus und Bestand nicht auseinanderlaufen können.
BESTANDSPFAD = AUFBEREITET / "suchbestand"

#: Wo Vorlage und Gestaltung liegen.
OBERFLAECHE = Path(__file__).resolve().parent.parent / "weboberflaeche"


def neubewertung_an() -> bool:
    """Ob der Kreuzbewerter die Vorauswahl neu bewerten darf.

    Vorgabe ist *aus*, und zwar aus einem gemessenen Grund: der Kreuzbewerter
    (bge-reranker-v2-m3) liest Frage und Fundstelle gemeinsam und ist dadurch
    genauer — aber er rechnet dafür 30 Textpaare durch ein Modell mit über
    einer halben Milliarde Gewichten. Auf einem Rechner ohne Grafikkarte
    dauert eine einzige Suche damit gemessene 100 Sekunden. Eine Antwort, die
    nach anderthalb Minuten kommt, ist keine Antwort. Wer eine Grafikkarte hat,
    schaltet die Neubewertung mit HELFER_NEUBEWERTUNG=1 ein und bekommt eine
    messbar bessere Reihenfolge der Fundstellen.
    """
    wert = os.environ.get("HELFER_NEUBEWERTUNG", "0").strip().lower()
    return wert in ("1", "ja", "true", "an", "ein", "yes")


#: Fremde Adressen dürfen die Schnittstelle nicht aus dem Browser aufrufen.
#: Vorgabe sind nur die beiden Schreibweisen des eigenen Rechners. Wer den
#: Dienst in ein Netz stellt, setzt HELFER_HERKUNFT ausdrücklich.
VORGABE_HERKUNFT = ("http://localhost:8000", "http://127.0.0.1:8000", "http://localhost:5173")


# ------------------------------------------------------------------- Zustand


@dataclass
class Zustand:
    """Was der Dienst beim Start lädt und über alle Anfragen hinweg behält."""

    einheiten: list[Einheit] = field(default_factory=list)
    bestand: Suchbestand | None = None
    pruefer: Pruefer | None = None
    sprachmodell: Any = None
    sprachmodell_name: str = "ohne Sprachmodell (Antwort aus dem Regelwerk)"
    stand_korpus: date | None = None
    stand_regeln: date | None = None
    bestand_aus_datei: bool = False
    startdauer_ms: int = 0
    gestartet: float = 0.0
    warnungen: list[str] = field(default_factory=list)

    @property
    def einbettungsmodell(self) -> str:
        return self.bestand.einbetter.name if self.bestand else "keines"

    @property
    def zustandswort(self) -> str:
        if not self.einheiten or self.bestand is None:
            return "nicht_bereit"
        if self.warnungen:
            return "eingeschraenkt"
        return "bereit"


def _einbetter_waehlen() -> tuple[Any, str]:
    """Welches Einbettungsmodell der Dienst nimmt, wenn er selbst bauen muss.

    Gilt nur für diesen Fall: liegt der Bestand als Datei vor, steht das
    Modell in der Datei und hier wird nichts gewählt.

    Hier steckt eine gemessene Erfahrung. Mit bge-m3 dauert das Einbetten
    einer Fundstelle auf einem Rechner ohne Grafikkarte rund sechs Sekunden.
    Bei 2721 Rechtsstellen sind das mehrere Stunden — ein Dienst, der so lange
    startet, ist nicht gestartet, sondern hängengeblieben, und im Container
    sieht man dabei nur einen Zustandsbericht, der nicht antwortet.

    Darum: fehlt der abgelegte Bestand, wird mit dem Ersatzmodell gebaut, auch
    wenn ein gutes Modell daliegt — in Sekunden statt in Stunden, mit einer
    Warnung, die den Befehl zum Bauen des Bestands nennt. Wer es trotzdem im
    Dienst bauen lassen will, setzt HELFER_BESTAND_BAUEN=1 und weiß dann, dass
    er wartet.
    """
    gewuenscht = os.environ.get("HELFER_EINBETTUNG", "").strip()
    if not gewuenscht or gewuenscht == Streuwerk.name:
        return Streuwerk(), ""

    erlaubnis = os.environ.get("HELFER_BESTAND_BAUEN", "0").strip().lower()
    if erlaubnis not in ("1", "ja", "true", "an", "ein", "yes"):
        return Streuwerk(), (
            f"Der abgelegte Suchbestand fehlt. Mit {gewuenscht} würde sein Aufbau hier "
            "Stunden dauern, darum läuft die Suche mit dem Ersatzmodell "
            "'streuwerk-ersatz': es vergleicht nur Wörter, nicht Bedeutung, "
            "und findet deutlich schlechter. Richtig ist, den Bestand einmal "
            "zu bauen — python -m scripts.bestand_bauen — und ihn als "
            f"{BESTANDSPFAD.name}.vektoren.npy und "
            f"{BESTANDSPFAD.name}.bestand.json.gz abzulegen. Wer stattdessen "
            "hier und jetzt warten will: HELFER_BESTAND_BAUEN=1 setzen."
        )
    return waehlen(gewuenscht), ""


def zustand_laden(mit_sprachmodell: bool = True) -> Zustand:
    """Lädt alles, was der Dienst braucht — einmal, beim Start.

    ``mit_sprachmodell=False`` überspringt die Suche nach einem Antwortgeber.
    Das braucht die Kommandozeile beim Befehl ``suchen``: dort wird nichts
    formuliert, und die Erreichbarkeitsprüfung kostet bis zu drei Sekunden und
    meldet einen Mangel, der für diesen Befehl keiner ist.
    """
    beginn = time.perf_counter()
    z = Zustand(gestartet=time.time())
    z.warnungen.extend(umgebung_pruefen())

    fehlende = fragebogen_pruefen()
    if fehlende:
        z.warnungen.append(
            "Der Fragebogen nennt Angaben, die das Datenmodell nicht kennt: {}. "
            "Antworten darauf würden verfallen.".format(", ".join(fehlende))
        )

    try:
        z.einheiten = laden()
        z.stand_korpus = max((e.stand for e in z.einheiten if e.stand), default=None)
    except FileNotFoundError as fehler:
        z.warnungen.append(
            f"Der Rechtskorpus fehlt ({KORPUS}). Erst bauen: python -m helfer.korpus.bauen"
        )
        protokoll.error("Korpus nicht geladen: %s", protokollsicher(fehler))
        return z

    # Der abgelegte Bestand ist der Normalfall. Fehlt er, wird er im Speicher
    # gebaut — das dauert mit dem Ersatzmodell unter einer Sekunde und hält den
    # Dienst arbeitsfähig, statt ihn mit einer Fehlermeldung stehen zu lassen.
    # Der Beipack liegt als gepacktes JSON (.bestand.json.gz). Frühere
    # Fassungen legten ihn als pickle ab; eine solche Datei wird nicht mehr
    # gelesen, und Suchbestand.laden sagt das mit einer eigenen Meldung.
    beipack = BESTANDSPFAD.with_suffix(".bestand.json.gz")
    npy = BESTANDSPFAD.with_suffix(".vektoren.npy")

    # Wer ausdrücklich das Ersatzverfahren verlangt (HELFER_EINBETTUNG=ersatz),
    # bekommt es auch dann, wenn ein abgelegter Bestand danebenliegt. Sonst
    # zöge ein Prüflauf, der schnell sein soll, das volle Einbettungsmodell
    # nach — und wartete Minuten auf etwas, das er gar nicht wollte.
    gewuenscht = os.environ.get("HELFER_EINBETTUNG", "").strip().lower()
    ersatz_gewuenscht = gewuenscht in {"ersatz", "streuwerk", Streuwerk.name}

    if beipack.exists() and npy.exists() and not ersatz_gewuenscht:
        try:
            z.bestand = Suchbestand.laden(BESTANDSPFAD, z.einheiten)
            z.bestand_aus_datei = True
        except Exception as fehler:
            z.warnungen.append(
                "Der abgelegte Suchbestand passt nicht zum Korpus und wurde "
                f"nicht genommen ({type(fehler).__name__}). Der Bestand wird im Speicher gebaut."
            )
            protokoll.warning("Bestand nicht geladen: %s", protokollsicher(fehler))

    if z.bestand is None:
        einbetter, grund = _einbetter_waehlen()
        z.bestand = Suchbestand(z.einheiten, einbetter)
        z.bestand.bauen()
        if grund:
            z.warnungen.append(grund)
        elif einbetter.name == Streuwerk.name:
            z.warnungen.append(
                "Die Suche läuft mit dem Ersatzmodell 'streuwerk-ersatz'. Es "
                "vergleicht nur Wörter, nicht Bedeutung — die Fundstellen sind "
                "deutlich schlechter. Für den Betrieb den Suchbestand bauen: "
                "python -m scripts.bestand_bauen"
            )

    z.pruefer = Pruefer()
    werk = regelwerk()
    z.stand_regeln = werk.stand

    wunsch = os.environ.get("HELFER_MODELL", "auto").strip().lower()
    if not mit_sprachmodell:
        wunsch = "ohne"
    # Das Sprachmodell wird einmal gewählt, nicht je Anfrage: die Prüfung, ob
    # ein Anbieter erreichbar ist, kostet bis zu drei Sekunden Wartezeit.
    if wunsch in ("ohne", "keines", "regelwerk"):
        protokoll.info("Sprachmodell abgeschaltet — Antworten kommen aus dem Regelwerk")
    else:
        z.sprachmodell = modell_waehlen(wunsch if wunsch != "auto" else None)
        if z.sprachmodell is not None:
            z.sprachmodell_name = z.sprachmodell.name
        else:
            z.warnungen.append(
                "Kein Sprachmodell erreichbar. Die Auskunft entsteht allein aus "
                "dem Regelwerk und ist dadurch knapper formuliert — inhaltlich "
                "ist sie dieselbe."
            )

    z.startdauer_ms = int((time.perf_counter() - beginn) * 1000)
    protokoll.info(
        "Start in %d ms: %d Einheiten, Suche mit %s, Formulierung mit %s",
        z.startdauer_ms,
        len(z.einheiten),
        z.einbettungsmodell,
        z.sprachmodell_name,
    )
    for warnung in z.warnungen:
        protokoll.warning("%s", protokollsicher(warnung))
    return z


# -------------------------------------------------------------- Hilfsarbeiten


def _klartext_klassen(klassen: tuple[Risikoklasse, ...]) -> tuple[Klartext, ...]:
    return tuple(Klartext(kennung=k.value, klartext=k.klartext) for k in klassen)


def _klartext_rollen(rollen: tuple[Rolle, ...]) -> tuple[Klartext, ...]:
    return tuple(Klartext(kennung=r.value, klartext=r.erklaerung) for r in rollen)


def _lernhinweis_und_faelle(einheiten: list[Einheit]) -> tuple[str, tuple[str, ...]]:
    """Holt den Lernhinweis aus dem bestgetroffenen Anwendungsfall.

    Die Anwendungsfälle liegen als gewöhnliche Einheiten im Korpus; ihr Text
    trägt den Abschnitt "Worauf es ankommt". Dieser Satz ist der eigentliche
    Weiterbildungseffekt des Werkzeugs — er wird deshalb eigens herausgezogen
    und nicht im Belegtext versteckt.
    """
    hinweis = ""
    titel: list[str] = []
    for einheit in einheiten:
        if einheit.art is not Einheitsart.FALLBEISPIEL:
            continue
        titel.append(einheit.titel or einheit.nummer)
        if hinweis:
            continue
        for abschnitt in einheit.text.split("\n\n"):
            if abschnitt.startswith("Worauf es ankommt:"):
                hinweis = abschnitt.split(":", 1)[1].strip()
                break
    return hinweis, tuple(titel[:5])


#: Welche Felder der Beschreibung welche Art von Wert erwarten. Gebraucht, um
#: die Angaben aus dem Fragebogen zu übersetzen: ein Browser schickt "ja",
#: "true" und "1" — alles dasselbe, aber keins davon ist ein Wahrheitswert.
_JA = frozenset(("true", "ja", "1", "yes", "wahr", "on"))
_NEIN = frozenset(("false", "nein", "0", "no", "falsch", "off"))


def _wahrheitswert(wert: object) -> bool | None:
    if isinstance(wert, bool):
        return wert
    if wert is None:
        return None
    text = str(wert).strip().lower()
    if text in _JA:
        return True
    if text in _NEIN:
        return False
    if text in ("", "unbekannt", "weiss_nicht", "weiß nicht"):
        return None
    return None


def beschreibung_bauen(anfrage: EinstufungAnfrage) -> tuple[Systembeschreibung, tuple[str, ...]]:
    """Baut aus Freitext und Fragebogenangaben das Prüfobjekt.

    Der Freitext wird zuerst gelesen (er erkennt Rolle und Merkmale als
    *Hinweis*), danach überschreiben die ausdrücklichen Angaben aus dem
    Fragebogen — denn was der Nutzer angekreuzt hat, wiegt schwerer als was ein
    Stichwort vermuten lässt.
    """
    text = beschreibung_pruefen(anfrage.beschreibung)
    grundform = beschreibung_aus_text(text)
    werte: dict[str, Any] = grundform.model_dump()
    if anfrage.rollen:
        werte["rollen"] = tuple(anfrage.rollen)

    felder = Systembeschreibung.model_fields
    unbekannt: list[str] = []
    for name, roh in anfrage.merkmale.items():
        if name not in felder or name in ("freitext",):
            unbekannt.append(name)
            continue
        if name == "rollen":
            continue  # Rollen kommen über das eigene Feld, nicht über Merkmale.
        erwartet = str(felder[name].annotation)
        if "bool" in erwartet:
            wert = _wahrheitswert(roh)
            if wert is not None:
                werte[name] = wert
        elif "int" in erwartet and "float" not in erwartet:
            try:
                werte[name] = int(float(str(roh)))
            except (TypeError, ValueError):
                unbekannt.append(name)
        elif "float" in erwartet:
            try:
                werte[name] = float(str(roh))
            except (TypeError, ValueError):
                unbekannt.append(name)
        elif roh not in (None, ""):
            werte[name] = str(roh)[:500]

    return Systembeschreibung(**werte), tuple(sorted(set(unbekannt)))


def _fehlerantwort(zustandscode: int, satz: str, hinweis: str = "") -> JSONResponse:
    return JSONResponse(
        status_code=zustandscode, content=Fehlerantwort(fehler=satz, hinweis=hinweis).model_dump()
    )


# ------------------------------------------------------------- Die Anwendung


def anwendung_bauen() -> FastAPI:
    """Baut den Dienst. Als Funktion, damit Prüfläufe eigene Abläufe starten können."""

    logging.getLogger().addFilter(SchluesselFilter())

    @asynccontextmanager
    async def lebenslauf(app: FastAPI) -> AsyncIterator[None]:
        app.state.zustand = zustand_laden()
        app.state.zaehler = zaehler_aus_umgebung()
        yield
        # Nichts freizugeben: alles liegt im Speicher und geht mit dem Ablauf.

    dienst = FastAPI(
        title="Konformitätshelfer",
        description="Belegte Auskunft zur KI-Verordnung und zum Datenschutzrecht. "
        "Keine Rechtsberatung.",
        version="1.0.0",
        lifespan=lebenslauf,
        # Die Fehlersuchseiten von FastAPI zeigen Innereien — abgeschaltet.
        debug=False,
    )

    herkunft = [
        h.strip()
        for h in os.environ.get("HELFER_HERKUNFT", ",".join(VORGABE_HERKUNFT)).split(",")
        if h.strip()
    ]
    dienst.add_middleware(
        CORSMiddleware,
        allow_origins=herkunft,  # keine Sternchen: fremde Seiten dürfen nicht
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    # ---------------------------------------------------------- Zwischenschicht

    @dienst.middleware("http")
    async def takt_und_grenze(anfrage: Request, weiter: Callable) -> Response:
        """Zählt Anfragen je Adresse und misst die Zeit."""
        adresse = anfrage.client.host if anfrage.client else "unbekannt"
        # Die Oberfläche und die Zustandsabfrage bleiben frei: ein Prüfprogramm,
        # das jede Minute fragt, soll sich nicht selbst aussperren.
        if anfrage.url.path.startswith("/api/"):
            zaehler = getattr(dienst.state, "zaehler", None)
            if zaehler is not None:
                erlaubt, warten = zaehler.pruefen(adresse)
                if not erlaubt:
                    antwort = _fehlerantwort(
                        429,
                        zaehler.meldung(warten),
                        "Die Grenze schützt den Dienst vor Überlast. Sie lässt "
                        "sich über HELFER_ANFRAGEN_JE_MINUTE ändern.",
                    )
                    antwort.headers["Retry-After"] = str(warten)
                    return antwort

        beginn = time.perf_counter()
        try:
            antwort = await weiter(anfrage)
        except Exception as fehler:
            # Letzte Auffanglinie. Was hier ankommt, darf nach außen nur als
            # Satz, nicht als Rückverfolgung.
            protokoll.exception(
                "Unbehandelter Fehler auf %s: %s",
                protokollsicher(anfrage.url.path),
                protokollsicher(fehler),
            )
            return _fehlerantwort(
                500,
                "Im Dienst ist ein unerwarteter Fehler aufgetreten.",
                "Die Einzelheiten stehen im Protokoll des Betreibers. Bitte "
                "die Anfrage erneut senden oder den Betreiber verständigen.",
            )
        dauer = int((time.perf_counter() - beginn) * 1000)
        antwort.headers["X-Dauer-ms"] = str(dauer)
        fertig: Response = antwort
        return fertig

    # ---------------------------------------------------------- Fehlerbehandlung

    @dienst.exception_handler(Eingabefehler)
    async def eingabefehler(_a: Request, fehler: Eingabefehler) -> JSONResponse:
        return _fehlerantwort(400, str(fehler))

    @dienst.exception_handler(RequestValidationError)
    async def formfehler(_a: Request, fehler: RequestValidationError) -> JSONResponse:
        """Übersetzt die englischen Meldungen der Formprüfung ins Deutsche.

        Die Meldungen von Pydantic nennen interne Feldwege und englische
        Begriffe. Was der Nutzer braucht, ist: welches Feld, was ist daran falsch.
        """
        teile: list[str] = []
        for punkt in fehler.errors()[:6]:
            ort = ".".join(str(t) for t in punkt.get("loc", ()) if t != "body")
            art = str(punkt.get("type", ""))
            if art == "json_invalid":
                teile.append("Der Inhalt der Anfrage ist kein gültiges JSON.")
            elif art == "missing":
                teile.append("Das Feld %r fehlt." % (ort or "?"))
            elif "too_long" in art or "max_length" in art:
                teile.append(f"Das Feld {ort!r} ist zu lang.")
            elif "too_short" in art or "min_length" in art:
                teile.append(f"Das Feld {ort!r} ist zu kurz oder leer.")
            elif art == "extra_forbidden":
                teile.append(f"Das Feld {ort!r} kennt der Dienst nicht.")
            elif "enum" in art:
                teile.append(f"Das Feld {ort!r} hat einen Wert, der nicht vorgesehen ist.")
            else:
                teile.append("Das Feld %r hat einen unzulässigen Wert." % (ort or "?"))
        return _fehlerantwort(
            422,
            " ".join(teile) or "Die Anfrage hat nicht die erwartete Form.",
            "Die erwartete Form steht unter /openapi.json.",
        )

    @dienst.exception_handler(StarletteHTTPException)
    async def httpfehler(_a: Request, fehler: StarletteHTTPException) -> JSONResponse:
        """Die Meldungen von Starlette sind englisch — hier werden sie deutsch.

        Sonst steht im einen Fall ein deutscher Satz und im anderen
        ``{"detail": "Not Found"}``; wer die Schnittstelle anspricht, müsste
        beide Formen behandeln.
        """
        saetze = {
            404: ("Diesen Weg gibt es nicht.", "Die vorhandenen Wege stehen unter /openapi.json."),
            405: (
                "Dieser Weg nimmt dieses Verfahren nicht an.",
                "Die Auskunftswege werden mit POST angesprochen, der "
                "Fragebogen und die Fristen mit GET.",
            ),
            413: ("Die Anfrage ist zu groß.", ""),
            429: ("Zu viele Anfragen.", ""),
        }
        satz, hinweis = saetze.get(
            fehler.status_code,
            (f"Die Anfrage konnte nicht bearbeitet werden (Code {fehler.status_code:d}).", ""),
        )
        return _fehlerantwort(fehler.status_code, satz, hinweis)

    @dienst.exception_handler(Exception)
    async def alles_andere(anfrage: Request, fehler: Exception) -> JSONResponse:
        protokoll.exception(
            "Fehler auf %s: %s", protokollsicher(anfrage.url.path), protokollsicher(fehler)
        )
        return _fehlerantwort(
            500,
            "Im Dienst ist ein unerwarteter Fehler aufgetreten.",
            "Die Einzelheiten stehen im Protokoll des Betreibers.",
        )

    # --------------------------------------------------------------- Oberfläche

    vorlagen = Jinja2Templates(directory=str(OBERFLAECHE / "vorlagen"))
    dienst.mount(
        "/gestaltung", StaticFiles(directory=str(OBERFLAECHE / "gestaltung")), name="gestaltung"
    )

    @dienst.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def oberflaeche(anfrage: Request) -> Response:
        z: Zustand = dienst.state.zustand
        return vorlagen.TemplateResponse(
            anfrage,
            "seite.html",
            {
                "stand_korpus": z.stand_korpus,
                "stand_regeln": z.stand_regeln,
                "einheiten": len(z.einheiten),
                # Deutsche Tausendertrennung von Hand: locale umzustellen wäre ein
                # Eingriff in den ganzen Ablauf, nur um einen Punkt zu setzen.
                "einheiten_text": f"{len(z.einheiten):,}".replace(",", "."),
                "einbettungsmodell": z.einbettungsmodell,
                "sprachmodell": z.sprachmodell_name,
                "fristenvorbehalt": regelwerk().fristenvorbehalt,
                "standhinweis": regelwerk().standhinweis,
                "warnungen": z.warnungen,
                "fragebogen": FRAGEBOGEN,
                "fragebogen_hinweis": FRAGEBOGEN_HINWEIS,
            },
        )

    # --------------------------------------------------------------- Zustand

    @dienst.get("/gesundheit", response_model=Gesundheit, summary="Zustand des Dienstes")
    async def gesundheit() -> Gesundheit:
        z: Zustand = dienst.state.zustand
        return Gesundheit(
            zustand=z.zustandswort,  # type: ignore[arg-type]
            korpus_geladen=bool(z.einheiten),
            bestand_geladen=z.bestand is not None,
            einheiten=len(z.einheiten),
            einbettungsmodell=z.einbettungsmodell,
            sprachmodell=z.sprachmodell_name,
            stand_korpus=z.stand_korpus,
            stand_regeln=z.stand_regeln,
            bestand_aus_datei=z.bestand_aus_datei,
            neubewertung=neubewertung_an(),
            startdauer_ms=z.startdauer_ms,
            laufzeit_sekunden=int(time.time() - z.gestartet),
            warnungen=tuple(z.warnungen),
        )

    # ------------------------------------------------------------ Einstufung

    @dienst.post(
        "/api/einstufung",
        response_model=EinstufungAntwort,
        summary="Nur die Einstufung, ohne Sprachmodell",
    )
    async def einstufung(anfrage: EinstufungAnfrage) -> EinstufungAntwort:
        z: Zustand = dienst.state.zustand
        if z.pruefer is None:
            raise Eingabefehler(
                "Der Prüfer ist nicht geladen. Der Dienst ist nicht betriebsbereit "
                "— der Zustand steht unter /gesundheit."
            )
        beginn = time.perf_counter()
        beschreibung, unbekannt = beschreibung_bauen(anfrage)
        ergebnis = z.pruefer.pruefen(beschreibung)
        return EinstufungAntwort(
            einstufung=ergebnis,
            schwerste_klasse=ergebnis.schwerste,
            schwerste_klartext=ergebnis.schwerste.klartext,
            klassen_klartext=_klartext_klassen(ergebnis.klassen),
            rollen_klartext=_klartext_rollen(ergebnis.rollen),
            nicht_erkannte_merkmale=unbekannt,
            stand_regeln=z.stand_regeln,
            fristenvorbehalt=regelwerk().fristenvorbehalt,
            dauer_ms=int((time.perf_counter() - beginn) * 1000),
        )

    # ----------------------------------------------------------------- Suche

    @dienst.post(
        "/api/suche", response_model=SucheAntwort, summary="Nur die Suche im Rechtsbestand"
    )
    async def suche(anfrage: SucheAnfrage) -> SucheAntwort:
        z: Zustand = dienst.state.zustand
        if z.bestand is None:
            raise Eingabefehler(
                "Der Suchbestand ist nicht geladen — der Zustand steht unter /gesundheit."
            )
        beginn = time.perf_counter()
        frage = frage_pruefen(anfrage.frage)
        treffer = z.bestand.suchen(
            frage,
            anzahl=anfrage.anzahl,
            nur_rechtsakte=anfrage.nur_rechtsakte,
            mit_neubewertung=neubewertung_an(),
        )
        warnungen: list[str] = []
        if z.bestand.einbetter.name == Streuwerk.name:
            warnungen.append(
                "Die Suche läuft mit dem Ersatzmodell und vergleicht nur Wörter, "
                "nicht Bedeutung. Die Fundstellen sind deshalb schlechter."
            )
        return SucheAntwort(
            frage=frage,
            belege=als_belegstellen(treffer),
            einbettungsmodell=z.bestand.einbetter.name,
            dauer_ms=int((time.perf_counter() - beginn) * 1000),
            warnungen=tuple(warnungen),
        )

    # ----------------------------------------------------------------- Frage

    @dienst.post(
        "/api/frage",
        response_model=FrageAntwort,
        summary="Die volle Auskunft: Einstufung, Pflichten, Belege",
    )
    async def frage_stellen(anfrage: FrageAnfrage) -> FrageAntwort:
        z: Zustand = dienst.state.zustand
        if z.bestand is None or z.pruefer is None:
            raise Eingabefehler(
                "Der Dienst ist nicht betriebsbereit — der Zustand steht unter /gesundheit."
            )
        beginn = time.perf_counter()
        frage = frage_pruefen(anfrage.frage)
        beschreibungstext = beschreibung_pruefen(anfrage.beschreibung)

        # Ohne eigene Beschreibung wird die Frage selbst geprüft: wer fragt
        # "Dürfen wir Bewerbungen vorsortieren?", beschreibt damit sein System.
        beschreibung = beschreibung_aus_text(beschreibungstext or frage)
        ergebnis = z.pruefer.pruefen(beschreibung)

        suchtext = f"{frage}\n{beschreibungstext}" if beschreibungstext else frage
        treffer = z.bestand.suchen(
            suchtext[:4000],
            anzahl=anfrage.anzahl_belege,
            nur_rechtsakte=anfrage.nur_rechtsakte,
            mit_neubewertung=neubewertung_an(),
        )
        belege = als_belegstellen(treffer)
        lernhinweis, faelle = _lernhinweis_und_faelle([t.einheit for t in treffer])

        # Der Modellwunsch je Anfrage: "ohne" erzwingt die Regelantwort, ein
        # anderer Name als der beim Start gewählte lässt neu wählen.
        wunsch = (anfrage.modell or "").strip().lower()
        modell = z.sprachmodell
        if wunsch in ("ohne", "keines", "regelwerk"):
            modell = None
        elif wunsch and wunsch != "auto" and (modell is None or not modell.name.startswith(wunsch)):
            modell = modell_waehlen(wunsch)

        antwort = formulieren(
            frage,
            beschreibungstext,
            ergebnis,
            belege,
            modell=modell,
            lernhinweis=lernhinweis,
            beispielfaelle=faelle,
        )
        dauer = int((time.perf_counter() - beginn) * 1000)
        antwort = antwort.model_copy(update={"dauer_ms": dauer})

        return FrageAntwort(
            antwort=antwort,
            schwerste_klasse=ergebnis.schwerste,
            schwerste_klartext=ergebnis.schwerste.klartext,
            klassen_klartext=_klartext_klassen(ergebnis.klassen),
            rollen_klartext=_klartext_rollen(ergebnis.rollen),
            stand_regeln=z.stand_regeln,
            stand_korpus=z.stand_korpus,
            fristenvorbehalt=regelwerk().fristenvorbehalt,
            dauer_ms=dauer,
        )

    # ------------------------------------------------------------ Fragebogen

    @dienst.get(
        "/api/fragebogen", response_model=Fragebogen, summary="Die Fragen, die der Prüfer stellt"
    )
    async def fragebogen() -> Fragebogen:
        return Fragebogen(punkte=FRAGEBOGEN, hinweis=FRAGEBOGEN_HINWEIS)

    # --------------------------------------------------------------- Fristen

    @dienst.get(
        "/api/fristen",
        response_model=Fristen,
        summary="Die Geltungsdaten nach Artikel 113 samt Vorbehalt",
    )
    async def fristen() -> Fristen:
        werk = regelwerk()
        roh = werk.risikoklassen.get("fristen") or {}
        heute = date.today()
        stufen: list[Fristenstufe] = []
        for stufe in werk.fristen:
            datum = stufe.get("datum")
            if not isinstance(datum, date):
                try:
                    datum = date.fromisoformat(str(datum))
                except ValueError:
                    continue
            stufen.append(
                Fristenstufe(
                    datum=datum,
                    was=" ".join(str(stufe.get("was", "")).split()),
                    schon_in_kraft=datum <= heute,
                )
            )
        return Fristen(
            fundstelle=str(roh.get("fundstelle", "Artikel 113 KI-VO")),
            rechtsgrundlage=tuple(roh.get("rechtsgrundlage", ["KI-VO/art-113"])),
            stufen=tuple(sorted(stufen, key=lambda s: s.datum)),
            vorbehalt=" ".join(werk.fristenvorbehalt.split()),
            stand_regeln=werk.stand,
            hinweis_zum_stand=" ".join(werk.standhinweis.split()),
        )

    return dienst


#: Für ``uvicorn helfer.dienst.anwendung:dienst``. Der Aufbau passiert hier
#: beim Einlesen, das Laden erst im Lebenslauf — darum kostet das nichts.
dienst = anwendung_bauen()


def starten(adresse: str = "127.0.0.1", port: int = 8000, neuladen: bool = False) -> None:
    """Startet den Dienst. Vorgabe ist der eigene Rechner, nicht alle Netze.

    Wer von außen erreichbar sein will, muss es ausdrücklich sagen — ein Dienst,
    der ungefragt auf 0.0.0.0 hört, ist ein Dienst im Netz, ohne dass es jemand
    beschlossen hat. Im Container ist 0.0.0.0 richtig, dort steht es im Befehl.
    """
    import uvicorn

    uvicorn.run(
        "helfer.dienst.anwendung:dienst" if neuladen else dienst,
        host=adresse,
        port=port,
        reload=neuladen,
        log_level="info",
    )
