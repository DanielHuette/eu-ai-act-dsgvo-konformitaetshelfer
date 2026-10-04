# Datenquellen und Datenstand

Eine Rechtsauskunft ohne Datum ist wertlos. Dieses Blatt sagt, woher jedes
Stück Text kommt, wann es geholt wurde, wie viel es ist und wie es
lizenzrechtlich steht.

## Der Stand in drei Zahlen

| | Datum | Woher die Zahl kommt |
|---|---|---|
| **Fragefolge** (woraus die Einstufung entsteht) | **19.05.2026** | Entwurf der Leitlinien der Kommission; Feld `stand` in `daten/regeln/fragefolge-aufbau.yaml`: 2026-10-04 |
| **Regelwerk** (Pflichten, Datenschutzpfad) | **31.05.2026** | Feld `stand` in den Dateien unter `daten/regeln`, nachgelesen am 04.10.2026 |
| **Rechtstext** (Wortlaut im Bestand) | **04.10.2026** | Feld `gebaut` in `daten/aufbereitet/korpus_befund.json` |

Die drei Daten unterscheiden sich, weil es drei verschiedene Dinge sind. Der
Wortlaut der Verordnung wurde am 04.10.2026 geholt. Die Fragen stammen aus dem
Entwurf der Leitlinien vom 19. Mai 2026. Die Bewertung, welche Pflicht aus
welcher Klasse folgt, ist von Hand geschrieben und auf dem Stand vom
31.05.2026. **Die Auskunft ist also inhaltlich auf dem Stand Mai 2026.**
Rechtsprechung, Leitlinien des Europäischen Datenschutzausschusses,
Angemessenheitsbeschlüsse der Kommission und delegierte Rechtsakte nach diesem
Datum sind nicht berücksichtigt.

Der Vorbehalt steht im Regelwerk selbst und wird in jeder Auskunft mitgegeben:

> Die Fristen stehen so im Amtsblatt vom 12. Juli 2024. Zum Datenstand dieses
> Regelsatzes wurden Änderungen einzelner Fristen politisch erörtert. Vor einer
> Entscheidung mit Geld- oder Rechtsfolgen ist der geltende Stand bei der
> zuständigen Behörde zu prüfen.

## 1. Die Leitlinien der Kommission — Grundlage der Einstufung

* **Dokument:** Entwurf der Leitlinien der Europäischen Kommission zur
  Einstufung von Hochrisiko-KI-Systemen nach Artikel 6 der Verordnung (EU)
  2024/1689, zur Anhörung der Beteiligten
* **Fassung:** 19. Mai 2026, englisch
* **Umfang:** 167 Seiten in drei Teilen — 148 Seiten zu Anhang III, 13 Seiten
  zu Anhang I, 6 Seiten allgemeine Grundsätze
* **Dateien:** `daten/roh/leitlinien/128559.pdf` (260 362 Byte),
  `128560.pdf` (337 928 Byte), `128561.pdf` (1 547 742 Byte), daneben der
  ausgelesene Text als `.txt`
* **Aufgeteilt in:** 60 Abschnitte unter `daten/roh/leitlinien/abschnitte/`,
  490 318 Zeichen, mit `karte.json` als Verzeichnis von Abschnittsnummer,
  Titel und Zeichenzahl
* **Bindungswirkung:** **keine.** Es ist ein Entwurf. Die öffentliche Anhörung
  lief bis zum 23. Juni 2026; eine endgültige Fassung lag bei Abschluss dieser
  Arbeit nicht vor. Leitlinien der Kommission binden Gerichte ohnehin nicht.
  Das Werkzeug sagt diesen Vorbehalt in jeder Auskunft mit, die sich darauf
  stützt.

Aus diesem Dokument stammt die Fragefolge. Jede Frage, jeder Ausschluss und
jedes Beispiel trägt im Feld `beleg` die Absatznummer der Stelle, auf der es
beruht — etwa `"(245)"`. Nachgemessen am 04.10.2026 über `Durchlauf.zahlen()`:

