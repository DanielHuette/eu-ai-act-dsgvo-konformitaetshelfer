# Mitarbeit

Danke, dass Sie sich die Mühe machen. Dieses Blatt sagt, wohin was gehört und
was eine Änderung erfüllen muss, um übernommen zu werden.

Eine Besonderheit vorweg: **Rechtsfehler werden anders behandelt als
Programmfehler.** Ein Programmfehler ärgert den, der ihn trifft. Ein falscher
Artikelverweis geht in eine Auskunft ein, nach der jemand eine Entscheidung
trifft. Deshalb hat er einen eigenen Weg, eine eigene Vorlage und Vorrang vor
allem anderen. Siehe [Rechtsfehler](#rechtsfehler).

## Welchen Weg nehme ich?

| Ihre Lage | Weg |
|---|---|
| Ein Artikelverweis, eine Frist, eine Einstufung oder ein Pflichttext ist falsch | Vorlage **Rechtsfehler** (`rechtsfehler.yml`) |
| Etwas stürzt ab oder tut nicht, was dasteht | Vorlage **Fehler** (`fehler.yml`) |
| Etwas fehlt | Vorlage **Wunsch** (`wunsch.yml`) |
| Eine Sicherheitslücke | **Nicht öffentlich.** Nach [SECURITY.md](SECURITY.md) |
| Eine Verständnisfrage | Diskussionen, oder ein Fehlerbericht, wenn die Dokumentation die Antwort hätte geben müssen |

## Rechtsfehler

### Warum ein eigener Weg

Das Werkzeug ordnet KI-Vorhaben rechtlich ein. Ist ein Verweis falsch, ist die
Auskunft falsch — und zwar für jeden, der das Werkzeug benutzt, nicht nur für
den, der den Fehler bemerkt hat. Deshalb:

* Rechtsfehler werden **vor** allen anderen Meldungen bearbeitet.
* Eine Meldung wird nicht geschlossen, weil sie alt ist.
* Lässt sich der Fehler nicht gleich beheben, kommt zuerst eine Warnung in den
  betroffenen Datensatz, dann die Berichtigung.

### Was in die Meldung gehört

Die Vorlage fragt es ab; hier die Begründung dazu:

1. **Was das Werkzeug sagt.** Die Eingabe, die zu der Auskunft geführt hat, und
   die Ausgabe — am besten als Text zum Mitlesen. Ohne die Eingabe ist der Fehler
   nicht nachzustellen, weil die Einstufung von der Beschreibung abhängt.
2. **Was richtig wäre.** Nicht nur „das stimmt nicht", sondern die richtige
   Angabe.
3. **Die Fundstelle, auf die Sie sich stützen.** Artikel, Absatz, Nummer,
   Buchstabe. Bei der KI-Verordnung bitte am Amtsblatt vom 12. Juli 2024 oder an
   einer späteren berichtigten Fassung — und sagen Sie, welche Sie benutzt
   haben. Bei nationalem Recht der Paragraf samt Gesetz.
4. **Woher Ihre Fundstelle kommt.** Amtsblatt, Bundesgesetzblatt, Entscheidung
   eines Gerichts mit Aktenzeichen, Leitlinie mit Datum. Ein Verweis auf einen
   Blogbeitrag genügt nicht, weil daraus keine Berichtigung werden kann.
5. **Welche Datei betroffen ist**, wenn Sie es wissen: `kivo_pflichten.yaml`,
   `kivo_risikoklassen.yaml`, `dsgvo_pruefpfad.yaml`, eine Fallbeispieldatei
   oder der Rechtsbestand selbst.

### Vier Arten von Rechtsfehlern und was mit ihnen geschieht

* **Falscher Verweis** (die Pflicht steht in Artikel 27, nicht 26). Wird
  berichtigt, sobald die Fundstelle belegt ist. Das ist der einfachste Fall.
* **Falsche Frist.** Wird berichtigt. Dabei wird der Stand in der Datei
  mitgeführt und der Vorbehalt geprüft.
* **Falscher Pflichtinhalt** (die Pflicht verlangt etwas anderes). Braucht die
  Fundstelle im Wortlaut, weil der Text in `was_zu_tun_ist` eine Zusammenfassung
  ist und daran gemessen wird.
* **Falsche Einstufung** (das System fällt nicht unter Anhang III, oder doch).
  Der schwierigste Fall, weil hier eine Wertung steckt. Ist die Rechtslage
  umstritten, wird die Einstufung nicht einfach umgedreht. Dann bekommt der
  betroffene Regelsatz einen Hinweis auf den Streitstand und eine niedrigere
  Sicherheit (`zu_pruefen` statt `wahrscheinlich`), und die offene Frage kommt
  dazu. Eine strittige Frage als entschieden darzustellen wäre der größere
  Fehler.

### Was nicht als Rechtsfehler gilt

* **„Die Liste ist zu lang."** Das ist bekannt und beschrieben: die Pflichten
  werden nach Klasse und Rolle ausgewählt, nicht nach den Merkmalen des
  Vorhabens. Siehe [docs/architektur.md](docs/architektur.md), „Grenzen des
  Systems". Ein Wunsch nach einer genaueren Auswahl ist willkommen — als
  Wunsch.
* **„Das ist keine Rechtsberatung."** Richtig, das steht so da. Siehe
  [docs/haftung.md](docs/haftung.md).
* **Eine andere Auffassung ohne Fundstelle.** Rechtsauffassungen können
  auseinandergehen; das Regelwerk folgt dem Wortlaut und sagt, wo es unsicher
  ist. Ohne Fundstelle lässt sich daran nichts ändern.

## Änderungen am Regelwerk

Das Regelwerk liegt in `daten/regeln/*.yaml`. Wer dort etwas ändert:

1. **Den Stand mitändern.** Jede Datei hat im Kopf ein Feld `stand` und einen
   `hinweis_zum_stand`. Der Stand erscheint in jeder Auskunft; ein falsches
   Datum ist schlimmer als ein altes.
2. **Kennungen nicht ändern.** Das Feld `kennung` einer Pflicht oder eines
   Abschnitts wird verwiesen — aus den Fallbeispielen, aus der App-Datenbank.
   Eine Pflicht, die inhaltlich etwas anderes wird, bekommt eine neue Kennung.
3. **Rechtsgrundlagen als Kennungen angeben**, in der Form
   `KI-VO/art-26/abs-1`, `DSGVO/art-35`, `BDSG/par-26`. Sie müssen im Korpus
   vorhanden sein, sonst erscheint die Pflicht ohne Belegstelle im Wortlaut.
   Prüfbefehl in [docs/betriebsanleitung.md](docs/betriebsanleitung.md),
   Abschnitt c.
4. **In Alltagssprache schreiben.** Der `titel` ist ein Satz, kein
   Gesetzeszitat. `was_zu_tun_ist` sagt, was zu tun ist, nicht was das Gesetz
   sagt. Jeden Fachbegriff beim ersten Vorkommen erklären, jede Abkürzung
   ausschreiben.
5. **Die Zahlen nachmessen**, nicht erinnern:

```bash
PYTHONPATH=src python -c "
from helfer.einstufung.pruefer import regelwerk
w = regelwerk()
print('Stand:', w.stand, '| Pflichten:', len(w.pflichten),
      '| Datenschutzabschnitte:', len(w.datenschutz))
"
```

6. **Den Export für die App erneuern**, damit Rechner und Telefon dasselbe
   Regelwerk haben:

```bash
python scripts/export_android.py
```

7. **In [CHANGELOG.md](CHANGELOG.md) eintragen**, unter „Unveröffentlicht".
   Eine Änderung am Regelwerk ist für die Nutzer wichtiger als jede
   Programmänderung.

## Änderungen am Programm

### Voraussetzungen

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[entwicklung]"
```

### Was laufen muss

Das Gleiche, was in `.github/workflows/pruefung.yml` läuft:

```bash
ruff check .
ruff format --check .
mypy src
bandit -c pyproject.toml -r src scripts --skip B301,B403,B310,B608,B615
pip-audit
pytest -m "not langsam and not netz"
```

**Was den Lauf abbricht und was nicht.** `bandit`, `pip-audit`, `pytest` und
die beiden Gegenproben am Regelwerk brechen ab — dort soll ein neuer Befund
auffallen. `ruff` und `mypy` laufen als Hinweis. Grund: nachgemessen am
03.10.2026 meldet `ruff check .` 277 Punkte, davon 246 die Regel UP031, also
die Schreibweise `"%s" % wert`, die im ganzen Projekt durchgehend verwendet
wird; `mypy src` meldet 28 Punkte. Ein Lauf, der von Anfang an rot ist, wird
nicht gelesen, und dann fällt der erste echte Fehler nicht auf.

Daraus folgt für Sie: **bringen Sie keine neuen Punkte hinzu.** Ohne die
Stilregeln sind es derzeit 16:

```bash
ruff check --ignore UP031,UP042,RUF100 .
```

Die fünf Ausnahmen bei `bandit` sind im Prüflauf einzeln begründet. Wer eine
davon braucht, begründet sie dort, nicht hier.

Zwei Marken sind festgelegt: `langsam` für Prüfungen, die die lokalen Modelle
brauchen, und `netz` für solche, die Netzzugang brauchen. Beides läuft in der
Prüfung **nicht** mit — der Lauf lädt keine Modelle herunter. Wer eine Prüfung
schreibt, die ein Modell braucht, markiert sie mit `@pytest.mark.langsam`.

**Stand:** das Verzeichnis `tests/` ist leer. Prüfungen für den Python-Teil
sind ein offener Punkt und besonders willkommen. Ein guter Anfang wären: die
Einstufung gegen die 44 Fallbeispiele (jeder Fall nennt seine erwartete
Einstufung), die Auflösung von Fundstellen, die Rangfusion und
`erfundene_fundstellen`.

### Was eine Änderung erfüllen muss

* **Deutsch.** Bezeichner, Kommentare, Meldungen. Siehe
  [docs/entscheidungen.md](docs/entscheidungen.md), E10.
* **Der Dateikopf sagt das Warum.** Jede Datei im Projekt beginnt mit einem
  Text, der erklärt, warum sie so ist, wie sie ist, und welche Entscheidung
  dahinter steht. Wer eine Datei anlegt, schreibt diesen Kopf mit. Wer eine
  Entscheidung ändert, ändert ihn mit.
* **Fachbegriffe erklären.** Beim ersten Vorkommen in Alltagssprache, jede
  Abkürzung ausgeschrieben. Das gilt im Quelltext wie in der Dokumentation.
* **Keine erfundene Zahl.** Jede Mengenangabe in Dokumentation oder Kommentar
  wird nachgemessen. `wc -l`, Zeilen zählen, die Datei öffnen — nicht
  schätzen, nicht erinnern.
* **Was nicht geprüft ist, steht als nicht geprüft da.** Eine Vermutung wird
  als Vermutung geschrieben.
* **Die Trennung von Einstufung und Formulierung bleibt.** Eine Änderung, nach
  der ein Sprachmodell die Risikoklasse oder eine Pflicht bestimmt, wird nicht
  übernommen — auch nicht als Rückfall, auch nicht hinter einem Schalter. Das
  ist die Grundentscheidung des Projekts, siehe
  [docs/entscheidungen.md](docs/entscheidungen.md), E1.
* **Keine Diagnoseanzeigen im fertigen Werkzeug.** Was das Werkzeug kann, muss
  am Ergebnis ablesbar sein. Betriebsmeldungen gehören ins Protokoll, nicht in
  die Auskunft.

### Änderungen an der Android-App

```bash
python android/pruefung/kotlin_pruefen.py     # Vorprüfung ohne Android-Paket
cd android && ./gradlew test                  # die 65 Prüfungen
```

Zwei Dinge sind dort aus Gründen festgelegt und werden nicht nebenbei geändert:

* Die Fassung der ONNX-Laufzeit ist auf 1.28.0 festgelegt, weil spätere
  Fassungen nach dem Prüfvermerk im Quelltext Berechtigungen anmelden und einen
  Dienst für Telemetrie starten. Wer sie erhöhen will, prüft das nach und
  schreibt das Ergebnis in `android/gradle/libs.versions.toml`.
* Die Berechtigungen `ACCESS_NETWORK_STATE` und `READ_PHONE_STATE` sind im
  Manifest ausdrücklich entfernt. Diese Zeilen bleiben stehen.

## Änderungsvorschläge einreichen

* Ein Vorschlag, eine Sache. Ein Vorschlag, der ein Regelwerk ändert **und**
  etwas umbaut, lässt sich nicht prüfen.
* In der Beschreibung steht, welchen Fehlerbericht er erledigt und wie man es
  nachprüft.
* Umbenennen, Umsortieren, Formatieren und Aufräumen ohne Wirkung werden nicht
  übernommen. Wer eine Sache verbessert, verbessert die Sache.
* Mit dem Einreichen stellen Sie Ihren Beitrag unter die Apache License 2.0
  (Abschnitt 5 des Lizenztexts). Ein Zusatzvertrag ist nicht zu
  unterschreiben.
* Wer mehr als eine Kleinigkeit beiträgt, darf sich in
  [AUTHORS.md](AUTHORS.md) eintragen.

## Umgangston

Es gilt der [Verhaltenskodex](CODE_OF_CONDUCT.md). Kurz: sachlich bleiben, auch
wenn jemand etwas Falsches sagt — besonders bei Rechtsfragen, wo
Auffassungen auseinandergehen und das nicht an der Person liegt.
