# Costruisce dist\CerchiaEChiedi-Setup-<versione>.exe
# Uso (dalla cartella del progetto):  .\pacchetto\costruisci.ps1 [-Versione 1.0.0]
# tkinter è escluso: non serve e i dati di Tcl contengono un file con un nome vietato su questa rete.
param([string]$Versione = "1.0.0")
$ErrorActionPreference = "Stop"
$radice = Split-Path -Parent $PSScriptRoot
Set-Location $radice
$python = Join-Path $radice ".venv\Scripts\python.exe"

$iscc = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $iscc) { throw "Inno Setup 6 non trovato: winget install JRSoftware.InnoSetup --source winget --scope user" }

Write-Host "1/4 Prove automatiche"
& $python -m pytest -q
if ($LASTEXITCODE -ne 0) { throw "Prove fallite: pacchetto non creato" }

Write-Host "2/4 Icona"
& $python pacchetto\crea_icona.py
if ($LASTEXITCODE -ne 0) { throw "Icona non creata" }

Write-Host "3/4 PyInstaller"
& $python -m PyInstaller --noconfirm --clean --windowed --onedir `
    --name CerchiaEChiedi `
    --icon (Join-Path $radice "pacchetto\icona.ico") `
    --distpath dist --workpath build\pyinstaller --specpath build `
    --collect-all uiautomation `
    --collect-submodules winrt `
    --exclude-module tkinter `
    (Join-Path $radice "avvia.pyw")
if ($LASTEXITCODE -ne 0) { throw "PyInstaller non riuscito" }

Write-Host "4/4 Inno Setup"
& $iscc "/DVersione=$Versione" pacchetto\installatore.iss
if ($LASTEXITCODE -ne 0) { throw "Inno Setup non riuscito" }

Get-Item "dist\CerchiaEChiedi-Setup-$Versione.exe" | Select-Object FullName, @{n = "MB"; e = { [math]::Round($_.Length / 1MB, 1) } }
