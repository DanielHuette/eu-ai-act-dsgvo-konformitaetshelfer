# Architekturentscheidungen

Je Entscheidung: die Lage, die Entscheidung, die Begründung, die Folgen — auch
die unangenehmen. Reihenfolge nach Gewicht, nicht nach Datum.

Ein Eintrag wird nicht gelöscht, wenn er überholt ist, sondern als überholt
gekennzeichnet und mit dem Eintrag verknüpft, der ihn ersetzt.

---

## E1 — Fragen statt Raten

**Lage.** Die Aufgabe ist: zu einem KI-System die Risikoklasse und die
Pflichten bestimmen. Der naheliegende Weg ist, den Nutzer sein Vorhaben
beschreiben zu lassen und daraus zu schließen. Genau so war es gebaut, in zwei
Stufen.

Die erste Stufe las Stichwörter: bestimmte Wortstämme in der Beschreibung
lösten ein Merkmal aus. Gemessen an 20 Beschreibungen, wie Unternehmen sie
wirklich einreichen — nicht an den eigenen Beispielen, an denen die Wortlisten
entwickelt worden waren — traf das **11 von 20**.

Die zweite Stufe verglich Bedeutung: ein Katalog von Zwecksätzen in
Unternehmenssprache, dazu ein Einbettungsmodell und ein Kreuzbewerter, der
entschied, welche Stelle des Gesetzes der Nutzer meint. Nach einer Nacht Arbeit
traf das **20 von 20**.

**Entscheidung.** Beides weg. Die Einstufung entsteht aus einer Fragefolge: der
Nutzer beantwortet in etwa sechs Schritten Fragen über sein System, und daraus
folgt der Befund. Gemessen 5,3 Schritte im Schnitt.

**Begründung.** 20 von 20 klingt gut und ist der falsche Maßstab. Ein Jurist
fragt fünf bis acht Dinge ab und hat danach Gewissheit, nicht 98 Prozent.
Genaues Raten ist schlechter als Fragen — und geraten wurden Antworten auf
Fragen, die sich stellen lassen. Wofür ist das System bestimmt? Wer setzt es
ein? Entscheidet es über Menschen? Das weiß der Nutzer, und niemand sonst.

Dazu drei Dinge, die der Ratenweg nicht leisten konnte:

* **Nachvollziehbarkeit.** Beim Raten stand am Ende eine Klasse und eine
  Ähnlichkeitszahl. Jetzt steht da, welche Antwort den Punkt getragen hat und
  welche Stelle der Leitlinien das sagt. Der Nutzer sieht, woran es hängt, und
  kann die Antwort ändern.
* **Herkunft.** Die Zwecksätze des Katalogs waren von mir formuliert. Jede
  Lücke darin war eine Lücke, die niemand sehen konnte. Die Fragen stammen Zeile
  für Zeile aus dem Entwurf der Leitlinien der Kommission vom 19. Mai 2026 und
  tragen jede eine Absatznummer.
* **Ein fremder Maßstab.** Vorher hatte ich sowohl die Regeln als auch die
  Prüffälle geschrieben; eine hohe Trefferquote hieß nur, dass das Werkzeug mit
  meiner Lesart übereinstimmt. Die 217 Beispiele der Leitlinien nennen die
  Wertung der Kommission. Davon werden **207 richtig eingestuft**.

**Folgen.**
* Gut: das Ergebnis ist nicht wahrscheinlich, sondern richtig, soweit die
  Angaben des Nutzers stimmen. Kein Modell kann es verändern.
* Gut: die Einstufung braucht kein Sprachmodell, kein Einbettungsmodell, kein
  Netz und keinen Schlüssel. Sie läuft im Browser.
* Schlecht: der Nutzer muss antworten. Wer nicht weiß, wofür sein System
  bestimmt ist, muss das erst klären — das Werkzeug kann es ihm nicht abnehmen.
