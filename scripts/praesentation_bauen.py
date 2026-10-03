"""Baut aus den einzelnen Folien eine eigenständige HTML-Präsentation.

Die Folien liegen einzeln unter ``praesentation/folien/`` — eine Datei je
Folie, jede ein ``<section>`` auf einer Fläche von 1920 auf 1080 Punkten, alle
Angaben unmittelbar am Element. ``praesentation/deck.json`` nennt die
Reihenfolge und die Schriften.

Dieses Skript setzt daraus eine einzelne Datei zusammen: ``docs/praesentation.html``.
Sie läuft in jedem Browser, ohne Netz und ohne Dienst, blättert mit den
Pfeiltasten und druckt eine Folie je Seite.

Warum einzelne Folien und nicht gleich eine Datei: eine Folie ist dann eine
überschaubare Einheit, die man ändern kann, ohne die anderen anzufassen — und
die Reihenfolge steht an einer Stelle statt in der Reihenfolge des Textes.

Aufruf:
    python scripts/praesentation_bauen.py
    python scripts/praesentation_bauen.py --messen   # zusätzlich nachmessen
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
FOLIEN = WURZEL / "praesentation" / "folien"
INDEX = WURZEL / "praesentation" / "deck.json"
ZIEL = WURZEL / "docs" / "praesentation.html"

#: Eine Folie ist so groß entworfen. Die Seite rechnet sie auf die Breite des
#: Fensters herunter, damit sie überall so aussieht wie gemeint.
BREITE, HOEHE = 1920, 1080


def folien_lesen(index: dict) -> list[tuple[str, str, str]]:
    """Liest die Folien in der Reihenfolge des Index: (Kennung, Abschnitt, Notiz)."""
    gelesen: list[tuple[str, str, str]] = []
    for kennung in index["order"]:
        datei = FOLIEN / f"{kennung}.html"
        if not datei.exists():
            raise SystemExit(f"Folie fehlt: {datei}")
        roh = datei.read_text(encoding="utf-8")

        # Die Sprechernotizen stehen im Abschnitt; auf der Seite stehen sie
        # darunter, damit man sie beim Vortrag mitlesen und ausblenden kann.
        notiz = ""
        treffer = re.search(r"<aside>(.*?)</aside>", roh, re.S)
        if treffer:
            notiz = treffer.group(1).strip()
            roh = roh[: treffer.start()] + roh[treffer.end() :]

        # Die data-Angaben des Folienformats steuern Übergänge im Vortragsmodus
        # eines anderen Werkzeugs; hier haben sie keine Wirkung.
        roh = re.sub(r'\s+data-(?:transition|section|build-in|build-out)="[^"]*"', "", roh)
        gelesen.append((kennung, roh.strip(), notiz))
    return gelesen


def seite_bauen(index: dict, folien: list[tuple[str, str, str]]) -> str:
    titel = index["title"]
    schriften = "\n".join(
        f'<link rel="stylesheet" href="{f["href"]}">'
        for f in index.get("faces", {}).values()
        if "href" in f
    )

    teile = []
    for nummer, (_kennung, abschnitt, notiz) in enumerate(folien, 1):
        zaehler = f'<p class="zaehler">{nummer} / {len(folien)}</p>'
        notizblock = f'<div class="notiz"><p>{notiz}</p></div>' if notiz else ""
        teile.append(
            f'<div class="buehne" id="folie-{nummer}">{abschnitt}{zaehler}</div>{notizblock}'
        )

    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title>
<meta name="description"
      content="Architektur, Funktionsweise und Betriebsanleitung des
               EU AI Act und DSGVO Konformitätshelfers.">
{schriften}
<style>
  :root {{ --rand: 24px; }}
  * {{ box-sizing: border-box; }}
  html, body {{ margin: 0; padding: 0; background: #11182B; }}
  body {{ font-family: 'IBM Plex Sans', Arial, sans-serif; -webkit-font-smoothing: antialiased; }}

  .kopf {{
    position: sticky; top: 0; z-index: 10;
    display: flex; flex-wrap: wrap; gap: 16px; align-items: center;
    padding: 14px var(--rand); background: #0B1220; color: #8FA3BF;
    border-bottom: 1px solid #22314F; font-size: 15px; line-height: 1.4;
  }}
  .kopf b {{ color: #FAFAF7; font-weight: 600; }}
  .kopf button {{
    font: inherit; color: #BCCBDD; background: #1B2A41; cursor: pointer;
    border: 1px solid #38496B; border-radius: 8px; padding: 6px 14px;
  }}
  .kopf button:hover {{ background: #24375A; color: #FAFAF7; }}
  .kopf .hinweis {{ margin-left: auto; }}

  .folge {{ display: flex; flex-direction: column; gap: 32px; padding: 32px var(--rand) 96px; }}

  /* Die Bühne hält das Seitenverhältnis; die Folie darin wird skaliert.
     Der Maßstab kommt aus dem Skript unten: scale() braucht eine blanke Zahl,
     und eine Breite geteilt durch {BREITE} ist in CSS eine Länge, keine Zahl.
     Ohne Skript bleibt der Maßstab 1 — dann ist die Folie in Originalgröße zu
     sehen, und die Bühne lässt sie verschieben. */
  .buehne {{
    position: relative; width: 100%; max-width: {BREITE}px; margin: 0 auto;
    aspect-ratio: 16 / 9; overflow: hidden;
    border-radius: 14px; box-shadow: 0 18px 50px rgba(0, 0, 0, .45);
  }}
  .buehne > section {{
    position: absolute; top: 0; left: 0;
    width: {BREITE}px; height: {HOEHE}px;
    transform-origin: top left; transform: scale(var(--massstab, 1));
  }}

  /* Das Folienformat kennt keine Ränder: der Abstand zwischen zwei Blöcken
     kommt allein aus dem gap des Elternelements. Ein Browser setzt aber von
     sich aus Ränder auf Überschriften, Absätze und Listen — und die summieren
     sich über eine Folie zu mehreren hundert Punkten, bis der Inhalt unten
     herausläuft. Also werden sie hier abgeräumt, genau wie es das Format
     vorsieht. */
  .buehne section :where(h1, h2, h3, h4, p, ul, ol, table, figure, blockquote) {{
    margin: 0;
  }}
  .buehne section :where(ul, ol) {{ padding-left: 1.3em; }}
  .buehne section table {{ border-collapse: collapse; }}
  .buehne section :where(td, th) {{ padding: 0.35em 0.6em; }}
  html:not(.skaliert) .buehne {{ overflow: auto; }}

  .zaehler {{
    position: absolute; right: 18px; bottom: 12px; margin: 0;
    font-size: 13px; color: rgba(138, 143, 126, .75);
  }}
  .notiz {{
    max-width: {BREITE}px; margin: -12px auto 0; padding: 18px 26px;
    background: #0B1220; border: 1px solid #22314F; border-left: 3px solid #C8742B;
    border-radius: 10px; color: #A9BBD4; font-size: 16px; line-height: 1.6;
  }}
  .notiz p {{ margin: 0; }}
  body.ohne-notizen .notiz {{ display: none; }}
  body.ohne-notizen .folge {{ gap: 28px; }}

  /* Gedruckt wird eine Folie je Seite, in Originalgröße, ohne Notizen. */
  @media print {{
    :root {{ --rand: 0; }}
    html, body {{ background: #FFFFFF; }}
    .kopf, .notiz, .zaehler {{ display: none !important; }}
    .folge {{ gap: 0; padding: 0; }}
    .buehne {{ border-radius: 0; box-shadow: none; break-after: page; }}
    @page {{ size: {BREITE}px {HOEHE}px; margin: 0; }}
  }}
</style>
</head>
<body>
<header class="kopf">
  <b>{titel}</b>
  <span>{len(folien)} Folien &middot; Stand des Rechtstextes 31.05.2026
        &middot; keine Rechtsberatung</span>
  <button type="button" id="notizschalter">Sprechernotizen ausblenden</button>
  <span class="hinweis">Blättern mit &larr; und &rarr;
        &middot; Drucken ergibt eine Folie je Seite</span>
</header>
<main class="folge">
{chr(10).join(teile)}
</main>
<script>
  (function () {{
    var buehnen = Array.prototype.slice.call(document.querySelectorAll('.buehne'));
    if (!buehnen.length) return;

    // Jede Folie ist {BREITE} auf {HOEHE} Punkte entworfen und wird hier auf die
    // Breite ihrer Bühne heruntergerechnet.
    function massstabSetzen() {{
      var breite = buehnen[0].clientWidth;
      document.documentElement.style.setProperty('--massstab', breite / {BREITE});
      document.documentElement.classList.add('skaliert');
    }}
    massstabSetzen();
    window.addEventListener('resize', massstabSetzen);
    if ('ResizeObserver' in window) new ResizeObserver(massstabSetzen).observe(buehnen[0]);

    // Beim Drucken wieder Originalgröße, danach zurück.
    if (window.matchMedia) {{
      var druck = window.matchMedia('print');
      var umschalten = function (e) {{
        if (e.matches) document.documentElement.style.setProperty('--massstab', 1);
        else massstabSetzen();
      }};
      if (druck.addEventListener) druck.addEventListener('change', umschalten);
    }}

    // Blättern heißt hier: zur nächsten Folie rollen. Kein eigener
    // Anzeigezustand, damit die Seite ohne JavaScript vollständig lesbar
    // bleibt — sie ist dann eine lange Folge von Folien.
    var stand = 0;
    function zeigen(n) {{
      stand = Math.max(0, Math.min(buehnen.length - 1, n));
      buehnen[stand].scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    }}
    document.addEventListener('keydown', function (e) {{
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === 'ArrowRight' || e.key === 'PageDown' || e.key === ' ') {{
        e.preventDefault(); zeigen(stand + 1);
      }} else if (e.key === 'ArrowLeft' || e.key === 'PageUp') {{
        e.preventDefault(); zeigen(stand - 1);
      }} else if (e.key === 'Home') {{ e.preventDefault(); zeigen(0); }}
      else if (e.key === 'End') {{ e.preventDefault(); zeigen(buehnen.length - 1); }}
    }});
    if ('IntersectionObserver' in window) {{
      var wache = new IntersectionObserver(function (eintraege) {{
        eintraege.forEach(function (e) {{
          if (e.isIntersecting) stand = buehnen.indexOf(e.target);
        }});
      }}, {{ rootMargin: '-45% 0px -45% 0px' }});
      buehnen.forEach(function (b) {{ wache.observe(b); }});
    }}

    var schalter = document.getElementById('notizschalter');
    schalter.addEventListener('click', function () {{
      var aus = document.body.classList.toggle('ohne-notizen');
      schalter.textContent = aus ? 'Sprechernotizen einblenden' : 'Sprechernotizen ausblenden';
    }});
  }})();
</script>
</body>
</html>
"""


