# Entfernt Laufzeitordner, die Inno sonst stehen lässt:
# PostgreSQL-data, logs, workshop, __pycache__, runtime.json.
[CmdletBinding()]
param(
    [string]$HomeDir = ""
)

$ErrorActionPreference = "SilentlyContinue"
if (-not $HomeDir) {
    $HomeDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$DataDir = Join-Path $HomeDir "data"
$PgBin = Join-Path $HomeDir "pgsql\bin"
$PgCtl = Join-Path $PgBin "pg_ctl.exe"
$env:PATH = "$PgBin;" + $env:PATH

if ((Test-Path $PgCtl) -and (Test-Path $DataDir)) {
    & $PgCtl -D $DataDir stop -m immediate 2>&1 | Out-Null
    Start-Sleep -Milliseconds 400
}

Get-Process -Name "postgres", "pg_ctl" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and ($_.Path -like "$PgBin*") } |
    ForEach-Object { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue }

function Remove-TreeRetry {
    param([string]$Path, [int]$Tries = 10)
    if (-not $Path) { return }
    for ($i = 0; $i -lt $Tries; $i++) {
        if (-not (Test-Path -LiteralPath $Path)) { return }
        Get-ChildItem -LiteralPath $Path -Force -Recurse -ErrorAction SilentlyContinue |
            ForEach-Object {
                try { $_.Attributes = "Normal" } catch { }
            }
        try {
            Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
        } catch {
            Start-Sleep -Milliseconds 350
        }
    }
}

Remove-TreeRetry $DataDir
Remove-TreeRetry (Join-Path $HomeDir "logs")
Remove-TreeRetry (Join-Path $HomeDir "workshop")
Remove-Item -LiteralPath (Join-Path $HomeDir "runtime.json") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $HomeDir "mcp-status.json") -Force -ErrorAction SilentlyContinue

Get-ChildItem -LiteralPath $HomeDir -Recurse -Force -Directory -Filter "__pycache__" -ErrorAction SilentlyContinue |
    Sort-Object { $_.FullName.Length } -Descending |
    ForEach-Object { Remove-TreeRetry $_.FullName -Tries 4 }

Get-ChildItem -LiteralPath $HomeDir -Recurse -Force -File -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in ".pyc", ".pyo" } |
    Remove-Item -Force -ErrorAction SilentlyContinue

exit 0
