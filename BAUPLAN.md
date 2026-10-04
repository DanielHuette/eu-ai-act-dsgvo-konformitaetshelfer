# Bauplan: der Konformitätshelfer in einem Durchgang

Dieses Dokument ist ein Auftrag an einen Programmierassistenten. Wer es ihm
vorlegt, bekommt den **EU AI Act und DSGVO Konformitätshelfer** gebaut — den
Rechtsbestand, die Einstufung, die Suche, die Oberflächen, die Prüfungen und
die Präsentation — ohne eine einzige Rückfrage.

Es ist zugleich die Beschreibung dessen, was hier steht: jede Zahl darin ist an
diesem Projekt nachgemessen, und jede Regel ist aus einem Fehler entstanden,
der wirklich gemacht wurde.

| | |
|---|---|
| **Aufwand** | ein Arbeitstag für einen Assistenten mit Werkzeugen, davon rund eine Stunde reine Rechenzeit |
| **Ergebnis** | 2.811 Rechtsstellen · 57 Pflichten · 55 Zweckeinträge · 44 Anwendungsfälle · 100 Unternehmensfragen zu 100 % richtig eingestuft · PC, Container, Android, Präsentation |
| **Voraussetzung** | Python 3.11+, Netzzugang zu EUR-Lex und Hugging Face, Docker, rund 20 GB Platte |
| **Nicht vorausgesetzt** | Rechtskenntnis des Assistenten — die Rechtsfragen stehen unten als Prüfkriterien |

---

## Wie dieser Bauplan zu benutzen ist

Kopieren Sie den Abschnitt **„Der Auftrag"** vollständig in Ihren Assistenten.
Alles darüber und darunter ist Erläuterung für Sie, nicht für ihn.

Der Auftrag ist so geschrieben, dass keine Frage offenbleibt: Jede Entscheidung,
die sonst eine Rückfrage auslösen würde, ist vorweg getroffen und begründet. Die
Begründungen stehen dabei, weil ein Assistent eine Regel ohne Grund an der
erstbesten Gelegenheit aufgibt.

---

## Der Auftrag

> Baue einen RAG-Bot, der Unternehmen hilft, ihre KI-Systeme nach der
> KI-Verordnung (EU) 2024/1689 und dem Datenschutzrecht einzuschätzen. Er heißt
> **EU AI Act und DSGVO Konformitätshelfer**. Arbeite die elf Stufen unten der
> Reihe nach ab. Frage nichts — jede Entscheidung ist hier getroffen. Halte dich
> an die zehn Grundsätze; sie stehen über jeder Einzelanweisung.

### Die zehn Grundsätze

**1. Die Einstufung kommt aus dem Regelwerk, nie aus dem Sprachmodell.**
Risikoklasse und Pflichten entstehen aus Entscheidungsbäumen in YAML-Dateien,
bevor ein Modell den Text sieht. Das Modell formuliert nur. Ein Sprachmodell,
das die Rechtsfolge selbst bestimmt, ist nicht nachprüfbar — man kann nicht
nachlesen, warum es so entschieden hat.

**2. Nie schätzen, immer messen.** Keine Zahl in Programmtext, Dokumentation
oder Präsentation, die nicht gemessen wurde. „Rund 2.700 Einheiten" ist keine
Angabe, sondern ein Versäumnis.

**3. Jeder eigene Fehler wird zur Prüfung.** Wer einen Fehler behebt, schreibt
eine Prüfung mit dem Fehler im Namen und der Ursache im Beschreibungstext.
Beispiel: `test_kamera_auf_foerderband_ist_keine_rechtspflege` — der Wortstamm
„gericht" traf „gerichtet".

**4. Rechtsfragen gehören in Daten, nicht in Programmtext.** Welche Wörter
einen Bereich des Anhangs III kennzeichnen, ist eine Rechtsfrage. Sie steht in
einer YAML-Datei, die ein Jurist ohne Programmierkenntnis ändern kann.

**5. Was offen ist, wird genannt — nicht weggelassen.** Schweigt die
Beschreibung zu einem Merkmal, erscheint die Pflicht mit Vorbehalt.
Weggelassen wird nur, was ausgeschlossen ist. Die vorsichtige Richtung ist die
richtige.

**6. Nichts verlässt das Gerät, außer der Nutzer will es.** Rechtsbestand,
Regelwerk und Suche liegen lokal. Ein Sprachmodell wird nur angesprochen, wenn
ein Schlüssel hinterlegt ist, und das steht in der Oberfläche.

**7. Keine Datei, die beim Laden Code ausführen kann.** Kein `pickle`, kein
`allow_pickle`, keine `eval`. Was mit dem Repository ausgeliefert wird, kommt
beim Nutzer über Kopien und Spiegel an — eine veränderte Kopie darf falsche
Treffer verursachen, aber keinen fremden Code starten.

