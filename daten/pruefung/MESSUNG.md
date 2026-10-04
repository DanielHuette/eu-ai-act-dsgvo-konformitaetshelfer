# Was nachgemessen ist

Stand: 4. Oktober 2026

## Die Zahl

**207 von 217 amtlichen Beispielen** der Europäischen Kommission werden richtig
eingestuft. Im Schnitt **5,3 Schritte** je Fall.

Gemessen wurde so: Die 217 Beispiele stammen aus dem Entwurf der Leitlinien der
Kommission vom 19. Mai 2026. Jedes beschreibt ein KI-System und nennt die
Wertung der Kommission. Ein Leser, der nur die Beschreibung kennt — nicht die
Wertung —, beantwortet damit die Fragen des Durchlaufs. Verglichen wird, ob der
Durchlauf zur selben Wertung kommt wie die Kommission.

## Was die Zahl wert ist

Die Soll-Wertungen stammen von der Kommission, nicht von mir. Das ist der
Unterschied zur vorigen Fassung, in der ich sowohl die Regeln als auch die
Prüffälle geschrieben hatte: dort hiess eine hohe Trefferquote nur, dass der
Helfer mit meiner Lesart übereinstimmt.

Die Beschreibungen der Beispiele sind kurz. Ein Mitarbeiter, der sein eigenes
System einstuft, weiss mehr über es als in zwei Sätzen steht — in diese
Richtung ist die gemessene Zahl eher zu niedrig als zu hoch.

## Die zehn Abweichungen

Sieben davon messen nicht den Durchlauf. Die Beispiele 2, 6, 13, 47, 48, 72 und
114 stammen aus dem Abschnitt der Leitlinien zur Ausnahme des Artikels 6
Absatz 3. Sie beschreiben ausdrücklich nur das Ausnahmemerkmal und nennen
keinen Bereich des Anhangs III. Der Durchlauf fragt die Ausnahme erst, wenn ein
Bereich trägt — so steht es im Gesetz, denn Artikel 6 Absatz 3 nimmt nur aus,
was zuvor unter Anhang III fällt. Ohne Bereich kommt die Frage nie an die
Reihe. Für den Nutzer ist die Folge dieselbe: keine Hochrisiko-Pflichten.

Rechnet man diese sieben heraus, sind es **207 von 210**.

Die übrigen drei:

| Fall | Ursache |
|---|---|
| 108 | Die Beschreibung nennt nicht, dass eine Strafverfolgungsbehörde das System einsetzt. |
| 141 | Die Beschreibung nennt keinen Bereich; das Beispiel ist ein Gegenbeispiel zur Ausnahme. |
| 187 | Die Beschreibung nennt für ein Übersetzungswerkzeug im Strassenverkehr keine Schutzaufgabe. |

Alle drei liegen daran, dass der Beispieltext das entscheidende Merkmal nicht
nennt — die einsetzende Behörde, der Bereich, die Schutzaufgabe. Wer sein
eigenes System einstuft, kennt es.

Eine vierte Abweichung, Fall 92, ist am 4. Oktober 2026 geschlossen worden.
Die Vorfrage nach der Bewertung von Menschen trug den Satz aus Absatz 73 nicht:
ein Betrieb bleibt ein Betrieb, auch wenn er einem einzelnen Menschen gehört
und keine Rechtsperson ist. Wer allein Bilanzen, Umsätze und Zahlungsverhalten
des Betriebs auswertet, bewertet damit keinen Menschen. Der Satz steht jetzt in
der Frage; vorher stand er nur in der Begründung, wo ihn der Nutzer nicht
beantworten konnte.

## Was sonst nachgemessen ist

| Was | Ergebnis |
|---|---|
| Webseite und Programm rechnen gleich | 400 von 400 Läufen, `scripts/pruefe_zwei_wege.py` |
| Jede Belegstelle zeigt auf echten amtlichen Text | 303 von 303 |
| Rechtsbestand ohne Verlust zerlegt | 2811 Einheiten, keine Warnung |
| Das gebaute Paket startet und zeigt die Fragefolge | `verpacken/start_pruefen.py` |

## Was nicht nachgemessen ist

Die abgeleiteten Pflichten. Sie stammen aus `daten/regeln/kivo_pflichten.yaml`
und sind gegen den Verordnungstext geprüft, aber nicht gegen eine fremde
Sollvorgabe gemessen — es gibt dafür keine amtliche Beispielsammlung.

Kein Jurist hat den Durchlauf gegengelesen.
