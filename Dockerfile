# Der Konformitätshelfer als Container.
#
# Drei Stufen, damit im fertigen Abbild nur liegt, was zum Laufen gebraucht
# wird — kein Übersetzer, kein Paketzwischenspeicher, keine Werkzeuge zum
# Herunterladen. Jedes Werkzeug, das im Abbild bleibt, ist eine Stelle, an der
# jemand etwas tun könnte, was der Dienst selbst nicht tun muss.
#
#   1. abhaengigkeiten — baut die Pakete in eine eigene Umgebung
#   2. modelle         — holt das Einbettungsmodell
#   3. (unbenannt)     — das fertige Abbild
#
# ENTSCHEIDUNG ZUM EINBETTUNGSMODELL: Es wird beim Bauen heruntergeladen und
# ins Abbild gelegt, nicht beim ersten Start in ein benanntes Volumen geholt.
# Der Grund ist nicht Bequemlichkeit, sondern Notwendigkeit: die mitgelieferte
# Suchdatenbank besteht aus Zahlenreihen, die bge-m3 erzeugt hat. Um eine
# *Frage* mit dieser Datenbank zu vergleichen, muss die Frage mit demselben
# Modell in eine Zahlenreihe verwandelt werden. Ohne das Modell im Abbild wäre
# die mitgelieferte Datenbank also wertlos, und der Container könnte ohne Netz
# nicht suchen — genau das soll er aber können. Ein benanntes Volumen würde
# zusätzlich bedeuten, dass der erste Start 2,3 Gigabyte zieht und bis dahin
# falsch antwortet; ein Werkzeug, das beim ersten Lauf schlechter arbeitet als
# beim zweiten, ist nicht prüfbar.
#
# Der Preis ist ein großes Abbild (rund 8 Gigabyte auf der Platte). Wer das nicht will, baut
# mit --build-arg MIT_SUCHMODELL=0: dann fehlen Modell und Rechenpakete, der
# Dienst läuft mit dem Ersatzmodell und sagt das in /gesundheit und in der
# Oberfläche. Für einen Prüflauf reicht das, für den Betrieb nicht.

ARG PYTHON_FASSUNG=3.13-slim

# ------------------------------------------------------- 1. Abhängigkeiten

FROM python:${PYTHON_FASSUNG} AS abhaengigkeiten

ARG MIT_SUCHMODELL=1

