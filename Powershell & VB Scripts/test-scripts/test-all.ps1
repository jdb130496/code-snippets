# ======================================================
# Master Test Script: Test All Build Environments
# ======================================================

Write-Host "`n======================================================" -ForegroundColor Magenta
Write-Host "  TESTING ALL BUILD ENVIRONMENTS" -ForegroundColor Magenta
Write-Host "======================================================" -ForegroundColor Magenta

Write-Host "`nThis will test:" -ForegroundColor Yellow
Write-Host "  1. Windows Clang-cl + CMake + Ninja (MSVC toolchain)" -ForegroundColor White
Write-Host "  2. MSYS2 Clang + CMake + Ninja (MinGW toolchain)" -ForegroundColor White
Write-Host ""

$testsPassed = 0
$testsFailed = 0

# Test 1: Windows Clang-cl
Write-Host "`nStarting Test 1..." -ForegroundColor Cyan
try {
    & .\test_windows_clang.ps1
    if ($LASTEXITCODE -eq 0) {
        $testsPassed++
    } else {
        $testsFailed++
    }
} catch {
    Write-Host "Test 1 encountered an error: $_" -ForegroundColor Red
    $testsFailed++
}

# Test 2: MSYS2 Clang
Write-Host "`nStarting Test 2..." -ForegroundColor Cyan
try {
    & .\test_msys2_clang.ps1
    if ($LASTEXITCODE -eq 0) {
        $testsPassed++
    } else {
        $testsFailed++
    }
} catch {
    Write-Host "Test 2 encountered an error: $_" -ForegroundColor Red
    $testsFailed++
}

# Summary
Write-Host "`n======================================================" -ForegroundColor Magenta
Write-Host "  TEST SUMMARY" -ForegroundColor Magenta
Write-Host "======================================================" -ForegroundColor Magenta
Write-Host "  Tests Passed: $testsPassed" -ForegroundColor Green
Write-Host "  Tests Failed: $testsFailed" -ForegroundColor $(if ($testsFailed -eq 0) { "Green" } else { "Red" })
Write-Host "======================================================`n" -ForegroundColor Magenta

if ($testsFailed -eq 0) {
    Write-Host "✓ ALL TESTS PASSED!" -ForegroundColor Green
    Write-Host "  Your PowerShell profile is configured correctly!" -ForegroundColor Green
    Write-Host "  Windows Clang-cl and MSYS2 Clang toolchains are working!" -ForegroundColor Green
    Write-Host "`n  To test other toolchains, run:" -ForegroundColor Yellow
    Write-Host "    .\test_windows_msvc.ps1   (Windows MSVC)" -ForegroundColor White
    Write-Host "    .\test_msys2_gcc.ps1      (MSYS2 GCC)`n" -ForegroundColor White
} else {
    Write-Host "✗ SOME TESTS FAILED" -ForegroundColor Red
    Write-Host "  Please check the error messages above.`n" -ForegroundColor Red
}