**8. Deutsch, durchgehend.** Modulnamen, Feldnamen, Kommentare,
Fehlermeldungen, Oberfläche. Das Werkzeug erklärt deutsches und europäisches
Recht auf Deutsch; ein Mischwort wie `EingabeError` bricht die Benennung des
ganzen Projekts.

**9. Keine Rechtsberatung, und das wird gesagt.** Jede Auskunft nennt den
Datenstand, den Fristenvorbehalt und den Satz, dass die Anwendung auf den
Einzelfall ein Mensch mit Zulassung entscheidet.

**10. Nichts halb.** Bricht die Arbeit ab, bleibt sie offen, nicht halb fertig.
Ein Lauf, der eine Stunde rechnet, legt Zwischenstände ab.

### Stufe 1 — Rechtstexte beschaffen

Hole den amtlichen deutschen Volltext aus EUR-Lex:

- KI-Verordnung: CELEX `32024R1689`
- Datenschutz-Grundverordnung: CELEX `32016R0679`

**Fallstrick, der Stunden kostet:** EUR-Lex antwortet auf einen Aufruf ohne
vollständigen Browser-Kopf mit HTTP 202 und null Bytes — kein Fehler, nur
nichts. Setze `Sec-Fetch-Dest`, `Sec-Fetch-Mode`, `Sec-Fetch-Site`,
`Sec-Fetch-User`, `Upgrade-Insecure-Requests` und `Accept-Encoding: identity`.
Kommt trotzdem eine Seite von rund 2 KB zurück, ist es ein Captcha der
Firewall: nimm dann `dsgvo-gesetz.de` artikelweise als zweite Quelle und
**schreibe in `docs/datenquellen.md`, welcher Text woher stammt.**

Hole außerdem das Bundesdatenschutzgesetz von `gesetze-im-internet.de`.

Jedes Beschaffungsskript lässt nur `https` durch (eine eigene kleine Prüfung
vor dem Aufruf) und legt die Rohdateien unverändert ab.

### Stufe 2 — Zerlegen

Zerlege **ausschließlich an der Gliederung des Dokuments**, nie an Textmustern.

**Der Fehler, den jeder einmal macht:** Ein Zerleger, der nach „Artikel" sucht,
findet 132 statt 113 Artikel — ein Querverweis im Fließtext („… nach Artikel
99 …") sieht aus wie ein Artikelanfang, und Artikel 5 wird 31.828 Zeichen lang.
EUR-Lex trägt `div#art_6`, `div#006.003` (Artikel 6 Absatz 3), `div#anx_III`,
`#rct_71`. Daran wird getrennt. Das Bundesdatenschutzgesetz trägt
`div.jnnorm` mit `.jnenbez`, `.jnentitel`, `.jnhtml`.

Jede Einheit bekommt eine Kennung in genau dieser Form:

```
KI-VO/art-6            DSGVO/art-13/abs-1-a       BDSG/par-26/abs-1
KI-VO/art-6/abs-3      KI-VO/anh-III/nr-4-a       KI-VO/erw-71
KI-VO/art-3/nr-39      KI-VO/anh-I/nr-A-11        KI-VO/anh-VIII/nr-A-1
```

**Zerlege die Anhänge bis zum Buchstaben, nicht bis zur Nummer.** Anhang III
nennt acht Bereiche, aber die Einstufung hängt nicht am Bereich, sondern am
Buchstaben darunter: Nummer 4 Buchstabe a trifft die Einstellung, Buchstabe b
die Arbeitsbedingungen — zwei verschiedene Sachverhalte unter einer
Überschrift. Wer nur die Nummer erfasst, kann einen Fall nicht auf die Stelle
zurückführen, die ihn trägt, und hat für die Einstufung nur acht sehr ähnlich
formulierte Texte statt dreiundzwanzig unterscheidbarer.

**Drei Fallen in den Aufzählungstabellen von EUR-Lex:**

* *Die Zählung steht nicht immer in der ersten Zelle.* Eingerückte
  Aufzählungen haben davor eine leere Zelle, die die Einrückung trägt. Anhang I
  ist so gebaut. Wer blind `zellen[0]` liest, findet nichts und verliert den
  ganzen Anhang — 20 Rechtsakte, auf die Artikel 6 Absatz 1 verweist.
  Überspringe führende leere Zellen.
* *Abschnittsköpfe setzen die Zählung zurück.* Anhang VIII hat drei
  Abschnitte, jeder zählt wieder ab 1. Ohne den Abschnitt in der Kennung trägt
  jede Nummer dreimal denselben Namen und zwei Drittel gehen beim Entdoppeln
  verloren. Ein Abschnittskopf heißt „Abschnitt A — …", „Abschnitt 1" oder
  „1. Schengener Informationssystem". Eine **zweite** Überschrift unter dem
  Abschnittskopf darf den Abschnitt nicht löschen — Anhang XI hat das.
* *Verschachtelte Aufzählungen.* Artikel 5 Absatz 1 Buchstabe c enthält „i)",
  „ii)" — im Fließtext sieht „i)" wie der Buchstabe i aus, und denselben
  Buchstaben gibt es dort auch echt. Darum über die Tabellenstruktur gehen,
  nie über den Fließtext.

