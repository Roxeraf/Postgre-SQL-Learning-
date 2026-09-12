# plx.learnSQL — Startet PostgreSQL, die Lern-App und ein Tray-Symbol.
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$LogDir = Join-Path $Root "logs"
$DataDir = Join-Path $Root "data"
$AppDir = Join-Path $Root "app"
$Python = Join-Path $Root "python\python.exe"
$PgBin = Join-Path $Root "pgsql\bin"
$SqlFile = Join-Path $Root "db\init\01_schema_and_data.sql"
$InitDbPy = Join-Path $Root "init-db.py"
$env:PATH = "$PgBin;" + $env:PATH
$RuntimeFile = Join-Path $Root "runtime.json"
$MarkerFile = Join-Path $DataDir ".learnsql_initialized"
$IconFile = Join-Path $Root "flowapp.ico"
$MutexName = "Local\FlowAppLearnSingleton"

New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$LogFile = Join-Path $LogDir "launcher.log"

function Write-Log {
    param([string]$Message)
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $LogFile -Value $line -Encoding UTF8
}

function Show-Error {
    param([string]$Message)
    Write-Log "FEHLER: $Message"
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    [System.Windows.Forms.MessageBox]::Show(
        $Message,
        "plx.learnSQL",
        [System.Windows.Forms.MessageBoxButtons]::OK,
        [System.Windows.Forms.MessageBoxIcon]::Error
    ) | Out-Null
}

function Test-PortOpen {
    param([int]$Port)
    $client = New-Object System.Net.Sockets.TcpClient
    try {
        $task = $client.ConnectAsync("127.0.0.1", $Port)
        if (-not $task.Wait(400)) { return $false }
        return $client.Connected
    } catch {
        return $false
    } finally {
        $client.Close()
    }
}

function Test-PortBindable {
    param([int]$Port)
    try {
        $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::Parse("127.0.0.1"), $Port)
        $listener.Start()
        $listener.Stop()
        return $true
    } catch {
        return $false
    }
}

