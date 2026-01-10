# build.ps1
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  SECURE BUILD - QUAN LY DOAN HOI" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Check files
Write-Host "Step 1: Checking required files..." -ForegroundColor Yellow
Write-Host ""

$files = @("app.py", "secure_config.py", "encrypt_config.py", ".env", "credentials.json", "assets/favicon.ico", "QuanLyDoanHoi.spec")
$allOk = $true

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "  [OK] $file" -ForegroundColor Green
    } else {
        Write-Host "  [MISSING] $file" -ForegroundColor Red
        $allOk = $false
    }
}

if (-not $allOk) {
    Write-Host ""
    Write-Host "ERROR: Missing files!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] All files found" -ForegroundColor Green

# Step 2: Encrypt
Write-Host ""
Write-Host "Step 2: Encrypting config files..." -ForegroundColor Yellow
Write-Host ""

python encrypt_config.py

if (-not (Test-Path ".env.encrypted")) {
    Write-Host "ERROR: .env.encrypted not created" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "credentials.json.encrypted")) {
    Write-Host "ERROR: credentials.json.encrypted not created" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Encryption successful" -ForegroundColor Green

# Step 3: Clean
Write-Host ""
Write-Host "Step 3: Cleaning old build..." -ForegroundColor Yellow
Write-Host ""

if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "  Removed build/" -ForegroundColor Green
}

if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Write-Host "  Removed dist/" -ForegroundColor Green
}

Write-Host ""
Write-Host "[OK] Clean completed" -ForegroundColor Green

# Step 4: Build
Write-Host ""
Write-Host "Step 4: Building with PyInstaller..." -ForegroundColor Yellow
Write-Host ""

pyinstaller --clean --noconfirm QuanLyDoanHoi.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Build failed!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Build successful" -ForegroundColor Green

# Step 5: Verify
Write-Host ""
Write-Host "Step 5: Verifying output..." -ForegroundColor Yellow
Write-Host ""

$exePath = "dist\QuanLyDoanHoi\QuanLyDoanHoi.exe"
$assetsPath = "dist\QuanLyDoanHoi\assets"

if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    Write-Host "  [OK] $exePath" -ForegroundColor Green
    Write-Host "  Size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
} else {
    Write-Host "  [ERROR] EXE not found" -ForegroundColor Red
    exit 1
}

# Check assets folder
if (Test-Path $assetsPath) {
    Write-Host "  [OK] assets/ folder found" -ForegroundColor Green
    
    # List assets
    $assetFiles = Get-ChildItem -Path $assetsPath
    Write-Host "  Assets:" -ForegroundColor Cyan
    foreach ($file in $assetFiles) {
        Write-Host "    - $($file.Name)" -ForegroundColor Gray
    }
} else {
    Write-Host "  [WARNING] assets/ folder not found" -ForegroundColor Yellow
    Write-Host "  Copying assets manually..." -ForegroundColor Cyan
    
    if (Test-Path "assets") {
        Copy-Item -Path "assets" -Destination $assetsPath -Recurse -Force
        Write-Host "  [OK] assets/ copied" -ForegroundColor Green
    } else {
        Write-Host "  [ERROR] assets/ folder missing in source" -ForegroundColor Red
    }
}

# Step 6: Security check
Write-Host ""
Write-Host "Step 6: Security check..." -ForegroundColor Yellow
Write-Host ""

$unsafe = @(
    "dist\QuanLyDoanHoi\.env",
    "dist\QuanLyDoanHoi\credentials.json"
)

$safe = $true
foreach ($f in $unsafe) {
    if (Test-Path $f) {
        Write-Host "  [WARNING] Unencrypted: $f" -ForegroundColor Yellow
        $safe = $false
    }
}

if ($safe) {
    Write-Host "  [OK] No unencrypted files" -ForegroundColor Green
}

# Step 7: Installer
Write-Host ""
$answer = Read-Host "Create installer? (y/n)"

if ($answer -eq 'y') {
    Write-Host ""
    Write-Host "Step 7: Creating installer..." -ForegroundColor Yellow
    
    $iscc = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    
    if (Test-Path $iscc) {
        if (Test-Path "QuanLyDoanHoi_Setup.iss") {
            & $iscc "QuanLyDoanHoi_Setup.iss"
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host ""
                Write-Host "[OK] Installer created" -ForegroundColor Green
            }
        }
    } else {
        Write-Host ""
        Write-Host "[WARNING] Inno Setup not found" -ForegroundColor Yellow
    }
}

# Done
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  BUILD COMPLETED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Output: $exePath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  1. Test: .\dist\QuanLyDoanHoi.exe" -ForegroundColor White
Write-Host "  2. Verify encrypted config works" -ForegroundColor White
Write-Host ""