**Baue die Entdopplung so, dass sie den Verlust nennt.** Zwei Einheiten mit
derselben Kennung und *verschiedenem* Text bedeuten, dass Inhalt verschwindet.
Die Warnung muss die betroffenen Kennungen aufzählen — eine Zahl allein sagt
nicht, wo zu suchen ist. Der Lauf muss am Ende **ohne Warnung** durchgehen.

**Zielzahlen — sie sind Prüfkriterien, nicht Angaben:**

| Rechtsakt | Artikel | Anhangseinheiten | Erwägungsgründe | Einheiten |
|---|---:|---:|---:|---:|
| KI-Verordnung | 113 | 164 | 180 | 1.386 |
| Datenschutz-Grundverordnung | 99 | — | 173 | 1.024 |
| Bundesdatenschutzgesetz | — | — | — | 357 |
| Anwendungsfälle | — | — | — | 44 |
| **Zusammen** | | | | **2.811** |

Darin enthalten: 23 Buchstabenpunkte des Anhangs III, 20 Rechtsakte des
Anhangs I, 68 Begriffsbestimmungen des Artikels 3 und 26 der DSGVO.

Stimmt eine Zahl nicht, ist der Zerleger falsch — nicht die Zahl.

Baue daraus `daten/aufbereitet/korpus.jsonl`, eine Zeile je Einheit, und einen
Befund mit den gezählten Beständen.

### Stufe 3 — Das Regelwerk

Vier YAML-Dateien unter `daten/regeln/`:

**`kivo_risikoklassen.yaml`** — der Entscheidungsbaum. 8 Verbote nach Artikel 5
mit ihren Ausnahmen, Anhang I, die 8 Bereiche des Anhangs III, die Ausnahme
nach Artikel 6 Absatz 3 mit der Gegenausnahme Profiling, 4 Transparenzfälle
nach Artikel 50, GPAI mit der Schwelle von 10²⁵ Rechenoperationen, der
Rollenwechsel nach Artikel 25, die Fristen nach Artikel 113, die Sanktionen
nach Artikel 99.

Jeder Anhang-III-Bereich trägt drei Wortlisten, und die Trennung ist der Kern:

