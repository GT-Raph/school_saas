param(
    [string]$OutputDirectory = "backups"
)

$ErrorActionPreference = "Stop"

if (-not $env:DIRECT_DATABASE_URL) {
    throw "DIRECT_DATABASE_URL is not configured."
}

if (-not (Get-Command pg_dump -ErrorAction SilentlyContinue)) {
    throw "pg_dump is not installed or not available in PATH."
}

New-Item `
    -ItemType Directory `
    -Force `
    -Path $OutputDirectory `
    | Out-Null

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

$outputFile = Join-Path `
    $OutputDirectory `
    "school-saas-$timestamp.backup"

Write-Host "Creating database backup..."

pg_dump `
    --dbname="$env:DIRECT_DATABASE_URL" `
    --format=custom `
    --no-owner `
    --no-privileges `
    --file="$outputFile"

if ($LASTEXITCODE -ne 0) {
    throw "Database backup failed."
}

Write-Host "Backup created:"
Write-Host $outputFile