#!/usr/bin/env python3
"""Prüft die Kotlin-Dateien, ohne sie zu übersetzen.

Hier im Behälter gibt es kein Android-SDK, also kann nichts übersetzt werden.
Was man ohne Übersetzer finden kann, findet dieses Skript - damit ein Fehler
auffällt, bevor die Bauanlage zehn Minuten läuft:

* unbalancierte Klammern, Zeichenfolgen und Kommentare
* fehlende oder zum Ordner nicht passende Paketzeile
* Einfuhren, für die keine Abhängigkeit im Bau steht
* Einfuhren aus dem eigenen Paket, die es nicht gibt

Aufruf:
    python3 android/pruefung/kotlin_pruefen.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

WURZEL = Path(__file__).resolve().parent.parent
EIGENES_PAKET = "de.konformitaetshelfer"

#: Welcher Paketanfang von welcher Abhängigkeit kommt. Links der Anfang, wie er
#: in einer Einfuhr steht, rechts der Name im Fassungsverzeichnis.
#: Was die Java- und Kotlin-Standardbibliothek mitbringt, braucht keinen Eintrag.
AUS_ABHAENGIGKEIT = {
    "androidx.compose": "compose-sammlung",
    "androidx.activity": "tatigkeit-compose",
    "androidx.lifecycle": "lebenslauf-ansichtsmodell",
    "androidx.core": "kern-ktx",
    "androidx.sqlite.driver.bundled": "sqlite-mitgeliefert",
    "androidx.sqlite": "sqlite",
    "androidx.security.crypto": "schluesselspeicher",
    "ai.onnxruntime": "onnx-laufzeit",
    "kotlinx.serialization": "serialisierung-json",
    "kotlinx.coroutines": "nebenlaeufig",
    "okhttp3": "okhttp",
    "org.junit": "junit",
}

#: Was das Android-Grundgerüst selbst mitbringt und keine Zeile im Bau braucht.
VOM_SYSTEM = ("android.", "java.", "javax.", "kotlin.", "dalvik.")

#: Namen, die das Bauwerkzeug selbst erzeugt - sie stehen in keiner Quelldatei.
#: BuildConfig entsteht nur, wenn buildFeatures.buildConfig an ist; das wird
#: deshalb mitgeprüft.
ERZEUGT = {
    EIGENES_PAKET + ".BuildConfig": "buildConfig = true",
    EIGENES_PAKET + ".R": None,
}


def bauzeilen() -> str:
    text = (WURZEL / "app" / "build.gradle.kts").read_text(encoding="utf-8")
    text += (WURZEL / "gradle" / "libs.versions.toml").read_text(encoding="utf-8")
    return text


def ohne_text_und_kommentar(quelle: str) -> str:
    """Löscht Zeichenfolgen und Kommentare und meldet, was nicht geschlossen ist.

    Ohne diesen Schritt zählt eine Klammer in einem Text mit, und dann meldet
    die Klammerprüfung Fehler, wo keine sind.
    """
    ergebnis = []
    i = 0
    laenge = len(quelle)
    while i < laenge:
        zeichen = quelle[i]
        if quelle.startswith('"""', i):
            ende = quelle.find('"""', i + 3)
            if ende < 0:
                raise Fehlerhaft("ein dreifach begrenzter Text wird nicht geschlossen")
            i = ende + 3
            ergebnis.append('""')
            continue
        if zeichen == '"':
            i += 1
            while i < laenge and quelle[i] != '"':
                if quelle[i] == "\\":
                    i += 1
                if i < laenge and quelle[i] == "\n":
                    raise Fehlerhaft("ein Text läuft über das Zeilenende")
                i += 1
            if i >= laenge:
                raise Fehlerhaft("ein Text wird nicht geschlossen")
            i += 1
            ergebnis.append('""')
            continue
        if zeichen == "'":
            i += 1
            while i < laenge and quelle[i] != "'":
                if quelle[i] == "\\":
                    i += 1
                i += 1
            i += 1
            ergebnis.append("''")
            continue
        if quelle.startswith("//", i):
            ende = quelle.find("\n", i)
            i = laenge if ende < 0 else ende
            continue
        if quelle.startswith("/*", i):
            tiefe = 0
            while i < laenge:
                if quelle.startswith("/*", i):
                    tiefe += 1
                    i += 2
                elif quelle.startswith("*/", i):
                    tiefe -= 1
                    i += 2
                    if tiefe == 0:
                        break
                else:
                    i += 1
            if tiefe != 0:
                raise Fehlerhaft("ein Blockkommentar wird nicht geschlossen")
            continue
        ergebnis.append(zeichen)
        i += 1
    return "".join(ergebnis)


class Fehlerhaft(Exception):
    pass


def klammern_pruefen(sauber: str) -> list[str]:
    paare = {")": "(", "]": "[", "}": "{"}
    stapel: list[tuple[str, int]] = []
    zeile = 1
    beanstandet = []
    for zeichen in sauber:
        if zeichen == "\n":
            zeile += 1
        elif zeichen in "([{":
            stapel.append((zeichen, zeile))
        elif zeichen in ")]}":
            if not stapel:
                beanstandet.append(f"Zeile {zeile:d}: '{zeichen}' ohne Gegenstück")
            elif stapel[-1][0] != paare[zeichen]:
                auf, aufzeile = stapel.pop()
                beanstandet.append(
                    f"Zeile {zeile:d}: '{zeichen}' schließt '{auf}' aus Zeile {aufzeile:d}"
                )
            else:
                stapel.pop()
    for auf, aufzeile in stapel:
        beanstandet.append(f"Zeile {aufzeile:d}: '{auf}' wird nicht geschlossen")
    return beanstandet