- `starke_woerter` — Wörter, die den Bereich **allein** kennzeichnen
  („Bewerbung", „Kreditwürdigkeit", „Täuschungsversuch")
- `stichworte` — Wortgruppen, bei denen **alle** Wörter vorkommen müssen
- `kombination: {traeger, handlung}` — ein Trägerwort **und** ein Handlungswort
  zusammen, für die Fälle ohne kennzeichnendes Einzelwort

Dazu, einmal für alle Bereiche, `entlastung`: Wendungen, mit denen eine
Beschreibung ausdrücklich sagt, dass niemand betroffen ist („die Vorschläge
sind unverbindlich", „geprüft werden Teile, nicht Menschen").

**`kivo_pflichten.yaml`** — 57 Pflichten. Jede trägt: `kennung`, `titel`,
`was_zu_tun_ist` (Alltagssprache, als Handlungsanweisung), `rechtsgrundlage`
(Kennungen aus dem Korpus), `auch_genannt` (Normen, auf die der Handlungstext
verweist, ohne die Pflicht zu begründen), `fundstellen_text`, `rollen`,
`klassen`, `schwere`, `gilt_ab`, `nachweis`, `bei_verstoss`, und wo nötig
`nur_wenn` / `nur_wenn_alle` / `bei_unbekannt` / `vorbehalt`.

**`dsgvo_pruefpfad.yaml`** — 26 Prüfabschnitte, davon 14, die immer gelten, und
12 mit Bedingung.

**`kivo_zweckkatalog.yaml`** — 55 Einträge, 107 Zwecke, 21 Gegenzwecke. Zu jeder
Fundstelle derselbe Zweck in Unternehmenssprache. Stufe 4 sagt, wie die Sätze
zu schreiben sind und warum die Form entscheidend ist. Felder: `fundstelle`
(Kennung im Korpus, wird gegen den amtlichen Text geprüft), `klasse`, `regel`
(die **bestehende** Kennung aus `kivo_risikoklassen.yaml`), `zwecke`, `ausser`,
`verlangt`.

### Stufe 4 — Die Einstufung

Ein Prüfer, der eine Beschreibung in eine Einstufung überführt. Geprüft wird in
der Reihenfolge der Schwere; die erste Stufe, die greift, bestimmt die Klasse.

Drei Dinge, an denen jede naive Fassung scheitert:

**Wortstämme treffen zu viel.** „gericht" trifft „gerichtet" — und macht eine
Kamera, die auf ein Förderband gerichtet ist, zur Rechtspflege. „assistent"
macht einen Notbremsassistenten zum Gesprächssystem. „Maschine" macht einen
Maschinenbauer, der Handbücher übersetzt, zum Hochrisikoanbieter. Prüfe jedes
Einzelwort gegen einen Gegenfall, bevor du es in `starke_woerter` schreibst.

**Wortgruppen treffen zu wenig.** „bewerbung filtern" trifft „Bewerbungen
vorsortieren" nicht. Verlange bei Wortgruppen alle Wörter als Wortstamm, und
stelle kennzeichnende Einzelwörter daneben.

**Die Ausnahme nach Artikel 6 Absatz 3 wird nie von allein angenommen.** Sie
greift nur, wenn die Beschreibung einen der vier Fälle erkennbar macht **und**
ausdrücklich sagt, dass die Entscheidung nicht beeinflusst wird. Greift sie,
**ersetzt** sie die Einordnung in Anhang III — beide Klassen zugleich wären ein
Widerspruch in der Auskunft.

Die Pflichtenliste wird dreifach gefiltert: nach Klasse, nach Rolle **und nach
Merkmalen**. Ohne den dritten Filter bekommt ein Bewerbungsfilter Artikel 26
Absatz 10 zur biometrischen Fernidentifizierung mitgeliefert, und der Nutzer
muss selbst aussortieren — genau die Arbeit, die ihm abgenommen werden soll.

**Wortlisten allein reichen nicht — und das merkt man erst spät.** Auf der
eigenen Fallsammlung trifft eine gut gepflegte Wortliste 44 von 44 Fällen. Auf
zwanzig Beschreibungen, wie Unternehmen sie wirklich einreichen, traf dieselbe
Liste 14. Alle sechs Fehlgriffe waren derselbe: nichts erkannt, also „minimal" —
und das ist der gefährliche Fehler, weil der Nutzer dann gar nichts tut. Eine
Wortliste trifft nur, was jemand vorher aufgeschrieben hat.

**Baue darum einen zweiten Eingang in dieselben Regeln: einen Zweckkatalog.**
`daten/regeln/kivo_zweckkatalog.yaml` nennt zu jeder Fundstelle denselben Zweck
in der Sprache, in der ein Unternehmen ihn beschreibt. Das Feld `regel` zeigt
auf die **bestehende** Kennung in `kivo_risikoklassen.yaml` — es ist ein
zweiter Eingang in dieselbe Regel, kein zweites Regelwerk. So gelten
Rollenprüfung, Merkmalsfilter, Ausnahmen und Pflichtenableitung unverändert,
und Grundsatz 1 bleibt wörtlich wahr: das Modell findet die Stelle, das
Regelwerk entscheidet.

Vier Dinge daran sind gemessen und nicht verhandelbar:

**a) Vergleiche Zweck mit Zweck, nicht mit dem Gesetzestext.** Anhang III
formuliert 23 seiner 25 Punkte mit derselben Formel („KI-Systeme, die
bestimmungsgemäß … verwendet werden sollen"). Wer die Beschreibung gegen den
Gesetzestext stellt, misst überwiegend diese gemeinsame Formel. Gemessen: ein
richtiger Treffer lag bei 0,0017, ein falscher bei 0,1009 — die Reihenfolge
stimmte, die Höhe nicht, und eine Schwelle ist darauf nicht zu setzen.

**b) Schreibe jeden Zwecksatz als Aussagesatz in der ersten Person Plural.**
Drei Formen, je gegen dieselben drei Beschreibungen gemessen:

| Form des Zwecksatzes | richtige Treffer | falsche |
|---|---|---|
| „Bilder oder Fotos erzeugen" | 0,036–0,447 | bis 0,141 |
| „Das System erzeugt Bilder." | 0,037–0,546 | bis 0,159 |
| **„Wir erzeugen mit KI Bilder."** | **0,986–0,989** | **bis 0,073** |

Nur die dritte Form trennt. Eine Beschreibung ist ein Aussagesatz in der ersten
Person, und der Kreuzbewerter vergleicht Satz mit Satz. Ein Infinitiv ohne
Handelnden liest sich wie ein Stichwort und bringt dieselbe Unschärfe zurück,
die zu beheben war.

