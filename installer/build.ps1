#requires -Version 5.1
<#
.SYNOPSIS
  Baut plx.learnSQL-Setup.exe (Windows-Installer ohne Docker).
#>
[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$InstallerDir = $PSScriptRoot
$ProjectRoot = Split-Path -Parent $InstallerDir
$CacheDir = Join-Path $InstallerDir "cache"
$StagingDir = Join-Path $InstallerDir "staging"
$DistDir = Join-Path $ProjectRoot "dist"
$Iscc = Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"

$PythonEmbedUrl = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-embed-amd64.zip"
$PythonZipName = "python-3.12.10-embed-amd64.zip"
$GetPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$PgJarUrl = "https://repo1.maven.org/maven2/io/zonky/test/postgres/embedded-postgres-binaries-windows-amd64/16.10.0/embedded-postgres-binaries-windows-amd64-16.10.0.jar"
$PgJarName = "embedded-postgres-windows-amd64-16.10.0.jar"

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Get-CachedFile {
    param([string]$Url, [string]$FileName)
    $dest = Join-Path $CacheDir $FileName
    if (Test-Path $dest) {
        Write-Host "Cache: $FileName"
        return $dest
    }
    Write-Host "Download: $Url"
    Invoke-WebRequest -Uri $Url -OutFile $dest -UseBasicParsing
    return $dest
}

function Copy-WithBom {
    param([string]$Source, [string]$Destination)
    $text = [System.IO.File]::ReadAllText($Source)
    $enc = New-Object System.Text.UTF8Encoding $true
    [System.IO.File]::WriteAllText($Destination, $text, $enc)
}

New-Item -ItemType Directory -Force -Path $CacheDir, $DistDir | Out-Null
if (Test-Path $StagingDir) { Remove-Item $StagingDir -Recurse -Force }
New-Item -ItemType Directory -Force -Path $StagingDir | Out-Null

if (-not (Test-Path $Iscc)) {
    throw "Inno Setup Compiler nicht gefunden: $Iscc"
}

Write-Step "Python 3.12 (embeddable) vorbereiten"
$pythonZip = Get-CachedFile $PythonEmbedUrl $PythonZipName
$pythonDir = Join-Path $StagingDir "python"
Expand-Archive -Path $pythonZip -DestinationPath $pythonDir -Force
$pth = Get-ChildItem $pythonDir -Filter "python*._pth" | Select-Object -First 1
if (-not $pth) { throw "python._pth nicht gefunden" }
@(
    "python312.zip"
    "."
    "Lib\site-packages"
    "..\app"
    "import site"
) | Set-Content -Path $pth.FullName -Encoding ascii

$getPip = Get-CachedFile $GetPipUrl "get-pip.py"
$pythonExe = Join-Path $pythonDir "python.exe"
& $pythonExe $getPip --no-warn-script-location
if ($LASTEXITCODE -ne 0) { throw "get-pip.py fehlgeschlagen" }

$req = Join-Path $ProjectRoot "app\requirements.txt"
& $pythonExe -m pip install --no-warn-script-location --disable-pip-version-check -r $req
if ($LASTEXITCODE -ne 0) { throw "pip install fehlgeschlagen" }
& $pythonExe -c "import flask, psycopg2; print('python-ok', flask.__version__)"
if ($LASTEXITCODE -ne 0) { throw "Flask/psycopg2 Import fehlgeschlagen" }
Copy-Item (Join-Path $InstallerDir "runtime\sitecustomize.py") (Join-Path $pythonDir "sitecustomize.py")
Get-ChildItem $pythonDir -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

Write-Step "PostgreSQL 16 Binaries entpacken"
$pgJar = Get-CachedFile $PgJarUrl $PgJarName
$pgExtract = Join-Path $CacheDir "pgsql-extract"
if (Test-Path $pgExtract) { Remove-Item $pgExtract -Recurse -Force }
New-Item -ItemType Directory -Force -Path $pgExtract | Out-Null
& tar.exe -xf $pgJar -C $pgExtract
if ($LASTEXITCODE -ne 0) { throw "PostgreSQL-Jar konnte nicht entpackt werden" }
$txz = Get-ChildItem $pgExtract -Filter "*.txz" -Recurse | Select-Object -First 1
if (-not $txz) { $txz = Get-ChildItem $pgExtract -Filter "*.tar.xz" -Recurse | Select-Object -First 1 }
if (-not $txz) { throw "Kein PostgreSQL-Archiv (.txz) im Jar gefunden" }
$pgUnpacked = Join-Path $CacheDir "pgsql-unpacked"
if (Test-Path $pgUnpacked) { Remove-Item $pgUnpacked -Recurse -Force }
New-Item -ItemType Directory -Force -Path $pgUnpacked | Out-Null
& tar.exe -xf $txz.FullName -C $pgUnpacked
if ($LASTEXITCODE -ne 0) { throw "tar -xf $($txz.Name) fehlgeschlagen" }
$initdb = Get-ChildItem $pgUnpacked -Recurse -Filter "initdb.exe" | Select-Object -First 1
if (-not $initdb) { throw "initdb.exe nach dem Entpacken nicht gefunden" }
$pgRoot = $initdb.Directory.Parent.FullName
$stagingPg = Join-Path $StagingDir "pgsql"
New-Item -ItemType Directory -Force -Path $stagingPg | Out-Null
Copy-Item -Path (Join-Path $pgRoot "*") -Destination $stagingPg -Recurse -Force
if (-not (Test-Path (Join-Path $stagingPg "bin\pg_ctl.exe"))) {
    throw "pg_ctl.exe fehlt in staging\pgsql\bin"
}

Write-Step "App-Dateien kopieren"
$stagingApp = Join-Path $StagingDir "app"
New-Item -ItemType Directory -Force -Path $stagingApp | Out-Null
# Every top-level module, not a hand-kept list: app.py imports learn_db and
# claude_cli, and an enumerated list silently ships a package that dies with
# ModuleNotFoundError the first time a colleague starts it.
Get-ChildItem (Join-Path $ProjectRoot "app") -File -Filter "*.py" | ForEach-Object {
    Copy-Item $_.FullName $stagingApp
}
Copy-Item (Join-Path $ProjectRoot "app\requirements.txt") $stagingApp
Copy-Item (Join-Path $ProjectRoot "app\templates") (Join-Path $stagingApp "templates") -Recurse
Copy-Item (Join-Path $ProjectRoot "app\static") (Join-Path $stagingApp "static") -Recurse
Copy-Item (Join-Path $ProjectRoot "app\lessons") (Join-Path $stagingApp "lessons") -Recurse
Get-ChildItem (Join-Path $stagingApp "lessons") -Recurse -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

$stagingMcp = Join-Path $StagingDir "mcp"
New-Item -ItemType Directory -Force -Path $stagingMcp | Out-Null
foreach ($name in @("learnsql_mcp.py", "install_mcp.py", "ANLEITUNG.md")) {
    Copy-Item (Join-Path $ProjectRoot "mcp\$name") $stagingMcp
}

$stagingWorkshop = Join-Path $StagingDir "workshop"
New-Item -ItemType Directory -Force -Path $stagingWorkshop | Out-Null
Set-Content -Path (Join-Path $stagingWorkshop ".gitkeep") -Value "" -Encoding ascii

$stagingDb = Join-Path $StagingDir "db\init"
New-Item -ItemType Directory -Force -Path $stagingDb | Out-Null
Copy-Item (Join-Path $ProjectRoot "db\init\01_schema_and_data.sql") $stagingDb

Write-Step "Launcher und Icon"
$runtimeDir = Join-Path $InstallerDir "runtime"
foreach ($name in @(
    "Start-FlowAppLearn.ps1",
    "Stop-FlowAppLearn.ps1",
    "Start-FlowAppLearn.bat",
    "Stop-FlowAppLearn.bat",
    "Start-FlowAppLearn.vbs",
    "KOLLEGE.txt",
    "init-db.py",
    "Configure-LearnSqlMcp.ps1",
    "Remove-LearnSqlMcp.ps1"
)) {
    $src = Join-Path $runtimeDir $name
    $dst = Join-Path $StagingDir $name
    if ($name -like "*.ps1" -or $name -like "*.txt") { Copy-WithBom $src $dst } else { Copy-Item $src $dst }
}

& $pythonExe (Join-Path $InstallerDir "make-icon.py") (Join-Path $InstallerDir "flowapp.ico")
Copy-Item (Join-Path $InstallerDir "flowapp.ico") (Join-Path $StagingDir "flowapp.ico") -Force

Write-Step "Inno Setup kompilieren"
& $Iscc (Join-Path $InstallerDir "FlowAppLearn.iss")
if ($LASTEXITCODE -ne 0) { throw "ISCC fehlgeschlagen" }

$setup = Join-Path $DistDir "plx.learnSQL-Setup.exe"
if (-not (Test-Path $setup)) { throw "Setup.exe wurde nicht erzeugt: $setup" }
$item = Get-Item $setup
Write-Host ""
Write-Host ("Fertig: {0} ({1:N1} MB)" -f $item.FullName, ($item.Length / 1MB)) -ForegroundColor Green
Write-Host "Diese Datei kannst du deinem Kollegen schicken."
