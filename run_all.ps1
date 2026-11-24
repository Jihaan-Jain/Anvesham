# Hinglish Card Assistant - Windows PowerShell Runner
$ErrorActionPreference = 'Stop'

Write-Host '============================================================' -ForegroundColor Cyan
Write-Host '  Hinglish Card Assistant — Starting Demo on Windows' -ForegroundColor Cyan
Write-Host '============================================================' -ForegroundColor Cyan

# 1. Check Python
try {
    $pyVer = & python --version 2>&1
    Write-Host ('[OK] Python detected: ' + $pyVer) -ForegroundColor Green
} catch {
    Write-Host '[ERROR] Python not found in PATH. Please install Python 3.11+.' -ForegroundColor Red
    exit 1
}

# 2. Check or create .env
$envFile = Join-Path $PSScriptRoot '.env'
$envExample = Join-Path $PSScriptRoot '.env.example'

if (-not (Test-Path $envFile)) {
    if (Test-Path $envExample) {
        Copy-Item -Path $envExample -Destination $envFile
        Write-Host '[INFO] Created .env from .env.example' -ForegroundColor Yellow
    }
}

if (Test-Path $envFile) {
    $lines = Get-Content $envFile
    foreach ($line in $lines) {
        $t = $line.Trim()
        if ($t.Length -gt 0 -and -not $t.StartsWith('#') -and $t.Contains('=')) {
            $eqIdx = $t.IndexOf('=')
            $name = $t.Substring(0, $eqIdx).Trim()
            $val = $t.Substring($eqIdx + 1).Trim()
            if ($name.Length -gt 0) {
                [System.Environment]::SetEnvironmentVariable($name, $val, 'Process')
            }
        }
    }
}

$intentMode = [System.Environment]::GetEnvironmentVariable('INTENT_MODE')
if (-not $intentMode) { $intentMode = 'mock' }

$llmProvider = [System.Environment]::GetEnvironmentVariable('LLM_PROVIDER')
if (-not $llmProvider) { $llmProvider = 'mock' }

Write-Host ('[CONFIG] Intent Mode   : ' + $intentMode) -ForegroundColor White
Write-Host ('[CONFIG] LLM Provider  : ' + $llmProvider) -ForegroundColor White

# 3. Model Service (Port 8000)
if ($intentMode -eq 'service') {
    $weightsDir = Join-Path $PSScriptRoot 'model_service\muril_intent'
    if (-not (Test-Path $weightsDir)) {
        Write-Host '[WARNING] INTENT_MODE=service but weights directory not found.' -ForegroundColor Yellow
        Write-Host '          Using INTENT_MODE=mock for now.' -ForegroundColor Yellow
        [System.Environment]::SetEnvironmentVariable('INTENT_MODE', 'mock', 'Process')
    } else {
        Write-Host '[START] Launching MuRIL Intent Classifier on port 8000...' -ForegroundColor Green
        Start-Process powershell -ArgumentList '-NoExit', '-Command', "cd '$PSScriptRoot\model_service'; python -m uvicorn serve:app --host 0.0.0.0 --port 8000"
        Start-Sleep -Seconds 3
    }
} else {
    Write-Host '[INFO] Running with INTENT_MODE=mock (offline mock engine active).' -ForegroundColor Cyan
}

# 4. Open Browser
Start-Process powershell -ArgumentList '-Command', "Start-Sleep -Seconds 2; Start-Process 'http://localhost:8100'"

# 5. Check if uvicorn is installed, otherwise fall back to pure standard library server
$hasUvicorn = $false
try {
    $test = & python -c 'import uvicorn, fastapi; print("ok")' 2>&1
    if ($test -like '*ok*') { $hasUvicorn = $true }
} catch {
    $hasUvicorn = $false
}

if ($hasUvicorn) {
    Write-Host '[START] Starting FastAPI/Uvicorn on http://localhost:8100 ...' -ForegroundColor Green
    python -m uvicorn app.main:app --host 127.0.0.1 --port 8100 --reload
} else {
    Write-Host '[INFO] Uvicorn/FastAPI not found in Python environment.' -ForegroundColor Yellow
    Write-Host '[START] Launching zero-dependency built-in server on http://localhost:8100 ...' -ForegroundColor Green
    python app/server.py
}
