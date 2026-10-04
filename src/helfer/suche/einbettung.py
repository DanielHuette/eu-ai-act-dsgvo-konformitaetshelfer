"""Das Einbettungsmodell für die Suche im Rechtsbestand.

Eine Einbettung ist eine Zahlenreihe, die den Sinn eines Textstücks abbildet.
Zwei Texte, die dasselbe bedeuten, haben ähnliche Zahlenreihen. So findet die
Suche "Dürfen wir Bewerbungen vorsortieren?" auch dann, wenn im Gesetz
"Einstellung oder Auswahl natürlicher Personen" steht.

Genutzt wird **bge-m3**: mehrsprachig, 1024 Zahlen je Textstück, und es liefert
nicht nur die Sinn-Reihe, sondern zusätzlich Wortgewichte — damit ist ein Teil
der Stichwortsuche schon im Modell enthalten. Rund 2,3 GB groß, läuft ohne
Schlüssel und ohne Netz.

Es gibt bewusst nur ein Modell. Ein kleineres zweites für schwächere Geräte
hieße: dieselbe Auskunft, zwei Genauigkeiten, ein Name. Wer sich auf eine
Rechtsauskunft verlässt, darf nicht raten müssen, welche der beiden er bekommt.

Wichtig: Einbettungen verschiedener Modelle sind nicht vergleichbar. Deshalb
trägt jede Datenbank den Modellnamen, und beim Laden wird geprüft, dass Frage
und Bestand aus demselben Modell kommen.

Die EINSTUFUNG hängt an keinem dieser Modelle. Sie kommt aus der Fragefolge und
dem Regelwerk. Die Suche liefert den Gesetzestext zu Rückfragen und die
Fundstelle zum Nachlesen.
"""

from __future__ import annotations

import hashlib
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

protokoll = logging.getLogger(__name__)

#: Das Modell, mit dem die mitgelieferte Datenbank gebaut ist.
STANDARD_MODELL = "BAAI/bge-m3"


#: Diese Modelle wollen eine Anweisung vor dem Text - ohne sie fällt die
#: Trefferqualität messbar ab.
VORSILBEN = {
    "intfloat/multilingual-e5-small": {"frage": "query: ", "bestand": "passage: "},
    "intfloat/multilingual-e5-base": {"frage": "query: ", "bestand": "passage: "},
    "intfloat/multilingual-e5-large": {"frage": "query: ", "bestand": "passage: "},
}


@dataclass(frozen=True)
class Einbettungsbefund:
    """Was ein Modell liefert: die Sinn-Reihen und optional Wortgewichte."""

    dicht: np.ndarray
    wortgewichte: list[dict[str, float]] | None = None


class Einbetter(ABC):
    """Die Schnittstelle, an der die Suche hängt."""

    name: str
    dimensionen: int

    @abstractmethod
    def bestand(self, texte: list[str]) -> Einbettungsbefund:
        """Bettet Textstücke des Bestands ein."""

    @abstractmethod
    def frage(self, texte: list[str]) -> Einbettungsbefund:
        """Bettet Fragen ein - manche Modelle brauchen dafür eine andere Anweisung."""

    def eine_frage(self, text: str) -> np.ndarray:
        reihe: np.ndarray = self.frage([text]).dicht[0]
        return reihe


def _normieren(reihen: np.ndarray) -> np.ndarray:
    """Auf Länge eins bringen, damit das Skalarprodukt die Ähnlichkeit ist."""
    laengen = np.linalg.norm(reihen, axis=1, keepdims=True)
    laengen[laengen == 0] = 1.0
    genormt: np.ndarray = (reihen / laengen).astype(np.float32)
    return genormt


class BgeM3(Einbetter):
    """bge-m3 — liefert Sinn-Reihen und Wortgewichte in einem Durchgang.

    Die Wortgewichte sind der Grund, dieses Modell zu nehmen: sie ersetzen eine
    getrennte Stichwortsuche nicht, ergänzen sie aber um ein Gewicht, das den
    Zusammenhang kennt. "Artikel 9" wiegt in einer Frage nach Risikomanagement
    anders als in einer Frage nach besonderen Datenkategorien.
    """

    name = "BAAI/bge-m3"
    dimensionen = 1024

    def __init__(self, geraet: str | None = None, nur_dicht: bool = False) -> None:
        try:
            from FlagEmbedding import BGEM3FlagModel
        except ImportError as fehler:
            raise RuntimeError(
                "Für bge-m3 fehlt das Paket FlagEmbedding. "
                "Installieren mit: pip install 'konformitaetshelfer[suche]'"
            ) from fehler
        self._nur_dicht = nur_dicht
        self._modell = BGEM3FlagModel(self.name, use_fp16=geraet != "cpu", devices=geraet)

    def _rechnen(self, texte: list[str]) -> Einbettungsbefund:
        antwort: dict[str, Any] = self._modell.encode(
            texte,
            return_dense=True,
            return_sparse=not self._nur_dicht,
            return_colbert_vecs=False,
            batch_size=8,
            max_length=1024,
        )
        dicht = _normieren(np.asarray(antwort["dense_vecs"], dtype=np.float32))
        gewichte = None
        if not self._nur_dicht and antwort.get("lexical_weights") is not None:
            gewichte = [
                {str(k): float(v) for k, v in eintrag.items()}
                for eintrag in antwort["lexical_weights"]
            ]
        return Einbettungsbefund(dicht=dicht, wortgewichte=gewichte)

    def bestand(self, texte: list[str]) -> Einbettungsbefund:
        return self._rechnen(texte)

    def frage(self, texte: list[str]) -> Einbettungsbefund:
        return self._rechnen(texte)


