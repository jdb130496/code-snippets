# ======================================================
# Test Script: Windows MSVC + CMake + Ninja
# ======================================================

Write-Host "`n======================================================" -ForegroundColor Cyan
Write-Host "  TEST: Windows MSVC + CMake + Ninja" -ForegroundColor Cyan
Write-Host "======================================================`n" -ForegroundColor Cyan

# Switch to Windows MSVC environment
Write-Host "Setting up Windows MSVC environment..." -ForegroundColor Yellow
use-msvc

# Create build directory
$buildDir = "build-windows-msvc"
if (Test-Path $buildDir) {
    Write-Host "Cleaning previous build directory..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force $buildDir
}
New-Item -ItemType Directory -Path $buildDir | Out-Null

# Configure with CMake (using Windows CMake)
Write-Host "`nConfiguring with CMake (Windows MSVC + Ninja)..." -ForegroundColor Yellow
Push-Location $buildDir
cmake .. -DCMAKE_BUILD_TYPE=Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nCMake configuration FAILED!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Build with Ninja
Write-Host "`nBuilding with Ninja..." -ForegroundColor Yellow
cmake --build . --config Release

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nBuild FAILED!" -ForegroundColor Red
    Pop-Location
    exit 1
}

# Find and run the test executable
# Ninja puts exe directly in build dir, VS/NMake uses Release\ subdirectory
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

Write-Host "`n✓ TEST PASSED: Windows MSVC build successful!" -ForegroundColor Green
Write-Host "  Build directory: $buildDir" -ForegroundColor Gray
Write-Host "  Executable: $buildDir\$($exePath.TrimStart('.\'))`n" -ForegroundColor Gray
