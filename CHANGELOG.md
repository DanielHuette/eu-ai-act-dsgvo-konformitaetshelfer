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

## Unveröffentlicht

### Dokumentation

* README, Lizenz- und Hinweisdateien, die sechs Blätter unter `docs/`, die
  Mitarbeitsregeln, der Verhaltenskodex, die Sicherheitsmeldung, diese
  Änderungsliste, die Zitierangabe, die Vorlagen für Fehlerberichte und
  Änderungsvorschläge sowie der Prüflauf für den Python-Teil angelegt.
* Alle Mengenangaben darin sind am 03.10.2026 am Verzeichnis nachgemessen.

### Festgehalten, nicht behoben

Diese Punkte sind beim Schreiben der Dokumentation aufgefallen und
nachgemessen. Sie sind in [docs/architektur.md](docs/architektur.md) unter
„Grenzen des Systems" und „Was noch nicht da ist" beschrieben:

* Die App-Datenbank `android/app/src/main/assets/recht.db` ist älter als der
  Rechtsbestand: 1972 Einheiten gegen 2721, und die Prüfsumme des Korpus in
  `daten/aufbereitet/android_export_befund.json` (`ee77d5ad…`) weicht von der
  heutigen (`77d4cb0a…`) ab. Behoben wird das durch einen Lauf von
  `scripts/export_android.py`.
* Der Suchbestand für den Rechner liegt nicht im Verzeichnis. Der Lauf vom
  03.10.2026 ist nach dem Laden des Modells abgebrochen; das Protokoll
  `daten/aufbereitet/_bestand_lauf.log` endet bei „Bestand bauen: 2721
  Einheiten".
* Das Container-Abbild ist in diesem Verzeichnis nie gebaut worden. Die
  Angaben dazu in README und Betriebsanleitung stammen aus `Dockerfile`,
  `docker-compose.yml` und den Startskripten, nicht aus einem Lauf.
* `ruff check .` meldet 277 Punkte, davon 246 die Regel UP031 — die durchgehend
  verwendete Schreibweise `"%s" % wert`. `mypy src` meldet 28 Punkte in 10
  Dateien. Beides ist im Prüflauf als Hinweis geführt und bricht ihn nicht ab.
* Das Verzeichnis `tests/` ist leer. Für den Python-Teil gibt es keine
  Prüfungen; der Prüflauf behandelt „keine Prüfungen gefunden" deshalb nicht
  als Fehler.

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
