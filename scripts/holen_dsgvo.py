"""Holt die Datenschutz-Grundverordnung absatzgenau.

Der amtliche Volltext aus dem Amtsblatt ist die erste Wahl, EUR-Lex sperrt
maschinelle Zugriffe aber mit einer Bot-Abwehr. Diese Quelle liefert dieselbe
deutsche Fassung je Artikel auf einer eigenen Seite — und zwar so, dass die
Absätze erkennbar bleiben: der Normtext steht als Listenpunkte einer Liste im
Inhaltsbereich, ein Listenpunkt ist ein Absatz.

Deshalb wird hier nicht der Seitentext gespeichert, sondern die Gliederung:
Absatz für Absatz. Nur so kann eine Auskunft später auf "Artikel 35 Absatz 3
Buchstabe a" zeigen statt auf "irgendwo in Artikel 35".

Das Seitenbeiwerk trägt eigene Klassen (``empfehlung-erwaegungsgruende``,
``page-navigation``, ``feedback``) und wird daran entfernt — nicht an Textmustern.

Aufruf:
    python scripts/holen_dsgvo.py          # holt, was fehlt
    python scripts/holen_dsgvo.py --neu    # holt alles neu

Ergebnis: daten/roh/dsgvo/artikel/art-NN.json mit Feld "absaetze"
Protokoll: daten/roh/dsgvo/_holen.log
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

from bs4 import BeautifulSoup, Tag

WURZEL = Path(__file__).resolve().parent.parent
ZIEL = WURZEL / "daten" / "roh" / "dsgvo"
KOPF = {"User-Agent": "Mozilla/5.0 (kompatibel; Konformitaetshelfer/1.0)"}
PAUSE = 0.35
ARTIKEL = 99
ERWAEGUNG = 173

#: Blöcke, die zur Webseite gehören und nicht zum Normtext.
BEIWERK = (
    "empfehlung-erwaegungsgruende",
    "empfehlung-bdsg-paragraphen",
    "empfehlung-dsgvo-artikel",
    "page-navigation",
    "link-to-overview",
    "feedback",
    "hidden-print",
    "widget",
    "widget-area",
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
                timeout=40,
            ) as antwort:
                return antwort.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as fehler:
            if fehler.code == 404:
                return None
            time.sleep(1.5 * (versuch + 1))
        except Exception:
            time.sleep(1.5 * (versuch + 1))
    return None


def _saeubern(text: str) -> str:
    text = text.replace(" ", " ").replace("‑", "-")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _inhaltsbereich(html: str) -> Tag | None:
    suppe = BeautifulSoup(html, "lxml")
    for weg in suppe(["script", "style", "noscript", "nav", "footer", "header", "form"]):
        weg.decompose()
    bereich = suppe.select_one("div.entry-content") or suppe.find("article")
    if bereich is None:
        return None
    for klasse in BEIWERK:
        for weg in bereich.select(f"[class*={klasse}]"):
            weg.decompose()
    return bereich


def absaetze_lesen(html: str) -> tuple[list[dict], str]:
    """Liefert (Absätze, Volltext). Ein Absatz ist ein Listenpunkt der Norm."""
    bereich = _inhaltsbereich(html)
    if bereich is None:
        return [], ""

    absaetze: list[dict] = []
    liste = bereich.find("ol", recursive=False) or bereich.find("ol")
    if liste is not None:
        for nummer, punkt in enumerate(liste.find_all("li", recursive=False), 1):
            # Buchstabenpunkte stehen als verschachtelte Liste darin.
            unterpunkte = []
            for unter in punkt.find_all(["ol", "ul"], recursive=False):
                for stelle, zeile in enumerate(unter.find_all("li", recursive=False)):
                    buchstabe = chr(ord("a") + stelle)
                    inhalt = _saeubern(zeile.get_text(" ", strip=True))
                    if len(inhalt) > 20:
                        unterpunkte.append({"buchstabe": buchstabe, "text": inhalt})
                unter.decompose()
            text = _saeubern(punkt.get_text(" ", strip=True))
            if len(text) < 15 and not unterpunkte:
                continue
            absaetze.append({"nummer": str(nummer), "text": text, "buchstaben": unterpunkte})
    volltext = _saeubern(bereich.get_text("\n"))
    return absaetze, volltext


def inhaltsverzeichnis() -> dict[str, dict]:
    """Kapitel, Abschnitt und Titel je Artikel aus der Startseite."""
    html = holen("https://dsgvo-gesetz.de/")
    if not html:
        return {}
    suppe = BeautifulSoup(html, "lxml")
    karte: dict[str, dict] = {}
    kapitel = abschnitt = ""
    for knoten in suppe.find_all(["h2", "h3", "h4", "a"]):
        text = _saeubern(knoten.get_text(" ", strip=True))
        if not text:
            continue
        if re.match(r"^Kapitel\s+\d+", text):
            kapitel, abschnitt = text, ""
            continue
        if re.match(r"^Abschnitt\s+\d+", text):
            abschnitt = text
            continue
        treffer = re.match(r"^Artikel\s+(\d{1,3})\s*[:\-–]?\s*(.*)$", text)
        if treffer:
            nummer, titel = treffer.group(1), treffer.group(2).strip()
            if nummer not in karte or (titel and not karte[nummer]["titel"]):
                karte[nummer] = {"titel": titel, "kapitel": kapitel, "abschnitt": abschnitt}
    return karte


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser()
    zerleger.add_argument("--neu", action="store_true", help="alles neu holen")
    args = zerleger.parse_args(argv)

    (ZIEL / "artikel").mkdir(parents=True, exist_ok=True)
    (ZIEL / "erwaegung").mkdir(parents=True, exist_ok=True)
    beginn = time.time()
    sagen("HOLEN DSGVO - {}".format(time.strftime("%Y-%m-%d %H:%M:%S")))

    karte = inhaltsverzeichnis()
    sagen(f"Inhaltsverzeichnis: {len(karte):d} Artikeltitel")
    (ZIEL / "inhaltsverzeichnis.json").write_text(
        json.dumps(karte, ensure_ascii=False, indent=1), encoding="utf-8"
    )

    fehlend: list[str] = []
    ohne_absaetze: list[str] = []

    for nummer in range(1, ARTIKEL + 1):
        ziel = ZIEL / "artikel" / ("art-%02d.json" % nummer)
        if ziel.exists() and not args.neu:
            try:
                if json.loads(ziel.read_text(encoding="utf-8")).get("absaetze"):
                    continue
            except (OSError, json.JSONDecodeError):
                pass
        adresse = f"https://dsgvo-gesetz.de/art-{nummer:d}-dsgvo/"
        html = holen(adresse)
        if not html:
            fehlend.append(f"Artikel {nummer:d}")
            continue
        absaetze, volltext = absaetze_lesen(html)
        if not absaetze:
            ohne_absaetze.append(str(nummer))
        kopf = karte.get(str(nummer), {})
        ziel.write_text(
            json.dumps(
                {
                    "rechtsakt": "DSGVO",
                    "rechtsakt_lang": "Verordnung (EU) 2016/679 (Datenschutz-Grundverordnung)",
                    "einheit": "artikel",
                    "nummer": nummer,
                    "titel": kopf.get("titel", ""),
                    "kapitel": kopf.get("kapitel", ""),
                    "abschnitt": kopf.get("abschnitt", ""),
                    "quelle": adresse,
                    "text": volltext,
                    "absaetze": absaetze,
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        if nummer % 15 == 0:
            sagen(f"  Artikel {nummer:d}/{ARTIKEL:d}")
        time.sleep(PAUSE)

    for nummer in range(1, ERWAEGUNG + 1):
        ziel = ZIEL / "erwaegung" / ("erw-%03d.json" % nummer)
        if ziel.exists() and not args.neu:
            continue
        adresse = f"https://dsgvo-gesetz.de/erwaegungsgruende/nr-{nummer:d}/"
        html = holen(adresse)
        if not html:
            fehlend.append(f"Erwägungsgrund {nummer:d}")
            continue
        _, volltext = absaetze_lesen(html)
        ziel.write_text(
            json.dumps(
                {
                    "rechtsakt": "DSGVO",
                    "rechtsakt_lang": "Verordnung (EU) 2016/679 (Datenschutz-Grundverordnung)",
                    "einheit": "erwaegungsgrund",
                    "nummer": nummer,
                    "titel": f"Erwägungsgrund {nummer:d}",
                    "quelle": adresse,
                    "text": volltext,
                    "absaetze": [],
                },
                ensure_ascii=False,
                indent=1,
            ),
            encoding="utf-8",
        )
        if nummer % 40 == 0:
            sagen(f"  Erwägungsgrund {nummer:d}/{ERWAEGUNG:d}")
        time.sleep(PAUSE)

    sagen("")
    sagen("Artikel: %d von %d" % (len(list((ZIEL / "artikel").glob("*.json"))), ARTIKEL))
    sagen(
        "Erwägungsgründe: %d von %d" % (len(list((ZIEL / "erwaegung").glob("*.json"))), ERWAEGUNG)
    )
    if ohne_absaetze:
        sagen("ohne erkannte Absätze (einteilige Artikel): {}".format(", ".join(ohne_absaetze)))
    if fehlend:
        sagen("FEHLEND: {}".format(", ".join(fehlend[:40])))
    sagen("Dauer: %.0f s" % (time.time() - beginn))
    sagen("FERTIG")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
