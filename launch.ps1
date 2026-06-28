# Launch the Dinner Suggestion App, reachable from phones on the same Wi-Fi.
# Usage:  ./launch.ps1
$ErrorActionPreference = "Stop"

Set-Location -Path $PSScriptRoot

$wifiIp = "192.168.86.23"   # this machine's Wi-Fi IP
$port   = 8501

Write-Host ""
Write-Host "Starting Dinner Suggester..." -ForegroundColor Cyan
Write-Host "  On this computer: http://localhost:$port" -ForegroundColor Green
Write-Host "  On your phone:    http://${wifiIp}:$port  (same Wi-Fi)" -ForegroundColor Green
Write-Host ""

python -m streamlit run app.py --server.headless true --server.address 0.0.0.0 --server.port $port