**c) Vergleiche satzweise und leite die Satzform an.** „Wir sind ein Softwarehaus
und verkaufen eine Recruiting-Software. Die KI liest Lebensläufe und schlägt
dem Personaler die drei besten Kandidaten vor. Was müssen wir beachten?" — zwei
von drei Sätzen sagen über den Zweck nichts, und die Rückfrage am Ende zieht
den Wert herunter. Zerlege in Sätze, wirf reine Rückfragen weg, und leite zu
jedem Satz mit Verkäufervorspann („Wir verkaufen eine Software, die X") oder
mit dem System als Subjekt („Die KI liest X") **zusätzlich** den Satz „Wir X"
ab. Gemessen: 0,35 mit Vorspann, 0,75 ohne ihn, bei einer Schwelle von 0,50.
Dass der abgeleitete Satz grammatisch hinkt, ist hingenommen — gemessen zählt
die Person des Satzes, nicht die Beugung. Nimm aber nur Subjekte, die das
System bezeichnen: „Eine Kollegin liest alles gegen" darf nicht zu „Wir lesen
alles gegen" werden, denn dort handelt ein Mensch, und genau das entlastet nach
Artikel 6 Absatz 3.

**d) Drei Dinge halten die Fehltreffer draußen.**

* *Gegenzwecke.* Zu jeder Stelle gehören Zwecke, die ihr ähnlich sehen und
  nicht erfasst sind: die Sichtprüfung in der Fertigung neben dem
  Sicherheitsbauteil, die Suche nach Vertragsfristen neben der Kündigung, das
  Besprechungsprotokoll neben der Stimmauswertung. Ein Gegenzweck wirkt auf die
  **ganze Regel**, nicht nur auf die Fundstelle, bei der er steht — angestoßen
  wird die Regel. Trifft er deutlich (ab 0,90) und besser als der Zweck einer
  Stelle, so ist er die bessere Lesart und schlägt **jede** Regel: er
  beschreibt einen Zweck, den die Verordnung nicht erfasst.
* *Eine eigene, höhere Schwelle für Verbote.* „Verboten" heißt: das System darf
  so nicht betrieben werden, und wer sich darauf verlässt, stellt ein Geschäft
  ein. Gemessen traf eine Lernplattform, die Aufsätze benotet, den Satz „Wir
  erkennen die Gefühle von Schülern" mit 0,6297 — verboten wäre das falsch; die
  App, die die Stimmung von Mitarbeitern misst, traf ihren Satz mit 0,9974.
  0,85 für Verbote, 0,50 für alles andere. In der anderen Richtung gilt das
  Gegenteil: ein übersehenes hohes Risiko kostet den Nutzer die Vorbereitung
  auf Pflichten, die er erfüllen muss.
* *Verlangter Wortlaut.* Manche Tatbestände verlangen ein Merkmal, das kein
  Bedeutungsvergleich ersetzt. Artikel 5 Absatz 1 Buchstabe d verbietet die
  Vorhersage von Straftaten nur, wenn sie **ausschließlich** auf Profiling
  beruht. Fehlt das Wort, greift Anhang III Nummer 6 Buchstabe d — Pflichten
  statt Verbot. Für den Nutzer ist das der Unterschied zwischen weitermachen
  mit Auflagen und einstellen; er darf nicht an der Ähnlichkeit einer
  Wortgruppe hängen. Setze das auf **beiden** Wegen durch, im Katalog als
  `verlangt` und im Regelwerk als `verlangt_wortlaut`.

**Zwei Stufen, damit es nichts kostet.** Der Kreuzbewerter rechnet je Paar.
Erst wählt die Sinn-Nähe des Einbetters je Satz höchstens fünf Fundstellen aus,
davon höchstens zwei je Regel; nur diese Paare bewertet der Kreuzbewerter. Die
Grenze je Regel ist nötig: Anhang I nennt 20 Produktgattungen mit gleich
gebauten Sätzen, deren gemeinsames Satzgerüst sonst die ganze Vorauswahl
belegt — derselbe Fehler wie in a), nur eine Stufe früher. Der Einbetter taugt
zum Auswählen (bei 15 von 20 Beschreibungen stand die richtige Stelle schon bei
ihm auf Platz eins), nicht zum Entscheiden (falsche Stellen bis 0,745, richtige
bei 0,673).

**Fehlt eines der Modelle, liefert der Zweckweg eine leere Liste** und die
Wortlisten bleiben allein zuständig — mit einer Meldung im Protokoll. Der
Container ohne Netz und das Telefon müssen weiter einstufen können.

**Rechtliche Feinheiten, die ohne Hinweis falsch werden:**

