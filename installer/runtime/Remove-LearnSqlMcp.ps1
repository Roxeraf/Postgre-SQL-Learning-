# Entfernt nur mcpServers.learnsql aus Claude Desktop und Claude Code.
[CmdletBinding()]
param(
    [string]$HomeDir = ""
)

$ErrorActionPreference = "Stop"
if (-not $HomeDir) {
    $HomeDir = Split-Path -Parent $MyInvocation.MyCommand.Path
}

$wrapper = Join-Path $HomeDir "Configure-LearnSqlMcp.ps1"
if (Test-Path $wrapper) {
    & $wrapper -HomeDir $HomeDir -Action uninstall -Quiet
    exit $LASTEXITCODE
}

$Python = Join-Path $HomeDir "python\python.exe"
$Script = Join-Path $HomeDir "mcp\install_mcp.py"
if ((Test-Path $Python) -and (Test-Path $Script)) {
    & $Python $Script uninstall --home $HomeDir
    exit $LASTEXITCODE
}
exit 0
