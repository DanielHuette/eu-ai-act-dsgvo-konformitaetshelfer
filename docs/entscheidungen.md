# Architekturentscheidungen

Je Entscheidung: die Lage, die Entscheidung, die Begründung, die Folgen — auch
die unangenehmen. Reihenfolge nach Gewicht, nicht nach Datum.

Ein Eintrag wird nicht gelöscht, wenn er überholt ist, sondern als überholt
gekennzeichnet und mit dem Eintrag verknüpft, der ihn ersetzt. Bisher ist
keiner überholt.

---

## E1 — Die Einstufung ist deterministisch und kommt nicht vom Sprachmodell

**Lage.** Die Aufgabe ist: aus einer Beschreibung in eigenen Worten die
Risikoklasse und die Pflichten ableiten. Ein Sprachmodell kann das scheinbar
unmittelbar — man legt ihm den Verordnungstext vor und fragt. Deterministisch
heißt: dieselbe Eingabe ergibt immer dieselbe Ausgabe.

**Entscheidung.** Die Einstufung entsteht ausschließlich in
`src/helfer/einstufung/pruefer.py` aus einem Entscheidungsbaum, der in
YAML-Dateien liegt. Das Sprachmodell bekommt das Ergebnis als feststehende
Tatsache vorgelegt und darf es nicht ändern. Es formuliert nur.

**Begründung.** Ein Modell, das Pflichten erfinden darf, erfindet Pflichten. Es
antwortet höflich und plausibel auch dann, wenn der genannte Artikel nicht
existiert, und es ist bei derselben Frage zweimal verschieden. Dazu kommt die
Haftungsseite: wer ein Hochrisikosystem für harmlos hält, verfehlt ein Dutzend
Pflichten — Artikel 99 sieht dafür bis zu 15 Millionen Euro oder 3 Prozent des
weltweiten Jahresumsatzes vor, bei verbotenen Praktiken bis zu 35 Millionen
oder 7 Prozent. Eine Auskunft, nach der jemand ein Produkt umbaut oder eben
nicht umbaut, muss nachvollziehbar sein. Der Entscheidungsbaum ist das: jede
Verzweigung trägt eine Regelkennung und eine Fundstelle.

**Folgen.**
* Gut: wiederholbar, bis zur Regel zurückverfolgbar, läuft ohne Modell und ohne
  Netz, und die Einstufung lässt sich nicht durch untergeschobene Anweisungen
  kippen.
* Schlecht: der Baum versteht nur, was in seinen Stichwortlisten steht. Wer
  sein Vorhaben mit anderen Worten beschreibt, wird falsch oder gar nicht
  eingestuft. Ein Sprachmodell wäre hier beweglicher.
* Daher die Gegenmaßnahme: jeder Treffer trägt eine Sicherheit (`sicher`,
  `wahrscheinlich`, `zu_pruefen`), und was die Beschreibung nicht hergibt, wird
  als offene Frage ausgegeben statt geraten.
* Die Pflege wird aufwendiger: jede neue Fallgestaltung braucht eine Regel. Das
  ist der Preis dafür, dass niemand raten muss, woher eine Pflicht kam.

