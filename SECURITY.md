# Sicherheitslücken melden

## Nicht öffentlich melden

Eine Sicherheitslücke gehört **nicht** in einen öffentlichen Fehlerbericht.

Melden Sie sie an **dhuette@gmx.net** mit „Sicherheit" im Betreff. Falls Sie
verschlüsseln wollen, fragen Sie in einer ersten Nachricht ohne Einzelheiten
nach einem Schlüssel.

## Was in die Meldung gehört

* Was die Lücke erlaubt.
* Wie man sie nachstellt, Schritt für Schritt.
* Welche Fassung betroffen ist: Marke oder Commit, und ob es die Webseite,
  das fertige Paket oder den Quelltext betrifft.
* Ihre Einschätzung, wen es trifft.

## Was Sie erwarten können

Dieses Projekt wird von einer einzelnen Person nebenher betrieben. Daraus
folgt, was versprochen wird und was nicht:

* **Eingangsbestätigung:** innerhalb von 7 Tagen.
* **Erste Einschätzung:** innerhalb von 30 Tagen.
* **Behebung:** kein Termin. Es gibt kein Sicherheitsteam und keine
  Bereitschaft. Was behoben wird, wird in [CHANGELOG.md](CHANGELOG.md)
  eingetragen.
* **Nennung:** wer es möchte, wird in der Änderungsliste genannt.
* **Kein Geld.** Es gibt kein Belohnungsprogramm.

Antwortet niemand innerhalb von 30 Tagen, dürfen Sie die Lücke veröffentlichen.
Eine Lücke, die unbemerkt bleibt, ist schlimmer als eine veröffentlichte.

## Welche Fassungen betreut werden

Nur die jeweils neueste. Es gibt keine Pflege älterer Fassungen.

## Was in diesem Projekt eine Sicherheitslücke ist

| Ja | Nein |
|---|---|
| Ein Weg, über den die Beschreibung des Nutzers unbemerkt das Gerät verlässt | Die Beschreibung geht an Claude oder GPT, wenn ein Schlüssel eingetragen ist. Das ist beschrieben und gewollt. |
| Ein Weg, über den ein eingetragener Schlüssel ausgelesen werden kann | Dass der Schlüssel im Schlüsselspeicher des Geräts liegt, ist die Absicht |
| Programmausführung über eine untergeschobene Datei oder Eingabe | Der Suchbestand liegt als gepacktes JSON (`.bestand.json.gz`); eine veränderte Datei kann falsche Treffer verursachen, aber keinen Code starten. Eine Datei im alten `pickle`-Format wird abgewiesen, nicht gelesen |
| Eine Abhängigkeit, die Berechtigungen oder Telemetrie einschleppt | Eine Abhängigkeit mit bekannter Schwachstelle ohne Weg zum Missbrauch hier: bitte als gewöhnlichen Fehlerbericht |
| Ein Weg, der die deterministische Einstufung durch das Sprachmodell ersetzbar macht | Dass eine formulierte Antwort schlecht formuliert ist |

## Was keine Sicherheitslücke ist, aber genauso wichtig

**Ein falscher Artikelverweis.** Der geht in eine Auskunft ein, nach der jemand
eine Entscheidung trifft. Er gehört in die Vorlage **Rechtsfehler** und wird
vor allen anderen Meldungen bearbeitet. Siehe
[CONTRIBUTING.md](CONTRIBUTING.md).

## Was geprüft ist und was nicht

Damit niemand mehr annimmt, als geprüft wurde:

* Es gibt **keine Prüfreihe für den Python-Teil**; das Verzeichnis `tests/` ist
  leer.
* Es wurde **kein Angriffsversuch** auf den Schutz gegen untergeschobene
  Anweisungen durchgeführt. Die Vorkehrungen sind begründet, nicht erprobt.
* `bandit` und `pip-audit` laufen in der Prüfung, `dependabot` meldet neue
  Fassungen wöchentlich. Das ist Werkzeugprüfung, keine Durchsicht durch
  Menschen.
* Die **fertigen Pakete sind nicht unterschrieben**. Woher ein Paket stammt,
  lässt sich nur über den öffentlichen Lauf in GitHub Actions nachvollziehen.
  Eine Unterschrift für Windows und Mac setzt ein kostenpflichtiges Zertifikat
  voraus. Auf dem Mac verlangt das System darum beim ersten Start den Weg über
  das Kontextmenü.

Einzelheiten dazu, wo Daten liegen und was ein Gerät verlässt:
[docs/sicherheit.md](docs/sicherheit.md).
