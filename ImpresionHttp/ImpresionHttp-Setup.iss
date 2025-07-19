; Script de Inno Setup para Sistema de Impresión HTTP
[Setup]
AppName=Sistema de Impresión HTTP
AppVersion=1.0
DefaultDirName=C:\ImpresionHttp
DefaultGroupName=ImpresionHttp
OutputDir=.
OutputBaseFilename=ImpresionHttp-Setup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\app.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "dist\worker.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "templates\*"; DestDir: "{app}\templates"; Flags: ignoreversion recursesubdirs
Source: "poppler\*"; DestDir: "{app}\poppler"; Flags: ignoreversion recursesubdirs
Source: "printjobs.sqlite3"; DestDir: "{app}"; Flags: onlyifdoesntexist

[Icons]
Name: "{group}\Portal de Impresión"; Filename: "{app}\app.exe"
Name: "{group}\Worker de Impresión"; Filename: "{app}\worker.exe"
Name: "{group}\Abrir Portal Web"; Filename: "http://localhost:5000"

[Run]
Filename: "{app}\app.exe"; Description: "Iniciar Portal Web"; Flags: nowait postinstall skipifsilent
Filename: "{app}\worker.exe"; Description: "Iniciar Worker de Impresión"; Flags: nowait postinstall skipifsilent

[Code]
{ Función para agregar al PATH }
procedure AddToPath(Path: string; User: Boolean);
var
  OldPath: string;
  NewPath: string;
  Key: string;
  RootKey: Integer;
begin
  if User then begin
    RootKey := HKEY_CURRENT_USER;
    Key := 'Environment';
  end else begin
    RootKey := HKEY_LOCAL_MACHINE;
    Key := 'SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment';
  end;
  if not RegQueryStringValue(RootKey, Key, 'Path', OldPath) then
    OldPath := '';
  if Pos(';' + Path + ';', ';' + OldPath + ';') = 0 then begin
    if (OldPath = '') or (OldPath[Length(OldPath)] = ';') then
      NewPath := OldPath + Path
    else
      NewPath := OldPath + ';' + Path;
    RegWriteStringValue(RootKey, Key, 'Path', NewPath);
  end;
end;

{ Agrega poppler al PATH del usuario }
procedure CurStepChanged(CurStep: TSetupStep);
var
  Path: string;
begin
  if CurStep = ssPostInstall then begin
    Path := ExpandConstant('{app}\poppler\Library\bin');
    if not DirExists(Path) then
      Path := ExpandConstant('{app}\poppler\bin');
    AddToPath(Path, True);
  end;
end; 