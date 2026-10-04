"""Was beim Doppelklick auf den Konformitätshelfer passiert.

Der Nutzer soll nichts tun müssen als installieren. Also: Dienst starten,
freien Netzwerkanschluss suchen, Browser öffnen, fertig. Keine Befehlszeile,
keine Umgebungsvariablen, keine Frage nach einem Schlüssel.

Der Helfer läuft in zwei Ausbaustufen, und das ist Absicht:

* **Die Einstufung** — die Fragefolge aus den amtlichen Leitlinien — braucht
  kein Modell, keine Netzverbindung und keine Einrichtung. Sie läuft sofort.
* **Die Volltextsuche im Verordnungstext** braucht ein Sprachmodell von rund
  2,3 Gigabyte. Liegt es nicht da, sagt der Helfer das an der Stelle, wo es
  gebraucht wird, und bietet an, es einmalig zu holen. Er startet deshalb
  nicht später und zeigt keine Fehlermeldung beim Öffnen.

So ist das Paket klein genug zum Herunterladen und trotzdem beim ersten Start
vollständig brauchbar.
"""

from __future__ import annotations

import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def wurzel() -> Path:
    """Wo die mitgelieferten Daten liegen — gebündelt wie entpackt."""
    gebuendelt = getattr(sys, "_MEIPASS", None)
    return Path(gebuendelt) if gebuendelt else Path(__file__).resolve().parents[1]


def freier_anschluss(von: int = 8713, bis: int = 8799) -> int:
    """Ein Netzwerkanschluss, der gerade frei ist.

    Fest auf eine Nummer zu setzen geht schief, sobald etwas anderes sie
    belegt — und der Nutzer sähe nur ein Fenster, das sich nicht öffnet.
    """
    for nummer in range(von, bis + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", nummer))
                return nummer
            except OSError:
                continue
    raise RuntimeError("Zwischen %d und %d ist kein Anschluss frei." % (von, bis))


def browser_oeffnen(adresse: str) -> None:
    """Den Browser öffnen, sobald der Dienst antwortet."""
    import urllib.error
    import urllib.request

    for _ in range(100):
        try:
            with urllib.request.urlopen(adresse, timeout=1):  # nosec B310
                break
        except (urllib.error.URLError, OSError):
            time.sleep(0.2)
    webbrowser.open(adresse)


def main() -> int:
    # Der Packer legt "daten" neben die Programmdatei; orte.wurzel() findet
    # das von allein, aber die ausdrückliche Angabe macht es nachvollziehbar
    # und erlaubt es, die Daten bewusst woanders hinzulegen.
    if "HELFER_WURZEL" not in os.environ:
        os.environ["HELFER_WURZEL"] = str(wurzel())
    # Ohne Schlüssel kein Sprachmodell: die Einstufung kommt ohnehin aus dem
    # Regelwerk, und eine Nachfrage beim Start wäre genau die Hürde, die es
    # nicht geben soll.
    os.environ.setdefault("HELFER_MODELL", "ohne")

    sys.path.insert(0, str(wurzel() / "src"))
    import uvicorn

    from helfer.dienst.anwendung import anwendung_bauen

    anschluss = freier_anschluss()
    adresse = f"http://127.0.0.1:{anschluss}/"
    print("Der Konformitätshelfer läuft unter " + adresse)
    print("Zum Beenden dieses Fenster schliessen.")
    threading.Thread(target=browser_oeffnen, args=(adresse,), daemon=True).start()
    uvicorn.run(anwendung_bauen(), host="127.0.0.1", port=anschluss, log_level="warning")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
