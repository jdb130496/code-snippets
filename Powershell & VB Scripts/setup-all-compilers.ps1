# =====================================================
# Setup All Compilers Environment Script
# =====================================================
# Usage: 
#   .\setup-all-compilers.ps1
# Or dot-source it to apply to current session:
#   . .\setup-all-compilers.ps1

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Configuring All Compiler Environments" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# =====================================================
# MSVC Environment Variables
# =====================================================
$env:VSCMD_ARG_HOST_ARCH="x64"
$env:VSCMD_ARG_TGT_ARCH="x64"
$env:VCToolsVersion="14.50.35717"
$env:WindowsSDKVersion="10.0.26100.0\"
$env:VCToolsInstallDir="D:\dev\msvc\VC\Tools\MSVC\14.50.35717\"
$env:WindowsSdkBinPath="D:\dev\msvc\Windows Kits\10\bin\"
$env:WindowsSDKDir="D:\dev\msvc\Windows Kits\10"
$env:DISTUTILS_USE_SDK="1"
$env:MSSdk="1"

# =====================================================
# INCLUDE Paths (MSVC, Windows SDK, Clang, GCC)
# =====================================================
$env:INCLUDE="D:\dev\msvc\VC\Tools\MSVC\14.50.35717\include;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\ucrt;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\shared;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\um;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\winrt;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\cppwinrt;D:\Programs\clang\include;D:\Programs\msys64\ucrt64\include"

# =====================================================
# LIB Paths (MSVC, Windows SDK, Clang, GCC)
# =====================================================
$env:LIB="D:\dev\msvc\VC\Tools\MSVC\14.50.35717\lib\x64;D:\dev\msvc\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64;D:\dev\msvc\Windows Kits\10\Lib\10.0.26100.0\um\x64;D:\Programs\clang\lib;D:\Programs\msys64\ucrt64\lib"

# =====================================================
# PATH (All compiler bin directories)
# =====================================================
$env:PATH="D:\Programs\msys64\ucrt64\bin;D:\Programs\clang\bin;D:\dev\msvc\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64;D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64;D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64\ucrt;$env:PATH"

Write-Host "`n✓ MSVC environment configured" -ForegroundColor Green
Write-Host "✓ Clang (portable) environment configured" -ForegroundColor Green
Write-Host "✓ GCC/Clang (MSYS2 UCRT64) environment configured" -ForegroundColor Green

# =====================================================
# Verify Compilers
# =====================================================
Write-Host "`nVerifying compilers..." -ForegroundColor Yellow

$compilers = @{
    "MSVC (cl)" = "cl"
    "Clang (portable)" = "clang"
    "GCC (MSYS2)" = "gcc"
}

Write-Host ""
foreach ($name in $compilers.Keys) {
    $cmd = $compilers[$name]
    try {
        if ($cmd -eq "cl") {
            # Special handling for cl.exe which outputs to stderr
            $output = & $cmd 2>&1 | Out-String
            if ($output -match "Microsoft") {
                Write-Host "  ✓ $name : " -NoNewline -ForegroundColor Green
                $version = ($output -split "`n")[0].Trim()
                Write-Host "$version" -ForegroundColor Gray
            } else {
                Write-Host "  ✗ $name not found" -ForegroundColor Red
            }
        } else {
            $version = & $cmd --version 2>&1 | Select-Object -First 1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✓ $name : " -NoNewline -ForegroundColor Green
                Write-Host "$version" -ForegroundColor Gray
            } else {
                Write-Host "  ✗ $name not found" -ForegroundColor Red
            }
        }
    } catch {
        Write-Host "  ✗ $name not found" -ForegroundColor Red
    }
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  All Compiler Environments Ready!" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Available compilers:" -ForegroundColor Yellow
Write-Host "  cl       - MSVC Compiler" -ForegroundColor White
Write-Host "  clang    - Clang Compiler (portable or MSYS2)" -ForegroundColor White
Write-Host "  gcc      - GCC Compiler (MSYS2 UCRT64)" -ForegroundColor White
Write-Host "  g++      - G++ Compiler (MSYS2 UCRT64)" -ForegroundColor White
Write-Host "  clang++  - Clang++ Compiler" -ForegroundColor White
Write-Host "  ml64     - Microsoft MASM Assembler" -ForegroundColor White
Write-Host ""
