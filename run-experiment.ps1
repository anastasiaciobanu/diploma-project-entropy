New-Item -ItemType Directory -Force -Path ".\runs" | Out-Null

Write-Host "[+] Starting entro(py) experiment container..."
Write-Host "[+] noVNC will open at:"
Write-Host "    http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale"
Write-Host ""
Write-Host "[+] Experiment output will be saved in:"
Write-Host "    .\runs"
Write-Host ""

Start-Process "http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale"

docker compose run --rm --service-ports experiment run
