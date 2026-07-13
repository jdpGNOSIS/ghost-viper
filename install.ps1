# GHOST VIPER Installer for Windows
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

Write-Host "╔═══════════════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║           GHOST VIPER - INSTALLER v4.2.0                   ║" -ForegroundColor Green
Write-Host "║           PowerShell Deployment Script                     ║" -ForegroundColor Green
Write-Host "╚═══════════════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check Python
try {
    $py = (Get-Command python).Source
    Write-Host "[✓] Python: $py" -ForegroundColor Green
} catch {
    Write-Host "[✗] Python not found! Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Create virtual environment
$venvPath = Join-Path $Root "ghost_env"
if (-not (Test-Path $venvPath)) {
    Write-Host "[*] Creating virtual environment..." -ForegroundColor Yellow
    & python -m venv $venvPath
}
$pip = if ($IsWindows -or $env:OS) {
    Join-Path $venvPath "Scripts\pip.exe"
} else {
    Join-Path $venvPath "bin\pip"
}
$python = if ($IsWindows -or $env:OS) {
    Join-Path $venvPath "Scripts\python.exe"
} else {
    Join-Path $venvPath "bin\python"
}

Write-Host "[*] Installing dependencies..." -ForegroundColor Yellow
& $pip install requests pillow customtkinter packaging pyinstaller --quiet

Write-Host "[*] Generating resources..." -ForegroundColor Yellow
& $python "$Root\utils\icon_gen.py"

Write-Host "[*] Creating shortcuts..." -ForegroundColor Yellow
& $python -c "import sys; sys.path.insert(0, '$Root'); from utils.shortcut import create_onedrive_shortcut; from core.config import GhostConfig; create_onedrive_shortcut(GhostConfig())"

Write-Host ""
Write-Host "[+] Installation complete!" -ForegroundColor Green
Write-Host "[*] To launch: python ghost_viper.py" -ForegroundColor Cyan
Write-Host "[*] Shortcut created on your Desktop" -ForegroundColor Cyan
Write-Host ""

$launch = Read-Host "Launch GHOST VIPER now? (Y/N)"
if ($launch -eq 'Y' -or $launch -eq 'y') {
    Start-Process -FilePath $python -ArgumentList "$Root\ghost_viper.py" -WorkingDirectory $Root
}
