; =====================================================================
; Remodax - Inno Setup Script
; Generates: dist\Installer\Remodax_Setup.exe
; Target OS: Windows 10 & 11 (64-bit)
; =====================================================================

#define MyAppName "Remodax"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "RemodaxCorp"
#define MyAppURL "https://github.com/dasmo100/remodax"
#define MyAppExeName "Remodax.exe"
#define MyAppSourceDir "..\dist\Remodax"
#define MyAppIcon "..\assets\icons\app_icon.ico"
#define MyAppOutputDir "..\dist\Installer"

[Setup]
; Unique application GUID
AppId={{D1A3F5B8-9A78-43C6-9D11-4775B83E1A92}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Destination directory & user selection
DefaultDirName={autopf}\{#MyAppName}
DisableDirPage=no
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Architecture & Platform Constraints
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0

; Installer Branding & Output
OutputDir={#MyAppOutputDir}
OutputBaseFilename=Remodax_Setup
SetupIconFile={#MyAppIcon}
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
WizardStyle=modern

; Compression
Compression=lzma2/ultra64
SolidCompression=yes

; Privileges: allows non-admin install to user local programs or admin install to Program Files
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

; Clean update / installation behavior
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
; All files from the PyInstaller onedir distribution
Source: "{#MyAppSourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; Start Menu Shortcut
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app_icon.ico"; Comment: "Asistente Inteligente de Entrevistas y RAG Documental"
; Desktop Shortcut
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\assets\icons\app_icon.ico"; Tasks: desktopicon; Comment: "Asistente Inteligente de Entrevistas y RAG Documental"

[Run]
; Option to launch application immediately after setup finishes
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up any temp or cached files created inside the app directory
Type: filesandordirs; Name: "{app}\__pycache__"
