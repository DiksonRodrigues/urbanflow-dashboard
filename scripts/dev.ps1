$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $PSScriptRoot
$backendDir = Join-Path $repoRoot "backend"

$python = "C:\Users\amoza\AppData\Local\Programs\Python\Python312\python.exe"
if (-not (Test-Path $python)) {
  $python = "python"
}

$viteOut = Join-Path $repoRoot "vite.out"
$viteErr = Join-Path $repoRoot "vite.err"
$uvOut = Join-Path $backendDir "uvicorn.out"
$uvErr = Join-Path $backendDir "uvicorn.err"

# Frontend
Start-Process -FilePath "npm.cmd" -ArgumentList @("run","dev") -WorkingDirectory $repoRoot -RedirectStandardOutput $viteOut -RedirectStandardError $viteErr -NoNewWindow

# Backend
Start-Process -FilePath $python -ArgumentList @("-m","uvicorn","main:app","--port","8000") -WorkingDirectory $backendDir -RedirectStandardOutput $uvOut -RedirectStandardError $uvErr -NoNewWindow

Write-Host "Frontend: http://localhost:8080"
Write-Host "Backend:  http://localhost:8000"
