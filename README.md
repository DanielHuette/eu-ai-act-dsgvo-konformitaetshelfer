# EU AI Act Konformitätshelfer

Sechs Fragen, und Sie wissen, in welche Risikoklasse der KI-Verordnung
(EU) 2024/1689 Ihr KI-System fällt — mit der genauen Stelle im Gesetz, auf der
die Einstufung beruht. Nicht „Anhang III", sondern „Anhang III Nummer 4
Buchstabe a".

![Lizenz](https://img.shields.io/badge/Lizenz-Apache--2.0-blue)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)
[![Prüfung](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/pruefung.yml/badge.svg)](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/pruefung.yml)
[![Pakete](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/pakete.yml/badge.svg)](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/pakete.yml)

**Im Browser ausprobieren:** <https://konformitaetshelfer.speedofthespirit.dev/>
— ohne Anmeldung, ohne Installation, auch auf dem Handy.
**Für den eigenen Rechner:** [fertige Pakete für Windows, Mac und
Linux](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/releases).

## Das ist keine Rechtsberatung

Dieses Werkzeug ordnet ein KI-System anhand des Verordnungstextes ein und nennt
die Fundstellen dazu. Es ist **keine Rechtsberatung**, **kein Ersatz für eine
Prüfung im Einzelfall** und es wird **keine Richtigkeit gewährleistet**. Vor
einer Entscheidung mit Geld- oder Rechtsfolgen ist der geltende Stand bei einer
Rechtsanwältin, einem Rechtsanwalt oder der zuständigen Aufsichtsbehörde zu
prüfen. Ausführlich: [docs/haftung.md](docs/haftung.md).

## Wie genau ist es?

**206 von 217 amtlichen Beispielen** der Europäischen Kommission
werden richtig eingestuft. Im Schnitt **5.3 Schritte** je Fall.

Die Beispiele stammen aus dem Entwurf der Leitlinien der Kommission vom
19. Mai 2026 zur Einstufung von Hochrisiko-KI-Systemen. Jedes beschreibt ein
System und nennt die Wertung der Kommission. Gemessen wurde, ob der Helfer zur
selben Wertung kommt, wenn jemand nur die Beschreibung kennt.

Sieben der elf Abweichungen messen den Helfer nicht: ihre Beschreibungen nennen
gar keinen Anwendungsbereich, und die Ausnahme des Artikels 6 Absatz 3 kommt
ohne Bereich zu Recht nie an die Reihe. Rechnet man sie heraus, sind es
**206 von 210**. Das Verfahren und jede einzelne Abweichung stehen in
[daten/pruefung/MESSUNG.md](daten/pruefung/MESSUNG.md).

Was diese Zahl nicht hergibt: kein Jurist hat den Durchlauf gegengelesen.

## Warum Fragen statt Raten

Die erste Fassung ließ den Nutzer sein System beschreiben und erriet daraus die
Einstufung — erst über Stichwortlisten, dann über Bedeutungsvergleich. Auf
zwanzig Beschreibungen, wie Unternehmen sie wirklich einreichen, traf das 11 von
20; nach einer Nacht Arbeit 20 von 20.

Trotzdem war der Ansatz falsch. Ein Jurist fragt fünf bis acht Dinge ab und hat
danach Gewissheit, nicht 98 Prozent. Genaues Raten ist schlechter als Fragen —
und der Helfer riet die Antworten auf Fragen, die er stellen konnte.

Heute entscheidet die Fragefolge. Weil die Antworten vom Nutzer kommen, ist das
Ergebnis nicht wahrscheinlich, sondern richtig, soweit seine Angaben stimmen.
Und er sieht, woran es hängt.

## Was drinsteckt

| | |
|---|---|
| Rechtsbestand | 2811 einzeln ansprechbare Textstellen: 1386 aus der KI-Verordnung, 1024 aus der Datenschutz-Grundverordnung, dazu das Bundesdatenschutzgesetz |
| Fragefolge | 379 Fragen zu 31 Stellen des Gesetzes, 214 ausdrückliche Ausschlüsse, 187 amtliche Beispiele |
| Belegt | Jede Frage, jeder Ausschluss, jedes Beispiel trägt die Absatznummer der amtlichen Auslegung |
| Zwei Wege, ein Ergebnis | Webseite und Programm rechnen nachweislich gleich — 400 von 400 Prüfläufen |

Die Fragen stammen Zeile für Zeile aus dem Entwurf der Leitlinien der
Europäischen Kommission vom 19. Mai 2026: 148 Seiten zu Anhang III, 13 Seiten zu
Anhang I, 6 Seiten allgemeine Grundsätze. Nichts darin ist ausgedacht.

## Wie ein Durchlauf aussieht

1. **Drei Vorfragen** — Ist es überhaupt ein KI-System nach Artikel 3 Nummer 1?
   Bewertet es Menschen oder nur Firmen? Handeln Sie im Auftrag einer Behörde?
2. **Anhang I** — Steckt Ihr System in einem geregelten Produkt (Maschine,
   Spielzeug, Aufzug, Medizinprodukt, Fahrzeug) oder ist es selbst eines?
   15 Produktgattungen.
3. **Acht Bereichsfragen** — Womit hat Ihr System zu tun? Beschäftigung, Geld
   und Daseinsvorsorge, Körpermerkmale, Bildung, Versorgungsnetze, Gerichte und
   Wahlen, Polizei, Grenze. Diese acht Sätze sortieren nur.
4. **Die Rechtsfragen des gewählten Bereichs** — Erst hier wird entschieden.
5. **Die Ausnahme nach Artikel 6 Absatz 3** — nur, wenn vorher eine Stelle
   trägt. Vier Bedingungen und die Gegenausnahme Profiling.
6. **Der Befund** — Klasse, Fundstelle, die amtlichen Beispiele zum Vergleichen.

Jede Frage hat drei Antworten: Ja, Nein und **Trifft nicht zu**. Die dritte ist
nicht Bequemlichkeit. Ein Werkzeug, das Lebensläufe sichtet, schaltet keine
Stellenanzeigen — auf die Frage, ob eine Anzeige eine konkrete offene Stelle
anzeigt, gibt es dort weder Ja noch Nein. Ein erzwungenes Nein warf gemessen
genau solche Fälle aus der Einstufung.

## Loslegen

### Im Browser

<https://konformitaetshelfer.speedofthespirit.dev/> — nichts zu installieren.
Die Seite ist eine HTML-Datei, eine JavaScript-Datei und die Fragedaten. Keine
Anmeldung, kein Server, keine Übertragung Ihrer Angaben.

### Als Programm

Paket für Ihr System von der
[Veröffentlichungsseite](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/releases)
holen, installieren, starten. Die Bedienoberfläche öffnet sich im Browser. Kein
Python, kein Conda, keine Einrichtung.

Dazu kommt dort die **Volltextsuche im Verordnungstext**: eine Frage in eigenen
Worten, und der Helfer zeigt die Stellen, die sie beantworten. Sie braucht ein
Sprachmodell von rund 2,3 Gigabyte, das der Helfer auf Wunsch einmalig holt —
die Einstufung läuft ohne.

### Aus dem Quellcode

```bash
git clone https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer
cd eu-ai-act-dsgvo-konformitaetshelfer
pip install -e .
python verpacken/start_helfer.py
```

## Wie die Einstufung zustande kommt

Aus dem Regelwerk, nicht aus einem Sprachmodell. Drei Textdateien tragen sie:

- `daten/regeln/fragefolge/*.yaml` — die Fragen, Ausschlüsse und amtlichen
  Beispiele, je mit Absatznummer der Leitlinien
- `daten/regeln/fragefolge-aufbau.yaml` — die Reihenfolge: welche Frage wann,
  welche entscheidet, welche unterrichtet nur
- `daten/regeln/kivo_pflichten.yaml` — was aus einer Klasse und einer Rolle an
  Pflichten folgt

Ein Sprachmodell formuliert höchstens die Auskunft aus. Es kann das Ergebnis
nicht verändern. Grund: eine erfundene Einstufung kostet Geld und Vertrauen.

### Dass beide Wege gleich rechnen, ist nachgemessen

Die Einstufung läuft an zwei Orten — in `src/helfer/einstufung/fragefolge.py`
für das Programm und in `web/durchlauf.js` für die Webseite. Zwei Fassungen
derselben Logik laufen auseinander; beim Bau dieses Durchlaufs haben Fragefolge
und Auswertung genau das getan und 30 von 217 Beispielen gekostet.

`scripts/pruefe_zwei_wege.py` würfelt Antwortmuster und fährt beide Fassungen
damit: dieselbe Frage in derselben Reihenfolge, derselbe Befund. Der Prüflauf
baut kein Paket, bevor 400 von 400 Läufen gleich sind.

## Datenstand und Quellen

| Quelle | Stand | Umfang |
|---|---|---|
| Verordnung (EU) 2024/1689 (KI-Verordnung) | Amtsblatt 12.07.2024 | 1386 Textstellen |
| Verordnung (EU) 2016/679 (Datenschutz-Grundverordnung) | Amtsblatt 04.05.2016 | 1024 Textstellen |
| Entwurf der Leitlinien der Kommission zur Einstufung von Hochrisiko-KI-Systemen | 19.05.2026 | 167 Seiten |
| Bundesdatenschutzgesetz | geltende Fassung | im Bestand |

Der amtliche Wortlaut wird über Cellar geholt, den Datendienst des Amts für
Veröffentlichungen — nicht von der EUR-Lex-Webseite, die ohne vollständigen
Browser-Kopf leere Antworten liefert. `scripts/holen_amtsblatt.py`.

Der Entwurf der Leitlinien ist **nicht bindend**. Die öffentliche Anhörung lief
bis zum 23. Juni 2026; eine endgültige Fassung lag bei Abschluss dieser Arbeit
nicht vor. Der Helfer sagt diesen Vorbehalt in jeder Auskunft mit.

## Nachbauen

[BAUPLAN.md](BAUPLAN.md) beschreibt das ganze Projekt so, dass es sich in einem
Durchgang neu bauen lässt: Stufen, Grundsätze, Zielzahlen als Prüfkriterien und
die Fallstricke, die beim ersten Bau Zeit gekostet haben.

## Mitarbeit

Vor jedem Vorschlag:

```bash
scripts/alles_pruefen.sh           # was der Prüfstand prüft
scripts/alles_pruefen.sh --alles   # zusätzlich Container und Präsentation
```

Das Skript führt dieselben Befehle aus wie der Prüfstand auf GitHub, in
derselben Reihenfolge — wer nur einen Teil prüft, merkt einen Fehler erst dort.

Fehler und Wünsche gehören in die Fehlerverwaltung. Es gibt drei Vorlagen, und
die Wahl ist wichtig:

* **Fehler im Programm** — etwas stürzt ab oder tut nicht, was dasteht.
* **Wunsch** — etwas fehlt.
* **Rechtsfehler** — ein Artikelverweis, eine Frist, eine Einstufung oder ein
  Pflichttext ist falsch. Das ist der wichtigste Weg: ein falscher Verweis
  trifft jeden, der das Werkzeug benutzt. Diese Meldungen werden vor allen
  anderen bearbeitet.

Wie eine Änderung am Regelwerk geprüft wird und was einer Meldung über einen
Rechtsfehler beiliegen muss, steht in [CONTRIBUTING.md](CONTRIBUTING.md).
Sicherheitslücken nicht öffentlich melden, sondern nach
[SECURITY.md](SECURITY.md).

## Weiterlesen

| Datei | Inhalt |
|---|---|
| [docs/architektur.md](docs/architektur.md) | Der Weg einer Frage, Baustein für Baustein, mit den Grenzen des Systems |
| [docs/betriebsanleitung.md](docs/betriebsanleitung.md) | Benutzen, aufstellen, Rechtsdaten aktualisieren — und was tun, wenn etwas nicht geht |
| [docs/datenquellen.md](docs/datenquellen.md) | Jede Quelle mit Datum, Umfang und Lizenzlage |
| [docs/sicherheit.md](docs/sicherheit.md) | Wo Daten liegen, was das Gerät verlässt, Schutz gegen untergeschobene Anweisungen |
| [docs/entscheidungen.md](docs/entscheidungen.md) | Die Architekturentscheidungen mit Begründung und Folgen |
| [docs/haftung.md](docs/haftung.md) | Was das Werkzeug nicht ist |

## Lizenz

Apache License 2.0, siehe [LICENSE](LICENSE). Copyright 2026 Daniel Hütte.

Für die mitgelieferten Rechtstexte gilt die Lizenz dieses Werks nicht — dafür
gilt die Rechtslage der jeweiligen Quelle, siehe [NOTICE](NOTICE).
