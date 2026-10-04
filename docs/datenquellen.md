# Datenquellen und Datenstand

Eine Rechtsauskunft ohne Datum ist wertlos. Dieses Blatt sagt, woher jedes
Stück Text kommt, wann es geholt wurde, wie viel es ist und wie es
lizenzrechtlich steht.

## Der Stand in zwei Zahlen

| | Datum | Woher die Zahl kommt |
|---|---|---|
| **Regelwerk** (Einstufung, Pflichten, Datenschutzpfad) | **31.05.2026** | Feld `stand` in den Dateien unter `daten/regeln`, nachgelesen am 04.10.2026 |
| **Rechtstext** (Wortlaut im Bestand) | **04.10.2026** | Feld `gebaut` in `daten/aufbereitet/korpus_befund.json` |

Die beiden Daten unterscheiden sich, weil es zwei verschiedene Dinge sind. Der
Wortlaut der Verordnung wurde am 04.10.2026 geholt. Die Bewertung, welche
Pflicht aus welcher Klasse folgt, ist von Hand geschrieben und auf dem Stand
vom 31.05.2026. **Die Auskunft ist also inhaltlich auf dem Stand Mai 2026.**
Rechtsprechung, Leitlinien des Europäischen Datenschutzausschusses,
Angemessenheitsbeschlüsse der Kommission und delegierte Rechtsakte nach diesem
Datum sind nicht berücksichtigt.

Der Vorbehalt steht im Regelwerk selbst und wird in jeder Auskunft mitgegeben:

> Die Fristen stehen so im Amtsblatt vom 12. Juli 2024. Zum Datenstand dieses
> Regelsatzes wurden Änderungen einzelner Fristen politisch erörtert. Vor einer
> Entscheidung mit Geld- oder Rechtsfolgen ist der geltende Stand bei der
> zuständigen Behörde zu prüfen.

## Was im Bestand liegt

Nachgemessen am 04.10.2026 an `daten/aufbereitet/korpus.jsonl`: 2811
Rechtseinheiten, 2 089 375 Zeichen. Der Korpusbau lief **ohne Warnung**.

| Rechtsakt | Art der Einheit | Stück |
|---|---|---|
| KI-Verordnung | Artikel, Absätze und Nummern | 1042 |
| KI-Verordnung | Anhänge, Nummern und Buchstaben | 164 |
| KI-Verordnung | Erwägungsgründe | 180 |
| Datenschutz-Grundverordnung | Artikel, Absätze und Nummern | 851 |
| Datenschutz-Grundverordnung | Erwägungsgründe | 173 |
| Bundesdatenschutzgesetz | Paragrafen | 357 |
| Anwendungsfälle (keine Rechtsquelle) | Fallbeispiele | 44 |

Eine Rechtseinheit ist das kleinste Stück, auf das sich zeigen lässt: ein
Absatz eines Artikels, eine Nummer oder ein Buchstabe eines Anhangs, eine
Begriffsbestimmung, ein Erwägungsgrund, ein Paragraf.

Darin enthalten und für die Einstufung entscheidend:

* die **23 Buchstabenpunkte des Anhangs III** unter den acht Bereichen. Nummer
  4 Buchstabe a trifft die Einstellung, Buchstabe b die Arbeitsbedingungen —
  zwei verschiedene Sachverhalte unter einer Überschrift.
* die **20 Rechtsakte des Anhangs I**, auf die Artikel 6 Absatz 1 für das hohe
  Risiko über das Produktsicherheitsrecht verweist.
* die **68 Begriffsbestimmungen des Artikels 3** und die **26 des Artikels 4
  der Datenschutz-Grundverordnung**, jede als eigene Einheit.

## Quelle für Quelle

Beide Verordnungen kommen aus dem amtlichen Volltext des Amtsblatts. Geholt
werden sie nicht über die Webseite von EUR-Lex, sondern über deren Ablage
**Cellar**:

```
http://publications.europa.eu/resource/cellar/<Kennung>
Accept: application/xhtml+xml
Accept-Language: deu
```

