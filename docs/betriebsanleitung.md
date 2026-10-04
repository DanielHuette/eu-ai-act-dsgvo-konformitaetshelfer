# Betriebsanleitung

Drei Leserkreise, drei Abschnitte. Lesen Sie den, der auf Sie passt.

* [a) Ich will es nur benutzen](#a-ich-will-es-nur-benutzen)
* [b) Ich stelle es im Unternehmen auf](#b-ich-stelle-es-im-unternehmen-auf)
* [c) Ich will die Rechtsdaten und die Fragen pflegen](#c-ich-will-die-rechtsdaten-und-die-fragen-pflegen)
* [Wenn etwas nicht geht](#wenn-etwas-nicht-geht)

---

## a) Ich will es nur benutzen

### Im Browser — nichts zu installieren

<https://konformitaetshelfer.speedofthespirit.dev/>

Sie beantworten Fragen über Ihr System und bekommen die Einstufung mit der
genauen Stelle im Gesetz. Keine Anmeldung, kein Konto, kein Server: die Seite
besteht aus einer HTML-Datei, einer JavaScript-Datei und den Fragedaten. Ihre
Angaben werden im Browser verrechnet und nicht übertragen.

Ein Durchlauf dauert im Schnitt 5,3 Schritte. Jede Frage hat drei Antworten:
**Ja**, **Nein** und **Weiß ich nicht**. Die dritte ist nicht Bequemlichkeit —
nehmen Sie sie, wenn eine Frage auf Ihr System nicht passt. Beispiel: Ein
Werkzeug, das Lebensläufe sichtet, schaltet keine Stellenanzeigen; auf die
Frage, ob eine Anzeige eine konkrete offene Stelle anzeigt, gibt es dort weder
Ja noch Nein. Ein erzwungenes Nein warf gemessen genau solche Fälle aus der
Einstufung.

Zu jedem Befund stehen die amtlichen Beispiele der Kommission dabei. Lesen Sie
sie: wenn Ihr Fall einem davon gleicht, ist die Einstufung belegt; wenn nicht,
sehen Sie, woran es hängt.

### Als Programm auf dem eigenen Rechner

Von der
[Veröffentlichungsseite](https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer/releases)
das Paket für Ihr System holen:

| System | Datei |
|---|---|
| Windows | Installationsprogramm `.exe` |
| Mac | Abbild `.dmg` — hineinziehen nach „Programme" |
| Linux | Archiv `.tar.gz` — entpacken, `Konformitaetshelfer` starten |

Starten, fertig. Die Bedienoberfläche öffnet sich im Browser unter einer
Adresse zwischen `http://127.0.0.1:8713` und `:8799` — das Programm sucht einen
freien Anschluss, damit es nicht an einer belegten Nummer scheitert. Kein
Python, keine Umgebung, kein Nachladen von Paketen.

Im Paket liegen der Rechtsbestand, das Regelwerk, die Fragefolge und die
Anwendungsfälle. Damit läuft die Einstufung sofort und ohne Netz.

Dazu kommt dort die **Volltextsuche im Verordnungstext** unter `/suche`: eine
Frage in eigenen Worten, und das Werkzeug zeigt die Stellen, die sie
beantworten. Sie braucht ein Sprachmodell von rund 2,3 Gigabyte — vierzigmal so
groß wie das Paket selbst, deshalb liegt es nicht darin. Wie es dazukommt,
steht unten in Abschnitt b.

### Aus dem Quellcode

Gebraucht werden Python 3.11 oder neuer und dieses Verzeichnis.

```bash
git clone https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer
cd eu-ai-act-dsgvo-konformitaetshelfer
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e .
python verpacken/start_helfer.py
```

Lieber nur den Dienst, ohne dass sich ein Browser öffnet:

```bash
konformitaetshelfer dienst --port 8000
```

Dann liegt die Fragefolge unter `http://127.0.0.1:8000/einstufung/` und die
Volltextsuche unter `http://127.0.0.1:8000/suche`.

Prüfen, womit das Werkzeug gerade arbeitet und was fehlt:

```bash
konformitaetshelfer stand
```

Keine Farbe im Protokoll: `--ohne-farbe`, oder `NO_COLOR` setzen. Geht die
Ausgabe in eine Datei statt an ein Fenster, schaltet sich die Farbe von selbst
ab.

---

## b) Ich stelle es im Unternehmen auf

### Was Sie entscheiden müssen, bevor Sie anfangen

1. **Reicht die Webseite?** Für die Einstufung braucht niemand eine
   Installation. Wer sie im Haus anbieten will, nimmt die drei Dateien aus
   `web/` und legt sie auf einen beliebigen Webserver — mehr ist es nicht.
2. **Soll im Verordnungstext gesucht werden?** Dann brauchen Sie das
   Einbettungsmodell (rund 2,3 Gigabyte) und einen einmaligen Rechenlauf.
3. **Soll eine Antwort ausformuliert werden?** Ohne Sprachmodell läuft alles,
   nur nüchterner. Mit Sprachmodell geht die Frage des Nutzers an den Anbieter
   dieses Modells — bei einem Vorhaben, das Geschäftsinterna enthält, ist das
   eine Entscheidung mit Folgen.
4. **Wer pflegt den Datenstand?** Die Rechtslage ändert sich. Ohne
   Zuständigkeit dafür veraltet das Werkzeug still.

### Die Webseite im Haus aufstellen

```bash
python scripts/fragefolge_ausgeben.py --ziel web/fragefolge.json
```

Danach enthält `web/` alles: `index.html`, `durchlauf.js`, `fragefolge.json`
und die Beigaben. Diese Dateien brauchen keinen Anwendungsserver und keine
Datenbank. `web/_headers` enthält die Kopfzeilen, mit denen die Seite
ausgeliefert werden soll — Cloudflare Pages liest die Datei von allein, jeder
andere Webserver braucht die Angaben in seiner eigenen Form.

### Als Container — der kürzeste Weg zum vollen Umfang

```bash
git clone https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer.git
cd eu-ai-act-dsgvo-konformitaetshelfer
cp .env.example .env          # und ausfüllen, soweit nötig
./scripts/start.sh            # Windows: scripts\start.ps1
```

Das Skript prüft die Voraussetzungen und sagt bei jedem Mangel, was zu tun ist,
statt eine Meldung von Docker durchzulassen. Schalter: `--klein` (ohne das
große Suchmodell), `--neu` (ohne Zwischenspeicher neu bauen), `--stopp`.

Von Hand: `docker compose up --build`. Das Abbild wird rund 5 Gigabyte groß,
weil das Einbettungsmodell mit hineinkommt — ohne es wäre die mitgelieferte
Suchdatenbank ohne Netz wertlos.

Was im Verbund so eingestellt ist: der Dienst läuft unter dem Nutzer `helfer`
(Kennung 10001) ohne Verwalterrechte, mit nur lesendem Dateisystem, mit
abgelegten Fähigkeiten und nach außen nur an `127.0.0.1` gebunden. Der
Zustandsbericht fragt `/gesundheit` und wertet „nicht_bereit" als krank — ein
Dienst, dessen Korpus fehlt, antwortet zwar, ist aber nicht betriebsbereit.

**Nicht geprüft:** dass dieser Bau durchläuft. In diesem Verzeichnis ist das
Abbild nie gebaut worden.

### Ohne Container, mit Suche

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[suche]"            # mit Suche
# pip install -e ".[suche,modelle]"  # zusätzlich Claude oder GPT
python scripts/bestand_bauen.py
```

Der Lauf holt das Modell und rechnet die Einbettungen einmal — gemessen am
04.10.2026 auf einem Hauptprozessor 3547 Sekunden für 2811 Einheiten, also knapp
eine Stunde. Er schreibt sein Protokoll nach
`daten/aufbereitet/_bestand_lauf.log`, legt alle 64 Einheiten einen
Zwischenstand ab und prüft sich am Ende selbst mit einer Frage, deren Antwort
bekannt ist. Danach liegen neben `daten/aufbereitet/suchbestand` die
Dateien `.vektoren.npy`, `.bestand.json.gz` und `.bestand.json`.

Ein kleines Modell zum Ausprobieren, falls 2,3 Gigabyte zu viel sind:

```bash
python scripts/bestand_bauen.py --modell intfloat/multilingual-e5-small
```

Dann muss aber auch die Suche mit diesem Modell laufen — ein Bestand lässt sich
nur mit dem Modell abfragen, mit dem er gebaut wurde. Das wird beim Laden
geprüft.

### Den Webdienst betreiben

```bash
konformitaetshelfer dienst --adresse 127.0.0.1 --port 8000
```

Dieselben Werte stehen auch in Umgebungsvariablen:

| Variable | Wirkung |
|---|---|
| `HELFER_ADRESSE`, `HELFER_PORT` | wo der Dienst hört |
| `HELFER_MODELL` | welches Sprachmodell formulieren soll: `anthropic`, `openai`, `auto` oder `ohne` |
| `HELFER_EINBETTUNG` | welches Einbettungsmodell die Suche nimmt |
| `HELFER_NEUBEWERTUNG` | auf `1` setzen, damit der Kreuzbewerter die besten 30 Treffer neu sortiert |
| `HELFER_ANFRAGEN_JE_MINUTE` | Obergrenze je Adresse gegen Überlast |

**Standardmäßig hört der Dienst nur auf `127.0.0.1`**, also nur auf dem eigenen
Rechner. Wer ihn im Haus anbietet, beachtet:

* Der Dienst hat **keine Anmeldung**. Wer ihn erreicht, kann ihn benutzen. Eine
  Zugangssperre gehört davor — ein vorgeschalteter Server oder das Netz selbst.
* Es gibt einen Zähler je Adresse gegen Überlast, aber keine Benutzerverwaltung
  und keine Abrechnung.
* Der Dienst soll **nicht als Verwalter** laufen. `konformitaetshelfer stand`
  weist darauf hin, wenn er das tut.
* `GET /gesundheit` eignet sich als Prüfpunkt für eine Überwachung.
* Was die Schnittstellen annehmen und zurückgeben, zeigt der Dienst selbst an:
  `/api/einstufung`, `/api/suche`, `/api/frage`, `/api/fragebogen`,
  `/api/fristen`.

Der Dienst lädt Korpus, Suchbestand und Regelwerk beim Start in den Speicher.
Der erste Start dauert deshalb länger als die erste Antwort danach.

### Schlüssel setzen, wenn ein Sprachmodell formulieren soll

```bash
export ANTHROPIC_API_KEY="…"     # für Claude
export OPENAI_API_KEY="…"        # für GPT
```

Ohne Wunsch wird in dieser Reihenfolge gesucht: Claude, GPT. Ist nichts
erreichbar, entsteht die Auskunft aus dem Regelwerk und sagt das in einer
Warnung dazu. Die Einstufung selbst kommt in jedem Fall aus der Fragefolge; ein
Sprachmodell kann sie nicht ändern.

Legen Sie Schlüssel nicht in eine Datei im Verzeichnis. `.gitignore` hält
`.env` zwar heraus, aber ein Schlüssel in einer Datei ist ein Schlüssel, der
einmal versehentlich mitwandert.

### Die Pakete selbst bauen

Der Lauf `.github/workflows/pakete.yml` baut auf drei Maschinen — Windows, Mac
und Linux. Ein Paket enthält die Laufzeitumgebung des Systems, auf dem es
gebaut wurde; ein auf Linux gebautes Windows-Programm gibt es nicht.

* Eine Marke mit `v` davor schieben (etwa `v1.2.0`), dann baut der Lauf und
  hängt die Pakete an die Veröffentlichung.
* Oder den Lauf „Pakete bauen" von Hand starten; dann liegen sie als Artefakt
  beim Lauf.

Der Lauf erzeugt zuerst die Fragefolge neu, vergleicht dann beide Wege mit 400
Antwortmustern und baut erst danach. Grund: laufen Programm und Webseite
auseinander, bekommt derselbe Fall zwei Antworten. Nach dem Bau startet
`verpacken/start_pruefen.py` das Paket und sieht nach, ob es antwortet und die
Fragefolge ausliefert — sonst merkt es der erste Nutzer.

Örtlich:

```bash
pip install pyinstaller
python scripts/fragefolge_ausgeben.py --ziel web/fragefolge.json
cp web/fragefolge.json daten/aufbereitet/fragefolge.json
python scripts/pruefe_zwei_wege.py --laeufe 400
python -m PyInstaller verpacken/helfer.spec --noconfirm
python verpacken/start_pruefen.py
```

### Was Sie den Nutzern sagen müssen

Dass es keine Rechtsberatung ist. Dass die Einstufung so gut ist wie ihre
Antworten — wer nicht weiß, wofür sein System bestimmt ist, muss das erst
klären. Und dass die Pflichtenliste eher zu lang als zu kurz ist: sie enthält
alle Pflichten der erkannten Klasse und Rolle, auch solche, die auf das
einzelne Vorhaben nicht passen. Siehe
[architektur.md](architektur.md), Abschnitt „Grenzen des Systems", und
[haftung.md](haftung.md).

---

## c) Ich will die Rechtsdaten und die Fragen pflegen

Es gibt drei Dinge, die veralten, und sie werden getrennt gepflegt:

1. **Die Fragefolge** — die Fragen, Ausschlüsse und Beispiele aus den
   Leitlinien der Kommission. Sie liegt in `daten/regeln/fragefolge/` samt
   `daten/regeln/fragefolge-aufbau.yaml`. Sie veraltet, wenn die Kommission
   ihre Leitlinien ändert — und der Entwurf vom 19.05.2026 wird noch eine
   endgültige Fassung bekommen.
2. **Der Rechtstext** — der Wortlaut der Verordnungen und des Gesetzes. Er
   liegt in `daten/roh` und wird zu `daten/aufbereitet/korpus.jsonl` gebaut.
3. **Das Regelwerk** — die 57 Pflichten und die 26 Abschnitte des
   Datenschutzpfads in `daten/regeln`. Sie veralten nicht durch einen neuen
   Textstand, sondern durch neue Rechtsakte und Rechtsprechung.

### Eine Frage ändern oder hinzufügen

Eine Frage gehört in die Datei ihres Bereichs. Pflicht ist:

* `frage` — ein Satz, den jemand über sein eigenes Unternehmen beantworten
  kann. Kein Gesetzeszitat.
* `bei_ja` und `bei_nein` — `erfasst`, `nicht_erfasst` oder `weiter`.
* `beleg` — die Absatznummer der Leitlinien, etwa `"(245)"`. **Ohne Absatz
  keine Frage.** Eine Frage ohne Fundstelle ist eine ausgedachte Frage, und
  genau das soll es hier nicht geben.

Die Reihenfolge und die Tore stehen getrennt in
`daten/regeln/fragefolge-aufbau.yaml`. Dort wird auch festgelegt, welche Frage
nur unterrichtet (`art: hinweis`) und welche den Weg lenkt (`art: tor`).

Nach jeder Änderung — in dieser Reihenfolge:

```bash
PYTHONPATH=src python -c "
from helfer.einstufung.fragefolge import Durchlauf
print(Durchlauf.laden().zahlen())
"
python scripts/fragefolge_ausgeben.py --ziel web/fragefolge.json
python scripts/pruefe_zwei_wege.py --laeufe 400
```

Erwartet, nachgemessen am 04.10.2026: 379 Fragen, 31 Punkte, 214 Ausschlüsse,
187 Beispiele, 3 Vorfragen, 4 Hinweise. Und 400 von 400 Läufen gleich.

**Der letzte Befehl ist der wichtigste.** Die Ablauflogik steht zweimal da — in
`src/helfer/einstufung/fragefolge.py` und in `web/durchlauf.js`. Beim Bau
dieses Durchlaufs sind die beiden auseinandergelaufen und haben 30 von 217
amtlichen Beispielen gekostet. Wer die eine Fassung anfasst, fasst die andere
mit an und messt es nach.

Danach gegen die amtlichen Beispiele messen, wie es in
[../daten/pruefung/MESSUNG.md](../daten/pruefung/MESSUNG.md) beschrieben ist.
`scripts/fragen_beantworten.py` gibt dafür die nächsten offenen Fragen aus und
nimmt die Antworten entgegen.

### Rechtstext neu holen und bauen

```bash
python scripts/holen_amtsblatt.py   # amtlicher Volltext beider Verordnungen
```

Die Skripte überspringen Dateien, die schon vorliegen und groß genug sind. Wer
neu holen will, löscht die Datei in `daten/roh` vorher.

Dann bauen — erst zur Probe, ohne zu schreiben:

```bash
PYTHONPATH=src python -m helfer.korpus.bauen --pruefen
PYTHONPATH=src python -m helfer.korpus.bauen
```

Danach `daten/aufbereitet/korpus_befund.json` lesen. Dort stehen Stückzahlen je
Quelle und die Warnungen des Laufs. **Der Lauf vom 04.10.2026 hat keine
Warnung.** Steht eine da, ist sie zu lesen und nicht zu übergehen: die Warnung
„Kennungen doppelt MIT ABWEICHENDEM TEXT" nennt die betroffenen Kennungen und
heißt, dass Rechtstext verschwindet.

Prüfen Sie, dass die Stückzahlen zu den Erwartungen passen: die KI-Verordnung
hat 113 Artikel, 13 Anhänge und 180 Erwägungsgründe, die
Datenschutz-Grundverordnung 99 Artikel und 173 Erwägungsgründe; zusammen 2811
Einheiten. Diese Zahlen stehen als Erwartung in `src/helfer/korpus/eurlex.py`
und in `tests/test_korpus.py`; weicht ein Lauf ab, steht das als Warnung im
Befund und die Prüfung bricht ab.

**Nach jedem Korpusbau den Suchbestand neu bauen,** sonst passen die Vektoren
nicht mehr zum Text:

```bash
python scripts/bestand_bauen.py
```

### Das Regelwerk ändern

Jede Datei trägt im Kopf ein Feld `stand` und einen `hinweis_zum_stand`.
**Beides mit ändern** — der Stand erscheint in jeder Auskunft, und ein falsches
Datum ist schlimmer als ein altes.

Eine Pflicht in `daten/regeln/kivo_pflichten.yaml` hat diese Felder:

* `kennung` — eindeutig, wird nicht mehr geändert, weil daran verwiesen wird
* `titel` — ein Satz in Alltagssprache, kein Gesetzeszitat
* `klassen` und `rollen` — wer sie wann erfüllen muss; leer heißt: gilt für
  alle
* `rechtsgrundlage` — Kennungen wie `KI-VO/art-26/abs-1`, **die im Korpus
  vorhanden sein müssen**
* `fundstellen_text` — das Zitat, wie es in der Auskunft steht
* `gilt_ab` — der Geltungsbeginn nach Artikel 113
* `was_zu_tun_ist`, `nachweis`, `bei_verstoss`

Nach einer Änderung prüfen, dass die Dateien lesbar sind und die Zahlen
stimmen:

```bash
PYTHONPATH=src python -c "
from helfer.einstufung.pruefer import regelwerk
w = regelwerk()
print('Stand:', w.stand)
print('Pflichten:', len(w.pflichten))
print('Datenschutzabschnitte:', len(w.datenschutz))
print('Fristenstufen:', len(w.fristen))
"
```

Erwartet, nachgemessen am 04.10.2026: Stand 2026-05-31, 57 Pflichten, 26
Abschnitte, 5 Fristenstufen.

Und prüfen, dass jede genannte Rechtsgrundlage im Korpus steht:

```bash
PYTHONPATH=src python -c "
import json, yaml
vorhanden = {json.loads(z)['kennung'] for z in open('daten/aufbereitet/korpus.jsonl', encoding='utf-8')}
fehlt = set()
for datei in ('kivo_pflichten.yaml', 'dsgvo_pruefpfad.yaml'):
    d = yaml.safe_load(open('daten/regeln/' + datei, encoding='utf-8'))
    for satz in (d.get('pflichten') or d.get('abschnitte') or []):
        for k in satz.get('rechtsgrundlage', []):
            if k not in vorhanden:
                fehlt.add(k)
print('ohne Fundstelle im Korpus:', len(fehlt))
for k in sorted(fehlt)[:20]:
    print(' ', k)
"
```

Eine Pflicht, deren Rechtsgrundlage im Korpus fehlt, erscheint in der Auskunft
ohne Belegstelle im Wortlaut. Das ist kein Absturz, aber ein Mangel. Dasselbe
gilt für die `fundstelle` einer Frage: zeigt sie auf nichts, fehlt im Befund
der amtliche Text zum Nachlesen.

Jede Änderung gehört in [CHANGELOG.md](../CHANGELOG.md).

### Was sich erfahrungsgemäß ändert

* **Die Leitlinien.** Der Entwurf vom 19.05.2026 ist nicht bindend, und die
  Anhörung lief bis zum 23. Juni 2026. Kommt die endgültige Fassung, sind die
  Absatznummern neu zu prüfen — jede Frage trägt eine.
* **Fristen.** Artikel 113 nennt die Geltungstermine. Der Vorbehalt dazu steht
  im Regelwerk, weil einzelne Termine zum Datenstand politisch erörtert wurden.
* **Anhang III.** Die Kommission kann die Liste der Hochrisikobereiche durch
  delegierte Rechtsakte ändern. Dann ändern sich die Fragedateien **und**
  `daten/regeln/kivo_risikoklassen.yaml`.
* **Bundesdatenschutzgesetz.** Herangezogen sind nur Teile 1 und 2, also die
  Durchführungsbestimmungen zur Datenschutz-Grundverordnung. Teil 3 gilt nach
  § 45 nur für Behörden im Bereich der Strafverfolgung und ist absichtlich
  nicht dabei.

---

## Wenn etwas nicht geht

### Die Webseite zeigt keine Fragen

Dann fehlt `fragefolge.json` neben `index.html` oder sie ist unvollständig. Neu
erzeugen:

```bash
python scripts/fragefolge_ausgeben.py --ziel web/fragefolge.json
```

Die Seite lädt die Datei mit `fetch("./fragefolge.json")`, also aus demselben
Verzeichnis. Wird `index.html` als Datei vom Dateisystem geöffnet statt über
einen Webserver ausgeliefert, verweigern manche Browser diesen Abruf. Dann ein
beliebiger kleiner Webserver im Ordner `web/`:

```bash
python -m http.server 8080 --directory web
```

### Webseite und Programm stufen denselben Fall verschieden ein

Das ist ein Fehler und gehört gemeldet — mit den Antworten, die zu beiden
Ergebnissen geführt haben. Nachmessen:

```bash
python scripts/pruefe_zwei_wege.py --laeufe 400
```

Der Lauf nennt die erste Stelle, an der die beiden Fassungen auseinandergehen:
dieselbe Frage in derselben Reihenfolge, dieselbe Gruppe auf demselben Blatt,
derselbe Befund. Häufigste Ursache: `web/fragefolge.json` ist älter als die
YAML-Dateien. Erst neu erzeugen, dann vergleichen.

### Der Befund lautet „bedingt hochriskant"

Kein Fehler. Es heißt: alles trifft zu bis auf eine Bedingung, die Sie nicht
wissen können. Bei Anhang III Nummer 2 verlangt Absatz (190) der Leitlinien,
dass ein Mitgliedstaat den Betreiber förmlich als kritische Einrichtung benannt
hat — und Absatz (191) stellt fest, dass diese Benennung dem Anbieter nicht
offengelegt werden muss. Rechnen Sie damit, dass ein solcher Betreiber zu Ihren
Kunden gehört, so gelten die Pflichten für Hochrisiko-KI-Systeme.

### Der Dienst startet nicht: „Address already in use"

Der Port ist belegt. Anderen Port nehmen (`--port 8001`) oder nachsehen, was
dort hört:

```bash
ss -tlnp | grep 8000
```

Das gepackte Programm sucht sich selbst einen freien Anschluss zwischen 8713
und 8799.

### „Für bge-m3 fehlt das Paket FlagEmbedding"

Das Einbettungsmodell für die Volltextsuche ist nicht da. Entweder
nachinstallieren:

```bash
pip install -e ".[suche]"
```

oder mit dem kleinen Modell arbeiten
(`--modell intfloat/multilingual-e5-small`), oder ohne Suche auskommen — die
Einstufung braucht kein Modell.

`scripts/bestand_bauen.py` bricht ab, wenn das gewünschte Modell fehlt, und
schreibt dann nichts. Das ist gewollt: ein Bestand in Ersatzqualität sieht heil
aus und liefert still falsche Treffer. Wer wirklich ohne Modell bauen will, um
die Mechanik auszuprobieren, nimmt `--ersatz`; der Bestand taugt dann nicht für
den Betrieb.

### „Der Bestand wurde mit X gebaut, geladen ist Y"

Einbettungen verschiedener Modelle sind nicht vergleichbar — jedes Modell
rechnet seine eigenen Zahlenreihen. Entweder dasselbe Modell laden oder den
Bestand neu bauen:

```bash
python scripts/bestand_bauen.py --modell <das Modell des Bestands>
```

### „Bestand und Korpus passen nicht zusammen"

Der Korpus wurde nach dem Bestand neu gebaut. Das ist kein Fehler, sondern die
Prüfung, die genau das verhindern soll: ohne sie zeigte jeder Vektor auf die
falsche Fundstelle, und die Antwort sähe aus wie immer. Neu bauen:

```bash
python scripts/bestand_bauen.py
```

Der Lauf braucht auf einem Hauptprozessor knapp eine Stunde und legt alle 64
Einheiten einen Zwischenstand ab. Bricht er ab — unter 8 Gigabyte
Arbeitsspeicher kommt das vor —, einfach erneut starten: er überspringt, was
schon gerechnet ist, und sagt am Ende, wie viel er übernommen hat.

### „ANTHROPIC_API_KEY ist nicht gesetzt" / „OPENAI_API_KEY ist nicht gesetzt"

Kein Fehler, sondern eine Feststellung. Ohne Schlüssel läuft alles weiter; die
Auskunft kommt dann unmittelbar aus dem Regelwerk und trägt die Warnung „Diese
Auskunft ist ohne Sprachmodell entstanden und deshalb knapper formuliert." Wer
einen Schlüssel setzen will, siehe oben Abschnitt b.

### EUR-Lex liefert nur ein paar Kilobyte

Dann wird die falsche Adresse abgefragt. Die **Webseite** von EUR-Lex antwortet
ohne vollständigen Browser-Kopf mit HTTP 202 und null Byte und schickt danach
ein Captcha ihrer Firewall — sechs Versuche brachten jeweils 2035 Byte. Davor
hilft keine Wartezeit und keine Kopfzeile.

Der amtliche Text kommt darum nicht von der Webseite, sondern aus der Ablage
**Cellar**, vor der diese Firewall nicht steht:

```bash
python scripts/holen_amtsblatt.py
```

Das Skript holt beide Verordnungen über
`http://publications.europa.eu/resource/cellar/<Kennung>` mit
`Accept: application/xhtml+xml` und `Accept-Language: deu` und verwirft jede
Antwort unter der Mindestgröße — eine halbe Datei wäre schlimmer als keine. Die
Kennungen stehen in [datenquellen.md](datenquellen.md).

Die Rückfallquellen (`scripts/holen_kivo.py`, `scripts/holen_dsgvo.py`) greifen
nur noch ein, wenn der amtliche Text für einen Rechtsakt **ganz** fehlt. Das
ist Absicht: vorher mischten sie ihre Kennungen (`art-4/abs-14`) neben die
amtlichen (`art-4/nr-14`), und beide standen im Bestand.

### Die Prüfreihe wird mitten im Lauf abgebrochen („Killed")

Der Arbeitsspeicher reicht nicht. Die Suchprüfungen bauen den Suchbestand mit
bge-m3 im Speicher; unter 8 Gigabyte geht die ganze Reihe in einem Lauf nicht
durch. Dann dateiweise prüfen:

```bash
for f in tests/test_*.py; do python3 -m pytest "$f" -q; done
```

### ruff oder mypy melden etwas

Dann ist etwas zu beheben. Nachgemessen am 04.10.2026 laufen `ruff check .`,
`ruff format --check .` und `mypy src` ohne Beanstandung durch, und der
Prüfstand bricht bei einem Befund ab. Ein Lauf, der dauerhaft rot ist, wird
nicht gelesen — dann fällt auch der erste echte Fehler nicht auf. Jede Ausnahme
wird in `pyproject.toml` begründet.

Alles auf einmal, in derselben Reihenfolge wie der Prüfstand auf GitHub:

```bash
scripts/alles_pruefen.sh
scripts/alles_pruefen.sh --alles   # zusätzlich Container und Präsentation
```

### Der Dienst antwortet, aber die Suche findet nichts Brauchbares

`konformitaetshelfer stand` ansehen. Steht dort „Einbettungsmodell
streuwerk-ersatz", liegt kein Suchbestand vor; dann vergleicht die Suche nur
Wörter und keine Bedeutung. Abhilfe:

```bash
pip install -e ".[suche]"
python scripts/bestand_bauen.py
```

Die Einstufung ist davon nicht betroffen — sie braucht keinen Suchbestand.