Verknüpft mit [E2](#e2--das-regelwerk-steht-in-yaml-dateien-nicht-im-programmtext).

---

## E2 — Das Regelwerk steht in YAML-Dateien, nicht im Programmtext

**Lage.** Die Regeln sind umfangreich: 28 Einstufungsregeln, 57 Pflichten, 26
Abschnitte des Datenschutzpfads, dazu Fristen und Sanktionen. Sie ändern sich,
und zwar nicht durch Programmierung, sondern durch Rechtsänderungen.

**Entscheidung.** Alles davon liegt in `daten/regeln/*.yaml`. Der Programmtext
liest diese Dateien und wertet sie aus; er enthält selbst keine Pflicht und
keinen Artikelverweis. Jede Datei trägt im Kopf ein Feld `stand` und einen
Vorbehalt dazu.

**Begründung.** Wer eine Frist ändert, soll eine Textzeile ändern und nicht
Programmtext. Das ist für jemanden machbar, der die Rechtslage kennt, aber
nicht programmiert — und das ist genau die Person, die eine Rechtsänderung
zuerst bemerkt. Außerdem ist eine Textdatei in der Versionsverwaltung lesbar:
eine Änderung am Regelwerk ist als Unterschied sichtbar und damit prüfbar, ohne
den Programmtext zu verstehen.

**Folgen.**
* Gut: Rechtsänderung ohne Programmänderung; Änderungen sind nachlesbar; dieselbe
  Datei versorgt Rechner und Telefon, sodass die Einstufung auf beiden Seiten
  gleich ausfällt.
* Schlecht: die Dateien sind nicht schemageprüft. Ein Tippfehler in einem
  Feldnamen führt nicht zum Abbruch, sondern zu einer Pflicht ohne diese
  Angabe. Eine Schemaprüfung fehlt und wäre der nächste sinnvolle Schritt.
* Die Verknüpfung zwischen Regel und Rechtstext ist nur eine Zeichenfolge: eine
  Pflicht nennt `KI-VO/art-26/abs-1` als Rechtsgrundlage. Steht diese Kennung
  nicht im Korpus, erscheint die Pflicht ohne Belegstelle im Wortlaut.
  Nachgemessen am 03.10.2026 ist jede genannte Rechtsgrundlage vorhanden; der
  Prüfbefehl steht in [betriebsanleitung.md](betriebsanleitung.md).

---

## E3 — Vier Suchwege statt einem

**Lage.** Rechtsfragen werden auf zwei Arten gestellt. „Dürfen wir Bewerbungen
vorsortieren?" fragt nach Sinn — das Gesetz sagt „Einstellung oder Auswahl
natürlicher Personen", kein Wort stimmt überein. „Was steht in Artikel 6
Absatz 3?" fragt nach Wortlaut, und zwar genau.

**Entscheidung.** Vier Wege gleichzeitig: Vektorsuche für die Bedeutung,
Stichwortsuche nach BM25 für den Wortlaut, die Wortgewichte des
Einbettungsmodells für das Dazwischen, und ein Fundstellenweg, der eine
genannte Stelle unmittelbar auflöst. Zusammengeführt wird über die Rangplätze,
danach bewertet ein Kreuzbewerter die besten 30 neu.

**Begründung.** Eine Vektorsuche allein verliert genaue Fragen: Zahlen sehen
für sie fast gleich aus, „Artikel 6" und „Artikel 9" liegen dicht beieinander.
Eine Stichwortsuche allein verliert sinngleiche Fragen, weil die Bürger andere
Wörter benutzen als die Verordnung. Der Fundstellenweg ist der wichtigste und
der billigste: wer eine Stelle nennt, soll sie bekommen und nicht etwas
Ähnliches. Er wiegt deshalb dreifach, weil er kein Schätzwert ist, sondern eine
Tatsache.

**Zusammenführung über Rangplätze, nicht über Punktzahlen** (in der Literatur
*Reciprocal Rank Fusion*): für jeden Treffer wird `1 / (60 + Rangplatz)` je Weg
addiert, der ihn gefunden hat. Punktzahlen zu addieren wäre falsch, weil ein
BM25-Wert und ein Kosinusmaß verschiedene Maßstäbe haben — das wäre das
Addieren von Metern und Kilogramm. Die 60 ist der gebräuchliche Wert und dämpft
die Spitze, damit ein einzelner Weg die Liste nicht allein bestimmt.

**Folgen.**
* Gut: beide Frageformen funktionieren; ein Treffer, den nur ein Weg kennt,
  fällt nicht heraus; fällt ein Weg aus (etwa die Wortgewichte, die nur bge-m3
  liefert), tragen die anderen weiter.
* Schlecht: vier Wege sind vier Stellen, an denen etwas schieflaufen kann, und
  die Gewichtung des Fundstellenwegs mit dem Faktor 3 ist nicht gemessen,
  sondern gesetzt. Dass sie richtig ist, ist eine Annahme.
* Die Zahlen 50 Treffer je Weg, 30 zur Neubewertung und 60 in der Rangfusion
  sind ebenfalls gesetzt und nicht an diesem Bestand gemessen.
* Der Kreuzbewerter kostet Rechenzeit, deshalb nur 30 Treffer. Fehlt er, bleibt
  die Reihenfolge der Rangfusion — die Suche fällt nicht aus, sie wird
  ungenauer.

---

## E4 — Lokales Einbettungsmodell statt eines Modells über eine Schnittstelle

**Lage.** Für die Vektorsuche braucht man ein Einbettungsmodell. Die
Schnittstellen von OpenAI und anderen bieten das als Dienst an: bessere
Trefferqualität möglich, kein Modell auf dem Rechner, Abrechnung je Anfrage.

**Entscheidung.** Das Einbettungsmodell läuft örtlich — bge-m3 auf dem Rechner,
multilingual-e5-small auf dem Telefon. Nur die ausformulierte Antwort kann ein
Modell über eine Schnittstelle übernehmen, und das ist freiwillig.

**Begründung.** Zwei Gründe, und beide wiegen schwer. Erstens: wer sein
KI-Vorhaben beschreibt, verrät Geschäftsinterna. Eine Einbettung über eine
Schnittstelle schickt jede Frage zum Anbieter — auch dann, wenn am Ende kein
Sprachmodell formuliert. Zweitens: der mitgelieferte Rechtsbestand muss bei
jedem funktionieren, der das Projekt herunterlädt. Ein Bestand, dessen Vektoren
von einem Dienst stammen, ist ohne Schlüssel bei diesem Dienst nicht abfragbar
— man kann die Frage dann nicht in denselben Zahlenraum bringen. Der Bestand
wäre damit wertlos, und ein Werkzeug, das ohne Konto gar nichts tut, erreicht
die Leute nicht, für die es gedacht ist.

**Folgen.**
* Gut: läuft ohne Schlüssel, ohne Netz, ohne Kosten je Anfrage; die Frage
  verlässt den Rechner nicht; die App funktioniert im Flugmodus.
* Schlecht: 2,3 Gigabyte Modell auf dem Rechner und ein Rechenlauf von einigen
  Minuten, bevor die Suche läuft. Das ist eine Hürde.
* Schlecht: die Trefferqualität der großen Dienste ist nicht erreicht, und das
  ist hier nicht gemessen — es gibt keine Messreihe, die die Wege vergleicht.
* Die Suche hat einen Rückfall auf ein Verfahren über Streuwerte, damit sich die
  Mechanik ohne Modell ausprobieren lässt. `scripts/bestand_bauen.py` bricht
  aber ab, wenn das gewünschte Modell fehlt, statt einen Bestand in
  Ersatzqualität zu schreiben: ein solcher Bestand sieht heil aus und liefert
  still falsche Treffer.

---

## E5 — Zwei Vektorsätze: bge-m3 auf dem Rechner, e5-small auf dem Telefon

**Lage.** Dasselbe Werkzeug läuft auf einem Rechner und auf einem Telefon. Ein
Telefon hat weniger Speicher, weniger Rechenleistung und einen Akku.

**Entscheidung.** Zwei Modelle, zwei getrennte Vektorsätze. Auf dem Rechner
bge-m3 mit 1024 Zahlen je Textstück, auf dem Telefon multilingual-e5-small mit
384 Zahlen, auf 8-Bit-Werte heruntergerechnet. Jeder Bestand trägt den Namen
seines Modells; beim Laden wird geprüft, dass Frage und Bestand aus demselben
Modell kommen.

**Begründung.** bge-m3 ist rund 2,3 Gigabyte groß und liefert 1024 Zahlen je
Einheit — das passt nicht sinnvoll auf ein Telefon. e5-small ist umgewandelt
118,1 Megabyte groß und rechnet eine Frage in Sekundenbruchteilen. Umgekehrt
wäre es Verschwendung, auf dem Rechner das kleine Modell zu nehmen, wo das
große zusätzlich die Wortgewichte liefert und damit einen ganzen Suchweg
mitbringt. Die Prüfung beim Laden ist nötig, weil Einbettungen verschiedener
Modelle **nicht vergleichbar** sind: jedes Modell legt seinen eigenen
Zahlenraum. Ohne diese Prüfung kämen Treffer heraus, die zufällig aussehen und
plausibel sortiert sind.

**Folgen.**
* Gut: jede Seite bekommt das Modell, das zu ihr passt; der Vergleich beim
  Laden macht eine stille Verwechslung unmöglich.
* Schlecht: zwei Bestände müssen gepflegt werden, und nach jeder Änderung am
  Korpus müssen beide neu gebaut werden. Wird das vergessen, laufen sie
  auseinander — nachgemessen am 03.10.2026 war genau das der Fall: die
  App-Datenbank hat 1972 Einheiten, der Korpus 2721.
* Schlecht: dieselbe Frage kann auf Rechner und Telefon verschiedene
  Fundstellen hervorbringen. Die **Einstufung** bleibt gleich, weil sie aus dem
  Regelwerk kommt und nicht aus der Suche — das ist der Grund, warum diese
  Folge tragbar ist.
* Das Telefon hat drei Suchwege statt vier: die Wortgewichte liefert nur
  bge-m3.
* Die 8-Bit-Umwandlung kostet Genauigkeit. Der Ausgabebefund vom 03.10.2026
  nennt eine gemessene Ähnlichkeit von 0,9907 zwischen dem groben und dem
  feinen Modell. Was dieser Wert für die Trefferqualität bedeutet, ist nicht
  gemessen.

---

## E6 — SQLite mit FTS5 in der App statt Room

**Lage.** Die App braucht eine Datenbank für 1972 Rechtseinheiten samt
Volltextsuche, Vektoren, Regelwerk und Fällen. Der gewöhnliche Weg unter
Android ist Room, die Datenbankschicht von AndroidX.

**Entscheidung.** Eine fertig gebaute SQLite-Datei als Beigabe, geöffnet mit
`androidx.sqlite` und dem **mitgelieferten** SQLite
(`androidx.sqlite:sqlite-bundled`), nur lesend. Die Volltextsuche läuft über
FTS5 mit `bm25` und dem Zerteiler `unicode61` samt `remove_diacritics=2`. Kein
Room.

**Begründung.** Room ist dafür gebaut, dass eine App ihre Daten selbst anlegt
und ändert. Hier ist die Datenbank fertig, kommt aus
`scripts/export_android.py` und wird nie geschrieben. Room brächte dafür eine
Schicht aus Jahresmarken, Wanderungsschritten und erzeugten Zugriffsklassen,
die nichts zu tun hat. Entscheidend ist aber FTS5: das ist der Volltextindex
von SQLite, und ohne ihn gibt es keine Stichwortsuche. Dem SQLite des Telefons
fehlt FTS5 je nach Android-Fassung — und zwar still: die Suche liefert dann
einfach weniger. Die mitgelieferte Fassung hat FTS5 eingebaut, nachgemessen am
03.10.2026 an `androidx.sqlite:sqlite-bundled-android:2.7.1`, zusammen mit
`unicode61` und `remove_diacritics=2`. `remove_diacritics=2` macht aus Umlauten
a, o, u; deshalb fragt die App jede Frage auch in umlautfreier Form ab.

Nur lesend geöffnet (`SQLITE_OPEN_READONLY`), weil die App keinen Grund hat zu
schreiben und es mit diesem Zeichen auch durch einen Fehler nicht kann.

**Folgen.**
* Gut: kein Aufbau beim ersten Start, keine Wanderungsschritte, gleiche Suche
  auf jedem Gerät unabhängig von der Android-Fassung, und die Datenbank kann
  nicht beschädigt werden.
* Schlecht: die mitgelieferte SQLite-Fassung vergrößert das Paket. Bei einem
  Paket, das ohnehin ein Einbettungsmodell trägt, fällt das nicht auf.
* Schlecht: die Abfragen sind von Hand geschrieben. Ein Tippfehler in einer
  Abfrage fällt erst beim Ausführen auf, nicht beim Übersetzen — Room würde das
  früher merken. Dagegen stehen 65 Prüfungen im Kotlin-Teil.
* Eine Änderung am Aufbau der Datenbank bedeutet: Ausgabeskript und
  Zugriffsschicht gemeinsam ändern. Es gibt keinen Mechanismus, der das
  erzwingt.

---

## E7 — Ein Fundstellenweg neben den Ähnlichkeitswegen

**Lage.** Fragen zum Recht nennen oft die Stelle: „Was steht in Artikel 6
Absatz 3?", „Gilt Anhang III Nummer 4 für uns?", „§ 26
Bundesdatenschutzgesetz".

**Entscheidung.** Ein eigener Weg löst solche Angaben mit Textmustern in
Kennungen auf — „Art. 6 Abs. 3" wird `KI-VO/art-6/abs-3` — und holt die Einheit
unmittelbar. In der Rangfusion wiegt dieser Weg dreifach.

**Begründung.** Ohne diesen Weg antwortet das System auf eine genaue Frage mit
ungefährer Nähe, und das ist bei Recht die falsche Antwortart. Eine
Vektorsuche kann Artikelnummern nicht zuverlässig unterscheiden. Dass der Weg
dreifach wiegt, folgt daraus, dass er nicht schätzt: wer eine Stelle nennt,
meint sie.

**Folgen.**
* Gut: genaue Fragen bekommen genaue Antworten, und zwar ohne Modell und ohne
  Rechenaufwand.
* Schlecht: der Weg hängt an Textmustern. Eine ungewöhnliche Schreibweise wird
  nicht erkannt, und dann fällt der Weg still aus — die Frage wird dann nur
  noch über Ähnlichkeit beantwortet.
* Schlecht: nennt jemand eine Stelle, die es nicht gibt, findet der Weg nichts
  und sagt es nicht. Die Antwort kommt dann aus den anderen Wegen, ohne Hinweis
  darauf, dass die genannte Stelle nicht existiert.
* Der Faktor 3 ist gesetzt, nicht gemessen.

---

## E8 — Der Rechtsbestand liegt als JSONL im Verzeichnis

**Lage.** 2721 Rechtseinheiten müssen irgendwo liegen. Möglich wären eine
Datenbank, mehrere Dateien je Artikel oder eine einzelne Datei.

**Entscheidung.** Eine Datei, `daten/aufbereitet/korpus.jsonl`, mit einer
JSON-Zeile je Einheit. Sie wandert mit in die Versionsverwaltung.

**Begründung.** Die Form ist absichtlich einfach. Eine Zeile je Einheit ist in
der Versionsverwaltung lesbar: wer einen Rechtstext ändert, sieht genau eine
geänderte Zeile. Sie lässt sich zeilenweise prüfen, auch mit
Kommandozeilenwerkzeugen. Und die Android-Ausgabe kann sie ohne weiteres
einlesen.

**Folgen.**
* Gut: nachvollziehbare Änderungen, einfache Prüfung, keine Datenbank nötig.
* Gut: wer das Projekt herunterlädt, hat den Rechtstext sofort — ohne
  Beschaffungslauf, der an EUR-Lex scheitern kann.
* Schlecht: die Datei ist 2,9 Megabyte groß und wächst mit jeder
  Rechtsänderung in der Versionsverwaltung mit. Das ist tragbar.
* Schlecht: es gibt keine Prüfung, die sicherstellt, dass Korpus, Suchbestand
  und App-Datenbank zusammenpassen. Es gibt nur die Prüfsumme, mit der man es
  feststellen **kann** — und am 03.10.2026 passten sie nicht zusammen.

---

## E9 — Beschaffung getrennt von Verarbeitung

**Lage.** Die Rohquellen kommen aus dem Netz, und das Netz ist unzuverlässig.
EUR-Lex antwortet auf Anfragen ohne vollständigen Browser-Kopf mit HTTP 202 und
leerem Körper und bremst bei wiederholten Abrufen.

**Entscheidung.** Die Beschaffung liegt in eigenen Skripten unter `scripts/`
und schreibt nur nach `daten/roh`. Der Bau des Korpus liest von dort und geht
nie selbst ins Netz. Geholte Dateien werden nicht erneut geholt, wenn sie
vorliegen und eine Mindestgröße erreichen.

**Begründung.** Ein Netzproblem darf den Bestand nicht beschädigen. Wer baut,
soll wissen, dass die Eingangsdaten unverändert daliegen. Und wer die Quellen
prüfen will, hat sie als Datei vor sich, nicht als flüchtige Antwort.

**Folgen.**
* Gut: der Bau ist wiederholbar und läuft ohne Netz; die Rohdateien sind
  prüfbar.
* Gut: wenn EUR-Lex bremst, scheitert nur die Beschaffung, und das steht im
  Protokoll statt in einem halben Korpus.
* Schlecht: der Korpusbau greift bei fehlendem Volltext auf eine nicht amtliche
  Quelle zurück. Das ist eine Warnung im Befund, kein Abbruch. Am 03.10.2026
  ist das für die deutsche Fassung der Datenschutz-Grundverordnung eingetreten
  — 1021 Einheiten stammen daher nicht aus dem Amtsblatt. Siehe
  [datenquellen.md](datenquellen.md).
* Die Mindestgröße als Erkennungsmerkmal ist grob: eine Datei, die groß genug
  ist, aber inhaltlich fehlerhaft, wird nicht erneut geholt.

---

## E10 — Deutsch im Quelltext, in den Daten und in der Oberfläche

**Lage.** Das Werkzeug richtet sich an Mitarbeiter in deutschen Unternehmen.
Der Rechtstext ist deutsch, die Begriffe der Verordnung sind deutsch
festgelegt.

**Entscheidung.** Deutsch durchgehend: Bezeichner im Programmtext, Feldnamen in
den Daten, Spaltennamen in der Datenbank, Oberfläche, Dokumentation. Jeder
Fachbegriff wird beim ersten Vorkommen in Alltagssprache erklärt, jede
Abkürzung ausgeschrieben.

**Begründung.** Die Verordnung legt die Begriffe auf Deutsch fest: Anbieter,
Betreiber, Zweckbestimmung, Inverkehrbringen. Wer sie ins Englische übersetzt
und zurück, verliert die rechtliche Schärfe — „deployer" ist nicht einfach
„Nutzer". Und ein Werkzeug, dessen Zielgruppe Fachbegriffe ohne Übersetzung als
Zumutung empfindet, darf nicht selbst in Fachjargon dastehen.

**Folgen.**
* Gut: die Begriffe im Programmtext sind dieselben wie in der Verordnung; es
  gibt keine Übersetzungsschicht, in der Bedeutung verloren geht.
* Schlecht: wer international mitarbeiten will, stößt auf eine Hürde. Das ist
  in Kauf genommen.
* Schlecht: der Bestand ist deutsch. Englische Fassungen der beiden
  Verordnungen liegen in `daten/roh`, gehen aber nicht ein. Eine mehrsprachige
  Auskunft wäre möglich — die verwendeten Einbettungsmodelle sind mehrsprachig
  — ist aber nicht gebaut.
