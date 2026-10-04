# Änderungen

Alle nennenswerten Änderungen dieses Projekts. Der Aufbau folgt dem Gedanken
von „Keep a Changelog"; die Fassungsnummern folgen der semantischen
Versionierung (Hauptnummer bei unverträglichen Änderungen, Nebennummer bei
neuen Fähigkeiten, dritte Stelle bei Berichtigungen).

**Eine Besonderheit dieses Projekts:** Änderungen am Regelwerk und am
Rechtsbestand stehen vor den Programmänderungen. Für jemanden, der eine
Auskunft bekommt, ist ein geänderter Artikelverweis wichtiger als jede
Programmänderung. Jeder Eintrag zum Datenstand nennt das Datum, auf dem das
Regelwerk danach steht.

## 1.2.0 — 04.10.2026

Diese Fassung hört auf zu raten. Die Einstufung kam bisher aus der Auswertung
einer Beschreibung; jetzt kommt sie aus einer Fragefolge, die der Nutzer in
etwa sechs Schritten beantwortet. Gemessen 5,3 Schritte im Schnitt.

Der Grund ist nicht, dass das Raten zu schlecht war, sondern dass es Raten war.
Mit Stichwortlisten traf es 11 von 20 Beschreibungen, wie Unternehmen sie
wirklich einreichen; mit Bedeutungsvergleich nach einer Nacht Arbeit 20 von 20.
Ein Jurist fragt fünf bis acht Dinge ab und hat danach Gewissheit, nicht 98
Prozent — und geraten wurden Antworten auf Fragen, die sich stellen lassen:
wofür das System bestimmt ist, wer es einsetzt, ob es über Menschen
entscheidet. Das weiß der Nutzer, und niemand sonst.

### Die gemessenen Zahlen

* **206 von 217 amtlichen Beispielen** der Europäischen Kommission werden
  richtig eingestuft. Die Soll-Wertungen stammen von der Kommission, nicht von
  mir — das ist der Unterschied zu jeder Zahl der vorigen Fassungen, in denen
  ich Regeln und Prüffälle beide geschrieben hatte.
* **5,3 Schritte** je Fall im Schnitt.
* **400 von 400 Prüfläufen:** Webseite und Programm rechnen gleich.
* Sieben der elf Abweichungen messen den Durchlauf nicht: ihre Beschreibungen
  nennen gar keinen Anwendungsbereich, und die Ausnahme des Artikels 6 Absatz 3
  kommt ohne Bereich zu Recht nie an die Reihe. Herausgerechnet sind es 206 von
  210. Jede Abweichung einzeln steht in `daten/pruefung/MESSUNG.md`.
* Kein Jurist hat den Durchlauf gegengelesen.

### Datenstand

* Neu als Quelle: der **Entwurf der Leitlinien der Europäischen Kommission vom
  19. Mai 2026** zur Einstufung von Hochrisiko-KI-Systemen nach Artikel 6 —
  148 Seiten zu Anhang III, 13 Seiten zu Anhang I, 6 Seiten allgemeine
  Grundsätze. Liegt unter `daten/roh/leitlinien/`, aufgeteilt in 60 Abschnitte
  mit 490 318 Zeichen.
* **Jede Frage, jeder Ausschluss und jedes Beispiel trägt die Absatznummer**
  der Stelle, auf der es beruht. Ohne Absatz keine Frage: eine Frage ohne
  Fundstelle wäre eine ausgedachte Frage.
* Neu: `daten/regeln/fragefolge/*.yaml` — 379 Fragen zu 31 Stellen des
  Gesetzes, 214 ausdrückliche Ausschlüsse, 187 amtliche Beispiele. Dazu 3
  Vorfragen, 4 Hinweise, 8 Bereichsfragen und 15 Produktgattungen des Anhangs
  I.
* Neu: `daten/regeln/fragefolge-aufbau.yaml` — die Reihenfolge, getrennt vom
  Inhalt. Dort steht, welche Frage den Weg lenkt, welche nur unterrichtet und
  welcher Bereich alles zusammen verlangt.
