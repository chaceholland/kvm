# Mouse Jiggler Detector - PowerShell Setup & Run Script
# No pip install needed - uses built-in Python ctypes + Win32 API
#
# Usage (in PowerShell):
#   .\run_jiggler_detect.ps1
#   .\run_jiggler_detect.ps1 -Hook                    # detect software-injected events
#   .\run_jiggler_detect.ps1 -Sensitivity high
#   .\run_jiggler_detect.ps1 -Log mouse_events.csv

param(
    [switch]$Hook,
    [ValidateSet("low", "medium", "high")]
    [string]$Sensitivity = "medium",
    [int]$Duration = 300,
    [string]$Log,
    [switch]$Demo
)

Write-Host "=== Mouse Jiggler Detector (Windows) ===" -ForegroundColor Cyan
Write-Host ""

# Check for Python
$pythonCmd = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    Write-Host "Error: Python not found." -ForegroundColor Red
    Write-Host "Install Python 3 from python.org (check 'Add Python to PATH')"
    exit 1
}

# Download the script if not present
$scriptPath = Join-Path $PSScriptRoot "detect_jiggler.py"
if (-not (Test-Path $scriptPath)) {
    Write-Host "Downloading detect_jiggler.py..."
    $url = "https://raw.githubusercontent.com/chaceholland/kvm/claude/detect-mouse-jiggler-XaEl4/detect_jiggler.py"
    try {
        Invoke-WebRequest -Uri $url -OutFile $scriptPath
    } catch {
        Write-Host "Failed to download. Copy detect_jiggler.py manually to: $PSScriptRoot" -ForegroundColor Red
        exit 1
    }
    Write-Host ""
}

# Build arguments
$pyArgs = @($scriptPath, "--duration", $Duration, "--sensitivity", $Sensitivity)
if ($Hook) { $pyArgs += "--hook" }
if ($Log) { $pyArgs += @("--log", $Log) }
if ($Demo) { $pyArgs += "--demo" }

Write-Host "Starting jiggler detection (Ctrl+C to stop and see final report)..." -ForegroundColor Green
Write-Host ""
& python @pyArgs