**Warum nicht über die Webseite:** `eur-lex.europa.eu` antwortet ohne
vollständigen Browser-Kopf mit HTTP 202 und null Byte und schickt danach ein
Captcha der Firewall. Sechs Versuche brachten jeweils 2035 Byte statt der
erwarteten über einer Million. Vor Cellar steht diese Firewall nicht. Das
Skript `scripts/holen_amtsblatt.py` holt beide Verordnungen so und verwirft
jede Antwort, die unter der Mindestgröße bleibt — eine halbe Datei wäre
schlimmer als keine.

### 1. KI-Verordnung, amtlicher Volltext — 1386 Einheiten

* **Rechtsakt:** Verordnung (EU) 2024/1689 über künstliche Intelligenz
* **Kennung:** CELEX 32024R1689, Cellar `dc8116a1-3fe6-11ef-865a-01aa75ed71a1`
* **Fassung:** Amtsblatt der Europäischen Union vom 12. Juli 2024
* **Datei:** `daten/roh/kivo_amtsblatt_de.xhtml`
* **Geliefert:** 1386 Einheiten — 113 Artikel mit 929 Absätzen und Nummern,
  13 Anhänge mit 151 Nummern und Buchstaben, 180 Erwägungsgründe
* **Warnungen:** keine
* **Lizenzlage:** amtlicher Text der Europäischen Union. Für die
  Weiterverwendung von Kommissionsdokumenten gilt der Beschluss 2011/833/EU.
  Verbindlich ist allein die Veröffentlichung im Amtsblatt; die hier
  mitgelieferte Fassung ist eine maschinell zerlegte Kopie.

### 2. Datenschutz-Grundverordnung, amtlicher Volltext — 1024 Einheiten

* **Rechtsakt:** Verordnung (EU) 2016/679
* **Kennung:** CELEX 32016R0679, Cellar `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`
* **Fassung:** Amtsblatt L 119 vom 4. Mai 2016, Seite 1
* **Datei:** `daten/roh/dsgvo_amtsblatt_de.xhtml`
* **Geliefert:** 1024 Einheiten — 99 Artikel mit 752 Absätzen und Nummern,
  173 Erwägungsgründe
* **Warnungen:** keine
* **Lizenzlage:** wie bei der KI-Verordnung.

Die Fundstellen zur Datenschutz-Grundverordnung sind damit **absatzgenau**. Die
frühere Fassung kam von einer nicht amtlichen Seite und lag nur je Artikel vor;
sie wies gegenüber dem Amtsblatt 51 Prozent Abweichung auf, und Artikel 13
hatte dort 909 statt 3374 Zeichen. Die Rückfallquelle greift nur noch ein, wenn
der amtliche Text für einen Rechtsakt **ganz** fehlt — vorher mischte sie ihre
Kennungen (`art-4/abs-14`) neben die amtlichen (`art-4/nr-14`).

### 3. Der Zerleger

`src/helfer/korpus/eurlex.py` arbeitet über die Anker des Dokuments
(`div#art_6`, `div#006.003`, `div#anx_III`, `*#rct_60`,
`p.oj-ti-grseq-1`), nie über Textmuster. Ein Textmuster hielte jede Erwähnung
von „Artikel 99" im Fließtext für einen Artikelanfang und machte Artikel 5
31 828 Zeichen lang.

Vier Eigenheiten des Amtsblatts, an denen eine naive Fassung scheitert:

* **Die Zählung steht nicht immer in der ersten Tabellenzelle.** Eingerückte
  Aufzählungen haben davor eine leere Zelle, die die Einrückung trägt. Anhang I
  ist so gebaut und ging deshalb vollständig verloren.
* **Abschnittsköpfe setzen die Zählung zurück.** Anhang VIII hat drei
  Abschnitte, jeder zählt wieder ab 1; Anhang XI nennt seinen Abschnitt nur
  „Abschnitt 1" und stellt ihm eine zweite Überschrift nach. Der Abschnitt
  gehört in die Kennung, sonst tragen drei Nummern denselben Namen.
