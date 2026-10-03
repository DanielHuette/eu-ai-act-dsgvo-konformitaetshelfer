<#
.SYNOPSIS
  Baut und startet den Konformitätshelfer unter Windows.

.DESCRIPTION
  Prüft erst, ob Docker da ist und läuft, ob die Rechtstexte gebaut sind, und
  startet dann den Verbund. Bei jedem Mangel sagt das Skript, was zu tun ist —
  eine durchgereichte Fehlermeldung von Docker hilft niemandem.

.PARAMETER Klein
  Ohne das große Einbettungsmodell bauen. Schnell, aber die Suche vergleicht
  dann nur Wörter und keine Bedeutung. Für einen Prüflauf in Ordnung.

.PARAMETER MitOllama
  Zusätzlich ein Sprachmodell im Verbund starten (ohne Schlüssel, ohne Netz).

.PARAMETER Neu
  Ohne Zwischenspeicher neu bauen.

.PARAMETER Stopp
  Den Verbund anhalten.

.EXAMPLE
  .\scripts\start.ps1
.EXAMPLE
  .\scripts\start.ps1 -Klein
.EXAMPLE
  .\scripts\start.ps1 -Stopp
#>
[CmdletBinding()]
param(
    [switch]$Klein,
    [switch]$MitOllama,
    [switch]$Neu,
    [switch]$Stopp
)

$ErrorActionPreference = 'Stop'

# In das Projektverzeichnis wechseln, egal von wo das Skript gerufen wurde.
$Wurzel = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Wurzel

$Farbe = (-not $env:NO_COLOR)

function Sagen   { param([string]$T) Write-Host $T }
function Gut     { param([string]$T) if ($Farbe) { Write-Host "[ok] $T" -ForegroundColor Green } else { Write-Host "[ok] $T" } }
function Warnen  { param([string]$T) if ($Farbe) { Write-Host "[!]  $T" -ForegroundColor Yellow } else { Write-Host "[!]  $T" } }
function Abbruch {
    param([string]$T)
    if ($Farbe) { Write-Host "[x]  $T" -ForegroundColor Red } else { Write-Host "[x]  $T" }
    exit 1
}

if ($Farbe) { Write-Host "Konformitaetshelfer" -ForegroundColor White } else { Sagen "Konformitaetshelfer" }
Sagen ""

# ------------------------------------------------------------- 1. Docker da?

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Abbruch "Docker ist nicht installiert. Docker Desktop holen unter https://docs.docker.com/get-docker/"
}

# "docker info" schlaegt fehl, wenn der Dienst nicht laeuft. Die Ausgabe wird
# verworfen: gebraucht wird nur, ob es geklappt hat.
docker info 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Abbruch "Docker ist installiert, laeuft aber nicht. Docker Desktop starten und warten, bis das Walsymbol ruhig steht."
}

$Fassung = (docker version --format '{{.Server.Version}}' 2>$null)
if (-not $Fassung) { $Fassung = "Fassung unbekannt" }
Gut "Docker laeuft ($Fassung)"

docker compose version 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) {
    Abbruch "docker compose fehlt. Es gehoert zu Docker Desktop dazu; sonst nachinstallieren: https://docs.docker.com/compose/install/"
}

# ------------------------------------------------------------ 2. Anhalten?

if ($Stopp) {
    docker compose down
    Gut "Angehalten."
    exit 0
}

# ----------------------------------------------------- 3. Voraussetzungen

$Korpus = Join-Path $Wurzel 'daten\aufbereitet\korpus.jsonl'
if (-not (Test-Path $Korpus)) {
    Abbruch "Die Rechtstexte fehlen: daten\aufbereitet\korpus.jsonl`n     Erst bauen:  python -m helfer.korpus.bauen"
}
$Zeilen = (Get-Content $Korpus -ReadCount 0).Count
Gut "Rechtstexte da: $Zeilen Rechtsstellen"