def main(argv: list[str] | None = None) -> int:
    zerleger = argparse.ArgumentParser(description=__doc__)
    zerleger.add_argument(
        "--messen",
        action="store_true",
        help="nach dem Bauen im Browser nachsehen, ob alles auf die Folie passt",
    )
    args = zerleger.parse_args(argv)

    index = json.loads(INDEX.read_text(encoding="utf-8"))
    folien = folien_lesen(index)
    ZIEL.parent.mkdir(parents=True, exist_ok=True)
    ZIEL.write_text(seite_bauen(index, folien), encoding="utf-8")
    print(f"{ZIEL.relative_to(WURZEL)}: {len(folien)} Folien, {ZIEL.stat().st_size / 1024:.0f} KB")

    if args.messen:
        return nachmessen()
    return 0


def nachmessen() -> int:
    """Sieht im Browser nach, ob jede Folie hineinpasst.

    Eine Folie, deren Inhalt über die 1080 Punkte hinausläuft, wird beim
    Vortrag unten abgeschnitten — und das sieht man dem Text nicht an. Darum
    wird gemessen statt geschätzt.
    """
    try:
        import asyncio

        from playwright.async_api import async_playwright
    except ImportError:
        print("Zum Messen fehlt playwright: pip install playwright && playwright install chromium")
        return 0

    async def lauf() -> int:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            seite = await browser.new_page(viewport={"width": BREITE, "height": 1200})
            fehler: list[str] = []
            seite.on("pageerror", lambda e: fehler.append(str(e)))
            await seite.goto(ZIEL.as_uri())
            await seite.wait_for_timeout(1800)
            befund = await seite.evaluate(
                """() => {
                  const ms = parseFloat(getComputedStyle(document.documentElement)
                             .getPropertyValue('--massstab')) || 1;
                  const raus = [];
                  document.querySelectorAll('.buehne section').forEach((sec, i) => {
                    const sr = sec.getBoundingClientRect();
                    let unten = 0, klein = 0;
                    Array.from(sec.children).forEach(el => {
                      if (el.tagName === 'ASIDE') return;
                      if (getComputedStyle(el).position === 'absolute') return;
                      unten = Math.max(unten, (el.getBoundingClientRect().bottom - sr.top) / ms);
                    });
                    sec.querySelectorAll('*').forEach(el => {
                      if (el.children.length || !el.textContent.trim()) return;
                      // Hoch- und tiefgestellte Zeichen sind von Natur aus
                      // kleiner (10^25); das ist kein zu kleiner Text.
                      if (el.tagName === 'SUP' || el.tagName === 'SUB') return;
                      if (parseFloat(getComputedStyle(el).fontSize) / ms < 23.5) klein++;
                    });
                    raus.push([i + 1, sec.id, Math.round(unten), klein]);
                  });
                  return raus;
                }"""
            )
            await browser.close()

        beanstandet = 0
        for nummer, kennung, unten, klein in befund:
            marken = []
            if unten > 952:
                marken.append("läuft %d Punkte über" % (unten - 952))
            if klein:
                marken.append("%d Texte unter 24px" % klein)
            if marken:
                beanstandet += 1
            print("%2d %-22s %4d  %s" % (nummer, kennung, unten, "; ".join(marken)))
        if fehler:
            print("Fehler in der Seite:", fehler)
            beanstandet += 1
        print()
        print("Folien mit Beanstandung:", beanstandet, "von", len(befund))
        return 1 if beanstandet else 0

    return asyncio.run(lauf())


if __name__ == "__main__":
    sys.exit(main())
