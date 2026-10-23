param([string]$PythonPath = "python")

$ErrorActionPreference = "Stop"

$ProjectPath = $PSScriptRoot
$LogDirectory = Join-Path $ProjectPath "logs"

if (-not (Test-Path $LogDirectory)) {
    New-Item -ItemType Directory -Path $LogDirectory | Out-Null
}

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$LogPath = Join-Path $LogDirectory "daily_crawl_$Timestamp.log"

Set-Location $ProjectPath

"============================================================" | Tee-Object -FilePath $LogPath -Append
"Daily crawl started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $LogPath -Append
"Project: $ProjectPath" | Tee-Object -FilePath $LogPath -Append
"============================================================" | Tee-Object -FilePath $LogPath -Append

& $PythonPath -u -m src.main --seller ALL --category ALL --limit 20 2>&1 |
    Tee-Object -FilePath $LogPath -Append

$ExitCode = $LASTEXITCODE

"============================================================" | Tee-Object -FilePath $LogPath -Append
"Daily crawl finished: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Tee-Object -FilePath $LogPath -Append
"Exit code: $ExitCode" | Tee-Object -FilePath $LogPath -Append
"============================================================" | Tee-Object -FilePath $LogPath -Append

exit $ExitCode
