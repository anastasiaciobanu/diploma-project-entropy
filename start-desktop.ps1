New-Item -ItemType Directory -Force -Path ".\runs" | Out-Null

Write-Host "[+] Starting entro(py) Docker desktop..."
Write-Host "[+] Open this URL if the browser does not open automatically:"
Write-Host "    http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale"
Write-Host ""

Start-Process "http://127.0.0.1:6080/vnc.html?autoconnect=true&resize=scale"

docker compose run --rm --service-ports experiment desktop
