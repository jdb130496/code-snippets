# ======================================================
# Test Script: MSYS2 GCC + CMake + Ninja
# ======================================================

Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host "  TEST: MSYS2 GCC + CMake + Ninja" -ForegroundColor Cyan
Write-Host "======================================================`n" -ForegroundColor Cyan

# Switch to MSYS2 GCC environment
Write-Host "Setting up MSYS2 GCC environment..." -ForegroundColor Yellow
use-gcc

# Create build directory
$buildDir = "build-msys2-gcc"
if (Test-Path $buildDir) {
    Write-Host "Cleaning previous build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $buildDir
}
New-Item -ItemType Directory -Path $buildDir | Out-Null

# Configure with CMake (using MSYS2 CMake)
Write-Host "`nConfiguring with CMake (MSYS2 GCC + Ninja)..." -ForegroundColor Yellow
Push-Location $buildDir
cmake-msys .. -DCMAKE_BUILD_TYPE=Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nCMake configuration FAILED!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Build with Ninja
Write-Host "`nBuilding with Ninja..." -ForegroundColor Yellow
cmake-msys --build . --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nBuild FAILED!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Find and run the test executable
Write-Host "`nRunning test executable..." -ForegroundColor Yellow
$exePath = $null
if (Test-Path ".\test_build.exe") {
    $exePath = ".\test_build.exe"
} elseif (Test-Path ".\Release\test_build.exe") {
    $exePath = ".\Release\test_build.exe"
} else {
    Write-Host "`nERROR: Could not find test_build.exe!" -ForegroundColor Red
    Pop-Location
    exit 1
}

Write-Host "========================================" -ForegroundColor Green
& $exePath
Write-Host "========================================" -ForegroundColor Green

Pop-Location

Write-Host "`n✓ TEST PASSED: MSYS2 GCC build successful!" -ForegroundColor Green
Write-Host "  Build directory: $buildDir" -ForegroundColor Gray
Write-Host "  Executable: $buildDir\$($exePath.TrimStart('.\'))`n" -ForegroundColor Gray