* Schlecht: die Pflege wird aufwendiger. Ändern die Leitlinien einen Absatz,
  ändert sich eine Frage, und zwar an zwei Stellen nachzumessen (siehe
  [E3](#e3--die-ablauflogik-steht-zweimal-da-und-wird-gegeneinander-gemessen)).
* Der Freitext ist damit nicht wertlos: er bleibt der Weg in die Volltextsuche
  und in die ausformulierte Auskunft. Er entscheidet dort nichts.

---

## E2 — Die Fragen stehen in Textdateien, mit Absatznummer an jeder Zeile

**Lage.** 379 Fragen, 214 Ausschlüsse und 187 Beispiele zu 31 Stellen des
Gesetzes. Sie beruhen auf einem Dokument von 167 Seiten, das sich noch ändern
wird: der Entwurf der Leitlinien ist nicht bindend, und die öffentliche
Anhörung lief bis zum 23. Juni 2026.

**Entscheidung.** Alles davon liegt in `daten/regeln/fragefolge/*.yaml`, die
Reihenfolge getrennt in `daten/regeln/fragefolge-aufbau.yaml`. Jede Frage, jeder
Ausschluss und jedes Beispiel trägt im Feld `beleg` die Absatznummer der
Leitlinien. Der Programmtext enthält selbst keine Frage und keinen
Artikelverweis.

**Begründung.** Wer eine Frage ändert, soll eine Textzeile ändern und nicht
Programmtext. Das ist für jemanden machbar, der die Rechtslage kennt, aber
nicht programmiert — und das ist genau die Person, die eine Änderung der
Leitlinien zuerst bemerkt. Eine Textdatei ist außerdem in der Versionsverwaltung
lesbar: eine geänderte Frage ist als Unterschied sichtbar und damit prüfbar.

Die Absatznummer ist nicht Schmuck. Sie ist die Antwort auf die Frage „woher
wissen Sie das?". Ohne sie wäre jede Frage eine Behauptung, und niemand könnte
nachsehen, ob sie im amtlichen Text steht. Darum gilt: **ohne Absatz keine
Frage.**

Reihenfolge getrennt von Inhalt, weil beides verschiedenen Ursprungs ist. Die
Frage stammt aus dem amtlichen Text, die Reihenfolge aus der Erfahrung, wie
Leute antworten. Die acht Bereichsfragen sind der sichtbare Beweis: sie tragen
keine Absatznummer, weil sie nicht aus dem Text stammen — sie sortieren nur.

**Folgen.**
* Gut: eine Änderung der Leitlinien ändert Dateien, nicht Programmtext.
* Gut: dieselbe Datei versorgt Programm und Webseite, sodass die Einstufung auf
  beiden Seiten gleich ausfällt.
* Schlecht: die Dateien sind nicht schemageprüft. Ein Tippfehler in einem
  Feldnamen führt nicht zum Abbruch, sondern zu einer Frage ohne diese Angabe.
  Eine Schemaprüfung wäre der nächste sinnvolle Schritt.
* Die Verknüpfung zwischen Frage und Rechtstext ist nur eine Zeichenfolge: ein
  Punkt nennt `KI-VO/anh-III/nr-4-a` als Fundstelle. Steht diese Kennung nicht
  im Korpus, fehlt im Befund der amtliche Text zum Nachlesen.

---

## E3 — Die Ablauflogik steht zweimal da und wird gegeneinander gemessen

**Lage.** Die Einstufung soll ohne Installation im Browser laufen — und im
installierten Programm genauso. Die Daten sind dieselben, aber die Ablauflogik
müsste in zwei Sprachen vorliegen: Python für das Programm, JavaScript für die
Webseite. Die Alternative wäre, die Webseite rechnen zu lassen, indem sie einen
Server fragt.

**Entscheidung.** Zwei Fassungen —
`src/helfer/einstufung/fragefolge.py` und `web/durchlauf.js` — und eine
Prüfung, die sie gegeneinander fährt. `scripts/pruefe_zwei_wege.py` würfelt
Antwortmuster mit festem Startwert und vergleicht Schritt für Schritt:
dieselbe Frage in derselben Reihenfolge, dieselbe Gruppe auf demselben Blatt,
derselbe Befund. Der Lauf, der die Pakete baut, baut keines, bevor 400 von 400
Läufen gleich sind.

**Begründung.** Eine Webseite, die einen Server fragt, überträgt die Angaben
des Nutzers. Die Beschreibung eines KI-Vorhabens verrät Geschäftsinterna, und
eine Seite ohne Server hat keinen Betreiber, dem man vertrauen müsste. Darum
rechnet der Browser selbst.

Der Preis ist die doppelte Logik, und das ist die gefährlichste Stelle des
Projekts. **Zwei Fassungen derselben Logik laufen auseinander** — beim Bau
dieses Durchlaufs haben Fragefolge und Auswertung genau das getan und **30 von
217 amtlichen Beispielen gekostet**. Eine solche Abweichung sieht man nicht:
beide Seiten antworten, nur verschieden. Darum ist die Prüfung nicht
freiwillig, sondern Teil des Paketbaus.

**Folgen.**
* Gut: die Einstufung läuft ohne Server, ohne Anmeldung und ohne Übertragung.
* Gut: die Webseite besteht aus drei Dateien und lässt sich auf jeden
  Webserver legen.
* Schlecht: jede Änderung an einer Fassung ist eine Änderung an zwei Fassungen.
  Wer nur eine anfasst, bricht die Gleichheit — die Prüfung merkt es, aber die
  Arbeit fällt zweimal an.
* Die 400 Läufe sind gesetzt, nicht gemessen: es gibt keine Messreihe, die
  sagt, ab welcher Zahl ein Auseinanderlaufen zuverlässig auffällt.

---

## E4 — Drei Antworten, nicht zwei

**Lage.** Eine Fragefolge mit Ja und Nein ist die einfachste Form, und jede
Frage der Leitlinien ist so gestellt, dass sie mit Ja oder Nein beantwortbar
scheint.

**Entscheidung.** Jede Frage hat drei Antworten: Ja, Nein und **Trifft nicht
zu**. Die dritte lässt die Frage stehen, ohne zu entscheiden; ein Ausschluss
greift nur auf eine ausdrückliche Antwort.

**Begründung.** Gemessen an einem Fall: Zu Anhang III Nummer 4 Buchstabe a
gehört die Frage, ob eine Stellenanzeige aktiv eine konkrete offene Stelle
anzeigt. Ein Werkzeug, das Lebensläufe sichtet, schaltet keine Anzeigen —
darauf gibt es weder Ja noch Nein. Das erzwungene Nein warf einen Fall aus der
Einstufung, der nach dem amtlichen Text klar erfasst ist. Ein Jurist fragt an
dieser Stelle nicht weiter.

Dazu kommt ein zweiter Fall, der eine eigene Befundklasse nötig machte. Anhang
III Nummer 2 verlangt nach Absatz (190) der Leitlinien, dass der Betreiber
förmlich als kritische Einrichtung benannt ist — und Absatz (191) stellt im
selben Atemzug fest, dass diese Benennung dem Anbieter nicht offengelegt werden
muss. Ein Softwarehaus, das Netzleitsysteme verkauft, kann die Frage nicht
beantworten. Gemessen fielen so **zehn amtliche Beispiele** auf „kein hohes
Risiko", die die Kommission als hochriskant führt. Bleibt die Frage offen und
trägt der Rest, lautet der Befund darum `hochrisiko_bedingt` mit dem Satz, der
sagt, woran es hängt.

**Folgen.**
* Gut: Fragen, die auf das eigene System nicht passen, werfen es nicht aus der
  Einstufung.
* Gut: der Befund kann sagen „alles trifft zu bis auf eines, und das können Sie
  nicht wissen" — eine Auskunft, die der Lage entspricht.
* Schlecht: drei Antworten sind mehr zu bedenken als zwei, in der Oberfläche
  und in beiden Fassungen der Ablauflogik.
* Schlecht: wer „Trifft nicht zu" aus Bequemlichkeit wählt, bekommt einen
  unentschiedenen Befund statt einer Einstufung. Das Werkzeug kann nicht
  unterscheiden, ob die Frage wirklich nicht passt.

---

## E5 — Anhang III und Anhang I werden verschieden geprüft

**Lage.** Es gibt zwei Wege zum hohen Risiko. Artikel 6 Absatz 2 mit Anhang III
trifft zu, wenn **einer** von acht Bereichen passt. Artikel 6 Absatz 1 mit
Anhang I verlangt, dass **drei** Dinge zusammenkommen. Und innerhalb des
Anhangs III ist Nummer 2 anders gebaut als die übrigen sieben Bereiche: dort
müssen ebenfalls drei Dinge zusammentreffen.

**Entscheidung.** Drei Prüfformen, in `fragefolge-aufbau.yaml` auseinander
gehalten:

* **Aufzählung** — die Punkte eines Bereichs tragen einzeln. Der Regelfall.
* **Bedingungsgruppen** (`anhang_i`) — eine Produktgattung aus 15, die Rolle
  als Sicherheitsbauteil oder als Produkt selbst, eine Konformitätsbewertung
  durch eine dritte Stelle. Innerhalb einer Gruppe genügt eine Antwort, über
  die Gruppen hinweg müssen alle tragen.
* **Verbund** (`verbunde`) — für Nummer 2: Versorgungsbereich, benannte
  kritische Einrichtung und eigene Schutzaufgabe, alle drei zusammen.

Anhang I wird vor Anhang III geprüft, weil Artikel 6 Absatz 1 vor Absatz 2
steht.

**Begründung.** Die falsche Abbildung ist gemessen teuer. Als Aufzählung
gelesen konnte Nummer 2 **überhaupt keinen** Treffer ergeben, weil keine ihrer
Fragen allein zum Treffer führt — zehn amtliche Beispiele. Und bei Anhang I
verlangte der Durchlauf zunächst sowohl „ist Sicherheitsbauteil" als auch „ist
selbst das Produkt" und ließ damit jedes System durchfallen, das selbst ein
geregeltes Produkt ist. Artikel 6 Absatz 1 Buchstabe a verlangt das eine
**oder** das andere; ist das System selbst das Produkt, ist die Frage nach dem
Sicherheitsbauteil gegenstandslos.

**Folgen.**
* Gut: jeder Weg wird so geprüft, wie der amtliche Text ihn baut.
* Gut: die Ausnahme nach Artikel 6 Absatz 3 wird nur bei Anhang III gefragt —
  sie betrifft nur diesen Weg, und bei Anhang I sagt der Befund das
  ausdrücklich.
* Schlecht: drei Prüfformen sind drei Stellen, an denen etwas schieflaufen
  kann, und sie sind nur an den amtlichen Beispielen gemessen, nicht
  erschöpfend.
* Fünf Fragen der Leitlinien zu Anhang I werden nicht gestellt: sie fassen nur
  zusammen, was der Durchlauf selbst mitzählt, oder verweisen in den
  Gesetzestext, statt nach dem eigenen System zu fragen.

---

## E6 — Die Pflichten und der Datenschutzpfad bleiben im Regelwerk

**Lage.** Die Fragefolge liefert eine Klasse und eine Fundstelle. Was daraus an
Pflichten folgt, ist eine zweite Frage: 57 Pflichten der KI-Verordnung und 26
Abschnitte des Prüfpfads zum Datenschutzrecht.

**Entscheidung.** Beides bleibt, wo es war: in `daten/regeln/kivo_pflichten.yaml`
und `daten/regeln/dsgvo_pruefpfad.yaml`, ausgewählt nach Klasse und Rolle.
Jeder Eintrag nennt seine Rechtsgrundlagen als Kennungen, die im Korpus
vorhanden sein müssen.

**Begründung.** Die Pflichten hängen nicht an den Leitlinien, sondern am
Verordnungstext — sie ändern sich durch andere Ereignisse als die Fragen und
werden darum getrennt gepflegt. Und sie waren schon richtig: an den Pflichten
hat der Wechsel von Raten auf Fragen nichts geändert, weil sie ohnehin nur
Klasse und Rolle brauchen.

Dass 14 der 26 Datenschutzabschnitte immer gelten und 12 an einer Bedingung
hängen, ist ebenfalls eine Entscheidung gegen Vollständigkeit: ohne diese
Zuordnung bekäme jeder alle 26 Abschnitte, und das wäre keine Auskunft mehr,
sondern eine Materialsammlung.

**Folgen.**
* Gut: eine Rechtsänderung bei den Pflichten ändert eine Textzeile.
* Gut: nachgemessen am 04.10.2026 ist jede genannte Rechtsgrundlage im Korpus
  vorhanden; der Prüfbefehl steht in
  [betriebsanleitung.md](betriebsanleitung.md).
* Schlecht: die Pflichtenliste filtert nach Klasse und Rolle, nicht nach
  Merkmalen. Wer als Betreiber unter Anhang III fällt, bekommt alle
  Betreiberpflichten dieser Klasse — gemessen an einem Lauf vom 03.10.2026
  erhielt eine Beschreibung über die Vorsortierung von Bewerbungen 16
  Pflichten, darunter Artikel 26 Absatz 10 zur nachträglichen biometrischen
  Fernidentifizierung. Die Liste ist eher zu lang als zu kurz.
* Schlecht: die abgeleiteten Pflichten sind gegen den Verordnungstext geprüft,
  aber gegen keine fremde Sollvorgabe gemessen — eine amtliche Beispielsammlung
  dafür gibt es nicht.

---

## E7 — Vier Suchwege statt einem

**Lage.** Die Volltextsuche im Verordnungstext ist Beiwerk: sie beantwortet
Rückfragen, nicht die Einstufung. Rechtsfragen werden dabei auf zwei Arten
gestellt. „Dürfen wir Bewerbungen vorsortieren?" fragt nach Sinn — das Gesetz
sagt „Einstellung oder Auswahl natürlicher Personen", kein Wort stimmt
überein. „Was steht in Artikel 6 Absatz 3?" fragt nach Wortlaut, und zwar
genau.

**Entscheidung.** Vier Wege gleichzeitig: Vektorsuche für die Bedeutung,
Stichwortsuche nach BM25 für den Wortlaut, die Wortgewichte des
Einbettungsmodells für das Dazwischen, und ein Fundstellenweg, der eine
genannte Stelle unmittelbar auflöst. Zusammengeführt wird über die Rangplätze,
danach bewertet ein Kreuzbewerter die besten 30 neu.

**Begründung.** Eine Vektorsuche allein verliert genaue Fragen: Zahlen sehen
für sie fast gleich aus, „Artikel 6" und „Artikel 9" liegen dicht beieinander.
Eine Stichwortsuche allein verliert sinngleiche Fragen, weil die Leute andere
Wörter benutzen als die Verordnung. Der Fundstellenweg ist der wichtigste und
der billigste: wer eine Stelle nennt, soll sie bekommen und nicht etwas
Ähnliches. Er wiegt dreifach, weil er kein Schätzwert ist, sondern eine
Tatsache.

**Zusammenführung über Rangplätze, nicht über Punktzahlen** (in der Literatur
*Reciprocal Rank Fusion*): für jeden Treffer wird `1 / (60 + Rangplatz)` je Weg
addiert, der ihn gefunden hat. Punktzahlen zu addieren wäre falsch, weil ein
BM25-Wert und ein Kosinusmaß verschiedene Maßstäbe haben — das wäre das
Addieren von Metern und Kilogramm. Die 60 ist der gebräuchliche Wert und dämpft
die Spitze, damit ein einzelner Weg die Liste nicht allein bestimmt.

**Folgen.**
* Gut: beide Frageformen funktionieren; ein Treffer, den nur ein Weg kennt,
  fällt nicht heraus; fällt ein Weg aus, tragen die anderen weiter.
* Schlecht: vier Wege sind vier Stellen, an denen etwas schieflaufen kann, und
  die Gewichtung des Fundstellenwegs mit dem Faktor 3 ist nicht gemessen,
  sondern gesetzt. Dass sie richtig ist, ist eine Annahme.
* Die Zahlen 50 Treffer je Weg, 30 zur Neubewertung und 60 in der Rangfusion
  sind ebenfalls gesetzt und nicht an diesem Bestand gemessen.
* Der Kreuzbewerter kostet Rechenzeit, deshalb nur 30 Treffer. Fehlt er, bleibt
  die Reihenfolge der Rangfusion — die Suche fällt nicht aus, sie wird
  ungenauer.

---

## E8 — Das Einbettungsmodell läuft auf dem eigenen Rechner

**Lage.** Für die Vektorsuche braucht man ein Einbettungsmodell. Die
Schnittstellen von OpenAI und anderen bieten das als Dienst an: bessere
Trefferqualität möglich, kein Modell auf dem Rechner, Abrechnung je Anfrage.

**Entscheidung.** Das Einbettungsmodell läuft örtlich: bge-m3, mehrsprachig,
1024 Zahlen je Textstück, rund 2,3 Gigabyte. Nur die ausformulierte Antwort
kann ein Modell über eine Schnittstelle übernehmen, und das ist freiwillig.

**Begründung.** Zwei Gründe, und beide wiegen schwer. Erstens: wer sein
KI-Vorhaben beschreibt, verrät Geschäftsinterna. Eine Einbettung über eine
Schnittstelle schickt jede Frage zum Anbieter — auch dann, wenn am Ende kein
Sprachmodell formuliert. Zweitens: der mitgelieferte Rechtsbestand muss bei
jedem funktionieren, der das Projekt herunterlädt. Ein Bestand, dessen Vektoren
von einem Dienst stammen, ist ohne Schlüssel bei diesem Dienst nicht abfragbar
— man kann die Frage dann nicht in denselben Zahlenraum bringen. Der Bestand
wäre damit wertlos.

**Folgen.**
* Gut: läuft ohne Schlüssel, ohne Netz, ohne Kosten je Anfrage; die Frage
  verlässt den Rechner nicht.
* Schlecht: 2,3 Gigabyte Modell und ein Rechenlauf von knapp einer Stunde
  (gemessen 3547 Sekunden für 2811 Einheiten am 04.10.2026), bevor die Suche
  läuft. Das ist eine Hürde — und der Grund, warum die Einstufung ohne Modell
  auskommen muss.
* Schlecht: die Trefferqualität der großen Dienste ist nicht erreicht, und das
  ist hier nicht gemessen — es gibt keine Messreihe, die die Wege vergleicht.
* Die Suche hat einen Rückfall auf ein Verfahren über Streuwerte, damit sich
  die Mechanik ohne Modell ausprobieren lässt. `scripts/bestand_bauen.py`
  bricht aber ab, wenn das gewünschte Modell fehlt, statt einen Bestand in
  Ersatzqualität zu schreiben: ein solcher Bestand sieht heil aus und liefert
  still falsche Treffer.

---

## E9 — Der Rechtsbestand liegt als JSONL im Verzeichnis

**Lage.** 2811 Rechtseinheiten müssen irgendwo liegen. Möglich wären eine
Datenbank, mehrere Dateien je Artikel oder eine einzelne Datei.

**Entscheidung.** Eine Datei, `daten/aufbereitet/korpus.jsonl`, mit einer
JSON-Zeile je Einheit. Sie wandert mit in die Versionsverwaltung.

**Begründung.** Die Form ist absichtlich einfach. Eine Zeile je Einheit ist in
der Versionsverwaltung lesbar: wer einen Rechtstext ändert, sieht genau eine
geänderte Zeile. Sie lässt sich zeilenweise prüfen, auch mit
Kommandozeilenwerkzeugen, und ohne Hilfsmittel einlesen.

**Folgen.**
* Gut: nachvollziehbare Änderungen, einfache Prüfung, keine Datenbank nötig.
* Gut: wer das Projekt herunterlädt, hat den Rechtstext sofort — ohne
  Beschaffungslauf, der an EUR-Lex scheitern kann.
* Gut: der abgelegte Suchbestand trägt seit dem 04.10.2026 die Kennungen des
  Korpus, aus dem er gebaut wurde, und wird beim Laden abgewiesen, wenn sie
  nicht mehr passen. Die Anzahl allein genügte nicht: ein Bestand aus einem
  anderen Korpus kann zufällig gleich viele Einheiten haben, und dann zeigt
  jeder Vektor auf die falsche Fundstelle — die Antwort sähe aus wie immer.
* Schlecht: die Datei ist 2,9 Megabyte groß und wächst mit jeder
  Rechtsänderung in der Versionsverwaltung mit. Das ist tragbar.

---

## E10 — Beschaffung getrennt von Verarbeitung

**Lage.** Die Rohquellen kommen aus dem Netz, und das Netz ist unzuverlässig.
Die Webseite von EUR-Lex antwortet auf Anfragen ohne vollständigen
Browser-Kopf mit HTTP 202 und leerem Körper und schickt danach ein Captcha
ihrer Firewall.

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
* Gut: seit dem 04.10.2026 kommen beide Verordnungen über Cellar aus dem
  Amtsblatt. Die Rückfallquelle greift nur noch ein, wenn der amtliche Text für
  einen Rechtsakt **ganz** fehlt — vorher mischte sie ihre Kennungen
  (`art-4/abs-14`) neben die amtlichen (`art-4/nr-14`). Der Abgleich gegen das
  Amtsblatt hatte 51 Prozent Abweichung ergeben; Artikel 13 hatte 909 statt
  3374 Zeichen. Siehe [datenquellen.md](datenquellen.md).
* Die Mindestgröße als Erkennungsmerkmal ist grob: eine Datei, die groß genug
  ist, aber inhaltlich fehlerhaft, wird nicht erneut geholt.

---

## E11 — Deutsch im Quelltext, in den Daten und in der Oberfläche

**Lage.** Das Werkzeug richtet sich an Mitarbeiter in deutschen Unternehmen.
Der Rechtstext ist deutsch, die Begriffe der Verordnung sind deutsch
festgelegt. Die Leitlinien der Kommission liegen in diesem Entwurf auf
Englisch vor.

**Entscheidung.** Deutsch durchgehend: Bezeichner im Programmtext, Feldnamen in
den Daten, Fragen, Oberfläche, Dokumentation. Jeder Fachbegriff wird beim
ersten Vorkommen in Alltagssprache erklärt, jede Abkürzung ausgeschrieben. Die
Fragen sind aus dem englischen Entwurf in deutsche Alltagssprache übertragen
und tragen die Absatznummer des Originals.

**Begründung.** Die Verordnung legt die Begriffe auf Deutsch fest: Anbieter,
Betreiber, Zweckbestimmung, Inverkehrbringen. Wer sie ins Englische übersetzt
und zurück, verliert die rechtliche Schärfe — „deployer" ist nicht einfach
„Nutzer". Und ein Werkzeug, dessen Nutzer Fachbegriffe ohne Übersetzung als
Zumutung empfinden, darf nicht selbst in Fachjargon dastehen. Eine Frage, die
niemand versteht, wird falsch beantwortet, und dann ist der Befund falsch.

**Folgen.**
* Gut: die Begriffe im Programmtext sind dieselben wie in der Verordnung; es
  gibt keine Übersetzungsschicht, in der Bedeutung verloren geht.
* Schlecht: die Übertragung der Fragen aus dem englischen Entwurf ist von mir
  und von keinem Juristen gegengelesen. Die Absatznummer an jeder Zeile ist
  die Gegenprobe, die jeder selbst machen kann.
* Schlecht: wer international mitarbeiten will, stößt auf eine Hürde. Das ist
  in Kauf genommen.
* Schlecht: der Bestand ist deutsch. Englische Fassungen der beiden
  Verordnungen liegen in `daten/roh`, gehen aber nicht ein. Eine mehrsprachige
  Auskunft wäre möglich — die verwendeten Einbettungsmodelle sind mehrsprachig
  — ist aber nicht gebaut.