function Find-FreePort {
    param([int[]]$Candidates)
    foreach ($port in $Candidates) {
        if ((-not (Test-PortOpen $port)) -and (Test-PortBindable $port)) { return $port }
    }
    $listener = New-Object System.Net.Sockets.TcpListener ([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    $listener.Stop()
    return $port
}

function Read-Runtime {
    if (Test-Path $RuntimeFile) {
        return Get-Content $RuntimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    return $null
}

function Save-Runtime {
    param($Object)
    ($Object | ConvertTo-Json) | Set-Content -Path $RuntimeFile -Encoding UTF8
}

function Test-OurApp {
    param([int]$Port)
    try {
        $resp = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/" -UseBasicParsing -TimeoutSec 2
        return ($resp.Content -match "plx\.learnSQL")
    } catch {
        return $false
    }
}

function Initialize-Database {
    param([int]$DbPort, [string]$Password)

    Write-Log "initdb auf Port $DbPort"
    $pwFile = Join-Path $LogDir "pwfile.tmp"
    Set-Content -Path $pwFile -Value $Password -Encoding ascii -NoNewline

    $initdb = Join-Path $PgBin "initdb.exe"
    $localeArgs = @(@("--no-locale"), @("--locale=en-US"), @("--locale=C"))
    $ok = $false
    $err = ""
    foreach ($locale in $localeArgs) {
        $arguments = @(
            "-D", $DataDir,
            "-U", "postgres",
            "-A", "scram-sha-256",
            "--pwfile=$pwFile",
            "-E", "UTF8"
        ) + $locale
        $p = Start-Process -FilePath $initdb -ArgumentList $arguments -Wait -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir "initdb.out") -RedirectStandardError (Join-Path $LogDir "initdb.err")
        if ($p.ExitCode -eq 0) { $ok = $true; break }
        if (Test-Path $DataDir) { Remove-Item $DataDir -Recurse -Force -ErrorAction SilentlyContinue }
        $err = ""
        if (Test-Path (Join-Path $LogDir "initdb.err")) {
            $err = Get-Content (Join-Path $LogDir "initdb.err") -Raw -ErrorAction SilentlyContinue
        }
        Write-Log "initdb $($locale -join ' ') Exit $($p.ExitCode): $err"
    }
    Remove-Item $pwFile -Force -ErrorAction SilentlyContinue
    if (-not $ok) {
        throw "initdb fehlgeschlagen. $err"
    }
}

function Set-PostgresListen {
    param([int]$DbPort)
    $override = Join-Path $DataDir "flowapp.conf"
    Set-Content -Path $override -Value "listen_addresses = '127.0.0.1'`nport = $DbPort`n" -Encoding ascii
    $conf = Join-Path $DataDir "postgresql.conf"
    $raw = Get-Content $conf -Raw -ErrorAction SilentlyContinue
    if ($raw -notmatch "include = 'flowapp.conf'") {
        Add-Content -Path $conf -Value "`ninclude = 'flowapp.conf'`n" -Encoding ascii
    }
}

function Start-Postgres {
    param([int]$DbPort)

    $pgCtl = Join-Path $PgBin "pg_ctl.exe"
    $log = Join-Path $LogDir "postgres.log"
    Set-PostgresListen -DbPort $DbPort
    Write-Log "pg_ctl start port $DbPort"
    $env:PGPORT = "$DbPort"
    $env:PGHOST = "127.0.0.1"
    Start-Process -FilePath $pgCtl -ArgumentList @("-D", $DataDir, "-l", $log, "-W", "start") -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir "pg_ctl_start.out") -RedirectStandardError (Join-Path $LogDir "pg_ctl_start.err") | Out-Null
    Write-Log "pg_ctl start ausgeloest, warte auf Port $DbPort"

    for ($i = 0; $i -lt 50; $i++) {
        if (Test-PortOpen $DbPort) {
            Write-Log "PostgreSQL akzeptiert Verbindungen auf $DbPort"
            return
        }
        Start-Sleep -Milliseconds 400
    }
    throw "PostgreSQL antwortet nicht auf Port $DbPort."
}

function Import-Schema {
    param([int]$DbPort, [string]$Password)

    Write-Log "Schema importieren mit init-db.py"
    $env:PGPASSWORD = $Password
    $env:DB_PORT = "$DbPort"
    $env:DB_NAME = "learnsql"
    $output = & $Python $InitDbPy $SqlFile 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) {
        throw "SQL-Import fehlgeschlagen. $output"
    }
    Set-Content -Path $MarkerFile -Value (Get-Date -Format "o") -Encoding UTF8
}

function Start-Flask {
    param([int]$DbPort, [int]$AppPort, [string]$Password)

    $env:DB_HOST = "127.0.0.1"
    $env:DB_PORT = "$DbPort"
    $env:DB_NAME = "learnsql"
    $env:DB_USER = "lernuser"
    $env:DB_PASSWORD = "lernuser"
    $env:DB_ADMIN_USER = "postgres"
    $env:DB_ADMIN_PASSWORD = $Password
    $env:SQL_INIT_PATH = $SqlFile
    $env:LEARN_SQL_HOME = $Root
    $env:WORKSHOP_DIR = Join-Path $Root "workshop"
    $env:FLASK_DEBUG = "0"
    $env:APP_HOST = "127.0.0.1"
    $env:APP_PORT = "$AppPort"
    $env:PYTHONUNBUFFERED = "1"
    $env:PGPASSWORD = $Password

    $appPy = Join-Path $AppDir "app.py"
    $lessonMod = Join-Path $AppDir "lessons\academy_data.py"
    if (-not (Test-Path $lessonMod)) {
        throw "Lektionsdateien fehlen: $lessonMod. Bitte plx.learnSQL neu installieren."
    }
    # Absoluter Pfad, damit der Traceback nicht nach {app}\app.py (Installationswurzel) aussieht.
    # sys.path setzt app.py selbst — das eingebettete Python ignoriert PYTHONPATH und cwd.
    $flask = Start-Process -FilePath $Python -ArgumentList @($appPy) -WorkingDirectory $AppDir -PassThru -WindowStyle Hidden -RedirectStandardOutput (Join-Path $LogDir "flask.out") -RedirectStandardError (Join-Path $LogDir "flask.err")
    Write-Log "Flask PID $($flask.Id) auf Port $AppPort"

    for ($i = 0; $i -lt 40; $i++) {
        if (Test-OurApp $AppPort) { return $flask }
        if ($flask.HasExited) {
            $err = ""
            if (Test-Path (Join-Path $LogDir "flask.err")) {
                $err = Get-Content (Join-Path $LogDir "flask.err") -Raw -ErrorAction SilentlyContinue
            }
            throw "Die Lern-App ist sofort beendet. $err"
        }
        Start-Sleep -Milliseconds 400
    }
    throw "Die Lern-App antwortet nicht unter http://127.0.0.1:$AppPort"
}

