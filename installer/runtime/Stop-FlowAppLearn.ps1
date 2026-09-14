# plx.learnSQL — stoppt Lern-App und PostgreSQL.
$ErrorActionPreference = "SilentlyContinue"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$DataDir = Join-Path $Root "data"
$PgBin = Join-Path $Root "pgsql\bin"
$PgCtl = Join-Path $PgBin "pg_ctl.exe"
$env:PATH = "$PgBin;" + $env:PATH
$RuntimeFile = Join-Path $Root "runtime.json"
$AppDir = Join-Path $Root "app"
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "launcher.log"

function Write-Log {
    param([string]$Message)
    if (-not (Test-Path $LogDir)) { return }
    $line = "{0} STOP {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

Write-Log "Stop angefordert"

if (Test-Path $RuntimeFile) {
    try {
        $runtime = Get-Content $RuntimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($runtime.flaskPid) {
            Stop-Process -Id ([int]$runtime.flaskPid) -Force
            Write-Log "Flask PID $($runtime.flaskPid) beendet"
        }
    } catch { }
}

Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and ($_.CommandLine -like "*$AppDir*app.py*" -or $_.CommandLine -like "*FlowAppLearn*app.py*" -or $_.CommandLine -like "*plx.learnSQL*app.py*") } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force
        Write-Log "Prozess $($_.ProcessId) beendet"
    }

if ((Test-Path $PgCtl) -and (Test-Path $DataDir)) {
    & $PgCtl -D $DataDir stop -m fast 2>&1 | Out-Null
    Write-Log "pg_ctl stop -m fast Exit $LASTEXITCODE"
    $pidFile = Join-Path $DataDir "postmaster.pid"
    for ($i = 0; $i -lt 20; $i++) {
        if (-not (Test-Path $pidFile)) { break }
        Start-Sleep -Milliseconds 250
    }
    if (Test-Path $pidFile) {
        & $PgCtl -D $DataDir stop -m immediate 2>&1 | Out-Null
        Write-Log "pg_ctl stop -m immediate Exit $LASTEXITCODE"
        Start-Sleep -Milliseconds 400
    }
}

Get-Process -Name "postgres", "pg_ctl" -ErrorAction SilentlyContinue |
    Where-Object { $_.Path -and ($_.Path -like "$PgBin*") } |
    ForEach-Object {
        Stop-Process -Id $_.Id -Force
        Write-Log "PostgreSQL-Prozess $($_.Id) beendet"
    }

Add-Type -AssemblyName System.Windows.Forms | Out-Null
# Tray-Starter (falls noch offen) ebenfalls beenden
Get-CimInstance Win32_Process |
    Where-Object { $_.CommandLine -and $_.CommandLine -like "*Start-FlowAppLearn.ps1*" } |
    ForEach-Object {
        if ($_.ProcessId -ne $PID) {
            Stop-Process -Id $_.ProcessId -Force
        }
    }

Write-Log "Stop fertig"
exit 0
