# Datenquellen und Datenstand

Eine Rechtsauskunft ohne Datum ist wertlos. Dieses Blatt sagt, woher jedes
Stück Text kommt, wann es geholt wurde, wie viel es ist und wie es
lizenzrechtlich steht.

## Der Stand in zwei Zahlen

| | Datum | Woher die Zahl kommt |
|---|---|---|
| **Regelwerk** (Einstufung, Pflichten, Datenschutzpfad) | **31.05.2026** | Feld `stand` in den drei Dateien unter `daten/regeln`, nachgelesen am 03.10.2026 |
| **Rechtstext** (Wortlaut im Bestand) | **03.10.2026** | Feld `gebaut` in `daten/aufbereitet/korpus_befund.json` |

Die beiden Daten unterscheiden sich, weil es zwei verschiedene Dinge sind. Der
Wortlaut der Verordnung wurde am 03.10.2026 geholt. Die Bewertung, welche
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

Nachgemessen am 03.10.2026 an `daten/aufbereitet/korpus.jsonl`: 2721
Rechtseinheiten, 1 966 046 Zeichen.

| Rechtsakt | Art der Einheit | Stück |
|---|---|---|
| KI-Verordnung | Artikel und Absätze | 1054 |
| KI-Verordnung | Anhänge und Anhangspunkte | 65 |
| KI-Verordnung | Erwägungsgründe | 180 |
| Datenschutz-Grundverordnung | Artikel | 848 |
| Datenschutz-Grundverordnung | Erwägungsgründe | 173 |
| Bundesdatenschutzgesetz | Paragrafen | 357 |
| Anwendungsfälle (keine Rechtsquelle) | Fallbeispiele | 44 |

Eine Rechtseinheit ist das kleinste Stück, auf das sich zeigen lässt: ein
Absatz eines Artikels, eine Nummer eines Anhangs, ein Erwägungsgrund, ein
Paragraf. Dass es mehr Einheiten als Artikel gibt, liegt daran: Artikel 6 der
KI-Verordnung liefert mehrere Einheiten, eine je Absatz.

## Quelle für Quelle

### 1. KI-Verordnung, amtlicher Volltext — 1228 Einheiten

* **Rechtsakt:** Verordnung (EU) 2024/1689 über künstliche Intelligenz
* **Adresse:** `https://eur-lex.europa.eu/legal-content/DE/TXT/HTML/?uri=CELEX:32024R1689`
* **Kennung:** CELEX 32024R1689
* **Fassung:** Amtsblatt der Europäischen Union vom 12. Juli 2024
* **Geholt:** 03.10.2026, Datei `daten/roh/eurlex/ki-vo-de.html`, 1 340 252 Byte
* **Geliefert:** 1228 Einheiten — 113 Artikel mit 870 Absätzen, 13 Anhänge mit
  52 Punkten, 180 Erwägungsgründe
* **Warnung des Laufs:** 27 doppelte Kennungen übergangen. Das heißt: der
  Zerleger traf 27 Stellen, deren Kennung schon belegt war, und hat sie
  übersprungen. Welche das sind, ist nicht untersucht.
* **Lizenzlage:** amtlicher Text der Europäischen Union. Für die
  Weiterverwendung von Kommissionsdokumenten gilt der Beschluss 2011/833/EU.
  Verbindlich ist allein die Veröffentlichung im Amtsblatt; die hier
  mitgelieferte Fassung ist eine maschinell zerlegte Kopie.

Der Zerleger `src/helfer/korpus/eurlex.py` arbeitet über die Anker des
Dokuments (`div#art_6`, `div#006.003`, `div#anx_III`, `*#rct_60`), nicht über
Textmuster. Ein Textmuster hielte jede Erwähnung von „Artikel 99" im Fließtext
für einen Artikelanfang.

### 2. KI-Verordnung, artikelweise Ergänzung — 71 Einheiten

* **Adresse:** `https://artificialintelligenceact.eu/de/article/<Nummer>/`
* **Geholt:** 03.10.2026 über `scripts/holen_kivo.py`
* **Umfang:** 71 Einheiten, die im amtlichen Volltext nicht zugeordnet werden
  konnten — darunter 65 Einheiten zu Artikel 3, den
  Begriffsbestimmungen, sowie 6 Einheiten zu den Artikeln 108 und 110
* **Lizenzlage:** der Normtext ist der der Verordnung. Die redaktionelle
  Aufbereitung der Seite liegt bei ihrem Betreiber. Diese Quelle ist **nicht
  amtlich**.