function Register-LearnSqlMcp {
    $mcpSetup = Join-Path $Root "Configure-LearnSqlMcp.ps1"
    if (-not (Test-Path $mcpSetup)) { return }
    try {
        & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $mcpSetup -HomeDir $Root -Quiet
        Write-Log "MCP-Config geschrieben"
    } catch {
        Write-Log "MCP-Setup uebersprungen: $($_.Exception.Message)"
    }
}

function Stop-Stack {
    param($Runtime)
    if ($Runtime -and $Runtime.flaskPid) {
        try { Stop-Process -Id ([int]$Runtime.flaskPid) -Force -ErrorAction SilentlyContinue } catch { }
    }
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -and $_.CommandLine -like "*$AppDir*app.py*" } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

    $pgCtl = Join-Path $PgBin "pg_ctl.exe"
    if ((Test-Path $pgCtl) -and (Test-Path $DataDir)) {
        Start-Process -FilePath $pgCtl -ArgumentList @("-D", $DataDir, "stop", "-m", "fast") -Wait -WindowStyle Hidden -ErrorAction SilentlyContinue | Out-Null
    }
}

# --- already running? ----------------------------------------------
$ownsMutex = $false
$mutex = New-Object System.Threading.Mutex($false, $MutexName)
if (-not $mutex.WaitOne(0)) {
    $existing = Read-Runtime
    $port = 8080
    if ($existing) { $port = $existing.appPort }
    Start-Process "http://localhost:$port"
    $mutex.Dispose()
    exit 0
}
$ownsMutex = $true

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