# lxml braucht beim Übersetzen Kopfdateien; im fertigen Abbild nicht mehr.
RUN apt-get update \
 && apt-get install --yes --no-install-recommends build-essential libxml2-dev libxslt1-dev \
 && rm -rf /var/lib/apt/lists/*

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN python -m venv /opt/umgebung
ENV PATH="/opt/umgebung/bin:$PATH"

WORKDIR /bau
# Erst nur die Beschreibung der Abhängigkeiten kopieren: solange sich die
# nicht ändert, kann der Bau diese Stufe aus dem Zwischenspeicher nehmen.
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Die Abhängigkeiten stehen in pyproject.toml und werden von dort genommen —
# keine zweite Liste, die auseinanderlaufen kann. Für die Suche kommt torch in
# der Fassung ohne Grafikkarte dazu: die Fassung mit Grafikkartenunterstützung
# ist zweieinhalb Gigabyte größer und im Container ohne Grafikkarte nutzlos.
RUN if [ "$MIT_SUCHMODELL" = "1" ]; then \
      pip install --extra-index-url https://download.pytorch.org/whl/cpu ".[suche]" ; \
    else \
      pip install "." ; \
    fi

# ------------------------------------------------------------- 2. Modelle

FROM abhaengigkeiten AS modelle

ARG MIT_SUCHMODELL=1
ARG EINBETTUNGSMODELL=BAAI/bge-m3
ENV HF_HOME=/opt/modelle \
    HF_HUB_DISABLE_TELEMETRY=1 \
    MODELL=${EINBETTUNGSMODELL}

# Das Modell wird hier geholt und in der nächsten Stufe nur noch kopiert.
#
# Es wird VOLLSTÄNDIG geholt, obwohl das Lager von bge-m3 dieselben Gewichte
# zweimal enthält — einmal für Python (pytorch_model.bin, 2,27 GB) und einmal
# als ONNX-Datei (onnx/model.onnx_data, weitere 2,27 GB) — und obendrein
# Beispielbilder. Gebraucht wird davon nur die erste Fassung.
#
# Der Grund ist gemessen, nicht geraten: holt man nur die gebrauchten Dateien,
# gilt die Ablage für huggingface_hub als unvollständig, und im Offline-Betrieb
# verweigert es die Benutzung mit der Meldung "The cached snapshot ... is
# incomplete: 18 file(s) are missing" — selbst für Dateien, die niemand
# braucht (README.md, .gitattributes, imgs/.DS_Store). Es greift dann ins Netz,
# findet keins, und fällt auf das Ersatzmodell zurück. Genau das war im ersten
# Bauversuch so: das Abbild war klein, der Container startete, und die Suche
# arbeitete trotz mitgeliefertem Modell mit Wortvergleich. Mit vollständiger
# Ablage lädt dasselbe Modell ohne jeden Netzzugriff in rund 12 Sekunden und
# bettet eine Frage in 1,2 Sekunden ein.
#
# Der Preis sind 4,58 GB im Abbild statt 2,31 GB. Das ist der Preis dafür,
# dass der Container ohne Netz richtig arbeitet statt still schlechter.
#
# Danach wird NACHGEZÄHLT, nicht gehofft: fehlen die Gewichte oder sind sie
# kleiner als 100 Megabyte, bricht der Bau ab.
RUN mkdir -p /opt/modelle \
 && if [ "$MIT_SUCHMODELL" != "1" ]; then \
      echo "ohne Suchmodell gebaut — es gilt das Ersatzmodell" > /opt/modelle/HINWEIS.txt ; \
    else \
      python -c "import os, sys; from pathlib import Path; \
from huggingface_hub import snapshot_download; \
ordner = snapshot_download(os.environ['MODELL']); \
gewichte = [d for d in Path(ordner).glob('*') if d.name in ('pytorch_model.bin','model.safetensors')]; \
groesse = sum(d.stat().st_size for d in gewichte); \
sys.exit('Das Modell %s ist unvollstaendig geholt: Gewichte %d Byte. Vorhanden: %s' % (os.environ['MODELL'], groesse, sorted(q.name for q in Path(ordner).glob('*')))) if groesse < 100*1024*1024 else None; \
print('Modell %s vollstaendig: %.2f GB Gewichte, Ablage %.2f GB' % (os.environ['MODELL'], groesse/1e9, sum(d.stat().st_size for d in Path(ordner).rglob('*') if d.is_file())/1e9))" ; \
    fi

# ------------------------------------------------------------ 3. Das Abbild

FROM python:${PYTHON_FASSUNG}

ARG MIT_SUCHMODELL=1

LABEL org.opencontainers.image.title="Konformitätshelfer" \
      org.opencontainers.image.description="Belegte Auskunft zur KI-Verordnung (EU) 2024/1689 und zur Datenschutz-Grundverordnung. Keine Rechtsberatung." \
      org.opencontainers.image.licenses="Apache-2.0" \
      org.opencontainers.image.source="https://github.com/DanielHuette/eu-ai-act-dsgvo-konformitaetshelfer"

# Nur die Laufzeitbibliothek von lxml, nicht die Kopfdateien. curl für die
# Zustandsprüfung — der Container soll seinen Zustand selbst feststellen
# können, ohne dass von außen etwas hineingereicht wird.
RUN apt-get update \
 && apt-get install --yes --no-install-recommends libxml2 libxslt1.1 curl \
 && rm -rf /var/lib/apt/lists/* \
 # Ein Nutzer ohne Verwalterrechte. Feste Kennung 10001, damit die Rechte an
 # eingehängten Ordnern auf jedem Rechner dieselben sind.
 && groupadd --gid 10001 helfer \
 && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin helfer

COPY --from=abhaengigkeiten /opt/umgebung /opt/umgebung
# Das Modellverzeichnis gehört dem Dienstnutzer. Die Modellpakete legen beim
# Laden Verwaltungsdateien daneben; gehört der Ordner root, scheitert das und
# jeder Start beginnt mit einer Meldung über eine "beschädigte" Datei, die
# nicht beschädigt ist, sondern nur nicht beschreibbar.
COPY --from=modelle --chown=10001:10001 /opt/modelle /opt/modelle

WORKDIR /app

# Quelltext und Datenbank kommen MIT ins Abbild. Die Datenbank ist der Grund,
# dass der Dienst ohne Netz arbeiten kann: 2721 Rechtsstellen und die
# Suchzahlenreihen dazu.
# Der Dienstnutzer darf lesen, nicht schreiben. Ein Dienst, der seinen eigenen
# Quelltext ändern kann, lässt einem Angreifer, der ihn einmal zum Ausführen
# von Code bringt, die Möglichkeit, sich dauerhaft einzurichten: beim nächsten
# Start läuft dann sein Code mit. Darum gehören Quelltext, Rechtsdaten und
# Regeln dem Verwalter und sind für den Dienstnutzer nur lesbar (Rechte 0444
# für Dateien, 0555 für Ordner).
COPY --chown=0:0 src/ /app/src/
COPY --chown=0:0 daten/ /app/daten/
COPY --chown=0:0 pyproject.toml README.md /app/
RUN chmod -R a-w /app/src /app/daten /app/pyproject.toml /app/README.md

# PYTHONPATH zeigt auf /app/src, obwohl das Paket auch in der Umgebung liegt.
# Das ist kein Versehen: Korpus und Regeln werden über den Ort des Quelltextes
# gefunden (drei Ebenen über helfer/korpus/bauen.py). Liegt der Quelltext unter
# /app/src, findet er /app/daten. Aus der installierten Fassung heraus würde er
# im Paketordner suchen und nichts finden.
ENV PYTHONPATH=/app/src \
    PATH="/opt/umgebung/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/opt/modelle \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    HELFER_ADRESSE=0.0.0.0 \
    HELFER_PORT=8000 \
    HELFER_ANFRAGEN_JE_MINUTE=30 \
    HELFER_HERKUNFT=http://localhost:8000,http://127.0.0.1:8000 \
    HELFER_MODELL=auto \
    HELFER_NEUBEWERTUNG=0 \
    HELFER_BESTAND_BAUEN=0

# Ohne Suchmodell im Abbild wäre der Versuch, bge-m3 zu laden, ein Griff ins
# Netz, der in einem abgeschotteten Container nur hängen bleibt. Darum wird
# dann von vornherein das Ersatzmodell gesetzt.
RUN if [ "$MIT_SUCHMODELL" = "1" ]; then \
      echo "HELFER_EINBETTUNG=BAAI/bge-m3" > /app/.modellwahl ; \
    else \
      echo "HELFER_EINBETTUNG=streuwerk-ersatz" > /app/.modellwahl ; \
    fi \
 && chown 10001:10001 /app/.modellwahl
ENV HELFER_EINBETTUNG=""

USER 10001:10001

# Nur dieser eine Zugang. 8000 innen, außen bestimmt es docker-compose.
EXPOSE 8000

# Der Zustandsbericht fragt den Dienst selbst und prüft nicht nur, ob der
# Ablauf lebt: ein Dienst, dessen Korpus fehlt, antwortet zwar, ist aber nicht
# betriebsbereit. "nicht_bereit" gilt deshalb als krank.
HEALTHCHECK --interval=30s --timeout=5s --start-period=180s --retries=3 \
  CMD curl --fail --silent http://127.0.0.1:8000/gesundheit \
      | grep -q -e '"zustand":"bereit"' -e '"zustand":"eingeschraenkt"' || exit 1

# Start über den Eintrittspunkt aus pyproject.toml: so ist der Weg im
# Container derselbe wie auf dem Rechner.
CMD ["sh", "-c", ". /app/.modellwahl && export HELFER_EINBETTUNG && exec konformitaetshelfer dienst --adresse \"$HELFER_ADRESSE\" --port \"$HELFER_PORT\""]
