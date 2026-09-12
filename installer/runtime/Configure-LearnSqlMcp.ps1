# Trägt das LearnSQL-MCP in Claude Desktop ein (nur Schlüssel learnsql).
[CmdletBinding()]
param(
    [string]$HomeDir = "",
    [ValidateSet("install", "uninstall")]
    [string]$Action = "install",
    [switch]$Quiet
)

$ErrorActionPreference = "Stop"
if (-not $HomeDir) {
    $HomeDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$Python = Join-Path $HomeDir "python\python.exe"
$Script = Join-Path $HomeDir "mcp\install_mcp.py"
if (-not (Test-Path $Script)) {
    if (-not $Quiet) { Write-Host "install_mcp.py fehlt: $Script" }
    exit 0
}
if (-not (Test-Path $Python)) {
    $Python = "python"
}

& $Python $Script $Action --home $HomeDir
$code = $LASTEXITCODE
if (-not $Quiet -and $Action -eq "install") {
    Write-Host "Wenn Claude Desktop offen ist: einmal komplett beenden und neu starten."
}
exit $code