* Neu: `daten/pruefung/amtliche-beispiele.json` — die 217 Beispiele mit Lage,
  Soll-Wertung, Fundstelle, Absatznummer und der Begründung der Kommission im
  Wortlaut.
* Neu: `daten/pruefung/zahlen.json` und `daten/pruefung/MESSUNG.md` — die
  gemessenen Zahlen an einer Stelle, dazu das Verfahren und jede Abweichung.
* Rechtsbestand unverändert: 2811 Rechtseinheiten, 1386 aus der
  KI-Verordnung, 1024 aus der Datenschutz-Grundverordnung, 357 aus dem
  Bundesdatenschutzgesetz, 44 Anwendungsfälle.

### Einstufung

* **Drei Antworten je Frage statt zwei:** Ja, Nein und *Trifft nicht zu*. Die
  dritte lässt die Frage stehen, ohne zu entscheiden; ein Ausschluss greift nur
  auf eine ausdrückliche Antwort. Gemessen fiel ein Werkzeug zur Sichtung von
  Lebensläufen durch ein erzwungenes Nein aus der Einstufung: es schaltet keine
  Stellenanzeigen, und auf die Frage, ob eine Anzeige eine konkrete offene
  Stelle anzeigt, gibt es dort weder Ja noch Nein.
* **Neuer Befund „bedingt hochriskant".** Anhang III Nummer 2 verlangt nach
  Absatz (190) der Leitlinien, dass der Betreiber förmlich als kritische
  Einrichtung benannt ist — Absatz (191) stellt fest, dass diese Benennung dem
  Anbieter nicht offengelegt werden muss. Ein Nein darauf kostete gemessen zehn
  amtliche Beispiele. Bleibt die Frage offen und trägt der Rest, sagt der
  Befund, woran es hängt.
* **Nummer 2 verlangt alles zusammen.** Versorgungsbereich, benannte kritische
  Einrichtung und eigene Schutzaufgabe. Als Aufzählung gelesen konnte Nummer 2
  überhaupt keinen Treffer ergeben, weil keine ihrer Fragen allein zum Treffer
  führt.
* **Anhang I: oder statt und.** Artikel 6 Absatz 1 Buchstabe a verlangt
  Sicherheitsbauteil **oder** selbst ein geregeltes Produkt. Vorher verlangte
  der Durchlauf beides und ließ jedes System durchfallen, das selbst ein
  geregeltes Produkt ist.
* **Acht Bereichsfragen zum Sortieren.** Ohne sie standen 31 Rechtsfragen auf
  einem Blatt. Sie entscheiden nichts und tragen darum auch keine
  Absatznummer. Die Reihenfolge folgt der Häufigkeit in der Wirtschaft: wer
  zuerst nach Strafverfolgung gefragt wird, hält das Werkzeug für nicht
  gemacht.
* **Vier Hinweise werden gezeigt, nicht gefragt** — dass eine menschliche
  Nachprüfung die Einstufung nicht aufhebt, dass ein KI-System in einem
  zusammengesetzten Produkt stecken kann, was „bestimmungsgemäße Verwendung"
  heißt und was „soweit zulässig" heißt. Als Frage behandelt könnte sich der
  Nutzer mit einem Ja aus der Prüfung herausantworten.
* **Die Ausnahme nach Artikel 6 Absatz 3** wird erst gefragt, wenn eine Stelle
  trägt — so steht es im Gesetz. Vier Bedingungen, von denen eine genügt, dazu
  die Gegenausnahme Profiling.
* Der Freitext trägt jetzt die Volltextsuche und die ausformulierte Auskunft.
  Er entscheidet keine Einstufung mehr.

### Zwei Wege, ein Ergebnis

* Neu: `web/index.html`, `web/durchlauf.js`, `web/fragefolge.json` — die
  Einstufung läuft im Browser, ohne Installation, ohne Anmeldung, ohne Server
  und ohne Modell. Die Angaben werden nicht übertragen.