| Fall | Richtig | Grundlage |
|---|---|---|
| Stimmung in Kundenfreitexten | **nicht** verboten | Artikel 3 Nummer 39 setzt biometrische Daten voraus; Text ist keine |
| Emotionen aus Mimik im Bewerbungsgespräch | verboten | Artikel 5 Absatz 1 Buchstabe f; das Bewerbungsverfahren gehört zum Arbeitsplatz |
| Müdigkeitserkennung bei Fahrern | **nicht** verboten | Ausnahme aus Sicherheitsgründen, Artikel 5 Absatz 1 Buchstabe f |
| Biometrie am Werkstor | Hochrisiko, **nicht** Artikel 26 Absatz 10 | der verlangt zusätzlich Strafverfolgung |
| Lernplattform für Beschäftigte, unverbindlich | minimal | kein Einsatz *für* Entscheidungen über Beschäftigte |
| Rückfallprognose für die Polizei | Hochrisiko, **nicht** verboten | Artikel 5 Absatz 1 Buchstabe d verlangt „ausschließlich auf der Grundlage des Profiling"; sonst Anhang III Nummer 6 Buchstabe d |
| ChatGPT-Nutzer, der Texte erzeugen lässt | **keine** Kennzeichnungspflicht | Artikel 50 Absatz 2 bindet den Anbieter; der Betreiber trifft nur Absatz 3 und 4 |
| Schweißnahtprüfung per Kamera an der Maschine | minimal | Qualitätsprüfung ist kein Sicherheitsbauteil nach Anhang I |
| Schichtplan, der Nachtschichten nach Krankheitstagen verteilt | Hochrisiko | Anhang III Nummer 4 Buchstabe b: Aufgabenzuweisung nach persönlichen Merkmalen |
| Modell nur für die eigene Forschung, nicht in Verkehr | minimal | Ausnahme in Artikel 3 Nummer 63 |

### Stufe 5 — Die Suche

Vier Wege, weil Rechtsfragen auf zwei Arten gestellt werden:

1. **Vektorsuche** (Bedeutung) — bge-m3 auf dem Rechner, 1024 Dimensionen
2. **BM25-Stichwortsuche** (Wortlaut) — eigene Fassung, k1 = 1,5, b = 0,75
3. **Wortgewichte des Modells** — nur bge-m3
4. **Fundstellenweg** — „Art. 6 Abs. 3" wird per regulärem Ausdruck zu
   `KI-VO/art-6/abs-3` aufgelöst und direkt geholt

Zusammengeführt wird über **Reciprocal Rank Fusion** (`gewicht / (60 + rang)`),
nicht über die Punktzahlen: die sind zwischen den Wegen nicht vergleichbar. Der
Fundstellenweg bekommt Gewicht 3,0. Danach bewertet ein Kreuzbewerter
(bge-reranker-v2-m3) die besten 30 neu.

Der Bestand wird einmal gerechnet und abgelegt — **als gepacktes JSON, nie als
pickle** (Grundsatz 7). Beim Laden wird der Modellname verglichen: Einbettungen
verschiedener Modelle liegen in verschiedenen Räumen, und die Treffer wären
stiller Unsinn.

**Der Lauf dauert rund eine Stunde. Lege alle 64 Einheiten ein Teilstück ab**,
sonst kostet jeder Abbruch die ganze Rechenzeit. (Dieser Fehler wurde hier
zweimal gemacht, bevor die Zwischenstände eingebaut wurden.)

### Stufe 6 — Die Antwort

Die Einstufung wird dem Modell als feststehende Tatsache vorgelegt, und zwar
**nach** den Angaben des Nutzers: das Letzte, was es liest, ist das Regelwerk.

Gegen untergeschobene Anweisungen: eine je Anfrage gewürfelte Abschnittsmarke
(`secrets.token_hex(6)`). Wer eine Abschnittsgrenze nachbauen will, müsste sie
erraten. Die Systemanweisung erklärt Beschreibung und Belege ausdrücklich zu
Daten.

Nach dem Formulieren wird nachgesehen, ob die Antwort Fundstellen nennt, die in
keinem Beleg stehen. Ohne Schlüssel entsteht die Auskunft allein aus dem
Regelwerk — knapper formuliert, inhaltlich dieselbe.

### Stufe 7 — Die Oberflächen

- **Weboberfläche und Schnittstelle** (FastAPI): `/`, `/gesundheit`,
  `/api/einstufung`, `/api/suche`, `/api/frage`, `/api/fragebogen`,
  `/api/fristen`. `/gesundheit` nennt den wahren Zustand samt Warnungen — läuft
  die Suche mit Ersatzverfahren, muss das dort stehen.
- **Kommandozeile**: `pruefen`, `fragen`, `suchen`, `dienst`, `stand`, jeweils
  mit `--json`. **Fallstrick:** stehen die allgemeinen Schalter am Haupt- und am
  Unterbefehl, überschreibt argparse den Wert des Hauptbefehls mit der Vorgabe
  des Unterbefehls — `helfer --json stand` verliert dann sein `--json`. Sieh in
  `sys.argv` nach, was wirklich auf der Zeile stand.
- **Container**: Nutzer ohne Verwalterrechte (feste Kennung 10001), Quelltext
  und Daten gehören root und sind nur lesbar. Ratenbegrenzung 30 Anfragen je
  Minute auf `/api/`, nicht auf `/gesundheit` — ein Prüfprogramm soll sich nicht
  selbst aussperren.
