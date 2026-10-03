# Haftung: was dieses Werkzeug nicht ist

Dieses Blatt steht ohne Ausreden da. Wer es gelesen hat, weiß, was er in der
Hand hält.

## Keine Rechtsberatung

Dieses Werkzeug leistet **keine Rechtsberatung** im Sinne des
Rechtsdienstleistungsgesetzes. Es prüft keinen konkreten Einzelfall in fremder
Angelegenheit, sondern ordnet eine eingegebene Beschreibung anhand eines
Regelwerks ein und nennt die Stellen im Gesetz dazu.

Eine Rechtsberatung gibt es von Menschen mit Berufszulassung: Rechtsanwältin,
Rechtsanwalt, bei bestimmten Fragen die zuständige Aufsichtsbehörde. Wer eine
Entscheidung mit Geld- oder Rechtsfolgen trifft — ein Produkt umbauen oder
nicht umbauen, ein System in Betrieb nehmen oder nicht, eine Meldung abgeben
oder nicht — holt sich diese Beratung.

## Kein Ersatz für die Prüfung im Einzelfall

Die Einstufung entsteht aus einer Beschreibung in eigenen Worten und einem
Regelwerk aus Stichwörtern und Bedingungen. Sie kann nicht leisten, was eine
Prüfung im Einzelfall leistet:

* Sie kennt den Vertrag mit dem Anbieter nicht.
* Sie kennt die Betriebsanleitung des Systems nicht.
* Sie kennt die tatsächlichen Datenflüsse im Unternehmen nicht.
* Sie kennt die Absprachen mit dem Betriebsrat nicht.
* Sie kennt die Praxis der zuständigen Aufsichtsbehörde nicht.
* Sie kennt die Rechtsprechung nicht — keine einzige Entscheidung ist erfasst.

Genau an diesen Punkten entscheidet sich aber, ob eine Pflicht greift und wie
sie zu erfüllen ist.

## Keine Gewährleistung

Das Werkzeug steht unter der Apache License 2.0. Deren Abschnitte 7 und 8
gelten ohne Einschränkung: die Software wird „wie besehen" bereitgestellt, ohne
Gewährleistung jeder Art, und es wird für Schäden nicht gehaftet. Das ist keine
Formel am Rand, sondern die Lage.

Insbesondere wird nicht gewährleistet:

* dass die Einstufung richtig ist,
* dass die Pflichtenliste vollständig ist,
* dass die Pflichtenliste keine Pflichten enthält, die nicht gelten,
* dass die Artikelverweise stimmen,
* dass die Fristen aktuell sind,
* dass der mitgelieferte Gesetzestext mit der amtlichen Fassung übereinstimmt.

## Was konkret falsch sein kann

Das ist nicht abstrakt. Es ist nachgemessen und im Einzelnen aufgeführt in
[architektur.md](architektur.md), Abschnitt „Grenzen des Systems". Das
Wichtigste hier:

**Die Pflichtenliste ist eher zu lang als zu kurz.** Sie enthält alle Pflichten
der erkannten Risikoklasse und Rolle — auch solche, die auf das einzelne
Vorhaben nicht passen. Nachgemessen an einem Lauf vom 03.10.2026: eine
Beschreibung über die Vorsortierung von Bewerbungen erhielt 16 Pflichten,
darunter eine zur nachträglichen biometrischen Fernidentifizierung, die mit
Bewerbungen nichts zu tun hat. Jeder Punkt der Liste ist selbst zu prüfen.

**Die Einstufung kann zu niedrig ausfallen.** Der Prüfer erkennt Merkmale an
Stichwörtern. Wer sein Vorhaben mit anderen Worten beschreibt, als die Listen
vorsehen, wird möglicherweise nicht erkannt. Eine Beschreibung, die in keine
Regel fällt, landet bei „keine besonderen Pflichten außer KI-Kompetenz nach
Artikel 4" — und diese Einstufung ist ausdrücklich mit der Sicherheit
`wahrscheinlich` versehen, nicht mit `sicher`. Lesen Sie die Sicherheiten und
die offenen Fragen.

**Die Verweise auf die Datenschutz-Grundverordnung sind nicht absatzgenau.**
Der amtliche Volltext war bei der Beschaffung nicht erreichbar; verwendet wurde
eine Fassung, die je Artikel vorliegt. Eine Fundstelle zeigt daher auf die ganze
Vorschrift.

**Ein Teil des Gesetzestextes ist nicht amtlich.** 1021 Einheiten der
Datenschutz-Grundverordnung und 71 Einheiten der KI-Verordnung — darunter
Artikel 3 mit den Begriffsbestimmungen — stammen nicht aus dem Amtsblatt,
sondern von aufbereiteten Internetseiten. Einzelheiten:
[datenquellen.md](datenquellen.md).

**Die Fristen können sich geändert haben.** Der Vorbehalt steht im Regelwerk
und in jeder Auskunft: die Fristen stehen so im Amtsblatt vom 12. Juli 2024; zum
Datenstand des Regelsatzes wurden Änderungen einzelner Fristen politisch
erörtert.

**Die Anwendungsfälle sind nicht geprüft.** Die 44 Fallbeispiele sind selbst
geschrieben und von keiner Behörde und keiner Kanzlei geprüft. Sie sind
Anschauung, keine Rechtsquelle, und das Werkzeug führt sie ausdrücklich als
„Leitlinie", nicht als Gesetz.

**Erwägungsgründe sind keine Pflichten.** Ein Erwägungsgrund begründet eine
Verordnung, er regelt nicht. Er kann als Belegstelle erscheinen. Wer ihn als
Pflicht liest, liest falsch.

**Eine formulierte Antwort kann einen Artikel sinnverkehrt wiedergeben.** Die
Nachprüfung erkennt eine erfundene Nummer, aber keine falsche inhaltliche
Zusammenfassung einer vorhandenen Vorschrift. Wer sich auf eine Pflicht
verlässt, liest die Belegstelle im Wortlaut nach — sie steht dabei.

**Der Datenstand ist Mai 2026.** Das Regelwerk trägt den Stand 31.05.2026.
Rechtsprechung, Leitlinien, Angemessenheitsbeschlüsse und delegierte
Rechtsakte nach diesem Datum sind nicht berücksichtigt. Je weiter dieses Datum
zurückliegt, desto weniger belastbar ist die Auskunft.

## Was das Werkzeug kann

Damit das Bild nicht schief wird. Es kann:

* einen ersten Überblick geben, in welche Richtung ein Vorhaben läuft,
* die Stellen im Gesetz nennen, an denen man selbst weiterliest,
* die Fragen benennen, die vor einem Gespräch mit einer Kanzlei zu klären sind,
* Anbieter- und Betreibersicht auseinanderhalten,
* zeigen, dass KI-Verordnung und Datenschutzrecht nebeneinander gelten und
  nicht eines statt des anderen,
* das alles ohne Konto, ohne Netz und ohne dass die Beschreibung das Gerät
  verlässt.

Als Vorarbeit ist es brauchbar. Als Entscheidungsgrundlage nicht.

## Wenn Sie einen Fehler finden

Melden Sie ihn. Ein falscher Artikelverweis trifft jeden, der das Werkzeug
benutzt. Dafür gibt es einen eigenen Weg mit eigener Vorlage; die Einzelheiten
stehen in [CONTRIBUTING.md](../CONTRIBUTING.md) unter „Rechtsfehler".