* **Verschachtelte Aufzählungen.** Artikel 5 Absatz 1 Buchstabe c enthält „i)"
  und „ii)"; im Fließtext sieht „i)" wie der Buchstabe i aus, den es dort auch
  echt gibt.
* **Fremde Anker.** Artikel 107 und 108 zitieren fremde Rechtsakte mit deren
  Ankern (`005.004` steht in `art_107`). Die Absatznummer wird darum gegen die
  Artikelnummer geprüft.

Der Bau bricht ab, wenn eine Kennung zweimal mit **verschiedenem** Text
vorkommt, und nennt die betroffenen Kennungen — eine Zahl allein sagte nicht,
wo zu suchen ist.

### 4. Bundesdatenschutzgesetz — 357 Einheiten

* **Adresse:** `https://www.gesetze-im-internet.de/bdsg_2018/BJNR209710017.html`
* **Geholt:** 03.10.2026, Datei `daten/roh/bdsg.html`, 271 137 Byte
* **Umfang:** 357 Einheiten
* **Herangezogen:** nur Teile 1 und 2, also die Durchführungsbestimmungen zur
  Datenschutz-Grundverordnung. Teil 3 (§§ 45 bis 84) gilt nach § 45 nur für
  Verarbeitungen durch Behörden zur Verhütung, Ermittlung, Aufdeckung,
  Verfolgung oder Ahndung von Straftaten und Ordnungswidrigkeiten und ist
  daher nicht herangezogen, auch wo er inhaltlich parallele Vorschriften
  enthält.
* **Lizenzlage:** Gesetze sind nach § 5 Absatz 1 des Urheberrechtsgesetzes
  amtliche Werke ohne Urheberrechtsschutz. Die Darstellung auf
  gesetze-im-internet.de stammt vom Bundesministerium der Justiz und von der
  juris GmbH.

Der Zerleger arbeitet über die Gliederung der Seite (`div.jnnorm`, `.jnenbez`,
`.jnentitel`, `div.jurAbsatz`), nicht über Textmuster. Ein Textmuster trennte
sonst mitten im Satz, wenn ein Querverweis wie „§ 63 Nummer 3 der
Verwaltungsgerichtsordnung" auftritt.

### 5. Anwendungsfälle — 44 Einheiten, keine Rechtsquelle

* **Woher:** `daten/faelle/*.yaml`, neun Dateien, selbst geschrieben
* **Verteilung:** Beschäftigung 7, Kredit und Versicherung 5, Bildung 4,
  Kundenkontakt und Inhalte 5, Medizin und Produkte 4, eigene Modelle 4, kein
  hohes Risiko 6, verbotene Praktiken 5, Datenschutz-Mischfälle 4
* **Form je Fall:** Lage, Rolle, Einstufung, Begründung, Rechtsgrundlagen,
  Pflichten, Lernhinweis, Stolperstein, verwandte Fälle
* **Im Bestand geführt als:** Rechtsakt „Leitlinie", Art „fallbeispiel". Das
  Datenmodell behandelt „Leitlinie" ausdrücklich als nicht verbindlich.
* **Geprüft:** von keiner Behörde und von keiner Kanzlei. Sie sind Anschauung.

Sie gehen als Belegstellen in die Suche ein, weil ein ausgearbeitetes Beispiel
oft schneller trägt als der Verordnungstext. In der Auskunft erscheinen sie
unter „Anwendungsfall: <Titel>", nicht als Artikelzitat.

## Das Regelwerk

Vier Dateien, alle von Hand geschrieben, alle mit Stand 31.05.2026 — der
Zweckkatalog mit Stand 04.10.2026.