* Neu: `scripts/fragefolge_ausgeben.py` — schreibt die YAML-Dateien zu einer
  Datei zusammen, die Programm und Webseite beide laden. Eine Datenquelle, zwei
  Leser.
* Neu: `scripts/pruefe_zwei_wege.py` — würfelt Antwortmuster mit festem
  Startwert und fährt beide Fassungen damit: dieselbe Frage in derselben
  Reihenfolge, dieselbe Gruppe auf demselben Blatt, derselbe Befund. Beim Bau
  dieses Durchlaufs sind Fragefolge und Auswertung auseinandergelaufen und
  haben **30 von 217 amtlichen Beispielen** gekostet; eine solche Abweichung
  sieht man nicht, weil beide Seiten antworten, nur verschieden.
* Neu: `scripts/fragen_beantworten.py` — gibt die nächsten offenen Fragen aus
  und nimmt Antworten entgegen, damit sich die amtlichen Beispiele gegen den
  Durchlauf messen lassen.

### Fertige Pakete

* Neu: `verpacken/helfer.spec` — ein Bauplan für Windows, Mac und Linux. Im
  Paket liegen Rechtsbestand, Regelwerk, Fragefolge, Anwendungsfälle und
  Bedienoberfläche. Das Sprachmodell für die Volltextsuche liegt nicht darin:
  es würde das Paket vervierzigfachen, und die Einstufung braucht es nicht.
* Neu: `verpacken/start_helfer.py` — sucht einen freien Netzwerkanschluss
  zwischen 8713 und 8799 und öffnet den Browser. Fest auf eine Nummer zu setzen
  geht schief, sobald etwas anderes sie belegt, und der Nutzer sähe nur ein
  Fenster, das sich nicht öffnet.
* Neu: `verpacken/start_pruefen.py` — startet das gebaute Paket und sieht nach,
  ob es antwortet und die Fragefolge ausliefert. Ein Paket, das sich bauen
  lässt, muss sich noch lange nicht starten lassen.
* Neu: `.github/workflows/pakete.yml` — baut auf drei Maschinen, weil ein Paket
  die Laufzeitumgebung des Systems enthält, auf dem es gebaut wurde. Der Lauf
  erzeugt die Fragefolge neu, vergleicht beide Wege mit 400 Antwortmustern und
  baut erst danach. Dazu `verpacken/windows.iss` für das
  Installationsprogramm und `verpacken/linux-starter.desktop`.
* Der Webdienst liefert die Fragefolge unter `/einstufung` aus und die
  Volltextsuche unter `/suche`; `/` führt auf die Fragefolge.

## 1.1.0 — 04.10.2026

Diese Fassung dreht sich um eine einzige Zahl: wie oft die Einstufung richtig
ist, wenn die Frage nicht aus der eigenen Sammlung kommt. Sie lag bei 55 von
100 und liegt jetzt bei 100 von 100. Die Prüfung verlangt mindestens 95: eine
Grenze, die beim ersten neuen Zwecksatz bricht, wird hochgesetzt statt
behoben.

### Datenstand

* Rechtsbestand neu gebaut am **04.10.2026**: **2811** Rechtseinheiten,
  2 089 375 Zeichen, **keine Warnung** aus dem Korpusbau.
  * KI-Verordnung aus dem Amtsblatt, CELEX 32024R1689: 1386 Einheiten —
    113 Artikel mit 929 Absätzen und Nummern, 13 Anhänge mit 151 Nummern und
    Buchstaben, 180 Erwägungsgründe.
  * Datenschutz-Grundverordnung aus dem Amtsblatt, CELEX 32016R0679: 1024
    Einheiten — 99 Artikel mit 752 Absätzen und Nummern, 173 Erwägungsgründe.
    Die Rückfallquelle dsgvo-gesetz.de wird nicht mehr gebraucht.
  * Bundesdatenschutzgesetz: 357 Einheiten. Anwendungsfälle: 44.
