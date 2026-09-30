$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) {
  Write-Host 'First-time setup: creating a local Python environment...'
  if (Get-Command py -ErrorAction SilentlyContinue) { py -3 -m venv .venv } else { python -m venv .venv }
  if (-not (Test-Path $python)) { throw 'Python 3.10 or newer is required.' }
  Write-Host 'First-time setup: installing local dependencies...'
  & $python -m pip install -r requirements.txt
}
Start-Process 'http://127.0.0.1:8765'
Write-Host 'Voxera is running locally at http://127.0.0.1:8765'
& $python -m uvicorn app:app --host 127.0.0.1 --port 8765