| Datei | Inhalt | Nachgemessen |
|---|---|---|
| `daten/regeln/kivo_risikoklassen.yaml` | Verbote, Anhang I, Anhang III, die Ausnahme nach Artikel 6 Absatz 3, Transparenz, Modelle mit allgemeinem Verwendungszweck, Rollenwechsel, Fristen, Sanktionen | 8 Verbotstatbestände, 5 Fristenstufen, 3 Sanktionsstufen; als Einstufungsregeln in die App ausgegeben: 28 |
| `daten/regeln/kivo_pflichten.yaml` | die Pflichten mit Klasse, Rolle, Fundstelle, Frist, Nachweis und Folge bei Verstoß | 57 Pflichten |
| `daten/regeln/dsgvo_pruefpfad.yaml` | der Prüfpfad des Datenschutzrechts in der Reihenfolge, in der er abzuarbeiten ist | 26 Abschnitte, davon 14 immer geltend und 12 bedingt |
| `daten/regeln/kivo_zweckkatalog.yaml` | zu jeder Fundstelle derselbe Zweck in Unternehmenssprache; das Feld `regel` zeigt auf die bestehenden Kennungen der Risikoklassendatei | 55 Einträge, 107 Zwecke, 21 Gegenzwecke |

Jede Pflicht und jeder Abschnitt nennt seine Rechtsgrundlagen als Kennungen.
Nachgemessen am 04.10.2026: alle genannten Rechtsgrundlagen sind im Korpus
vorhanden, keine einzige ohne Fundstelle — das gilt auch für die 55
Fundstellen des Zweckkatalogs, die eine eigene Prüfung abgleicht. Der Befehl dafür steht in
[betriebsanleitung.md](betriebsanleitung.md), Abschnitt c.

## Was die App kennt

`android/app/src/main/assets/recht.db`, gebaut am 04.10.2026, 10 747 904 Byte:

| Tabelle | Zeilen |
|---|---|
| `einheit` | 2811 |
| `vektor` | 2811 |
| `pflicht` | 57 |
| `risikoregel` | 28 |
| `fall` | 44 |
| `pruefabschnitt` | 26 |
| `meta` | 12 |

**Die App kennt denselben Rechtstext wie der Rechner.** Die Datenbank trägt die
Prüfsumme des Korpus, aus dem sie gebaut wurde — `e6606acd97e9394a…` —, und das
ist die des heutigen Korpus. Jede Rechtsgrundlage der Pflichten findet dort ihre
Fundstelle; der Ausgabelauf prüft das und schreibt keine halbfertige Datenbank.

**Was die App nicht hat, ist der Zweckweg.** Der Kreuzbewerter wiegt 568
Millionen Werte und läuft nicht auf einem Telefon. Auf dem Gerät entscheiden die
Wortlisten allein — gemessen 55 von 100 Unternehmensfragen gegen 100 auf dem
Rechner. Für eine erste Einordnung unterwegs trägt das; für die Entscheidung
gehört die Frage auf den Rechner oder in den Container.

**Die Vektoren der App sind 8-Bit-Werte.** Das umgewandelte Modell
(`einbetter.onnx`, 118,1 MB) rechnet grober als das ursprüngliche; gemessene
Ähnlichkeit zwischen beiden am 04.10.2026: 0,9907.

## Was nicht drin ist

Damit niemand danach sucht:

* **Rechtsprechung.** Keine Entscheidung eines Gerichts, auch nicht des
  Gerichtshofs der Europäischen Union.
* **Leitlinien und Stellungnahmen.** Keine Leitlinie der Kommission, des
  Europäischen Datenschutzausschusses, des Büros für Künstliche Intelligenz
  oder einer deutschen Aufsichtsbehörde.
* **Harmonisierte Normen.** Die technischen Normen, über die sich die Vermutung
  der Konformität nach Artikel 40 herstellen lässt, sind nicht erfasst.
* **Delegierte Rechtsakte und Durchführungsrechtsakte** nach dem 31.05.2026.
* **Landesdatenschutzgesetze** und bereichsspezifische Vorschriften
  (Sozialgesetzbuch, Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz und
  weitere).
* **Teil 3 des Bundesdatenschutzgesetzes**, siehe oben.
* **Andere Sprachen.** Der Bestand ist deutsch. Englische Fassungen der beiden
  Verordnungen liegen in `daten/roh`, gehen aber nicht in den Bestand ein.