* **Anhang III bis zum Buchstaben zerlegt.** Vorher gab es acht
  Bereichsnummern, jetzt zusätzlich die 23 Buchstabenpunkte darunter. Die
  Einstufung hängt am Buchstaben, nicht am Bereich: Nummer 4 Buchstabe a trifft
  die Einstellung, Buchstabe b die Arbeitsbedingungen.
* **Anhang I war vollständig verloren** und ist jetzt da: 20 Rechtsakte, auf
  die Artikel 6 Absatz 1 für das hohe Risiko über das Produktsicherheitsrecht
  verweist. Ursache: seine Tabellen tragen vor der Zählung eine leere Zelle für
  die Einrückung, und der Zerleger las blind die erste Zelle.
* **Anhang XI wurde um zwei Drittel gekürzt.** Sein Abschnittskopf heißt nur
  „Abschnitt 1", und ihm folgt eine zweite Überschrift, die den Abschnitt
  wieder löschte — Abschnitt 2 trug danach die Kennungen von Abschnitt 1.
* Neu: `daten/regeln/kivo_zweckkatalog.yaml` — 55 Einträge, 107 Zwecke, 21
  Gegenzwecke.
* Neu: `daten/pruefung/unternehmensfragen.yaml` — 100 Beschreibungen, wie
  Unternehmen sie wirklich einreichen, mit der Fundstelle, auf die sich jedes
  Soll stützt.

### Einstufung

* **Zweiter Eingang in dasselbe Regelwerk.** Jede Stufe ist nun über
  kennzeichnende Wörter *und* über den Zweck erreichbar. Das Feld `regel` im
  Zweckkatalog zeigt auf die bestehenden Kennungen in
  `kivo_risikoklassen.yaml`; Rollenprüfung, Merkmalsfilter, Ausnahmen und
  Pflichtenableitung gelten unverändert. Die Einstufung kommt weiter aus dem
  Regelwerk — das Modell findet nur die Stelle.
* **Artikel 50 beachtet jetzt die Rolle.** Absatz 1 und 2 binden den Anbieter,
  Absatz 3 und 4 den Betreiber. Vorher bekam ein Unternehmen, das ChatGPT
  benutzt, die Kennzeichnungspflicht des Modellanbieters vorgehalten.
* **Verbote brauchen mehr Beleg als die übrigen Klassen.** Der Zweckweg
  verlangt für „verboten" 0,85 statt 0,50. Gemessen traf eine Lernplattform,
  die Aufsätze benotet, den Satz zur Emotionserkennung bei Schülern mit 0,6297
  — ein Verbot wäre dort falsch gewesen und hätte ein zulässiges Geschäft
  untersagt.
* **Verlangter Wortlaut.** Artikel 5 Absatz 1 Buchstabe d verbietet die
  Vorhersage von Straftaten nur, wenn sie *ausschließlich* auf Profiling
  beruht. Vorher löste das Wort „Rückfall" allein das Verbot aus, und eine
  zulässige Polizeiprognose nach Anhang III Nummer 6 Buchstabe d wurde
  untersagt. Das Merkmal wird nun auf beiden Wegen verlangt — im Regelwerk als
  `verlangt_wortlaut`, im Katalog als `verlangt`.
* **Modelle mit allgemeinem Verwendungszweck: Ausnahme des Artikels 3 Nummer
  63.** „Wir bringen es nicht in Verkehr" enthält alle Wörter der Wortgruppe
  „Modell in Verkehr" und löste die Pflichten für Modellanbieter aus — die
  Verneinung ging verloren. Jetzt entlastet die ausdrückliche Aussage.
* `kuendigung` und `befoerderung` lösen nicht mehr allein den Bereich
  Beschäftigung aus. Eine Suche nach Kündigungsfristen in Lieferverträgen
  wurde so zum Personalvorgang.

