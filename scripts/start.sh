#!/usr/bin/env bash
# Ein Befehl, der den Konformitätshelfer baut und startet.
#
# Das Skript prüft erst, ob die Voraussetzungen da sind, und sagt bei jedem
# Mangel, was zu tun ist — statt eine Fehlermeldung von Docker durchzulassen,
# aus der niemand schlau wird.
#
# Aufruf:
#   ./scripts/start.sh                 bauen und starten
#   ./scripts/start.sh --klein         ohne das große Suchmodell (schnell)
#   ./scripts/start.sh --neu           ohne Zwischenspeicher neu bauen
#   ./scripts/start.sh --stopp         anhalten

set -euo pipefail

WURZEL="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$WURZEL"

# Farbe nur, wenn die Ausgabe in ein Fenster geht und NO_COLOR nicht gesetzt
# ist — so ist es verabredet.
if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
  ROT=$'\033[1;31m'; GRUEN=$'\033[1;32m'; GELB=$'\033[1;33m'
  FETT=$'\033[1m'; AUS=$'\033[0m'
else
  ROT=''; GRUEN=''; GELB=''; FETT=''; AUS=''
fi

sagen()   { printf '%s\n' "$*"; }
gut()     { printf '%s✓%s %s\n' "$GRUEN" "$AUS" "$*"; }
warnen()  { printf '%s!%s %s\n' "$GELB" "$AUS" "$*"; }
abbruch() { printf '%s✗%s %s\n' "$ROT" "$AUS" "$*" >&2; exit 1; }

KLEIN=0; NEU=0; STOPP=0
for arg in "$@"; do
  case "$arg" in
    --klein)      KLEIN=1 ;;
    --neu)        NEU=1 ;;
    --stopp)      STOPP=1 ;;
    -h|--hilfe)   sed -n '2,15p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *)            abbruch "Unbekannte Angabe: $arg. Hilfe mit --hilfe." ;;
  esac
done

printf '%sKonformitätshelfer%s\n\n' "$FETT" "$AUS"

# ------------------------------------------------------------- 1. Docker da?

if ! command -v docker >/dev/null 2>&1; then
  abbruch "Docker ist nicht installiert. Zu holen unter https://docs.docker.com/get-docker/"
fi

if ! docker info >/dev/null 2>&1; then
  abbruch "Docker ist installiert, läuft aber nicht. Auf dem Mac und unter
  Windows: Docker Desktop starten. Unter Linux: sudo systemctl start docker"
fi
gut "Docker läuft ($(docker version --format '{{.Server.Version}}' 2>/dev/null || echo 'Fassung unbekannt'))"

if docker compose version >/dev/null 2>&1; then
  COMPOSE=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  COMPOSE=(docker-compose)
else
  abbruch "docker compose fehlt. Es gehört zu neueren Docker-Fassungen dazu;
  sonst nachinstallieren: https://docs.docker.com/compose/install/"
fi

# ------------------------------------------------------------ 2. Anhalten?

if [[ $STOPP -eq 1 ]]; then
  "${COMPOSE[@]}" down
  gut "Angehalten."
  exit 0
fi

# ----------------------------------------------------- 3. Voraussetzungen

if [[ ! -f daten/aufbereitet/korpus.jsonl ]]; then
  abbruch "Die Rechtstexte fehlen: daten/aufbereitet/korpus.jsonl
  Erst bauen:  python -m helfer.korpus.bauen"
fi
EINHEITEN=$(wc -l < daten/aufbereitet/korpus.jsonl | tr -d ' ')
gut "Rechtstexte da: $EINHEITEN Rechtsstellen"

if [[ -f daten/aufbereitet/suchbestand.bestand.json.gz ]]; then
  gut "Suchbestand da — der Dienst muss beim Start nicht rechnen"
else
  warnen "Der Suchbestand fehlt. Der Dienst baut ihn beim Start selbst;
  ohne das große Modell bedeutet das schlechtere Fundstellen.
  Besser vorher:  python -m scripts.bestand_bauen"
fi

if [[ ! -f .env ]]; then
  warnen "Keine .env vorhanden. Es gelten die Vorgaben.
  Für ein Sprachmodell:  cp .env.example .env  und Schlüssel eintragen."
fi

# ------------------------------------------------------------- 4. Bauen

BAU=("${COMPOSE[@]}" build)
[[ $NEU -eq 1 ]] && BAU+=(--no-cache)

if [[ $KLEIN -eq 1 ]]; then
  export MIT_SUCHMODELL=0
  export HELFER_SPEICHER="${HELFER_SPEICHER:-1g}"
  warnen "Kleines Abbild: ohne das Modell bge-m3. Die Suche vergleicht dann
  nur Wörter, nicht Bedeutung. Für einen Prüflauf in Ordnung, für den
  Betrieb nicht."
else
  export MIT_SUCHMODELL=1
  sagen ""
  sagen "Es wird gebaut. Beim ersten Mal dauert das lange: das"
  sagen "Einbettungsmodell ist rund 2,3 Gigabyte groß und wird mit ins Abbild"
  sagen "gelegt, damit der Container später ohne Netz arbeiten kann."
fi

sagen ""
"${BAU[@]}" || abbruch "Der Bau ist fehlgeschlagen. Die letzte Meldung oben sagt,
  woran es lag. Häufigste Ursachen: kein Netz beim Holen der Pakete, oder zu
  wenig Platz auf der Platte (für das große Abbild sind rund 8 Gigabyte frei
  nötig — nachsehen mit: docker system df)."

gut "Abbild gebaut"

# ------------------------------------------------------------ 5. Starten

HOCH=("${COMPOSE[@]}")
HOCH+=(up --detach)

"${HOCH[@]}" || abbruch "Der Start ist fehlgeschlagen. Protokoll ansehen mit:
  ${COMPOSE[*]} logs helfer"

# --------------------------------------------------------- 6. Warten

PORT="${HELFER_PORT:-8000}"
ADRESSE="http://127.0.0.1:${PORT}"

sagen ""
printf 'Der Dienst fährt hoch '
BEREIT=0
for _ in $(seq 1 90); do
  if curl --fail --silent --max-time 2 "${ADRESSE}/gesundheit" >/dev/null 2>&1; then
    BEREIT=1; break
  fi
  printf '.'
  sleep 2
done
sagen ""

if [[ $BEREIT -eq 0 ]]; then
  warnen "Der Dienst hat in drei Minuten nicht geantwortet.
  Das kann am großen Modell liegen. Protokoll ansehen mit:
    ${COMPOSE[*]} logs --follow helfer"
  exit 1
fi

ZUSTAND=$(curl --fail --silent "${ADRESSE}/gesundheit" || echo '{}')
sagen ""
gut "Der Konformitätshelfer läuft."
sagen ""
printf '   Oberfläche:       %s%s/%s\n' "$FETT" "$ADRESSE" "$AUS"
printf '   Zustandsbericht:  %s/gesundheit\n' "$ADRESSE"
printf '   Schnittstelle:    %s/openapi.json\n' "$ADRESSE"
sagen ""
printf '%s\n' "$ZUSTAND" | python3 -c '
import json,sys
try: d=json.load(sys.stdin)
except Exception: sys.exit(0)
print("   Rechtsstellen:    %s" % d.get("einheiten","?"))
print("   Suche mit:        %s" % d.get("einbettungsmodell","?"))
print("   Formulierung:     %s" % d.get("sprachmodell","?"))
for w in d.get("warnungen",[]):
    print("   Hinweis:          %s" % w)
' 2>/dev/null || true
sagen ""
sagen "Anhalten mit:  ./scripts/start.sh --stopp"
