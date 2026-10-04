; Installationsprogramm für Windows.
;
; Was der Nutzer tut: die Datei doppelklicken, auf Weiter klicken, fertig.
; Danach steht der Konformitätshelfer im Startmenü. Beim ersten Start öffnet
; sich die Bedienoberfläche im Browser.
;
; Was NICHT verlangt wird: Python, Conda, eine Befehlszeile, Verwalterrechte.
; Das Programm wird in den Benutzerordner gelegt — dafür braucht es keine
; erhöhten Rechte, und ein Rechtswerkzeug hat im Systemordner nichts verloren.

#define Name "Konformitätshelfer"
#define Fassung "1.2.4"
#define Herausgeber "Daniel Hütte"
#define Programmdatei "Konformitaetshelfer.exe"

[Setup]
AppId={{7B3A1E52-9C44-4C7E-9E2E-0D6E1A4C8F31}
AppName={#Name}
AppVersion={#Fassung}
AppPublisher={#Herausgeber}
DefaultDirName={autopf}\Konformitaetshelfer
DefaultGroupName={#Name}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Ausgabe
OutputBaseFilename=Konformitaetshelfer-Windows-Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "deutsch"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopsymbol"; Description: "Symbol auf dem Schreibtisch anlegen"; \
  GroupDescription: "Zusätzliche Aufgaben:"; Flags: unchecked

[Files]
Source: "..\dist\Konformitaetshelfer\*"; DestDir: "{app}"; \
  Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#Name}"; Filename: "{app}\{#Programmdatei}"
Name: "{autodesktop}\{#Name}"; Filename: "{app}\{#Programmdatei}"; Tasks: desktopsymbol

[Run]
; Nach der Installation gleich starten — der Nutzer soll nichts weiter tun
; müssen, als auf Fertigstellen zu klicken.
Filename: "{app}\{#Programmdatei}"; Description: "{#Name} jetzt starten"; \
  Flags: nowait postinstall skipifsilent