| Datei | Bereich des Anhangs III | Punkte | Ausschlüsse | Beispiele |
|---|---|---|---|---|
| `nr-1-biometrie.yaml` | Nummer 1, Abschnitt 3.1 | 3 | 25 | 21 |
| `nr-2-infrastruktur.yaml` | Nummer 2, Abschnitt 3.2 | 4 | 22 | 26 |
| `nr-3-bildung.yaml` | Nummer 3, Abschnitt 3.3 | 4 | 24 | 31 |
| `nr-4-beschaeftigung.yaml` | Nummer 4, Abschnitt 3.4 | 3 | 18 | 34 |
| `nr-5-dienste.yaml` | Nummer 5, Abschnitt 3.5 | 4 | 35 | 45 |
| `nr-6-7-8-behoerden.yaml` | Nummern 6 bis 8, Abschnitte 3.6 bis 3.8 | 13 | 90 | 30 |
| **zusammen** | | **31** | **214** | **187** |

Dazu `anhang-i-produkte.yaml` mit den 15 Produktgattungen und den Bedingungen
des Artikels 6 Absatz 1, und `vorfragen-und-filter.yaml` mit den 3 Vorfragen,
4 Hinweisen und der Ausnahme des Artikels 6 Absatz 3. Über alles gezählt: **379
Fragen.**

Ein Ausschluss ist ein Satz des amtlichen Textes, der sagt, was **nicht**
erfasst ist. Ein Beispiel ist ein Fall, den die Kommission selbst nennt. Beides
steht im Befund neben der Einstufung — ohne diese Sätze wäre der Befund eine
Behauptung.

### Die Prüffälle

`daten/pruefung/amtliche-beispiele.json` — **217 Beispiele** aus demselben
Dokument, je mit Lage, Soll-Wertung, Fundstelle, Absatznummer und der
Begründung der Kommission im Wortlaut:

```json
{"lage": "Ein Finanzintermediär bewertet mit einem System, ob bestehenden oder
          künftigen Kunden ein Wertpapierkredit … gewährt oder erhöht wird, und nur das.",
 "soll": "kein_hochrisiko",
 "punkt": "KI-VO/anh-III/nr-5-b",
 "beleg": "(nach 309)",
 "amtliche_begruendung": "Es ist allein für einen nicht grundlegenden privaten Dienst gedacht."}
```

Das ist der Maßstab: die Soll-Wertungen stammen von der Kommission, nicht von
mir. **206 von 217 werden richtig eingestuft.** Das Messverfahren und jede
einzelne Abweichung stehen in
[../daten/pruefung/MESSUNG.md](../daten/pruefung/MESSUNG.md).

## 2. Der Rechtstext — woher der Wortlaut kommt

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
Begriffsbestimmung, ein Erwägungsgrund, ein Paragraf. Die Fragefolge zeigt mit
ihrem Feld `fundstelle` auf genau diese Kennungen — darum steht im Befund der
amtliche Text und nicht nur eine Nummer.

Darin enthalten und für die Einstufung entscheidend:

* die **24 Buchstabenpunkte des Anhangs III** unter den acht Bereichen. Nummer
  4 Buchstabe a trifft die Einstellung, Buchstabe b die Arbeitsbedingungen —
  zwei verschiedene Sachverhalte unter einer Überschrift.
* die **20 Rechtsakte des Anhangs I**, auf die Artikel 6 Absatz 1 für das hohe
  Risiko über das Produktsicherheitsrecht verweist.
* die **68 Begriffsbestimmungen des Artikels 3** und die **26 des Artikels 4
  der Datenschutz-Grundverordnung**, jede als eigene Einheit.

### Der Weg über Cellar

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

### KI-Verordnung, amtlicher Volltext — 1386 Einheiten

* **Rechtsakt:** Verordnung (EU) 2024/1689 über künstliche Intelligenz
* **Kennung:** CELEX 32024R1689, Cellar `dc8116a1-3fe6-11ef-865a-01aa75ed71a1`
* **Fassung:** Amtsblatt der Europäischen Union vom 12. Juli 2024
* **Datei:** `daten/roh/kivo_amtsblatt_de.xhtml`, 1 338 179 Byte
* **Geliefert:** 1386 Einheiten — 113 Artikel mit 929 Absätzen und Nummern,
  13 Anhänge mit 151 Nummern und Buchstaben, 180 Erwägungsgründe
* **Warnungen:** keine
* **Lizenzlage:** amtlicher Text der Europäischen Union. Für die
  Weiterverwendung von Kommissionsdokumenten gilt der Beschluss 2011/833/EU.
  Verbindlich ist allein die Veröffentlichung im Amtsblatt; die hier
  mitgelieferte Fassung ist eine maschinell zerlegte Kopie.

