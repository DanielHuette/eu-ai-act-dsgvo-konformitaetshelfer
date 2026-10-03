#!/usr/bin/env bash
# Prüft genau das, was der Prüfstand auf GitHub prüft — in derselben
# Reihenfolge und mit denselben Befehlen.
#
# Der Grund für dieses Skript: wer nur einen Teil prüft, schiebt einen Fehler
# in den Prüfstand und merkt es erst dort. Einmal war es die Formatierung in
# einem Ordner, der beim Aufruf nicht dabeistand; einmal fehlten Typangaben
# fremder Pakete, die auf dem Entwicklungsrechner zufällig schon lagen.
#
#   scripts/alles_pruefen.sh            alles ausser Container und Präsentation
#   scripts/alles_pruefen.sh --alles    zusätzlich Container und Präsentation
set -uo pipefail
cd "$(dirname "$0")/.."

mit_allem=0
[[ "${1:-}" == "--alles" ]] && mit_allem=1

fehler=0
schritt() {
  local name="$1"; shift
  printf '\n\033[1m── %s\033[0m\n' "$name"
  if "$@"; then
    printf '   \033[32min Ordnung\033[0m\n'
  else
    printf '   \033[31mbeanstandet\033[0m\n'
    fehler=$((fehler + 1))
  fi
}

schritt "ruff — Programmtext auf Regeln"  python3 -m ruff check .
schritt "ruff format — Formatierung"      python3 -m ruff format --check .
schritt "mypy — Typen"                    python3 -m mypy src
schritt "bandit — unsichere Muster"       python3 -m bandit -c pyproject.toml -r src scripts android -q
# pip-audit prüft, was in der Umgebung liegt. Auf der Bauanlage ist das genau
# dieses Projekt samt Abhängigkeiten; auf einem Entwicklungsrechner liegt
# daneben alles Mögliche, und dessen Schwachstellen sagen über dieses Projekt
# nichts. Darum werden hier die Abhängigkeiten geprüft, die pyproject.toml
# nennt — dieselbe Aussage, unabhängig vom Rechner.
pruefliste=$(mktemp)
python3 - "$pruefliste" <<'PY'
import sys, tomllib
with open("pyproject.toml", "rb") as datei:
    satz = tomllib.load(datei)["project"]
zeilen = list(satz.get("dependencies", []))
for weitere in satz.get("optional-dependencies", {}).values():
    zeilen += list(weitere)
with open(sys.argv[1], "w", encoding="utf-8") as ziel:
    ziel.write("\n".join(sorted(set(zeilen))) + "\n")
PY
schritt "pip-audit — Schwachstellen"      python3 -m pip_audit -r "$pruefliste"
rm -f "$pruefliste"
schritt "pytest — Prüfungen"              python3 -m pytest -m "not langsam and not netz and not container" -q

if [[ $mit_allem -eq 1 ]]; then
  schritt "pytest — Container ohne Netz"  python3 -m pytest -m container -q
  schritt "Präsentation — passt alles?"   python3 scripts/praesentation_bauen.py --messen
fi

printf '\n'
if [[ $fehler -eq 0 ]]; then
  printf '\033[32mAlles in Ordnung.\033[0m\n'
else
  printf '\033[31m%d Schritte beanstandet.\033[0m\n' "$fehler"
fi
exit $fehler