- **Android** (Kotlin): Datenbank und Suche auf dem Gerät. `androidx.sqlite` mit
  mitgeliefertem SQLite (FTS5, `unicode61`, `remove_diacritics=2`), ONNX Runtime
  **1.28.0** (ab 1.29.0 Telemetrie), Schlüssel in `EncryptedSharedPreferences`.
  Eine Berechtigung: INTERNET. Die Installationsdatei baut die Bauanlage.

### Stufe 8 — Die Anwendungsfälle

44 Fälle in 9 Gebieten, jeder mit `lage` (Alltagssprache, kein Fachjargon),
`rolle`, `einstufung`, `begruendung` und `rechtsgrundlagen`.

Sie sind **der Maßstab, nicht die Illustration**: eine Prüfung schickt jeden
Fall durch den Prüfer und vergleicht mit der hinterlegten Einstufung. In diesem
Projekt lag der Prüfer beim ersten Durchgang bei **23 von 44** — und die 21
Abweichungen waren allesamt echte Mängel, keine Fehler der Fallsammlung.

### Stufe 9 — Die Prüfungen

Mindestens so viel wie hier, aufgeteilt nach Gegenstand:

| Datei | Gegenstand | Hier |
|---|---|---:|
| `test_einstufung.py` | alle 44 Fälle, Merkmalsfilter, Rückfallprüfungen | 33 |
| `test_zwecke.py` | Katalogform, Fundstellen im Korpus, Satzform, Schwellen | 12 |
| `test_korpus.py` | Zielzahlen, Kennungsform, keine Doppelten, kein Beiwerk | 18 |
| `test_suche.py` | vier Wege, Ablegen und Laden, kein pickle | 25 |
| `test_antwort.py` | Angriffsreihe, erfundene Fundstellen, Auskunft ohne Modell | 36 |
| `test_dienst.py` | sieben Pfade, Ratenbegrenzung, Fehlerantworten | 23 |
| `test_cli.py` | fünf Befehle, `--json`, Schutzwall | 16 |
| `test_container.py` | ohne Netz, ohne Verwalterrechte, Schreibschutz | 10 |

**Messe die Genauigkeit an Fragen, die nicht aus der eigenen Sammlung kommen.**
Die 44 Anwendungsfälle sind der Maßstab für die Pflichten, aber sie sind
dieselben, an denen die Wortlisten entwickelt wurden — 44 von 44 heißt dort nur,
dass nichts zurückgefallen ist. Schreibe daneben mindestens 100 Beschreibungen,
wie Unternehmen sie wirklich einreichen: knapp, in eigener Sprache, oft als
Frage, mit Produktnamen und ohne Rechtsbegriffe, aus Sicht des Softwarehauses,
das ein KI-Produkt verkauft, **und** aus Sicht des Anwenders. Bestimme die
Soll-Einstufung aus dem Verordnungstext, nicht aus dem, was der Prüfer gerade
liefert. Die Hälfte davon muss „minimal" sein — ein Prüfer, der alles für
Hochrisiko erklärt, ist genauso wertlos wie einer, der nichts erkennt.

Hier stand die Genauigkeit auf diesen Fragen bei 55 %, als nur die Wortlisten
liefen, bei 86 % mit dem Zweckkatalog in erster Fassung, bei 98 % nach dem
Abarbeiten der vierzehn Fehlschläge und bei 100 %, nachdem Artikel 50 nach
Rollen getrennt war. Jeder Fehlschlag hatte eine benennbare Ursache —
fehlender Zwecksatz, fehlender Gegenzweck, falsche Schwelle, fehlende
Rollenprüfung, fehlender verlangter Wortlaut. Keiner war „das Modell ist eben
ungenau".

Setze die Grenze in der Prüfung aber **nicht** auf 100. Eine Grenze, die beim
ersten neuen Zwecksatz bricht, wird hochgesetzt statt behoben; 95 lässt Luft
und fängt einen echten Rückfall.

Die **Angriffsreihe** gehört dazu: mindestens zehn Versuche, über die
Beschreibung Anweisungen unterzuschieben, jeder zweifach geprüft — die
Abschnittsmarke bleibt eindeutig, und die Einstufung bleibt dieselbe.

Der Container-Test prüft **beides**: dass der Dienst ohne Netz antwortet, und
dass das Netz wirklich fehlt. Ohne die Gegenprobe ist die erste Prüfung wertlos.

**ruff, ruff format, mypy, bandit und pip-audit müssen ohne Beanstandung
durchlaufen, und der Prüfstand muss bei einem Befund abbrechen.** Ein Lauf, der
dauerhaft rot ist, wird nicht gelesen — dann fällt auch der erste echte Fehler
nicht auf. Jede Ausnahme wird in `pyproject.toml` begründet.

