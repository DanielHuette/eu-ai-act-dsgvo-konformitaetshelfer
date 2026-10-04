# -*- mode: python ; coding: utf-8 -*-
"""Bauplan für die Pakete: Windows, Mac und Linux aus derselben Vorschrift.

Was mit ins Paket muss und warum:

* **Der Rechtsbestand** (daten/aufbereitet/korpus.jsonl) — ohne ihn gibt es
  keine Fundstelle zum Nachlesen.
* **Das Regelwerk und die Fragefolge** (daten/regeln/) — daraus entsteht die
  Einstufung.
* **Die amtlichen Anwendungsfälle** (daten/faelle/) — die Beispiele, mit denen
  der Nutzer seinen Fall vergleicht.
* **Die Bedienoberfläche** (src/helfer/weboberflaeche/, web/).

Was NICHT mit ins Paket kommt:

* **Das Sprachmodell für die Volltextsuche** (rund 2,3 Gigabyte). Es würde das
  Paket vervierzigfachen, und die Einstufung — der Kern — braucht es nicht.
  Der Helfer holt es auf Wunsch nach, an der Stelle, wo es gebraucht wird.
* **Der Rohbestand** (daten/roh/) — die heruntergeladenen Amtsblätter und
  Leitlinien. Sie sind die Quelle des Aufbereiteten, im Betrieb aber unnütz.
"""

from pathlib import Path

wurzel = Path(SPECPATH).parent

daten = [
    (str(wurzel / "daten" / "aufbereitet" / "korpus.jsonl"), "daten/aufbereitet"),
    (str(wurzel / "daten" / "aufbereitet" / "korpus_befund.json"), "daten/aufbereitet"),
    (str(wurzel / "daten" / "aufbereitet" / "fragefolge.json"), "daten/aufbereitet"),
    (str(wurzel / "daten" / "regeln"), "daten/regeln"),
    (str(wurzel / "daten" / "faelle"), "daten/faelle"),
    (str(wurzel / "src" / "helfer" / "weboberflaeche"), "helfer/weboberflaeche"),
    # Das Zeichen dafür, dass hier die Daten liegen: orte.wurzel() sucht nach
    # einem Ordner "daten" und findet ihn so auch im gebündelten Paket.
    (str(wurzel / "web"), "web"),
]

analyse = Analysis(
    [str(wurzel / "verpacken" / "start_helfer.py")],
    pathex=[str(wurzel / "src")],
    binaries=[],
    datas=daten,
    hiddenimports=[
        "uvicorn.logging",
        "uvicorn.loops.auto",
        "uvicorn.protocols.http.auto",
        "uvicorn.protocols.websockets.auto",
        "uvicorn.lifespan.on",
        "helfer.dienst.anwendung",
        "helfer.einstufung.fragefolge",
        "helfer.einstufung.pruefer",
    ],
    hookspath=[],
    runtime_hooks=[],
    # Die schweren Pakete bleiben draussen. Sie gehören zur Volltextsuche,
    # und die wird nachgeladen, wenn sie gebraucht wird.
    excludes=["torch", "sentence_transformers", "FlagEmbedding", "transformers",
              "matplotlib", "scipy", "pandas", "tkinter", "PyQt5", "PySide6"],
    noarchive=False,
)
pyz = PYZ(analyse.pure)

exe = EXE(
    pyz,
    analyse.scripts,
    [],
    exclude_binaries=True,
    name="Konformitaetshelfer",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    analyse.binaries,
    analyse.datas,
    strip=False,
    upx=False,
    name="Konformitaetshelfer",
)

# Auf dem Mac gehört das Programm in ein Anwendungsbündel, sonst lässt es sich
# nicht in den Programme-Ordner ziehen und taucht im Launchpad nicht auf.
import sys as _sys

if _sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="Konformitaetshelfer.app",
        icon=None,
        bundle_identifier="dev.speedofthespirit.konformitaetshelfer",
        info_plist={
            "CFBundleName": "Konformitätshelfer",
            "CFBundleDisplayName": "Konformitätshelfer",
            "CFBundleShortVersionString": "1.2.0",
            "NSHighResolutionCapable": True,
            # Das Programm spricht nur mit sich selbst auf 127.0.0.1. Der
            # Eintrag sagt das ausdrücklich, damit niemand rätselt, warum ein
            # Rechtswerkzeug einen Netzwerkanschluss öffnet.
            "NSLocalNetworkUsageDescription":
                "Der Helfer öffnet die Bedienoberfläche im Browser auf diesem Rechner. "
                "Es werden keine Daten ins Netz gesendet.",
        },
    )