if (Test-Path (Join-Path $Wurzel 'daten\aufbereitet\suchbestand.bestand.pkl')) {
    Gut "Suchbestand da - der Dienst muss beim Start nicht rechnen"
} else {
    Warnen "Der Suchbestand fehlt. Der Dienst baut ihn beim Start selbst; ohne das grosse Modell bedeutet das schlechtere Fundstellen.`n     Besser vorher:  python -m scripts.bestand_bauen"
}

if (-not (Test-Path (Join-Path $Wurzel '.env'))) {
    Warnen "Keine .env vorhanden. Es gelten die Vorgaben.`n     Fuer ein Sprachmodell:  copy .env.example .env  und Schluessel eintragen."
}

# ------------------------------------------------------------- 4. Bauen

if ($Klein) {
    $env:MIT_SUCHMODELL = "0"
    if (-not $env:HELFER_SPEICHER) { $env:HELFER_SPEICHER = "1g" }
    Warnen "Kleines Abbild: ohne das Modell bge-m3. Die Suche vergleicht dann nur Woerter, nicht Bedeutung."
} else {
    $env:MIT_SUCHMODELL = "1"
    Sagen ""
    Sagen "Es wird gebaut. Beim ersten Mal dauert das lange: das Einbettungsmodell"
    Sagen "ist rund 2,3 Gigabyte gross und wird mit ins Abbild gelegt, damit der"
    Sagen "Container spaeter ohne Netz arbeiten kann."
}

Sagen ""
$BauArgumente = @('compose', 'build')
if ($Neu) { $BauArgumente += '--no-cache' }
& docker @BauArgumente
if ($LASTEXITCODE -ne 0) {
    Abbruch "Der Bau ist fehlgeschlagen. Die letzte Meldung oben sagt, woran es lag. Haeufigste Ursachen: kein Netz beim Holen der Pakete, oder zu wenig Platz (fuer das grosse Abbild sind rund 8 Gigabyte frei noetig - nachsehen mit: docker system df)."
}
Gut "Abbild gebaut"

# ------------------------------------------------------------ 5. Starten

$HochArgumente = @('compose')
if ($MitOllama) { $HochArgumente += @('--profile', 'ollama') }
$HochArgumente += @('up', '--detach')
& docker @HochArgumente
if ($LASTEXITCODE -ne 0) {
    Abbruch "Der Start ist fehlgeschlagen. Protokoll ansehen mit: docker compose logs helfer"
}

# --------------------------------------------------------- 6. Warten

$Port = if ($env:HELFER_PORT) { $env:HELFER_PORT } else { "8000" }
$Adresse = "http://127.0.0.1:$Port"

Sagen ""
Write-Host "Der Dienst faehrt hoch " -NoNewline
$Bereit = $false
$Zustand = $null
for ($i = 0; $i -lt 90; $i++) {
    try {
        $Zustand = Invoke-RestMethod -Uri "$Adresse/gesundheit" -TimeoutSec 2 -ErrorAction Stop
        $Bereit = $true
        break
    } catch {
        Write-Host "." -NoNewline
        Start-Sleep -Seconds 2
    }
}
Sagen ""

if (-not $Bereit) {
    Warnen "Der Dienst hat in drei Minuten nicht geantwortet. Das kann am grossen Modell liegen.`n     Protokoll ansehen mit:  docker compose logs --follow helfer"
    exit 1
}

Sagen ""
Gut "Der Konformitaetshelfer laeuft."
Sagen ""
Sagen "   Oberflaeche:       $Adresse/"
Sagen "   Zustandsbericht:   $Adresse/gesundheit"
Sagen "   Schnittstelle:     $Adresse/openapi.json"
Sagen ""
Sagen ("   Rechtsstellen:     " + $Zustand.einheiten)
Sagen ("   Suche mit:         " + $Zustand.einbettungsmodell)
Sagen ("   Formulierung:      " + $Zustand.sprachmodell)
foreach ($w in $Zustand.warnungen) { Sagen ("   Hinweis:           " + $w) }
Sagen ""
Sagen "Anhalten mit:  .\scripts\start.ps1 -Stopp"
