"""Der Webdienst des Konformitätshelfers.

``anwendung_bauen()`` liefert den Dienst, ``dienst`` ist die fertige Anwendung
für uvicorn, ``starten()`` der Weg über die Kommandozeile.
"""

from helfer.dienst.anwendung import anwendung_bauen, dienst, starten

__all__ = ["anwendung_bauen", "dienst", "starten"]