class SatzUmformer(Einbetter):
    """Jedes Modell aus der sentence-transformers-Sammlung, ausdrücklich benannt.

    Dieser Weg wird nicht von allein gewählt. Er steht bereit, wenn jemand ein
    anderes Modell nennt und seinen Bestand damit selbst baut.
    """

    def __init__(self, name: str = STANDARD_MODELL, geraet: str | None = None) -> None:
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as fehler:
            raise RuntimeError(
                "Es fehlt das Paket sentence-transformers. "
                "Installieren mit: pip install 'konformitaetshelfer[suche]'"
            ) from fehler
        self.name = name
        self._modell = SentenceTransformer(name, device=geraet)
        # get_sentence_embedding_dimension() kann None liefern, wenn das Modell
        # keine Angabe mitbringt. Dann ist es für diesen Zweck unbrauchbar, und
        # das muss hier auffallen statt später als Längenfehler in der Suche.
        gemeldet = self._modell.get_sentence_embedding_dimension()
        if gemeldet is None:
            raise RuntimeError(
                f"Das Modell {name} nennt seine Zahl der Dimensionen nicht. "
                "Ohne diese Angabe lässt sich kein Bestand bauen."
            )
        self.dimensionen = int(gemeldet)
        self._vorsilben = VORSILBEN.get(name, {})

    def _rechnen(self, texte: list[str], rolle: str) -> Einbettungsbefund:
        vorsilbe = self._vorsilben.get(rolle, "")
        gefuettert = [vorsilbe + t for t in texte] if vorsilbe else texte
        reihen = self._modell.encode(
            gefuettert, batch_size=16, show_progress_bar=False, convert_to_numpy=True
        )
        return Einbettungsbefund(dicht=_normieren(np.asarray(reihen, dtype=np.float32)))

    def bestand(self, texte: list[str]) -> Einbettungsbefund:
        return self._rechnen(texte, "bestand")

    def frage(self, texte: list[str]) -> Einbettungsbefund:
        return self._rechnen(texte, "frage")


class Streuwerk(Einbetter):
    """Ein Ersatzmodell ohne Fremdpakete — nur für Tests.

    Es bildet Texte über ihre Wortstreuwerte ab. Das findet keine Bedeutung,
    sondern nur Wortübereinstimmung, ist dafür aber sofort verfügbar und
    nachvollziehbar. Damit laufen die Tests auch dort, wo kein Modell liegt.
    Im Betrieb hat es nichts zu suchen — darum sagt die Suche es in der Antwort.
    """

    name = "streuwerk-ersatz"
    dimensionen = 256

    def _rechnen(self, texte: list[str]) -> Einbettungsbefund:
        reihen = np.zeros((len(texte), self.dimensionen), dtype=np.float32)
        for zeile, text in enumerate(texte):
            for wort in text.lower().split():
                stelle = int(hashlib.blake2b(wort.encode("utf-8"), digest_size=4).hexdigest(), 16)
                reihen[zeile, stelle % self.dimensionen] += 1.0
        return Einbettungsbefund(dicht=_normieren(reihen))

    def bestand(self, texte: list[str]) -> Einbettungsbefund:
        return self._rechnen(texte)

    def frage(self, texte: list[str]) -> Einbettungsbefund:
        return self._rechnen(texte)


def waehlen(name: str | None = None, geraet: str | None = None) -> Einbetter:
    """Liefert das gewünschte Modell, mit Rückfall und klarer Meldung.

    Reihenfolge: ausdrücklich gewünschtes Modell, dann bge-m3, dann das
    Ersatzmodell für Prüfläufe. Jeder Rückfall wird protokolliert —
    stillschweigend schlechter zu suchen wäre schlimmer als eine Fehlermeldung.
    """
    if name == Streuwerk.name:
        return Streuwerk()
    versuche = [n for n in (name, STANDARD_MODELL) if n]
    for kandidat in versuche:
        try:
            if kandidat == "BAAI/bge-m3":
                return BgeM3(geraet=geraet)
            return SatzUmformer(kandidat, geraet=geraet)
        except Exception as fehler:
            protokoll.warning("Modell %s nicht verfügbar: %s", kandidat, fehler)
    protokoll.error(
        "Kein Einbettungsmodell verfügbar — es läuft das Ersatzmodell. "
        "Die Treffer sind damit deutlich schlechter."
    )
    return Streuwerk()


def modellordner() -> Path:
    """Wo heruntergeladene Modelle liegen — im Container und auf dem Rechner gleich."""
    import os

    return Path(os.environ.get("HF_HOME", Path.home() / ".cache" / "huggingface"))
