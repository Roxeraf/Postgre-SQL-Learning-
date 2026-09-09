#define MyAppName "plx.learnSQL"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "FlowApp Einarbeitung"

[Setup]
AppId={{8F3C1A2B-9D4E-4B71-A6C8-E1F2A3B4C5D6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={localappdata}\plx.learnSQL
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
UninstallDisplayName={#MyAppName}
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/ultra
SolidCompression=yes
WizardStyle=modern
OutputDir=..\dist
OutputBaseFilename=plx.learnSQL-Setup
SetupIconFile=flowapp.ico
UninstallDisplayIcon={app}\flowapp.ico
InfoBeforeFile=runtime\KOLLEGE.txt
CloseApplications=no
RestartIfNeededByRun=no

[Languages]
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "staging\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\Start-FlowAppLearn.bat"; WorkingDir: "{app}"; IconFilename: "{app}\flowapp.ico"; Comment: "plx.learnSQL starten"
Name: "{group}\{#MyAppName} beenden"; Filename: "{app}\Stop-FlowAppLearn.bat"; WorkingDir: "{app}"; Comment: "plx.learnSQL und Datenbank beenden"
Name: "{group}\Kurzanleitung"; Filename: "{app}\KOLLEGE.txt"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\Start-FlowAppLearn.bat"; WorkingDir: "{app}"; IconFilename: "{app}\flowapp.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\Start-FlowAppLearn.bat"; Description: "{#MyAppName} jetzt starten"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\Stop-FlowAppLearn.bat"; Flags: runhidden waituntilterminated; RunOnceId: "StopFlowAppLearn"

[UninstallDelete]
Type: filesandordirs; Name: "{app}\data"
Type: filesandordirs; Name: "{app}\logs"
Type: files; Name: "{app}\runtime.json"
