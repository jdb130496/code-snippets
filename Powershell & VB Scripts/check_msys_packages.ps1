# Comprehensive MSYS2 Package Check for PythonMonkey

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Checking MSYS2 UCRT64 Packages" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

$bashPath = "D:\Programs\msys64\usr\bin\bash.exe"

# Function to check if package is installed
function Check-Package {
    param([string]$Package)
    
    $result = & $bashPath -l -c "pacman -Q $Package 2>/dev/null"
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  ✓ $Package" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ✗ $Package (not installed)" -ForegroundColor Red
        return $false
    }
}

# Required packages for SpiderMonkey/PythonMonkey
$packages = @(
    "mingw-w64-ucrt-x86_64-autoconf2.13",
    "mingw-w64-ucrt-x86_64-automake",
    "mingw-w64-ucrt-x86_64-libtool",
    "mingw-w64-ucrt-x86_64-make",
    "mingw-w64-ucrt-x86_64-cmake",
    "mingw-w64-ucrt-x86_64-ninja",
    "mingw-w64-ucrt-x86_64-zlib",
    "mingw-w64-ucrt-x86_64-readline"
)

Write-Host "Checking required packages:" -ForegroundColor Yellow
$missing = @()
foreach ($pkg in $packages) {
    if (-not (Check-Package $pkg)) {
        $missing += $pkg
    }
}

Write-Host "`nSummary:" -ForegroundColor Cyan
if ($missing.Count -eq 0) {
    Write-Host "✓ All required packages are installed!" -ForegroundColor Green
} else {
    Write-Host "⚠ Missing $($missing.Count) packages:" -ForegroundColor Yellow
    $missing | ForEach-Object { Write-Host "  - $_" -ForegroundColor White }
    
    Write-Host "`nTo install missing packages, run:" -ForegroundColor Cyan
    $installCmd = "pacman -S --noconfirm " + ($missing -join " ")
    Write-Host "  & `"$bashPath`" -l -c `"$installCmd`"" -ForegroundColor Gray
}

# Check critical build tools
Write-Host "`nChecking build tools:" -ForegroundColor Yellow
$tools = @(
    "D:\Programs\msys64\ucrt64\bin\gcc.exe",
    "D:\Programs\msys64\ucrt64\bin\g++.exe",
    "D:\Programs\msys64\ucrt64\bin\make.exe",
    "D:\Programs\msys64\ucrt64\bin\cmake.exe",
    "D:\Programs\msys64\ucrt64\bin\ninja.exe"
)

foreach ($tool in $tools) {
    if (Test-Path $tool) {
        Write-Host "  ✓ $(Split-Path $tool -Leaf)" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $(Split-Path $tool -Leaf) (missing)" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
