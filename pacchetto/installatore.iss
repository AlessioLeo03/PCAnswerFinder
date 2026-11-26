; Installatore di PCAnswerFinder (Inno Setup 6).
; Si costruisce con pacchetto\costruisci.ps1, che prima prepara dist\PCAnswerFinder con PyInstaller.

#define Nome "PCAnswerFinder"
#define Exe "PCAnswerFinder.exe"
#ifndef Versione
  #define Versione "1.0.0"
#endif

[Setup]
AppId={{6F2B7C1E-3D4A-4E8B-9C21-5A7D0E4B8F13}
AppName={#Nome}
AppVersion={#Versione}
AppPublisher=PCAnswerFinder
AppPublisherURL=https://github.com/AlessioLeo03/PCAnswerFinder
DefaultDirName={localappdata}\Programs\PCAnswerFinder
DefaultGroupName={#Nome}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir=..\dist
OutputBaseFilename=PCAnswerFinder-Setup-{#Versione}
SetupIconFile=icona.ico
UninstallDisplayIcon={app}\{#Exe}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=force
ShowLanguageDialog=no

[Languages]
Name: "italiano"; MessagesFile: "compiler:Languages\Italian.isl"

[Tasks]
Name: "avvioautomatico"; Description: "Avvia PCAnswerFinder insieme a Windows"; GroupDescription: "Opzioni:"
Name: "desktop"; Description: "Crea un collegamento sul desktop"; GroupDescription: "Opzioni:"; Flags: unchecked

[Files]
Source: "..\dist\PCAnswerFinder\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "LEGGIMI.txt"; DestDir: "{app}"; Flags: ignoreversion isreadme

[Icons]
Name: "{autoprograms}\{#Nome}"; Filename: "{app}\{#Exe}"
Name: "{autodesktop}\{#Nome}"; Filename: "{app}\{#Exe}"; Tasks: desktop

[Registry]
; Vecchio nome del programma (Cerchia e Chiedi): via il suo avvio automatico
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "CerchiaEChiedi"; ValueType: none; Flags: deletevalue
; Stesso valore usato dalla voce "Avvia con Windows" dell'icona di notifica
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "PCAnswerFinder"; ValueData: """{app}\{#Exe}"""; Flags: uninsdeletevalue; Tasks: avvioautomatico

[Run]
Filename: "{app}\{#Exe}"; Description: "Avvia PCAnswerFinder adesso"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM {#Exe}"; Flags: runhidden; RunOnceId: "ChiudiProgramma"

[UninstallDelete]
Type: dirifempty; Name: "{app}"

[Code]
{ Versione del Microsoft Store: pacchetto registrato come Claude_<versione>_<arch>__<id> }
function ClaudeStorePresente(): Boolean;
var
  Pacchetti: TArrayOfString;
  I: Integer;
begin
  Result := False;
  if RegGetSubkeyNames(HKCU,
      'Software\Classes\Local Settings\Software\Microsoft\Windows\CurrentVersion\AppModel\Repository\Packages',
      Pacchetti) then
    for I := 0 to GetArrayLength(Pacchetti) - 1 do
      if Pos('claude_', Lowercase(Pacchetti[I])) = 1 then
      begin
        Result := True;
        Exit;
      end;
end;

function ClaudePresente(): Boolean;
begin
  Result := FileExists(ExpandConstant('{localappdata}\AnthropicClaude\claude.exe')) or ClaudeStorePresente();
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and (not ClaudePresente()) and (not WizardSilent()) then
    MsgBox('Non trovo l''app desktop di Claude su questo PC.' + #13#10 +
           'PCAnswerFinder manda le selezioni all''app di Claude: installala da https://claude.ai/download ' +
           'e accedi con il tuo account.', mbInformation, MB_OK);
end;
