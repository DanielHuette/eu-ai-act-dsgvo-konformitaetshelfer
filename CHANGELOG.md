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

Erste Fassung. Die Fassungsnummer steht in `pyproject.toml` und in
`android/app/build.gradle.kts` (`versionCode = 1`, `versionName = "1.0.0"`).

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
* Einbettungsmodell örtlich: bge-m3 auf dem Rechner, multilingual-e5-small auf
  dem Telefon. Kein Schlüssel nötig.
* Antwort auf Wunsch ausformuliert durch Claude, GPT oder ein Modell auf
  demselben Rechner über Ollama. Ohne Modell baut das Werkzeug die Auskunft
  selbst.
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

### Android-App

* 4730 Zeilen Kotlin, davon 3897 im Hauptteil, 65 Prüfungen.
* Rechtsbestand, Regelwerk und Einbettungsmodell auf dem Gerät; die
  Beschreibung verlässt das Telefon nicht.
* SQLite mit Volltextindex FTS5 aus mitgelieferter Bibliothek, nur lesend
  geöffnet.
* Genau eine Berechtigung (`INTERNET`), nur gebraucht, wenn ein eigener
  Schlüssel eingetragen ist. `ACCESS_NETWORK_STATE` und `READ_PHONE_STATE` sind
  im Manifest ausdrücklich entfernt; die Fassung der ONNX-Laufzeit ist dafür auf
  1.28.0 festgelegt.
* Keine Sicherung in eine Cloud, kein unverschlüsselter Netzverkehr,
  Schlüssel verschlüsselt im Schlüsselspeicher des Geräts.
* Gebaut von GitHub Actions. Das Paket ist nicht unterschrieben.
* App-Datenbank vom 03.10.2026: 1972 Einheiten, 1972 Vektoren mit 384 Zahlen,
  57 Pflichten, 28 Einstufungsregeln, 44 Fälle, 26 Prüfabschnitte. Gemessene
  Ähnlichkeit zwischen dem 8-Bit- und dem 32-Bit-Modell: 0,9907.
