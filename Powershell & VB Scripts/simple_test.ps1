Write-Host "Testing MSYS2 UCRT64..." -ForegroundColor Cyan

$testPaths = @(
    "D:\Programs\msys64\ucrt64\bin\gcc.exe",
    "D:\Programs\msys64\ucrt64\bin\clang.exe",
    "D:\Programs\msys64\usr\bin\bash.exe"
)

foreach ($path in $testPaths) {
    if (Test-Path $path) {
        Write-Host "✓ Found: $path" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing: $path" -ForegroundColor Red
    }
}

# Test GCC if found
$gcc = "D:\Programs\msys64\ucrt64\bin\gcc.exe"
if (Test-Path $gcc) {
    Write-Host "`nGCC Version:" -ForegroundColor Yellow
    & $gcc --version | Select-Object -First 1
}
