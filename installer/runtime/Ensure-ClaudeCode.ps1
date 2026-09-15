# Installiert die native Claude-Code-CLI, falls sie auf diesem Rechner fehlt.
# Idempotent, ohne Admin. Ein Fehlschlag darf den App-Start nicht verhindern.
[CmdletBinding()]
param(
    [string]$HomeDir = "",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

if (-not $HomeDir) {
    $HomeDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$NativeUrl = "https://claude.ai/install.ps1"
$Names = @("claude.exe", "claude.cmd", "claude.bat", "claude")

function Write-EnsureLog {
    param([string]$Message)
    $logDir = Join-Path $HomeDir "logs"
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
    $line = "{0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path (Join-Path $logDir "claude-code.log") -Value $line -Encoding UTF8
    if (-not $Quiet) { Write-Host $Message }
}

function Get-ClaudeCandidateDirs {
    $dirs = @(
        (Join-Path $env:USERPROFILE ".local\bin"),
        (Join-Path $env:USERPROFILE ".claude\local"),
        (Join-Path $env:USERPROFILE "bin")
    )
    if ($env:LOCALAPPDATA) {
        $dirs += (Join-Path $env:LOCALAPPDATA "Programs\claude")
    }
    if ($env:APPDATA) {
        $dirs += (Join-Path $env:APPDATA "npm")
    }
    return $dirs
}

function Add-ClaudePath {
    $native = Join-Path $env:USERPROFILE ".local\bin"
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $pieces = @($native)
    foreach ($dir in (Get-ClaudeCandidateDirs)) {
        if ($dir -and (Test-Path $dir)) { $pieces += $dir }
    }
    if ($userPath) { $pieces += $userPath }
    if ($machinePath) { $pieces += $machinePath }
    if ($env:PATH) { $pieces += $env:PATH }
    $env:PATH = ($pieces -join ";")
}

function Find-ClaudeCli {
    if ($env:CLAUDE_CLI -and (Test-Path -LiteralPath $env:CLAUDE_CLI)) {
        return $env:CLAUDE_CLI
    }
    foreach ($dir in (Get-ClaudeCandidateDirs)) {
        foreach ($name in $Names) {
            $candidate = Join-Path $dir $name
            if (Test-Path -LiteralPath $candidate) { return $candidate }
        }
    }
    $cmd = Get-Command claude -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source) { return $cmd.Source }
    return $null
}

function Save-ClaudeRuntime {
    param([string]$CliPath)
    $runtimeFile = Join-Path $HomeDir "runtime.json"
    $runtime = $null
    if (Test-Path $runtimeFile) {
        try {
            $runtime = Get-Content $runtimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            $runtime = $null
        }
    }
    if ($runtime) {
        $runtime | Add-Member -NotePropertyName claudeCli -NotePropertyValue $CliPath -Force
        ($runtime | ConvertTo-Json) | Set-Content -Path $runtimeFile -Encoding UTF8
    }
}

Add-ClaudePath
$found = Find-ClaudeCli
if ($found) {
    Write-EnsureLog "Claude Code bereits vorhanden: $found"
    $env:CLAUDE_CLI = $found
    Save-ClaudeRuntime $found
    Write-Output $found
    exit 0
}

Write-EnsureLog "Claude Code fehlt — Native Installer wird geladen."
$logDir = Join-Path $HomeDir "logs"
New-Item -ItemType Directory -Force -Path $logDir | Out-Null
$installer = Join-Path $logDir "claude-native-install.ps1"
$installed = $false

try {
    Invoke-WebRequest -Uri $NativeUrl -OutFile $installer -UseBasicParsing
    $p = Start-Process -FilePath "powershell.exe" -ArgumentList @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $installer
    ) -Wait -PassThru -WindowStyle Hidden
    if ($p.ExitCode -eq 0) { $installed = $true }
    else { Write-EnsureLog "Native Installer Exit $($p.ExitCode)" }
} catch {
    Write-EnsureLog "Native Installer fehlgeschlagen: $($_.Exception.Message)"
}

if (-not $installed) {
    $winget = Get-Command winget -ErrorAction SilentlyContinue
    if ($winget) {
        Write-EnsureLog "Fallback: winget Anthropic.ClaudeCode"
        try {
            $w = Start-Process -FilePath "winget.exe" -ArgumentList @(
                "install", "--id", "Anthropic.ClaudeCode", "-e",
                "--accept-package-agreements", "--accept-source-agreements",
                "--disable-interactivity"
            ) -Wait -PassThru -WindowStyle Hidden
            if ($w.ExitCode -eq 0) { $installed = $true }
            else { Write-EnsureLog "winget Exit $($w.ExitCode)" }
        } catch {
            Write-EnsureLog "winget fehlgeschlagen: $($_.Exception.Message)"
        }
    }
}

Add-ClaudePath
$found = Find-ClaudeCli
if ($found) {
    Write-EnsureLog "Claude Code eingerichtet: $found"
    $env:CLAUDE_CLI = $found
    Save-ClaudeRuntime $found
    Write-Output $found
    exit 0
}

Write-EnsureLog "Claude Code ist nach dem Setup nicht auffindbar."
exit 1
