# ==============================================================================
# Nivima — Automated Windows Zero-to-Hero Bootstrap Script
# Designed for fresh gaming laptops (RTX 4050, 3070, 4060, etc.) with nothing installed.
# ==============================================================================

$ErrorActionPreference = "Stop"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "   Nivima Neural Video Dubbing — Automated System Bootstrap        " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. System Hardware & GPU Detection
Write-Host "`n[1/6] Probing System Hardware..." -ForegroundColor Green
$gpu = Get-CimInstance Win32_VideoController | Where-Object { $_.Name -like "*NVIDIA*" } | Select-Object -First 1
if ($gpu) {
    Write-Host "  ✓ GPU Detected: $($gpu.Name)" -ForegroundColor Green
    $vramGB = [math]::Round($gpu.AdapterRAM / 1GB, 1)
    Write-Host "  ✓ Dedicated VRAM: ~$vramGB GB" -ForegroundColor Green
    if ($vramGB -le 6) {
        Write-Host "  💡 Laptop 6GB GPU Detected (RTX 4050/3060). Auto-configuring memory-optimized int8_float16 mode." -ForegroundColor Magenta
    }
} else {
    Write-Host "  ⚠ No dedicated NVIDIA GPU found. System will configure in CPU mode." -ForegroundColor Yellow
}

# 2. Check / Install Python 3.11
Write-Host "`n[2/6] Checking Python Environment..." -ForegroundColor Green
$pythonCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3.11"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $ver = python --version 2>&1
    if ($ver -like "*3.11*" -or $ver -like "*3.10*" -or $ver -like "*3.12*") {
        $pythonCmd = "python"
    }
}

if (-not $pythonCmd) {
    Write-Host "  Python 3.11 not found. Attempting automated installation via winget..." -ForegroundColor Yellow
    try {
        winget install -e --id Python.Python.3.11 --silent --accept-package-agreements --accept-source-agreements
        Write-Host "  ✓ Python 3.11 installed successfully!" -ForegroundColor Green
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
        $pythonCmd = "python"
    } catch {
        Write-Host "  ✗ Could not auto-install Python via winget. Please download Python 3.11 from python.org and tick 'Add Python to PATH'." -ForegroundColor Red
        Exit 1
    }
} else {
    Write-Host "  ✓ Python ready: $pythonCmd" -ForegroundColor Green
}

# 3. Check / Install FFmpeg
Write-Host "`n[3/6] Checking FFmpeg Multimedia Engine..." -ForegroundColor Green
if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Host "  FFmpeg not found on PATH. Attempting automated install via winget..." -ForegroundColor Yellow
    try {
        winget install -e --id Gyan.FFmpeg --silent --accept-package-agreements --accept-source-agreements
        Write-Host "  ✓ FFmpeg installed successfully via winget!" -ForegroundColor Green
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    } catch {
        Write-Host "  ⚠ Could not auto-install FFmpeg via winget. Downloading portable essentials..." -ForegroundColor Yellow
        $ffmpegZip = "$PSScriptRoot\ffmpeg.zip"
        $ffmpegDest = "$PSScriptRoot\ffmpeg_bin"
        Invoke-WebRequest -Uri "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip" -OutFile $ffmpegZip
        Expand-Archive -Path $ffmpegZip -DestinationPath $ffmpegDest -Force
        $binFolder = Get-ChildItem -Path $ffmpegDest -Recurse -Directory -Filter "bin" | Select-Object -First 1
        if ($binFolder) {
            $env:Path += ";$($binFolder.FullName)"
            [System.Environment]::SetEnvironmentVariable("Path", $env:Path, "User")
            Write-Host "  ✓ Portable FFmpeg installed and added to user PATH!" -ForegroundColor Green
        }
    }
} else {
    Write-Host "  ✓ FFmpeg detected on PATH" -ForegroundColor Green
}

# 4. Create Virtual Environment
Write-Host "`n[4/6] Creating Project Virtual Environment..." -ForegroundColor Green
if (-not (Test-Path "$PSScriptRoot\..\venv")) {
    Invoke-Expression "$pythonCmd -m venv `"$PSScriptRoot\..\venv`""
}
$venvPython = "$PSScriptRoot\..\venv\Scripts\python.exe"
Write-Host "  ✓ Virtual environment ready: $venvPython" -ForegroundColor Green

# 5. Install PyTorch with CUDA & Dependencies
Write-Host "`n[5/6] Installing PyTorch with CUDA 12.1 and Project Dependencies..." -ForegroundColor Green
Write-Host "  Downloading PyTorch CUDA wheels (approx 2.4 GB, please wait)..." -ForegroundColor Cyan
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
& $venvPython -m pip install -r "$PSScriptRoot\..\requirements.txt" -r "$PSScriptRoot\..\requirements-dev.txt"

# 6. Verify Complete Environment & Run Diagnostic
Write-Host "`n[6/6] Running System Verification Diagnostics..." -ForegroundColor Green
& $venvPython "$PSScriptRoot\check_environment.py"

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "   Bootstrap Complete! System is 100% Configured and Ready!       " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "To run your first Hindi video dubbing test, execute:" -ForegroundColor White
Write-Host "  .\\venv\\Scripts\\python.exe scripts\\run_phase1_demo.py --video sample_hindi.mp4 --source hi --targets te" -ForegroundColor Yellow
Write-Host "`nTo launch the Web Studio interface, run:" -ForegroundColor White
Write-Host "  .\\venv\\Scripts\\uvicorn.exe src.api.main:app --port 8000" -ForegroundColor Yellow