### Prüfungen

* Neu: `tests/test_zwecke.py` — 18 Prüfungen auf die Form des Zweckkatalogs
  (jede Fundstelle zeigt auf echten amtlichen Text, jede Regel existiert, jeder
  Zwecksatz steht in der gemessenen Satzform), auf die Satzzerlegung samt
  Gegenprobe, dass ein Mensch als Satzsubjekt nicht zum System wird, und auf
  die Genauigkeit über alle 100 Unternehmensfragen.
* Der Zerleger bricht ab, wenn eine Kennung zweimal mit *verschiedenem* Text
  vorkommt, und nennt die betroffenen Kennungen. Eine Zahl allein sagte nicht,
  wo zu suchen ist.

### Suchbestand

* Der abgelegte Bestand vergleicht beim Laden die **Kennungen** des Korpus und
  nicht nur ihre Anzahl. Ein Bestand aus einem anderen Korpus kann zufällig
  gleich viele Einheiten haben — oder, häufiger, derselbe Korpus ist umsortiert
  oder eine Einheit ersetzt. Dann zeigt jeder Vektor auf die falsche
  Fundstelle, und die Antwort sieht aus wie immer. Eine eigene Prüfung baut
  genau diesen Fall nach.
* Der Bestand liegt neu gebaut im Verzeichnis: 2811 Vektoren mit bge-m3,
  Stand 04.10.2026.

### Berichtigungen

* `_kennung()` rief sich selbst auf und brach mit Endlosrekursion ab. Der
  Zerleger war damit seit dem Aufräumen mit ruff unbrauchbar, während alle
  Prüfungen grün blieben — sie prüfen den fertigen Korpus, nicht den Zerleger.
* Die Buchstabenpunkte eines Absatzes werden über die Tabellenstruktur geholt,
  nicht über den Fließtext. Dort sah „i)" aus einer verschachtelten Aufzählung
  wie der Buchstabe i aus, und die Punkte a) bis b) aus Absatz 1 kollidierten
  mit a) bis d) aus Absatz 3 desselben Artikels.
* Die Begriffsbestimmungen fehlten: Artikel 3 der KI-Verordnung mit 68 Nummern
  und Artikel 4 der Datenschutz-Grundverordnung mit 26.
* `src/helfer/einstufung/bereiche.py` entfernt. Der erste Versuch eines
  Bedeutungswegs ging über die ganzen Bereichstexte und traf 7 von 11 — die
  acht Anhang-III-Texte sind juristisch zu ähnlich formuliert. Der Zweckkatalog
  ersetzt ihn.

## 1.0.0 — 03.10.2026

Erste Fassung. Die Fassungsnummer steht in `pyproject.toml`.

### Datenstand

* Regelwerk auf dem Stand **31.05.2026**: 28 Einstufungsregeln nach der
  KI-Verordnung, 57 Pflichten, 26 Abschnitte des Prüfpfads zum
  Datenschutzrecht, 5 Fristenstufen nach Artikel 113, 3 Sanktionsstufen nach
  Artikel 99.
* Rechtsbestand geholt und gebaut am **03.10.2026**: 2721 Rechtseinheiten,
  1 966 046 Zeichen.
  * KI-Verordnung aus dem Amtsblatt über EUR-Lex, CELEX 32024R1689: 1228
    Einheiten.
  * KI-Verordnung artikelweise ergänzt über artificialintelligenceact.eu: 71
    Einheiten, darunter Artikel 3.
  * Datenschutz-Grundverordnung über dsgvo-gesetz.de: 1021 Einheiten. Der
    amtliche Volltext war nicht erreichbar — sechs Versuche, jeder mit 2035
    Byte Antwort.
  * Bundesdatenschutzgesetz von gesetze-im-internet.de, Teile 1 und 2: 357
    Einheiten.
  * 44 selbst geschriebene Anwendungsfälle, als „Leitlinie" geführt und damit
    ausdrücklich nicht verbindlich.
