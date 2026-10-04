## Was diese Änderung tut

<!-- Ein bis drei Sätze. Was ändert sich für jemanden, der das Werkzeug
     benutzt? -->

Erledigt #

## Art der Änderung

- [ ] Berichtigung eines Rechtsfehlers (Verweis, Frist, Einstufung, Pflichttext)
- [ ] Änderung am Regelwerk aus einer Rechtsänderung
- [ ] Neuer Rechtstextstand (Korpus neu gebaut)
- [ ] Behebung eines Programmfehlers
- [ ] Neue Fähigkeit
- [ ] Dokumentation
- [ ] Bauablauf oder Prüfung

## Wie man es nachprüft

<!-- Die Befehle oder Schritte, mit denen jemand anders das Ergebnis sieht.
     Bei einer Änderung an der Einstufung: die Beschreibung, die vorher ein
     anderes Ergebnis gab. -->

```
```

## Bei einer Änderung am Regelwerk

- [ ] Das Feld `stand` in der geänderten Datei ist mitgeändert
- [ ] Vorhandene Kennungen (`kennung`) sind unverändert; inhaltlich Neues hat
      eine neue Kennung
- [ ] Jede genannte Rechtsgrundlage ist im Korpus vorhanden (Prüfbefehl in
      docs/betriebsanleitung.md, Abschnitt c)
- [ ] Die Fundstelle ist am amtlichen Text nachgelesen, und die Quelle steht im
      Fehlerbericht oder hier
      Telefon dasselbe Regelwerk haben
- [ ] Die Zahlen sind nachgemessen, nicht erinnert

## Bei einem neuen Rechtstextstand

- [ ] `daten/aufbereitet/korpus_befund.json` liegt bei oder ist im
      Änderungssatz, und die Warnungen darin sind benannt
- [ ] Suchbestand und App-Datenbank sind neu gebaut; die Prüfsumme in
- [ ] Die Stückzahlen in README und docs/datenquellen.md sind angepasst

## Immer

- [ ] `ruff check --ignore UP031,UP042,RUF100 .` meldet nicht mehr Punkte als
      vorher (derzeit 16)
- [ ] `mypy src` meldet nicht mehr Punkte als vorher (derzeit 28)
- [ ] `bandit -c pyproject.toml -r src scripts --skip B301,B403,B310,B608,B615`
      läuft durch
- [ ] `pytest -m "not langsam and not netz"` läuft durch
- [ ] Deutsch in Bezeichnern, Kommentaren und Meldungen; Fachbegriffe beim
      ersten Vorkommen erklärt, Abkürzungen ausgeschrieben
- [ ] Der Dateikopf jeder geänderten Datei sagt noch das Warum
- [ ] Die Einstufung entsteht weiterhin ohne Sprachmodell
- [ ] Was nicht geprüft ist, steht als nicht geprüft da
- [ ] CHANGELOG.md ist unter „Unveröffentlicht" ergänzt

## Was ich nicht geprüft habe

<!-- Hier hin. Lieber eine offene Stelle benannt als eine behauptete
     Vollständigkeit. -->