### Datenschutz-Grundverordnung, amtlicher Volltext — 1024 Einheiten

* **Rechtsakt:** Verordnung (EU) 2016/679
* **Kennung:** CELEX 32016R0679, Cellar `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`
* **Fassung:** Amtsblatt L 119 vom 4. Mai 2016, Seite 1
* **Datei:** `daten/roh/dsgvo_amtsblatt_de.xhtml`, 862 613 Byte
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

### Der Zerleger

`src/helfer/korpus/eurlex.py` arbeitet über die Anker des Dokuments
(`div#art_6`, `div#006.003`, `div#anx_III`, `*#rct_60`, `p.oj-ti-grseq-1`), nie
über Textmuster. Ein Textmuster hielte jede Erwähnung von „Artikel 99" im
Fließtext für einen Artikelanfang und machte Artikel 5 31 828 Zeichen lang.

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

### Bundesdatenschutzgesetz — 357 Einheiten

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

Der Zerleger `src/helfer/korpus/deutsche_quellen.py` arbeitet über die
Gliederung der Seite (`div.jnnorm`, `.jnenbez`, `.jnentitel`, `div.jurAbsatz`),
nicht über Textmuster. Ein Textmuster trennte sonst mitten im Satz, wenn ein
Querverweis wie „§ 63 Nummer 3 der Verwaltungsgerichtsordnung" auftritt.

### Anwendungsfälle — 44 Einheiten, keine Rechtsquelle

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

## 3. Das Regelwerk — was aus einer Klasse folgt

Von Hand geschrieben, Stand 31.05.2026, nachgemessen am 04.10.2026:

| Datei | Inhalt | Nachgemessen |
|---|---|---|
| `daten/regeln/kivo_pflichten.yaml` | die Pflichten mit Klasse, Rolle, Fundstelle, Frist, Nachweis und Folge bei Verstoß | 57 Pflichten |
| `daten/regeln/dsgvo_pruefpfad.yaml` | der Prüfpfad des Datenschutzrechts in der Reihenfolge, in der er abzuarbeiten ist | 26 Abschnitte, davon 14 immer geltend und 12 bedingt |
| `daten/regeln/kivo_risikoklassen.yaml` | Verbote nach Artikel 5, Transparenz nach Artikel 50, Modelle mit allgemeinem Verwendungszweck, Rollenwechsel, Fristen, Sanktionen | 8 Verbotstatbestände, 5 Fristenstufen, 3 Sanktionsstufen |
| `daten/regeln/kivo_zweckkatalog.yaml` | zu jeder Fundstelle derselbe Zweck in Unternehmenssprache; trägt die Suche im Verordnungstext und die ausformulierte Auskunft | 129 Zeilen zu 55 Fundstellen, 21 Gegenzwecke |

Jede Pflicht und jeder Abschnitt nennt seine Rechtsgrundlagen als Kennungen.
Nachgemessen am 04.10.2026: alle genannten Rechtsgrundlagen sind im Korpus
vorhanden, keine einzige ohne Fundstelle. Der Befehl dafür steht in
[betriebsanleitung.md](betriebsanleitung.md), Abschnitt c.

## Was nicht drin ist

Damit niemand danach sucht:

* **Rechtsprechung.** Keine Entscheidung eines Gerichts, auch nicht des
  Gerichtshofs der Europäischen Union.
* **Weitere Leitlinien und Stellungnahmen.** Keine Leitlinie des Europäischen
  Datenschutzausschusses, des Büros für Künstliche Intelligenz oder einer
  deutschen Aufsichtsbehörde. Vom Dokument der Kommission ist nur der Entwurf
  zur Einstufung von Hochrisiko-KI-Systemen erfasst.
* **Harmonisierte Normen.** Die technischen Normen, über die sich die Vermutung
  der Konformität nach Artikel 40 herstellen lässt, sind nicht erfasst.
* **Delegierte Rechtsakte und Durchführungsrechtsakte** nach dem 31.05.2026.
* **Landesdatenschutzgesetze** und bereichsspezifische Vorschriften
  (Sozialgesetzbuch, Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz und
  weitere).
* **Teil 3 des Bundesdatenschutzgesetzes**, siehe oben.
* **Andere Sprachen.** Der Bestand ist deutsch. Englische Fassungen der beiden
  Verordnungen liegen in `daten/roh`, gehen aber nicht in den Bestand ein.
