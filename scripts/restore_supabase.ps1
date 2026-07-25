param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,

    [Parameter(Mandatory = $true)]
    [string]$TargetDatabaseUrl
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $BackupFile)) {
    throw "Backup file does not exist."
}

if (-not (Get-Command pg_restore -ErrorAction SilentlyContinue)) {
    throw "pg_restore is not installed or not available in PATH."
}

Write-Host "WARNING:"
Write-Host "This will modify the target database."
Write-Host "Target: $TargetDatabaseUrl"

$confirmation = Read-Host "Type RESTORE to continue"

if ($confirmation -ne "RESTORE") {
    throw "Restore cancelled."
}

pg_restore `
    --dbname="$TargetDatabaseUrl" `
    --clean `
    --if-exists `
    --no-owner `
    --no-privileges `
    "$BackupFile"

if ($LASTEXITCODE -ne 0) {
    throw "Database restore failed."
}

Write-Host "Restore completed."