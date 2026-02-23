# start-webapp.ps1
# Quick-start script for the MK Mobile Assistant Laravel webapp.
# Run from the repository root: .\start-webapp.ps1

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$phpExe   = "$repoRoot\php8\php.exe"
$nodeDir  = "$repoRoot\node"

# Ensure PHP and Node are on PATH for this session
$env:PATH = "$repoRoot\php8;$nodeDir;$env:PATH"
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force

Write-Host "🔧 Starting MK Mobile Assistant webapp..." -ForegroundColor Cyan
Write-Host "   PHP:  $(& $phpExe --version | Select-Object -First 1)" -ForegroundColor Gray
Write-Host "   Node: $(node --version)" -ForegroundColor Gray

Set-Location "$repoRoot\webapp"

# Run pending migrations
Write-Host "`n📦 Running migrations..." -ForegroundColor Yellow
php artisan migrate --force

Write-Host "`n🚀 Server starting at http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "   (Python MK assistant API should be running on http://localhost:8080)" -ForegroundColor Gray
Write-Host "   Press Ctrl+C to stop.`n" -ForegroundColor Gray

php artisan serve --port=8000