Lege ein Skript an, das **genau dasselbe prüft wie der Prüfstand**, in
derselben Reihenfolge und mit denselben Befehlen. Wer nur einen Teil prüft,
schiebt einen Fehler in den Prüfstand und merkt es erst dort — hier war es
einmal die Formatierung eines Ordners, der beim Aufruf nicht dabeistand, und
einmal fehlende Typangaben fremder Pakete, die auf dem Entwicklungsrechner
zufällig schon lagen. Der zweite Fall ist der unangenehmere: der Prüfstand
meldet etwas, das lokal niemand nachvollziehen kann.

Darum gehören **alle** Prüfwerkzeuge samt Typangaben in die
Entwicklungsabhängigkeiten, nicht nur die, die gerade fehlen.

### Stufe 10 — Die Präsentation

14 Folien, 16:9, für Fachkundige **und** Fachfremde: Lage, Beispiel, der
Grundsatz, Rechtsbestand, Suche, Einstufung, Pflichten, Sicherheit, Orte, zwei
Betriebsanleitungen, Prüfstand, Grenzen.

Baue sie als einzelne Folien-Dateien plus ein Skript, das daraus eine
eigenständige HTML-Seite setzt — sie läuft ohne Netz, blättert mit den
Pfeiltasten und druckt eine Folie je Seite.

**Zwei Fallstricke, die beide erst beim Messen auffallen:**

1. `transform: scale(calc(100cqw / 1920))` wirkt nicht — `scale()` braucht eine
   blanke Zahl, und eine Breite geteilt durch eine Zahl ist in CSS eine Länge.
   Setze den Maßstab per Skript.
2. Ein Browser setzt von sich aus Ränder auf Überschriften, Absätze und Listen.
   Über eine Folie summieren sie sich auf mehrere hundert Punkte, und der Inhalt
   läuft unten heraus, **ohne dass man es dem Text ansieht**. Räume sie ab.

**Miss jede Folie nach**, statt die Höhe zu schätzen: Fläche 1920 × 1080, innen
1664 × 824, keine Schrift unter 24 px. In diesem Projekt liefen beim ersten Bau
**14 von 14** Folien über, die schlimmste um das Doppelte.

### Stufe 11 — Veröffentlichen

README, LICENSE (Apache-2.0), NOTICE, CONTRIBUTING, CODE_OF_CONDUCT, SECURITY,
CHANGELOG, AUTHORS, CITATION.cff, `.gitignore`, `.gitattributes`,
`.editorconfig`, Prüfstand, Dependabot, Vorlagen für Meldungen und Vorschläge.

Eine Vorlage verdient besondere Aufmerksamkeit: **`rechtsfehler.yml`** — eine
falsch eingeordnete Lage ist der schwerste Fehler, den dieses Werkzeug machen
kann, und die Meldung dazu braucht Fundstelle, erwartete und erhaltene
Einstufung.

Dokumentation unter `docs/`: Architektur, Betriebsanleitung, Datenquellen,
Entscheidungen, Haftung, Sicherheit.

### Zum Schluss: nachmessen, nicht behaupten

Zähle jede Zahl, die in README, Dokumentation und Präsentation steht, am
fertigen Stand nach. Was nicht stimmt, wird berichtigt — nicht gerundet.

Und lies die Dokumentation noch einmal gegen den fertigen Stand: Sätze wie „das
Verzeichnis `tests/` ist leer" oder „die App-Datenbank ist älter als der
Korpus" sind beim Schreiben richtig gewesen und sind es nach der nächsten Stufe
nicht mehr. Erledigtes wird gelöscht, nicht durchgestrichen. Eine Dokumentation,
die einen behobenen Mangel noch nennt, ist schlimmer als keine: der Leser sucht
nach einem Fehler, der nicht mehr da ist.

---

## Was dieser Bauplan absichtlich offenlässt

- **Die Wortlisten im Einzelnen.** Welches Wort einen Bereich des Anhangs III
  kennzeichnet, ist eine Rechtsfrage. Der Bauplan gibt die Form vor und die
  Gegenfälle, an denen sich die Listen bewähren müssen.
- **Die Gestaltung der Präsentation.** Vorgegeben sind Fläche, Mindestgröße der
  Schrift und die Pflicht zum Nachmessen.
- **Das Sprachmodell zum Formulieren.** Austauschbar; die Einstufung hängt nicht
  daran (Grundsatz 1).

## Was er nicht leistet

Er ersetzt keine juristische Prüfung der Regeldateien. Die 44 Anwendungsfälle
sind aus dem Verordnungstext erarbeitet und mit Fundstellen begründet — aber
wer das Werkzeug im Unternehmen einsetzt, lässt das Regelwerk von einem
Menschen mit Zulassung durchsehen.

---

<sub>Dieser Bauplan beschreibt das Repository, in dem er liegt. Alle Zahlen sind
am Stand vom 04.10.2026 nachgemessen. Apache-2.0 — nachbauen, ändern und
weitergeben ausdrücklich erwünscht.</sub>
