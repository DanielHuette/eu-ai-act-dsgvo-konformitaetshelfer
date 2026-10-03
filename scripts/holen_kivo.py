"""Holt die KI-Verordnung artikelweise als Rückfallquelle.

Erste Wahl ist der amtliche Volltext aus EUR-Lex (holen_eurlex.py). Weil
EUR-Lex nach wenigen Anfragen bremst, holt dieses Skript denselben Text aus der
Einzelansicht von artificialintelligenceact.eu - einer verbreiteten Fassung des
Verordnungstexts mit je einer Seite pro Artikel, Anhang und Erwägungsgrund.

Die Seiten tragen viel Beiwerk (Navigation, Inhaltsübersicht, Werbebanner).
Deshalb wird nicht der ganze Seitentext genommen, sondern der Bereich zwischen
der Artikelüberschrift und dem Beginn des nächsten Gliederungsblocks.

Ergebnis: daten/roh/kivo/{artikel,anhang,erwaegung}/*.json
Protokoll: daten/roh/kivo/_holen.log
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "daten" / "roh" / "kivo"
KOPF = {"User-Agent": "Mozilla/5.0 (kompatibel; Konformitaetshelfer/1.0)"}
PAUSE = 0.4

ARTIKEL = 113
ERWAEGUNG = 180
ANHAENGE = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI", "XII", "XIII"]

# Zeilen, die zum Beiwerk der Seite gehören und nie Teil des Rechtstexts sind.
BEIWERK = re.compile(
    r"^(BETA|Zum neuen AI Act Explorer|← ?Zurück zum Index|Inhaltsübersicht|"
    r"🔔 ?Neu:|Lesen Sie den offiziellen Text|Vergleichen Sie die Sprachversionen|"
    r"Ein individueller KI-Chatbot|Suche|Menü|Teilen|Drucken|Feedback|"
    r"Kapitel [IVXLC]+:|Abschnitt \d|Anhang [IVXLC]+:|Erwägungsgrund \d+$|"
    r"Artikel \d+:.*$)",
    re.IGNORECASE,
)

protokoll: list[str] = []


def _nur_https(adresse: str) -> str:
    """Lässt nur https-Adressen durch — und gibt sie unverändert zurück.

    ``urllib.request.urlopen`` nimmt auch ``file://`` und ``ftp://``. Die
    Adressen hier stehen fest im Quelltext, aber geprüft wird trotzdem: eine
    Zeichenkette, die in einen Netzaufruf geht, gehört geprüft, bevor sie
    hineingeht — und die Prüfung bleibt richtig, wenn die Adressen später
    einmal aus einer Datei kommen.
    """
    if not adresse.startswith("https://"):
        raise ValueError(f"Nur https ist erlaubt, bekommen: {adresse!r}")
    return adresse


def sagen(text: str) -> None:
    protokoll.append(text)
    (ZIEL / "_holen.log").write_text("\n".join(protokoll) + "\n", encoding="utf-8")
    print(text, flush=True)


def holen(adresse: str, versuche: int = 3) -> str | None:
    for versuch in range(versuche):
        try:
            req = urllib.request.Request(_nur_https(adresse), headers=KOPF)
            with urllib.request.urlopen(
                req,  # nosec B310
                timeout=45,
            ) as antwort:
                return antwort.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as fehler:
            if fehler.code == 404:
                return None
            time.sleep(2 * (versuch + 1))
        except Exception:
            time.sleep(2 * (versuch + 1))
    return None


def inhalt_schneiden(html: str, _ueberschrift_muster: str = "") -> tuple[str, str]:
    """Liefert (Titel, Text) - nur der Teil, der zur Einheit gehört.

    ``_ueberschrift_muster`` wird nicht mehr gebraucht: der erste Entwurf
    schnitt den Text an einem Textmuster für die Überschrift ab, und genau das
    war der Fehler, der aus 113 Artikeln 132 machte - ein Querverweis im
    Fließtext ("Artikel 99") sah wie ein Artikelanfang aus. Geschnitten wird
    seither an der Gliederung der Seite. Das Argument bleibt stehen, weil die
    drei Aufrufer es übergeben und ihre Zeilen ohne Not nicht angerührt werden;
    der Unterstrich sagt, dass es ohne Wirkung ist.
    """
    suppe = BeautifulSoup(html, "lxml")
    for weg in suppe(
        ["script", "style", "nav", "footer", "header", "aside", "form", "noscript", "iframe"]
    ):
        weg.decompose()

    titel = ""
    kopf = suppe.find("h1")
    if kopf:
        titel = re.sub(r"\s*\|.*$", "", kopf.get_text(" ", strip=True)).strip()

    # Der Rechtstext steckt in Absätzen und Listen unterhalb der Überschrift.
    kandidaten: list[str] = []
    bereich = suppe.find("article") or suppe.find("main") or suppe
    for knoten in bereich.find_all(["p", "li", "h2", "h3", "h4", "td"]):
        text = knoten.get_text(" ", strip=True)
        text = re.sub(r"[ \t ]+", " ", text).strip()
        if not text or len(text) < 3:
            continue
        if BEIWERK.match(text):
            continue
        if text.startswith("Artikel ") and len(text) < 90 and ":" in text:
            continue
        kandidaten.append(text)

    # Doppelte Zeilen (Inhaltsübersicht wiederholt oft den Text) einmal halten.
    gesehen: set[str] = set()
    zeilen: list[str] = []
    for zeile in kandidaten:
        schluessel = zeile[:120]
        if schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        zeilen.append(zeile)

    text = "\n\n".join(zeilen)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return titel, text


def schreiben(ordner: str, name: str, satz: dict) -> None:
    ziel = ZIEL / ordner / (f"{name}.json")
    ziel.write_text(json.dumps(satz, ensure_ascii=False, indent=1), encoding="utf-8")


def main() -> None:
    for ordner in ("artikel", "anhang", "erwaegung"):
        (ZIEL / ordner).mkdir(parents=True, exist_ok=True)
    beginn = time.time()
    sagen("HOLEN KI-VERORDNUNG - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))
    fehlend: list[str] = []

    for nummer in range(1, ARTIKEL + 1):
        if (ZIEL / "artikel" / ("art-%03d.json" % nummer)).exists():
            continue
        html = holen(f"https://artificialintelligenceact.eu/de/article/{nummer:d}/")
        if not html:
            fehlend.append(f"Artikel {nummer:d}")
            continue
        titel, text = inhalt_schneiden(html, rf"Artikel {nummer:d}")
        schreiben(
            "artikel",
            "art-%03d" % nummer,
            {
                "rechtsakt": "KI-VO",
                "rechtsakt_lang": "Verordnung (EU) 2024/1689 über künstliche Intelligenz",
                "einheit": "artikel",
                "nummer": str(nummer),
                "titel": titel,
                "text": text,
                "quelle": f"https://artificialintelligenceact.eu/de/article/{nummer:d}/",
            },
        )
        if nummer % 15 == 0:
            sagen(f"  Artikel {nummer:d}/{ARTIKEL:d}")
        time.sleep(PAUSE)

    for zahl in ANHAENGE:
        if (ZIEL / "anhang" / (f"anh-{zahl}.json")).exists():
            continue
        roemisch = {
            "I": 1,
            "II": 2,
            "III": 3,
            "IV": 4,
            "V": 5,
            "VI": 6,
            "VII": 7,
            "VIII": 8,
            "IX": 9,
            "X": 10,
            "XI": 11,
            "XII": 12,
            "XIII": 13,
        }[zahl]
        html = holen(f"https://artificialintelligenceact.eu/de/annex/{roemisch:d}/")
        if not html:
            fehlend.append(f"Anhang {zahl}")
            continue
        titel, text = inhalt_schneiden(html, rf"Anhang {zahl}")
        schreiben(
            "anhang",
            f"anh-{zahl}",
            {
                "rechtsakt": "KI-VO",
                "rechtsakt_lang": "Verordnung (EU) 2024/1689 über künstliche Intelligenz",
                "einheit": "anhang",
                "nummer": zahl,
                "titel": titel,
                "text": text,
                "quelle": f"https://artificialintelligenceact.eu/de/annex/{roemisch:d}/",
            },
        )
        time.sleep(PAUSE)
    sagen("  Anhänge geholt")

    for nummer in range(1, ERWAEGUNG + 1):
        if (ZIEL / "erwaegung" / ("erw-%03d.json" % nummer)).exists():
            continue
        html = holen(f"https://artificialintelligenceact.eu/de/recital/{nummer:d}/")
        if not html:
            fehlend.append(f"Erwägungsgrund {nummer:d}")
            continue
        titel, text = inhalt_schneiden(html, rf"Erwägungsgrund {nummer:d}")
        schreiben(
            "erwaegung",
            "erw-%03d" % nummer,
            {
                "rechtsakt": "KI-VO",
                "rechtsakt_lang": "Verordnung (EU) 2024/1689 über künstliche Intelligenz",
                "einheit": "erwaegungsgrund",
                "nummer": str(nummer),
                "titel": f"Erwägungsgrund {nummer:d}",
                "text": text,
                "quelle": f"https://artificialintelligenceact.eu/de/recital/{nummer:d}/",
            },
        )
        if nummer % 30 == 0:
            sagen(f"  Erwägungsgrund {nummer:d}/{ERWAEGUNG:d}")
        time.sleep(PAUSE)

    sagen("")
    for ordner, soll in (("artikel", ARTIKEL), ("anhang", len(ANHAENGE)), ("erwaegung", ERWAEGUNG)):
        sagen("%s: %d von %d" % (ordner, len(list((ZIEL / ordner).glob("*.json"))), soll))
    if fehlend:
        sagen("FEHLEND: {}".format(", ".join(fehlend[:40])))
    sagen("Dauer: %.0f s" % (time.time() - beginn))
    sagen("FERTIG")


if __name__ == "__main__":
    main()