try {
    Write-Log "Start in $Root"

    foreach ($needed in @($Python, (Join-Path $PgBin "pg_ctl.exe"), $SqlFile, $InitDbPy, (Join-Path $AppDir "app.py"), (Join-Path $AppDir "lessons\academy_data.py"))) {
        if (-not (Test-Path $needed)) { throw "Installationsdatei fehlt: $needed" }
    }

    # MCP unabhängig vom Flask-Start eintragen — sonst bleibt Claude leer, wenn die App abstürzt.
    Register-LearnSqlMcp

    $password = "postgres"
    $dbPort = 5432
    $existing = Read-Runtime
    $pidFile = Join-Path $DataDir "postmaster.pid"
    $postgresRunning = $false

    if (Test-Path $pidFile) {
        $pidLines = Get-Content $pidFile
        $pgPid = 0
        $pgPortFromPid = 0
        [int]::TryParse($pidLines[0], [ref]$pgPid) | Out-Null
        if ($pidLines.Count -ge 4) { [int]::TryParse(($pidLines[3] -split "\s+")[0], [ref]$pgPortFromPid) | Out-Null }
        if ($pgPid -gt 0 -and (Get-Process -Id $pgPid -ErrorAction SilentlyContinue)) {
            $postgresRunning = $true
            if ($pgPortFromPid -gt 0) { $dbPort = $pgPortFromPid }
            elseif ($existing -and $existing.dbPort) { $dbPort = [int]$existing.dbPort }
            Write-Log "PostgreSQL laeuft bereits (PID $pgPid, Port $dbPort)"
        }
    }

    if (-not $postgresRunning) {
        $dbPort = Find-FreePort -Candidates @(5432, 5433, 15432, 25432)
        if (-not (Test-Path $DataDir)) {
            $splash = New-Object System.Windows.Forms.Form
            $splash.Text = "plx.learnSQL"
            $splash.Width = 420
            $splash.Height = 140
            $splash.StartPosition = "CenterScreen"
            $splash.FormBorderStyle = "FixedDialog"
            $splash.MaximizeBox = $false
            $splash.MinimizeBox = $false
            $splash.TopMost = $true
            $label = New-Object System.Windows.Forms.Label
            $label.Text = "Einrichtung beim ersten Start...`nPostgreSQL und Lern-Datenbank werden vorbereitet."
            $label.Dock = "Fill"
            $label.TextAlign = "MiddleCenter"
            $splash.Controls.Add($label)
            $splash.Show()
            $splash.Refresh()
            try {
                Initialize-Database -DbPort $dbPort -Password $password
            } finally {
                $splash.Close()
            }
        }
        Start-Postgres -DbPort $dbPort
        if (-not (Test-Path $MarkerFile)) {
            Import-Schema -DbPort $dbPort -Password $password
        }
    }

    $flaskProc = $null
    $appPort = $null
    if ($existing -and $existing.flaskPid -and $existing.appPort) {
        $oldFlask = Get-Process -Id ([int]$existing.flaskPid) -ErrorAction SilentlyContinue
        if ($oldFlask -and (Test-OurApp ([int]$existing.appPort))) {
            $appPort = [int]$existing.appPort
            Write-Log "App laeuft bereits auf $appPort (PID $($existing.flaskPid))"
        }
    }
    if (-not $appPort) {
        $appPort = Find-FreePort -Candidates @(8080, 8081, 8090)
        $flaskProc = Start-Flask -DbPort $dbPort -AppPort $appPort -Password $password
    }

    $runtime = [pscustomobject]@{
        dbPort   = $dbPort
        appPort  = $appPort
        flaskPid = $(if ($flaskProc) { $flaskProc.Id } else { $null })
    }
    Save-Runtime $runtime
    Write-Log "Bereit: App=$appPort DB=$dbPort"

    New-Item -ItemType Directory -Force -Path (Join-Path $Root "workshop") | Out-Null
    Register-LearnSqlMcp

    Start-Process "http://localhost:$appPort"

    $notify = New-Object System.Windows.Forms.NotifyIcon
    if (Test-Path $IconFile) {
        $notify.Icon = New-Object System.Drawing.Icon($IconFile)
    } else {
        $notify.Icon = [System.Drawing.SystemIcons]::Application
    }
    $notify.Visible = $true
    $notify.Text = "plx.learnSQL"
    $notify.BalloonTipTitle = "plx.learnSQL"
    $notify.BalloonTipText = "Lern-App laeuft unter http://localhost:$appPort"
    $notify.ShowBalloonTip(4000)

    $menu = New-Object System.Windows.Forms.ContextMenuStrip
    $openItem = $menu.Items.Add("Lern-App oeffnen")
    [void]$menu.Items.Add("-")
    $exitItem = $menu.Items.Add("Beenden")
    $notify.ContextMenuStrip = $menu

    $appContext = New-Object System.Windows.Forms.ApplicationContext

    $openItem.add_Click({ Start-Process "http://localhost:$appPort" })
    $notify.add_DoubleClick({ Start-Process "http://localhost:$appPort" })
    $exitItem.add_Click({
        Write-Log "Beenden ueber Tray"
        $notify.Visible = $false
        Stop-Stack $runtime
        $appContext.ExitThread()
    })

    [System.Windows.Forms.Application]::Run($appContext)
    $notify.Dispose()
} catch {
    Show-Error ("plx.learnSQL konnte nicht gestartet werden:`n`n" + $_.Exception.Message + "`n`nDetails: " + $LogFile)
    try { Stop-Stack (Read-Runtime) } catch { }
    exit 1
} finally {
    if ($ownsMutex -and $mutex) {
        $mutex.ReleaseMutex() | Out-Null
        $mutex.Dispose()
    }
}