Dass Artikel 3 über diesen Weg kam, ist bemerkenswert, weil die
Begriffsbestimmungen für die Einstufung wichtig sind. Wer eine Auskunft prüft,
die sich auf Artikel 3 stützt, gleicht sie am Amtsblatt ab.

### 3. Datenschutz-Grundverordnung — 1021 Einheiten

* **Rechtsakt:** Verordnung (EU) 2016/679, CELEX 32016R0679
* **Verwendete Adresse:** `https://dsgvo-gesetz.de/art-<Nummer>-dsgvo/` und
  `https://dsgvo-gesetz.de/erwaegungsgruende/nr-<Nummer>/`
* **Geholt:** 03.10.2026 über `scripts/holen_dsgvo.py`
* **Umfang:** 848 Artikeleinheiten und 173 Erwägungsgründe
* **Lizenzlage:** der Normtext ist der der Verordnung; die redaktionelle
  Aufbereitung liegt beim Betreiber der Seite. **Nicht amtlich.**

**Warum nicht der amtliche Volltext:** EUR-Lex gab die deutsche Fassung nicht
heraus. Das Protokoll `daten/roh/eurlex/_holen.log` vom 03.10.2026 zeigt sechs
Versuche, jeder mit 2035 Byte Antwort statt der erwarteten über 100 000 Byte;
danach `dsgvo-de.html: NICHT GEHOLT`. Der Korpusbau hat deshalb auf die
artikelweise Fassung zurückgegriffen und das als Warnung vermerkt:

```
amtlicher Volltext fehlt: dsgvo-de.html - es wird die artikelweise Fassung genutzt
```

**Folge für die Genauigkeit:** diese Fassung liegt je Artikel vor, nicht nach
Absätzen getrennt. Eine Fundstelle zur Datenschutz-Grundverordnung zeigt daher
auf die ganze Vorschrift; der genaue Absatz steht im Text der Pflicht, nicht in
der Kennung. Der Hinweis dazu steht in `daten/regeln/dsgvo_pruefpfad.yaml` im
Feld `hinweis_zur_granularitaet`.

Die englische Fassung des amtlichen Volltextes liegt vor
(`daten/roh/eurlex/dsgvo-en.html`, 809 035 Byte) und geht derzeit nicht in den
Bestand ein.

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

Drei Dateien, alle von Hand geschrieben, alle mit Stand 31.05.2026.

| Datei | Inhalt | Nachgemessen |
|---|---|---|
| `daten/regeln/kivo_risikoklassen.yaml` | Verbote, Anhang I, Anhang III, die Ausnahme nach Artikel 6 Absatz 3, Transparenz, Modelle mit allgemeinem Verwendungszweck, Rollenwechsel, Fristen, Sanktionen | 8 Verbotstatbestände, 5 Fristenstufen, 3 Sanktionsstufen; als Einstufungsregeln in die App ausgegeben: 28 |
| `daten/regeln/kivo_pflichten.yaml` | die Pflichten mit Klasse, Rolle, Fundstelle, Frist, Nachweis und Folge bei Verstoß | 57 Pflichten |
| `daten/regeln/dsgvo_pruefpfad.yaml` | der Prüfpfad des Datenschutzrechts in der Reihenfolge, in der er abzuarbeiten ist | 26 Abschnitte, davon 14 immer geltend und 12 bedingt |

Jede Pflicht und jeder Abschnitt nennt seine Rechtsgrundlagen als Kennungen.
Nachgemessen am 03.10.2026: alle genannten Rechtsgrundlagen sind im Korpus
vorhanden, keine einzige ohne Fundstelle. Der Befehl dafür steht in
[betriebsanleitung.md](betriebsanleitung.md), Abschnitt c.

## Was die App kennt

`android/app/src/main/assets/recht.db`, gebaut am 03.10.2026, 8 396 800 Byte:

| Tabelle | Zeilen |
|---|---|
| `einheit` | 1972 |
| `vektor` | 1972 |
| `pflicht` | 57 |
| `risikoregel` | 28 |
| `fall` | 44 |
| `pruefabschnitt` | 26 |
| `meta` | 12 |

**Die Datei ist älter als der Korpus.** Sie trägt die Prüfsumme des Korpus, aus
dem sie gebaut wurde — `ee77d5ad168f28d9…` — und der heutige Korpus hat die
Prüfsumme `77d4cb0ada9d3cd8…` bei 2721 Einheiten. Die App kennt also 749
Einheiten weniger als der Rechner. Regelwerk, Pflichten, Fälle und Prüfpfad
sind auf beiden Seiten gleich; es fehlt Rechtstext für die Belegstellen. Der
nächste Lauf von `scripts/export_android.py` bringt beides zusammen.

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
