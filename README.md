# EU AI Act und DSGVO Konformitätshelfer

Beschreiben Sie Ihr KI-Vorhaben in eigenen Worten und erfahren Sie mit
Artikelverweis, was die KI-Verordnung (EU) 2024/1689 und die
Datenschutz-Grundverordnung von Ihnen verlangen — getrennt danach, ob Sie das
System anbieten oder einsetzen.

![Lizenz](https://img.shields.io/badge/Lizenz-Apache--2.0-blue)
![Python](https://img.shields.io/badge/Python-3.11%20%7C%203.12%20%7C%203.13-blue)
[![Prüfung](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/pruefung.yml/badge.svg)](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/pruefung.yml)
[![Android-Paket](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/android.yml/badge.svg)](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/actions/workflows/android.yml)

## Das ist keine Rechtsberatung

Dieses Werkzeug ordnet eine Beschreibung anhand des Verordnungstextes ein und
nennt die Fundstellen dazu. Es ist **keine Rechtsberatung**, **kein Ersatz für
eine Prüfung im Einzelfall** und es wird **keine Richtigkeit gewährleistet**.
Vor einer Entscheidung mit Geld- oder Rechtsfolgen ist der geltende Stand bei
einer Rechtsanwältin, einem Rechtsanwalt oder der zuständigen Aufsichtsbehörde
zu prüfen. Einzelne Geltungstermine der KI-Verordnung wurden zum Datenstand
politisch erörtert und können sich geändert haben. Ausführlich:
[docs/haftung.md](docs/haftung.md).

## Was es tut

Sie geben eine Beschreibung ein. Das Werkzeug

1. stuft das Vorhaben in eine Risikoklasse der KI-Verordnung ein — mit der
   Regel und der Fundstelle, über die es dort gelandet ist,
2. listet die Pflichten, die aus dieser Klasse und Ihrer Rolle folgen, je mit
   Artikel, Frist und einem Satz dazu, was zu tun ist,
3. geht den Prüfpfad des Datenschutzrechts durch, soweit er greift,
4. nennt die offenen Fragen, deren Antwort die Auskunft genauer machen würde,
5. legt die Stellen im Wortlaut daneben, auf die es sich stützt.

Die Einstufung kommt dabei **nicht** aus einem Sprachmodell, sondern aus einem
Entscheidungsbaum in Textdateien. Ein Sprachmodell formuliert die Auskunft
höchstens aus. Warum das so getrennt ist, steht unter
[Wie die Einstufung zustande kommt](#wie-die-einstufung-zustande-kommt).

### Ein echter Lauf

```
$ konformitaetshelfer pruefen "Wir entwickeln einen Chatbot für unsere
  Webseite, der Kundenfragen zu Lieferzeiten beantwortet. Er trifft keine
  Entscheidungen über Menschen."
```

Ausgabe, gekürzt — der Lauf vom 03.10.2026 lieferte 3 Pflichten nach der
KI-Verordnung und 16 Abschnitte des Datenschutzpfads:

```
Einstufung
──────────
  transparenz
  Transparenzpflichten nach Artikel 50

  Rolle anbieter — entwickelt ein KI-System oder lässt es entwickeln und
  bringt es unter eigenem Namen auf den Markt oder nimmt es in Betrieb

Warum
─────
  • Menschen müssen erfahren, dass sie mit einem KI-System sprechen — es sei
  denn, das ist aus den Umständen offensichtlich. (Artikel 50 Absatz 1 KI-VO)
    Sicherheit: zu_pruefen · Fundstellen: KI-VO/art-50/abs-1

Zu tun nach der KI-Verordnung (3 Punkte)
────────────────────────────────────────
   1. Personal im Umgang mit KI schulen
      Zu tun ist: Allen Mitarbeitern und allen Personen, die in Ihrem Auftrag
      mit dem KI-System arbeiten, ein ausreichendes Verständnis dafür
      verschaffen, was das System kann, wo seine Grenzen liegen und welche
      Risiken es mitbringt. […]
      Artikel 4 KI-VO · gilt ab 02.02.2025
   2. Offenlegen, dass der Mensch mit einem KI-System spricht
      […]
      Artikel 50 Absatz 1 KI-VO · gilt ab 02.08.2026
   3. Künstlich erzeugte Inhalte maschinenlesbar kennzeichnen
      […]
      Artikel 50 Absatz 2 KI-VO · gilt ab 02.08.2026

Damit die Auskunft genauer wird
───────────────────────────────
  ? Verarbeitet das System personenbezogene Daten — also Angaben, über die
  sich ein Mensch bestimmen lässt? Davon hängt ab, ob zusätzlich das
  Datenschutzrecht greift.
  ? Die Beschreibung ist noch dünn. Je genauer Zweck, Einsatzbereich und
  betroffene Personen benannt sind, desto belastbarer die Auskunft.

──────────────────────────────────────────────────────────────────────────────
Keine Rechtsberatung. […] Regelsatz Stand 31.05.2026
```

Dazwischen stand der Abschnitt „Zu tun nach dem Datenschutzrecht" mit 16
Punkten; er ist hier weggelassen.

Die Marke `zu_pruefen` hinter einer Begründung heißt: die Regel hat
angeschlagen, aber die Beschreibung belegt sie nicht sicher. Das Werkzeug
unterscheidet `sicher`, `wahrscheinlich` und `zu_pruefen` und schreibt es
jeweils dazu.

## Für wen

* **Mitarbeiter in Unternehmen**, die ein KI-Vorhaben haben und wissen müssen,
  was auf sie zukommt, bevor sie eine Kanzlei beauftragen. Man muss die
  Verordnung nicht kennen, um die Auskunft zu lesen.
* **Datenschutzbeauftragte und Betriebsräte**, die eine Vorlage im Haus
  beurteilen und die Fundstellen dazu brauchen.
* **Entwicklerinnen und Entwickler**, die prüfen wollen, in welche Klasse ihr
  Vorhaben fällt und welche Pflichten bei welcher Rolle greifen.

Nicht gedacht ist es für die abschließende rechtliche Bewertung. Die bleibt
Sache von Menschen mit Berufszulassung.

## Schnellstart

### Weg 1: Container — ein Befehl

```bash
./scripts/start.sh
```

Unter Windows `scripts\start.ps1`. Das Skript prüft die Voraussetzungen, baut
das Abbild und startet den Dienst auf `http://127.0.0.1:8000`. Weitere
Schalter: `--klein` (ohne das große Suchmodell, baut schnell), `--mit-ollama`
(zusätzlich ein Sprachmodell im Verbund), `--neu` (ohne Zwischenspeicher),
`--stopp`.

Von Hand, ohne Skript:

```bash
docker compose up --build
```

Das Abbild enthält Rechtsbestand, Regelwerk **und** das Einbettungsmodell, damit
der Container ohne Netz suchen kann — und ist dadurch rund 5 Gigabyte groß. Wer
das nicht will, baut mit `--build-arg MIT_SUCHMODELL=0` beziehungsweise
`./scripts/start.sh --klein`: dann läuft die Suche mit einem Ersatzverfahren,
das nur Wörter vergleicht, und der Dienst sagt das in `/gesundheit` und in der
Oberfläche. Für einen Prüflauf reicht das, für den Betrieb nicht.

Der Dienst läuft im Container unter dem Nutzer `helfer` (Kennung 10001), nicht
als Verwalter, mit nur lesendem Dateisystem, und ist nach außen nur an
`127.0.0.1` gebunden. Einstellungen kommen aus `.env`; die Vorlage dazu ist
`.env.example` — dort gehört nie ein echter Schlüssel hinein.

### Weg 2: Python unmittelbar

Gebraucht werden Python 3.11 oder neuer und ein Verzeichnis dieses Projekts.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e .
```

Damit stehen fünf Befehle bereit. Die Einstufung braucht kein Modell, keinen
Schlüssel und kein Netz — nur die Regeldateien unter `daten/regeln`:

```bash
konformitaetshelfer pruefen "Wir sortieren Bewerbungen mit einem Sprachmodell vor"
konformitaetshelfer fragen "Brauchen wir eine Folgenabschätzung?" --rolle betreiber
konformitaetshelfer suchen "Artikel 6 Absatz 3" --kurz
konformitaetshelfer dienst --port 8000
konformitaetshelfer stand
```

`stand` sagt, womit das Werkzeug gerade arbeitet und was fehlt — Rechtstexte,
Suchbestand, Regelsatz, Sprachmodell. Wer die Ausgabe weiterverarbeiten will,
nimmt `--json`.

Für die Suche im Rechtstext kommen das Einbettungsmodell und der Suchbestand
dazu — rund 2,3 Gigabyte Modell und ein Rechenlauf von einigen Minuten:

```bash
pip install -e ".[suche]"
```

Der Suchbestand liegt im Verzeichnis (2811 Vektoren, Stand 04.10.2026) und muss
nicht gebaut werden. Nur nach einer Änderung am Rechtsbestand:

```bash
python scripts/bestand_bauen.py
```

Der abgelegte Bestand trägt die Kennungen des Korpus, aus dem er gebaut wurde,
und wird beim Laden abgewiesen, wenn sie nicht mehr passen — sonst zeigte jeder
Vektor auf die falsche Fundstelle, und die Antwort sähe aus wie immer. Liegt
kein Bestand vor, läuft die Suche mit einem Ersatzverfahren, das nur Wörter
vergleicht und keine Bedeutung; `konformitaetshelfer stand` sagt das dann
ausdrücklich. Die Einstufung ist davon nicht betroffen.

### Weg 3: Webdienst im Browser

```bash
konformitaetshelfer dienst --port 8000
```

Dann `http://127.0.0.1:8000` öffnen. Der Dienst lädt Korpus, Suchbestand und
Regelwerk beim Start in den Speicher, nicht je Anfrage. Neben der Oberfläche
gibt es fünf Schnittstellen — `POST /api/einstufung`, `POST /api/suche`,
`POST /api/frage`, `GET /api/fragebogen`, `GET /api/fristen` — dazu
`GET /gesundheit`. `POST /api/einstufung` ist der Teil, der ohne Sprachmodell
arbeitet.

Standardmäßig hört der Dienst nur auf `127.0.0.1`, also nur auf dem eigenen
Rechner. Wer ihn im Netz anbietet, liest zuerst
[docs/sicherheit.md](docs/sicherheit.md).

### Weg 4: Android-App

Die App trägt Rechtsbestand, Regelwerk und Einbettungsmodell auf dem Gerät.
Sie braucht kein Netz und kein Konto; die Beschreibung verlässt das Telefon
nicht.

1. Unter **Releases** die Datei `konformitaetshelfer-<Fassung>.apk`
   herunterladen — auf dem Telefon. Gibt es noch keine Veröffentlichung, liegt
   das Paket unter **Actions** beim Lauf „Android-Paket bauen" als Artefakt
   `konformitaetshelfer-apk` (ein ZIP-Archiv, die APK-Datei steckt darin).
2. Die Datei antippen. Android fragt nach der Erlaubnis für Apps aus
   unbekannter Quelle: dem Hinweis folgen, den Schalter für die Browser- oder
   Dateien-App umlegen, zurückgehen, „Installieren" tippen.
3. Fertig.

Das Paket ist nicht unterschrieben — ein Unterschriftsschlüssel gehört nicht in
ein öffentliches Verzeichnis. Es ist groß, weil Rechtsbestand und Modell
mitkommen: die drei Beigaben im Verzeichnis messen zusammen 143 571 672 Byte,
also rund 144 Megabyte — Einbettungsmodell 118,1, Wortschatz 17,1, Datenbank
8,4. Mindestens Android 8.0 (Schnittstellenstufe 26).

## Wie die Einstufung zustande kommt

Zwei Dinge, streng getrennt:

**Was gilt**, entscheidet der Prüfer in `src/helfer/einstufung/pruefer.py` aus
den Regeldateien unter `daten/regeln`. Das ist ein Entscheidungsbaum: dieselbe
Beschreibung ergibt immer dieselbe Einstufung, und an jeder Verzweigung steht
die Fundstelle. Er arbeitet die Reihenfolge der Verordnung ab — verbotene
Praktiken nach Artikel 5, hohes Risiko über das Produktsicherheitsrecht
(Artikel 6 Absatz 1), hohes Risiko über den Einsatzbereich (Artikel 6 Absatz 2
mit Anhang III), die Ausnahme nach Artikel 6 Absatz 3, Transparenzpflichten
nach Artikel 50, Modelle mit allgemeinem Verwendungszweck ab Artikel 51, und
zuletzt die KI-Kompetenz nach Artikel 4.

**Wie die Stelle gefunden wird**, läuft auf zwei Wegen in dasselbe Regelwerk.
Der erste geht über kennzeichnende Wörter. Der zweite über den Zweck: in
`daten/regeln/kivo_zweckkatalog.yaml` steht zu jeder Fundstelle derselbe Zweck
in der Sprache, in der ein Unternehmen ihn beschreibt — *„Wir sichten
Bewerbungen und sortieren sie vor."* Beschreibung und Zwecksatz werden Satz für
Satz verglichen, und der Katalog zeigt auf die **bestehenden** Regelkennungen.
Er ist damit ein zweiter Eingang in dieselbe Regel und kein zweites Regelwerk:
Rollenprüfung, Merkmalsfilter, Ausnahmen und Pflichtenableitung gelten
unverändert. Das Modell findet die Stelle, das Regelwerk entscheidet.

Der Grund für diesen zweiten Weg ist gemessen. Mit Wortlisten allein traf der
Prüfer 44 von 44 Anwendungsfällen — aber nur 55 von 100 Beschreibungen, wie
Unternehmen sie wirklich einreichen. Eine Wortliste trifft nur, was jemand
vorher aufgeschrieben hat. Mit dem Zweckkatalog sind es 100 von 100; die
Sammlung liegt unter `daten/pruefung/unternehmensfragen.yaml` und wird bei
jedem Lauf nachgerechnet. Fehlen die lokalen Modelle, bleibt der Zweckweg aus
und die Wortlisten entscheiden allein — der Container ohne Netz und das Telefon
stufen weiter ein.

**Wie es gesagt wird**, macht ein Sprachmodell — und das ist freiwillig. Es
bekommt die Einstufung als feststehende Tatsache vorgelegt und darf sie nicht
ändern. Der Grund ist nicht Vorsicht, sondern Erfahrung: ein Modell, das
Pflichten erfinden darf, erfindet Pflichten. Es antwortet höflich und
plausibel auch dann, wenn der genannte Artikel nicht existiert. Bei einer
Auskunft, nach der jemand ein Produkt umbaut oder eben nicht umbaut, ist das
nicht hinnehmbar.

Ohne Sprachmodell läuft alles weiter; die Auskunft ist dann nüchterner
formuliert, aber inhaltlich dieselbe — das Beispiel oben ist ein solcher Lauf.
Dafür gibt es den Befehl `pruefen` und die Schnittstelle `/api/einstufung`:
beide arbeiten ohne Sprachmodell.

Gesucht wird im Rechtstext über vier Wege gleichzeitig: Bedeutung
(Vektorsuche), Wortlaut (Stichwortsuche nach dem Verfahren BM25), die
Wortgewichte des Einbettungsmodells, und ein Fundstellenweg, der „Art. 6
Abs. 3" unmittelbar in die Kennung `KI-VO/art-6/abs-3` auflöst. Die vier
Trefferlisten werden über ihre Rangplätze zusammengeführt und die besten 30
anschließend von einem Kreuzbewerter neu sortiert. Die Einzelheiten und die
Begründung jeder dieser Entscheidungen stehen in
[docs/architektur.md](docs/architektur.md) und in
[docs/entscheidungen.md](docs/entscheidungen.md).

## Datenstand und Quellen

Stand des Regelwerks: **31.05.2026**. Rechtsbestand geholt und gebaut am
**04.10.2026**. Nachgemessen am 04.10.2026:

| Was | Menge | Datei |
|---|---|---|
| Rechtseinheiten im Bestand | 2811 | `daten/aufbereitet/korpus.jsonl` |
| Einstufungsregeln | 28 | `daten/regeln/kivo_risikoklassen.yaml` |
| Einträge im Zweckkatalog | 55 | `daten/regeln/kivo_zweckkatalog.yaml` |
| Pflichten der KI-Verordnung | 57 | `daten/regeln/kivo_pflichten.yaml` |
| Abschnitte des Datenschutzpfads | 26 | `daten/regeln/dsgvo_pruefpfad.yaml` |
| Anwendungsfälle | 44 | `daten/faelle/*.yaml` |
| Unternehmensfragen zur Genauigkeit | 100 | `daten/pruefung/unternehmensfragen.yaml` |

Eine Rechtseinheit ist das kleinste Stück, auf das sich zeigen lässt: ein
Absatz eines Artikels, eine Nummer eines Anhangs, ein Erwägungsgrund, ein
Paragraf.

Woher der Text kommt:

* **KI-Verordnung** — amtlicher Volltext aus dem Amtsblatt über EUR-Lex
  (CELEX 32024R1689), 1386 Einheiten: 113 Artikel mit 929 Absätzen und
  Nummern, 13 Anhänge mit 151 Nummern und Buchstaben, 180 Erwägungsgründe.
* **Datenschutz-Grundverordnung** — amtlicher Volltext aus dem Amtsblatt über
  EUR-Lex (CELEX 32016R0679), 1024 Einheiten: 99 Artikel mit 752 Absätzen und
  Nummern, 173 Erwägungsgründe.
* **Bundesdatenschutzgesetz** — 357 Paragrafen von gesetze-im-internet.de,
  Teile 1 und 2.
* **Anwendungsfälle** — 44 selbst geschriebene Beispiele, keine Rechtsquelle.

Fristen können sich ändern; der Vorbehalt dazu steht im Regelwerk und in jeder
Auskunft. Alles Weitere, auch die Lizenzlage der Quellen:
[docs/datenquellen.md](docs/datenquellen.md). Lizenzhinweise zu den
mitgelieferten Rechtstexten: [NOTICE](NOTICE).

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

## Präsentation

[docs/praesentation.html](docs/praesentation.html) erklärt Architektur,
Funktionsweise und Betrieb auf 14 Folien — für Fachkundige und für Fachfremde.
Die Datei im Browser öffnen: sie läuft ohne Netz, blättert mit den Pfeiltasten
und ergibt gedruckt eine Folie je Seite (auch als PDF).

Geändert wird sie nicht in dieser Datei, sondern in den einzelnen Folien unter
`praesentation/folien/`; zusammengesetzt wird sie mit

```bash
python scripts/praesentation_bauen.py --messen
```

Das `--messen` sieht im Browser nach, ob jede Folie auf ihre Fläche passt und
keine Schrift unter 24 Punkte fällt. Eine Folie, deren Inhalt überläuft, wird
beim Vortrag unten abgeschnitten — und das sieht man dem Text nicht an.

## Nachbauen

[BAUPLAN.md](BAUPLAN.md) ist der vollständige Auftrag, mit dem sich dieses
Werkzeug in einem Durchgang nachbauen lässt: elf Stufen, zehn Grundsätze, die
Zielzahlen als Prüfkriterien und die Fallstricke, die hier Stunden gekostet
haben — von der Firewall bei EUR-Lex bis zu den Standardrändern des Browsers,
die eine Präsentation unbemerkt abschneiden.

Er ist an einen Programmierassistenten gerichtet und so geschrieben, dass keine
Rückfrage offenbleibt.

## Lizenz

Apache License 2.0, siehe [LICENSE](LICENSE). Copyright 2026 Daniel Hütte.

Für die mitgelieferten Rechtstexte gilt die Lizenz dieses Werks nicht — dafür
gilt die Rechtslage der jeweiligen Quelle, siehe [NOTICE](NOTICE).
