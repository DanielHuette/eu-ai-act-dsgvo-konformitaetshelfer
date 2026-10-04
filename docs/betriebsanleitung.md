# Betriebsanleitung

Drei Leserkreise, drei Abschnitte. Lesen Sie den, der auf Sie passt.

* [a) Ich will es nur benutzen](#a-ich-will-es-nur-benutzen)
* [b) Ich stelle es im Unternehmen auf](#b-ich-stelle-es-im-unternehmen-auf)
* [c) Ich will die Rechtsdaten aktualisieren](#c-ich-will-die-rechtsdaten-aktualisieren)
* [Wenn etwas nicht geht](#wenn-etwas-nicht-geht)

Eine Vorbemerkung zum Stand: es gibt vier Wege, das Werkzeug zu benutzen — den
Container, die Kommandozeile, den Webdienst im Browser und die Android-App. Das
Container-Abbild ist in diesem Verzeichnis allerdings noch nie gebaut worden;
die Angaben dazu stammen aus den Dateien. Was sonst fehlt, steht in
[architektur.md](architektur.md) unter „Was noch nicht da ist".

---

## a) Ich will es nur benutzen

### Der einfachste Weg: die Android-App

Die App trägt alles auf dem Gerät. Kein Konto, keine Anmeldung, kein Netz.

1. Auf dem Telefon das Verzeichnis
   `github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer` öffnen, dort
   **Releases**, und die Datei `konformitaetshelfer-<Fassung>.apk`
   herunterladen. Gibt es noch keine Veröffentlichung, liegt das Paket unter
   **Actions** beim letzten erfolgreichen Lauf „Android-Paket bauen" als
   Artefakt `konformitaetshelfer-apk` — das ist ein ZIP-Archiv, die APK-Datei
   steckt darin.
2. Die Datei antippen. Android fragt nach der Erlaubnis für Apps aus
   unbekannter Quelle: dem Hinweis folgen, den Schalter für die Browser- oder
   Dateien-App umlegen, zurückgehen, „Installieren" tippen.
3. Öffnen und das Vorhaben beschreiben oder den Fragebogen durchgehen.

Voraussetzung ist Android 8.0 oder neuer. Das Paket ist nicht unterschrieben;
Android zeigt deshalb den Hinweis auf die unbekannte Quelle.

Wollen Sie die Auskunft zusätzlich ausformuliert haben, können Sie in den
Einstellungen einen eigenen Schlüssel für Claude oder GPT eintragen. Dann — und
nur dann — braucht die App Netz. Die Einstufung selbst kommt immer aus dem
Regelwerk auf dem Gerät. Der Schlüssel liegt verschlüsselt im
Schlüsselspeicher des Geräts, wird nicht protokolliert und nicht gesichert.

### Auf dem Rechner, ohne Modell und ohne Schlüssel

Gebraucht werden Python 3.11 oder neuer und dieses Verzeichnis.

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e .
```

Eine Einstufung — ohne Modell, ohne Schlüssel, ohne Netz:

```bash
konformitaetshelfer pruefen "Wir sind eine Spedition mit 300 Mitarbeitern und
wollen eine zugekaufte Software einsetzen, die Bewerbungen automatisch
vorsortiert."
```

Prüfen, womit das Werkzeug gerade arbeitet und was fehlt:

```bash
konformitaetshelfer stand
```

Lieber im Browser? Dann den Dienst starten und `http://127.0.0.1:8000` öffnen:

```bash
konformitaetshelfer dienst --port 8000
```

Keine Farbe im Protokoll: `--ohne-farbe`, oder `NO_COLOR` setzen. Geht die
Ausgabe in eine Datei statt an ein Fenster, schaltet sich die Farbe von selbst
ab.

Je genauer die Beschreibung, desto belastbarer die Auskunft. Nützlich sind:
was das System tun soll, ob Sie es selbst entwickeln oder einkaufen, wie viele
Beschäftigte Sie haben, ob personenbezogene Daten verarbeitet werden, ob ein
Mensch das Ergebnis prüft, bevor es wirkt, und ob Daten in ein Land außerhalb
der Europäischen Union gehen.

Lesen Sie die offenen Fragen am Ende der Auskunft. Sie sagen, welche Angabe die
Einstufung noch kippen könnte.

---

## b) Ich stelle es im Unternehmen auf

### Was Sie entscheiden müssen, bevor Sie anfangen

1. **Soll eine Antwort ausformuliert werden?** Ohne Sprachmodell läuft alles,
   nur nüchterner. Mit Sprachmodell geht die Beschreibung des Nutzers an den
   Anbieter dieses Modells — bei einem Vorhaben, das Geschäftsinterna enthält,
   ist das eine Entscheidung mit Folgen. Ein Modell auf dem eigenen Rechner
   über Ollama vermeidet das.
2. **Soll im Rechtstext gesucht werden?** Dann brauchen Sie das
   Einbettungsmodell (rund 2,3 Gigabyte) und einen einmaligen Rechenlauf.
3. **Wer pflegt den Datenstand?** Die Rechtslage ändert sich. Ohne
   Zuständigkeit dafür veraltet das Werkzeug still.

### Aufstellen als Container — der kürzeste Weg

```bash
git clone https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer.git
cd eu-ai-act-dsgvo-konformitaetshelfer
cp .env.example .env          # und ausfüllen, soweit nötig
./scripts/start.sh            # Windows: scripts\start.ps1
```

Das Skript prüft die Voraussetzungen und sagt bei jedem Mangel, was zu tun ist,
statt eine Meldung von Docker durchzulassen. Schalter: `--klein` (ohne das
große Suchmodell), `--mit-ollama` (Sprachmodell im Verbund), `--neu` (ohne
Zwischenspeicher neu bauen), `--stopp`.

Von Hand: `docker compose up --build`. Das Abbild wird rund 5 Gigabyte groß,
weil das Einbettungsmodell mit hineinkommt — ohne es wäre die mitgelieferte
Suchdatenbank ohne Netz wertlos.

Was im Verbund so eingestellt ist: der Dienst läuft unter dem Nutzer `helfer`
(Kennung 10001) ohne Verwalterrechte, mit nur lesendem Dateisystem, mit
abgelegten Fähigkeiten und nach außen nur an `127.0.0.1` gebunden. Der
Zustandsbericht fragt `/gesundheit` und wertet „nicht_bereit" als krank — ein
Dienst, dessen Korpus fehlt, antwortet zwar, ist aber nicht betriebsbereit.
Ollama kommt nur mit, wenn das Profil `ollama` gewählt ist.

**Nicht geprüft:** dass dieser Bau durchläuft. In diesem Verzeichnis ist das
Abbild nie gebaut worden.

### Aufstellen ohne Container

```bash
git clone https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer.git
cd eu-ai-act-dsgvo-konformitaetshelfer
python -m venv .venv
source .venv/bin/activate
pip install -e ".[suche]"            # mit Suche
# pip install -e ".[suche,modelle]"  # zusätzlich Claude oder GPT
```

Suchbestand einmal bauen. Das Modell wird dabei heruntergeladen und dauert auf
einem Hauptprozessor einige Minuten:

```bash
python scripts/bestand_bauen.py
```

Der Lauf schreibt sein Protokoll nach `daten/aufbereitet/_bestand_lauf.log` und
prüft sich am Ende selbst mit einer Frage, deren Antwort bekannt ist. Danach
liegen neben `daten/aufbereitet/suchbestand` die Dateien `.vektoren.npy`,
`.bestand.json.gz` und `.bestand.json`.

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

Dieselben Werte stehen auch in Umgebungsvariablen: `HELFER_ADRESSE` und
`HELFER_PORT`. Weitere Schalter des Dienstes:

| Variable | Wirkung |
|---|---|
| `HELFER_MODELL` | welches Sprachmodell formulieren soll: `anthropic`, `openai`, `ollama` oder `auto` |
| `HELFER_EINBETTUNG` | welches Einbettungsmodell die Suche nimmt |
| `HELFER_NEUBEWERTUNG` | auf `1` setzen, damit der Kreuzbewerter die besten 30 Treffer neu sortiert |
| `HELFER_ADRESSE`, `HELFER_PORT` | wo der Dienst hört |

**Standardmäßig hört der Dienst nur auf `127.0.0.1`**, also nur auf dem eigenen
Rechner. Wer ihn im Haus anbietet, beachtet:

* Der Dienst hat **keine Anmeldung**. Wer ihn erreicht, kann ihn benutzen. Eine
  Zugangssperre gehört davor — ein vorgeschalteter Server oder das Netz selbst.
* Es gibt einen Zähler je Adresse gegen Überlast, aber keine Benutzerverwaltung
  und keine Abrechnung.
* Der Dienst soll **nicht als Verwalter** laufen. `konformitaetshelfer stand`
  weist darauf hin, wenn er das tut.
* `GET /gesundheit` eignet sich als Prüfpunkt für eine Überwachung.
* Was die Schnittstellen annehmen und zurückgeben, zeigt der Dienst selbst an.

Der Dienst lädt Korpus, Suchbestand und Regelwerk beim Start in den Speicher.
Der erste Start dauert deshalb länger als die erste Antwort danach.

### Schlüssel setzen, wenn ein Sprachmodell formulieren soll

```bash
export ANTHROPIC_API_KEY="…"     # für Claude
export OPENAI_API_KEY="…"        # für GPT
export OLLAMA_HOST="http://127.0.0.1:11434"   # für ein Modell auf dem Rechner
```

Ohne Wunsch wird in dieser Reihenfolge gesucht: Claude, GPT, Ollama. Ist nichts
erreichbar, entsteht die Auskunft aus dem Regelwerk und sagt das in einer
Warnung dazu.

Legen Sie Schlüssel nicht in eine Datei im Verzeichnis. `.gitignore` hält
`.env` zwar heraus, aber ein Schlüssel in einer Datei ist ein Schlüssel, der
einmal versehentlich mitwandert.

### Das Android-Paket selbst bauen

Der Bau läuft in GitHub Actions, weil er das Android-Entwicklungspaket, Java 21
und das Einbettungsmodell braucht — zusammen einige Gigabyte:

* Eine Marke mit `v` davor schieben (etwa `v1.0.1`), dann baut der Lauf und
  hängt das Paket an die Veröffentlichung.
* Oder den Lauf „Android-Paket bauen" von Hand starten; dann liegt das Paket
  als Artefakt beim Lauf.

Vor dem Bau des Pakets erzeugt der Lauf die App-Datenbank neu
(`scripts/export_android.py`) und bricht ab, wenn eine Tabelle leer bleibt oder
die Beispielsuche nichts findet. Danach laufen die 65 Kotlin-Prüfungen.

Örtlich, falls Android-Entwicklungspaket und Java 21 vorhanden sind:

```bash
pip install "sentence-transformers>=3.0" onnx onnxruntime pyyaml numpy
python scripts/export_android.py --stapel 32
cd android && ./gradlew test assembleRelease
```

### Was Sie den Nutzern sagen müssen

Dass es keine Rechtsberatung ist, und dass die Pflichtenliste eher zu lang als
zu kurz ist: sie enthält alle Pflichten der erkannten Klasse und Rolle, auch
solche, die auf das einzelne Vorhaben nicht passen. Siehe
[architektur.md](architektur.md), Abschnitt „Grenzen des Systems", und
[haftung.md](haftung.md).

---

## c) Ich will die Rechtsdaten aktualisieren

Es gibt zwei Dinge, die veralten, und sie werden getrennt gepflegt:

1. **Der Rechtstext** — der Wortlaut der Verordnungen und des Gesetzes. Er
   liegt in `daten/roh` und wird zu `daten/aufbereitet/korpus.jsonl` gebaut.
2. **Das Regelwerk** — die Einstufungsregeln, die 57 Pflichten und die 26
   Abschnitte des Datenschutzpfads. Das sind von Hand geschriebene
   YAML-Dateien in `daten/regeln`. Sie veralten nicht durch einen neuen
   Textstand, sondern durch neue Rechtsakte, Leitlinien und Rechtsprechung.

### Rechtstext neu holen und bauen

```bash
python scripts/holen_eurlex.py      # amtliche Volltexte, EUR-Lex
python scripts/holen_kivo.py        # KI-Verordnung, artikelweise
python scripts/holen_dsgvo.py       # Datenschutz-Grundverordnung, artikelweise
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
Einheiten. Diese Zahlen stehen als Erwartung in
`src/helfer/korpus/eurlex.py` und in `tests/test_korpus.py`; weicht ein Lauf
ab, steht das als Warnung im Befund und die Prüfung bricht ab.

**Nach jedem Korpusbau muss beides neu gebaut werden,** sonst passen die
Vektoren nicht mehr zum Text:

```bash
python scripts/bestand_bauen.py          # Suchbestand für den Rechner
python scripts/export_android.py         # Datenbank und Einbetter für die App
```

Der Befund der App-Ausgabe steht in
`daten/aufbereitet/android_export_befund.json`, mit Zeilenzahl je Tabelle, der
Prüfsumme des Korpus und einigen Stichproben. Vergleichen Sie die Prüfsumme mit
der des Korpus:

```bash
sha256sum daten/aufbereitet/korpus.jsonl
```

Stimmen die beiden nicht überein, ist die App-Datenbank älter als der Korpus.
Am 04.10.2026 stimmen sie: beide tragen `e6606acd97e9394a…` bei 2811
Einheiten.

### Das Regelwerk ändern

Jede der drei Dateien trägt im Kopf ein Feld `stand` und einen
`hinweis_zum_stand`. **Beides mit ändern** — der Stand erscheint in jeder
Auskunft, und ein falsches Datum ist schlimmer als ein altes.

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

Nach einer Änderung prüfen, dass die Dateien lesbar sind und die Zahlen stimmen:

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
Abschnitte, 5 Fristenstufen. Dazu der Zweckkatalog mit 55 Einträgen, 107
Zwecken und 21 Gegenzwecken:

```bash
PYTHONPATH=src python -c "
from helfer.einstufung.zwecke import katalog_lesen
z = katalog_lesen()
print('Zeilen:', len(z))
print('Fundstellen:', len({x.fundstelle for x in z}))
print('Gegenzwecke:', sum(1 for x in z if x.gegenzweck))
"
```

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
ohne Belegstelle im Wortlaut. Das ist kein Absturz, aber ein Mangel.

Dann den Export für die App erneuern, damit beide Seiten dasselbe Regelwerk
haben, und die Änderung in [CHANGELOG.md](../CHANGELOG.md) eintragen.

### Was sich erfahrungsgemäß ändert

* **Fristen.** Artikel 113 nennt die Geltungstermine. Der Vorbehalt dazu steht
  im Regelwerk, weil einzelne Termine zum Datenstand politisch erörtert wurden.
* **Anhang III.** Die Kommission kann die Liste der Hochrisikobereiche durch
  delegierte Rechtsakte ändern. Dann ändert sich
  `daten/regeln/kivo_risikoklassen.yaml`.
* **Leitlinien.** Sie binden Gerichte nicht, verschieben aber die Praxis. Das
  Datenmodell kennt dafür den Rechtsakt „Leitlinie"; wer solche Fundstellen
  aufnimmt, muss die fehlende Bindungswirkung in der Auskunft mitsagen.
* **Bundesdatenschutzgesetz.** Herangezogen sind nur Teile 1 und 2, also die
  Durchführungsbestimmungen zur Datenschutz-Grundverordnung. Teil 3 gilt nach
  § 45 nur für Behörden im Bereich der Strafverfolgung und ist absichtlich
  nicht dabei.

---

## Wenn etwas nicht geht

### „Für bge-m3 fehlt das Paket FlagEmbedding"

Das Einbettungsmodell ist nicht da. Entweder nachinstallieren:

```bash
pip install -e ".[suche]"
```

oder mit dem kleinen Modell arbeiten
(`--modell intfloat/multilingual-e5-small`), oder ganz ohne Suche auskommen —
die Einstufung braucht kein Modell.

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

### „Bestand und Korpus passen nicht zusammen: N Vektoren, M Einheiten"

Der Korpus wurde nach dem Bestand neu gebaut. Bestand neu bauen:

```bash
python scripts/bestand_bauen.py
```

Dasselbe gilt für die App: weicht die Prüfsumme in
`daten/aufbereitet/android_export_befund.json` von
`sha256sum daten/aufbereitet/korpus.jsonl` ab, muss
`scripts/export_android.py` erneut laufen. Am 04.10.2026 stimmen beide.

### „ANTHROPIC_API_KEY ist nicht gesetzt" / „OPENAI_API_KEY ist nicht gesetzt"

Kein Fehler, sondern eine Feststellung. Ohne Schlüssel läuft alles weiter; die
Auskunft kommt dann unmittelbar aus dem Regelwerk und trägt die Warnung „Diese
Auskunft ist ohne Sprachmodell entstanden und deshalb knapper formuliert." Wer
einen Schlüssel setzen will, siehe oben Abschnitt b.

### „Ollama ist unter … nicht erreichbar"

Die Erreichbarkeit wird beim Wählen geprüft und nicht erst beim Antworten —
sonst wartet man auf eine Antwort, die nie kommt. Prüfen:

```bash
curl http://127.0.0.1:11434/api/tags
ollama serve                       # falls nichts antwortet
```

Läuft Ollama, fehlt aber das Modell, sagt die Meldung, welche Modelle vorhanden
sind, und nennt den Befehl zum Holen:

```bash
ollama pull qwen2.5:7b-instruct
```

Steckt Ollama hinter einer anderen Adresse, `OLLAMA_HOST` setzen.

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

### Eine Einstufung dauert zehn Sekunden oder länger

Der Zweckweg rechnet mit einem Kreuzbewerter, und der kostet je verglichenem
Satzpaar Rechenzeit. Auf zwei Prozessorkernen sind 3 bis 20 Sekunden normal, je
nachdem, wie viele Sätze die Beschreibung hat. Mit Grafikkarte sind es
Millisekunden.

Wer die Einstufung ohne Zweckweg will — schneller, aber ungenauer —, benennt
die Katalogdatei um oder entfernt sie: der Prüfer meldet das im Protokoll und
entscheidet dann allein über die Wortlisten. Gemessen trifft er damit 55 von
100 Unternehmensfragen statt 100. Für den Betrieb ist das keine Empfehlung,
sondern eine Notlösung.

### ruff oder mypy melden etwas

Dann ist etwas zu beheben. Nachgemessen am 04.10.2026 laufen `ruff check .`,
`ruff format --check .` und `mypy src` ohne Beanstandung durch, und der
Prüfstand bricht bei einem Befund ab. Ein Lauf, der dauerhaft rot ist, wird
nicht gelesen — dann fällt auch der erste echte Fehler nicht auf. Jede Ausnahme
wird in `pyproject.toml` begründet.

### Der Dienst startet nicht: „Address already in use"

Der Port ist belegt. Anderen Port nehmen (`--port 8001`) oder nachsehen, was
dort hört:

```bash
ss -tlnp | grep 8000
```

### Der Dienst antwortet, aber die Suche findet nichts Brauchbares

`konformitaetshelfer stand` ansehen. Steht dort „Einbettungsmodell
streuwerk-ersatz", liegt kein Suchbestand vor; dann vergleicht die Suche nur
Wörter und keine Bedeutung. Abhilfe:

```bash
pip install -e ".[suche]"
```

Meldet das Laden „Der abgelegte Bestand gehört zu einem anderen
Rechtsbestand", so ist der Korpus seit dem Bau des Bestands geändert worden.
Das ist kein Fehler, sondern die Prüfung, die genau das verhindern soll: ohne
sie zeigte jeder Vektor auf die falsche Fundstelle, und die Antwort sähe aus
wie immer. Neu bauen:

```bash
python scripts/bestand_bauen.py
```

Der Lauf braucht auf einem Hauptprozessor rund eine Stunde und legt alle 64
Einheiten einen Zwischenstand ab. Bricht er ab — unter 8 Gigabyte
Arbeitsspeicher kommt das vor —, einfach erneut starten: er überspringt, was
schon gerechnet ist, und sagt am Ende, wie viel er übernommen hat.

### Die App findet nichts oder stürzt beim Start ab

Fehlt eine der drei Beigaben — `recht.db`, `einbetter.onnx`, `tokenizer.json` —
taugt das Paket nicht. Der Bau prüft das und bricht ab; ein von Hand gebautes
Paket kann die Prüfung übersprungen haben. Neu bauen lassen und den Befund
unter `daten/aufbereitet/android_export_befund.json` ansehen: `fehler` muss
leer sein, und `zeilen` muss für jede Tabelle eine Zahl größer als null nennen.

### Die App zeigt andere Fundstellen als der Rechner

Kein Fehler. Telefon und Rechner suchen mit verschiedenen Modellen und das
Telefon mit drei statt vier Suchwegen. Die **Einstufung** kommt auf beiden
Seiten aus demselben Regelwerk und muss gleich ausfallen. Fällt sie
unterschiedlich aus, ist das ein Fehler und gehört gemeldet — mit der
Beschreibung, die zu beiden Ergebnissen geführt hat.