* Zwei Warnungen aus dem Korpusbau, beide noch offen: 27 doppelte Kennungen in
  der KI-Verordnung übergangen; amtlicher Volltext der
  Datenschutz-Grundverordnung fehlt.

### Werkzeug

* Einstufung nach der KI-Verordnung aus einem Entscheidungsbaum in
  YAML-Dateien, in der Reihenfolge der Verordnung: Verbote nach Artikel 5,
  hohes Risiko nach Artikel 6 Absatz 1 und Absatz 2 mit Anhang III, die
  Ausnahme nach Artikel 6 Absatz 3, Transparenz nach Artikel 50, Modelle mit
  allgemeinem Verwendungszweck ab Artikel 51, KI-Kompetenz nach Artikel 4.
  Jeder Treffer mit Regelkennung, Fundstelle und einer Sicherheit (`sicher`,
  `wahrscheinlich`, `zu_pruefen`).
* Pflichtenliste getrennt nach Anbieter und Betreiber. Wird keine Rolle
  erkannt, werden beide Sichten dargestellt.
* Prüfpfad zum Datenschutzrecht: 14 Abschnitte gelten immer, 12 nach
  Bedingung.
* Offene Fragen aus fehlenden Angaben, statt zu raten.
* Suche über vier Wege — Bedeutung, Wortlaut nach BM25, Wortgewichte des
  Modells, Fundstellenweg —, zusammengeführt über die Rangplätze mit
  `1 / (60 + Rang)` und neu bewertet durch einen Kreuzbewerter über die besten
  30.
* Einbettungsmodell örtlich: bge-m3, rund 2,3 Gigabyte. Kein Schlüssel nötig.
* Antwort auf Wunsch ausformuliert durch Claude oder GPT. Ohne Modell baut das
  Werkzeug die Auskunft selbst.
* Kommandozeile mit fünf Befehlen: `pruefen` (Einstufung ohne Sprachmodell),
  `fragen` (volle Auskunft mit Belegen), `suchen` (nur Fundstellen), `dienst`
  (Webdienst starten), `stand` (zeigt, womit das Werkzeug arbeitet und was
  fehlt). Mit `--json` für die Weiterverarbeitung, Farbe abschaltbar über
  `--ohne-farbe` oder `NO_COLOR`.
* Webdienst mit Oberfläche und fünf Schnittstellen — `/api/einstufung`,
  `/api/suche`, `/api/frage`, `/api/fragebogen`, `/api/fristen` — dazu
  `/gesundheit`. Lädt alles beim Start, hört standardmäßig nur auf 127.0.0.1,
  gibt keine Rückverfolgung nach außen. Keine Anmeldung.
* Container in drei Baustufen mit `Dockerfile` und `docker-compose.yml`, dazu
  `scripts/start.sh` und `scripts/start.ps1` für den Start mit einem Befehl und
  `.env.example` als Vorlage der Einstellungen. Der Dienst läuft unter dem
  Nutzer `helfer` (Kennung 10001) ohne Verwalterrechte, mit nur lesendem
  Dateisystem und nur an 127.0.0.1 gebunden. Das Einbettungsmodell liegt im
  Abbild, damit die mitgelieferte Suchdatenbank ohne Netz brauchbar ist; das
  Abbild wird dadurch rund 5 Gigabyte groß, und `MIT_SUCHMODELL=0` baut es
  ohne.
* Eingabeschutz ohne Fremdpaket: Obergrenzen (Frage 2000, Beschreibung 20 000
  Zeichen), Entfernen von Steuer- und Richtungszeichen, Zähler je Adresse,
  Säubern der Protokollzeilen von Schlüsseln.
* Schutz gegen untergeschobene Anweisungen: Marken je Anfrage gewürfelt,
  Nutzerdaten ausdrücklich als Daten erklärt, Einstufung nach den Nutzerdaten
  vorgelegt, Nachprüfung auf Fundstellen, die in keinem Beleg standen.