def eigene_namen(dateien: list[Path]) -> dict[str, set[str]]:
    """Sammelt je Paket, welche Namen dort auf oberster Ebene erklärt werden."""
    muster = re.compile(
        r"^(?:@\w+\s+)*(?:public |internal |private |abstract |open |sealed |data |"
        r"enum |value |annotation |inline |expect |actual )*"
        r"(?:class|object|interface|fun|val|var|typealias)\s+([A-Za-z_][\w]*)",
        re.MULTILINE,
    )
    nach_paket: dict[str, set[str]] = {}
    for datei in dateien:
        quelle = datei.read_text(encoding="utf-8")
        treffer = re.search(r"^package\s+([\w.]+)", quelle, re.MULTILINE)
        if not treffer:
            continue
        paket = treffer.group(1)
        namen = nach_paket.setdefault(paket, set())
        for name in muster.findall(quelle):
            namen.add(name)
        # Erweiterungen wie "fun ColumnScope.Fragebogen" erklären Fragebogen.
        for name in re.findall(r"^\s*(?:@\w+\s+)*fun\s+[\w.]+\.([A-Za-z_]\w*)\s*\(",
                               quelle, re.MULTILINE):
            namen.add(name)
        # Geschachtelte Namen, die von außen eingeführt werden können.
        for name in re.findall(r"^\s{4}(?:data |sealed |enum |value )*"
                               r"(?:class|object|interface)\s+([A-Za-z_]\w*)",
                               quelle, re.MULTILINE):
            namen.add(name)
    return nach_paket


def haupt() -> int:
    quellen = sorted((WURZEL / "app" / "src").rglob("*.kt"))
    if not quellen:
        print("ABBRUCH: keine Kotlin-Dateien gefunden", file=sys.stderr)
        return 1

    bau = bauzeilen()
    bekannt = eigene_namen(quellen)
    beanstandet: list[str] = []
    einfuhren = 0

    for datei in quellen:
        kurz = datei.relative_to(WURZEL).as_posix()
        quelle = datei.read_text(encoding="utf-8")

        # Paketzeile vorhanden und zum Ordner passend?
        treffer = re.search(r"^package\s+([\w.]+)", quelle, re.MULTILINE)
        if not treffer:
            beanstandet.append(f"{kurz}: keine Paketzeile")
            continue
        paket = treffer.group(1)
        teile = datei.parent.as_posix().split("/")
        if "kotlin" in teile:
            erwartet = ".".join(teile[teile.index("kotlin") + 1:])
            if erwartet and paket != erwartet:
                beanstandet.append(
                    f"{kurz}: Paket '{paket}', Ordner sagt '{erwartet}'"
                )

        # Klammern, Texte, Kommentare
        try:
            sauber = ohne_text_und_kommentar(quelle)
        except Fehlerhaft as fehler:
            beanstandet.append(f"{kurz}: {fehler}")
            continue
        for meldung in klammern_pruefen(sauber):
            beanstandet.append(f"{kurz}: {meldung}")

        # Einfuhren
        for zeile in re.findall(r"^import\s+([\w.]+)", quelle, re.MULTILINE):
            einfuhren += 1
            if zeile.startswith(VOM_SYSTEM):
                continue
            if zeile in ERZEUGT:
                bedingung = ERZEUGT[zeile]
                if bedingung and bedingung not in bau:
                    beanstandet.append(
                        f"{kurz}: Einfuhr '{zeile}' entsteht nur mit '{bedingung}' im Bau"
                    )
                continue
            if zeile.startswith(EIGENES_PAKET + "."):
                rest = zeile[len(EIGENES_PAKET) + 1:]
                stuecke = rest.split(".")
                name = stuecke[-1]
                fremdes_paket = EIGENES_PAKET + ("." + ".".join(stuecke[:-1])
                                                 if len(stuecke) > 1 else "")
                if name not in bekannt.get(fremdes_paket, set()):
                    # Auch ein Name aus einer Begleitklasse ist zulässig.
                    tiefer = EIGENES_PAKET + "." + ".".join(stuecke[:-2]) \
                        if len(stuecke) > 2 else fremdes_paket
                    if stuecke[-2:-1] and stuecke[-2] in bekannt.get(tiefer, set()):
                        continue
                    beanstandet.append(
                        f"{kurz}: Einfuhr '{zeile}' zeigt auf keinen erklärten Namen"
                    )
                continue
            passend = [anfang for anfang in AUS_ABHAENGIGKEIT if zeile.startswith(anfang + ".")]
            if not passend:
                beanstandet.append(
                    f"{kurz}: Einfuhr '{zeile}' gehört zu keiner bekannten Abhängigkeit"
                )
                continue
            name = AUS_ABHAENGIGKEIT[max(passend, key=len)]
            if name not in bau:
                beanstandet.append(
                    f"{kurz}: Einfuhr '{zeile}' braucht '{name}', das steht nicht im Bau"
                )

    print(f"{len(quellen):d} Kotlin-Dateien, {einfuhren:d} Einfuhren geprüft")
    if beanstandet:
        print(f"\n{len(beanstandet):d} Beanstandungen:", file=sys.stderr)
        for meldung in beanstandet:
            print(f"  - {meldung}", file=sys.stderr)
        return 1
    print("Keine Beanstandung.")
    return 0


if __name__ == "__main__":
    sys.exit(haupt())
