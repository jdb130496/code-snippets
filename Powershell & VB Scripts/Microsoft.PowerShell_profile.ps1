# =====================================================
# MSVC Environment Setup
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
# PATH Setup (Order matters: MSYS64 -> Clang -> MSVC)
# =====================================================
$compilerPaths = @(
    "D:\Programs\msys64\ucrt64\bin"
    "D:\Programs\msys64\usr\bin"
    "D:\Programs\clang\bin"
    "D:\dev\msvc\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64"
    "D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64"
    "D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64\ucrt"
)

foreach ($path in $compilerPaths) {
    if (Test-Path $path) {
        if ($env:PATH -notlike "*$path*") {
            $env:PATH = "$path;$env:PATH"
        }
    }
}

# =====================================================
# Compiler Aliases
# =====================================================
# Alias for Windows Clang (portable version)
if (Test-Path "D:\Programs\clang\bin\clang.exe") {
    Set-Alias -Name clang-win -Value "D:\Programs\clang\bin\clang.exe"
    Set-Alias -Name clang++-win -Value "D:\Programs\clang\bin\clang++.exe"
}

# Alias for MSYS2 Clang
if (Test-Path "D:\Programs\msys64\ucrt64\bin\clang.exe") {
    Set-Alias -Name clang-msys -Value "D:\Programs\msys64\ucrt64\bin\clang.exe"
    Set-Alias -Name clang++-msys -Value "D:\Programs\msys64\ucrt64\bin\clang++.exe"
}

# =====================================================
# Rust/Cargo Functions
# =====================================================
function Update-Cargo {
    $customPackages = @{
        'ripgrep' = @{
            flags = '-C target-cpu=native'
            features = '--all-features'
        }
    }
    
    Write-Host "Checking cargo-binstall..." -ForegroundColor Cyan
    cargo install cargo-binstall
    
    Write-Host "`nUpdating custom-compiled packages..." -ForegroundColor Cyan
    foreach ($pkg in $customPackages.Keys) {
        Write-Host "  Updating $pkg with custom flags..." -ForegroundColor Yellow
        $env:RUSTFLAGS = $customPackages[$pkg].flags
        $featuresArg = $customPackages[$pkg].features
        Invoke-Expression "cargo install $pkg $featuresArg"
        Remove-Item Env:\RUSTFLAGS -ErrorAction SilentlyContinue
    }
    
    Write-Host "`nUpdating remaining cargo packages..." -ForegroundColor Cyan
    $excludeArgs = $customPackages.Keys | ForEach-Object { "--skip $_" }
    cargo install-update -a @excludeArgs
    
    Write-Host "`nAll updates complete!" -ForegroundColor Green
}

# =====================================================
# Compiler Setup Functions (Optional Manual Setup)
# =====================================================
function Setup-MSVC {
    Write-Host "MSVC environment already configured!" -ForegroundColor Green
}

function Setup-GCC {
    Write-Host "GCC environment already configured!" -ForegroundColor Green
}

function Setup-Clang {
    Write-Host "Clang environment already configured!" -ForegroundColor Green
}

function Setup-AllCompilers {
    Write-Host "All compiler environments already configured!" -ForegroundColor Green
}

Set-Alias -Name setupmsvc -Value Setup-MSVC
Set-Alias -Name setupgcc -Value Setup-GCC
Set-Alias -Name setupclang -Value Setup-Clang
Set-Alias -Name setupcc -Value Setup-AllCompilers

# =====================================================
# Profile Load Message
# =====================================================
Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  PowerShell Profile Loaded!" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`nAvailable custom commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo  - Update Rust/Cargo packages" -ForegroundColor White

Write-Host "`nCompiler setup commands:" -ForegroundColor Yellow
Write-Host "  setupcc       - All compilers already loaded" -ForegroundColor White
Write-Host "  setupmsvc     - MSVC already loaded" -ForegroundColor White
Write-Host "  setupgcc      - GCC already loaded" -ForegroundColor White
Write-Host "  setupclang    - Clang already loaded" -ForegroundColor White

Write-Host "`nCompiler aliases:" -ForegroundColor Yellow
if (Get-Command clang-win -ErrorAction SilentlyContinue) {
    Write-Host "  clang-win     - Windows Clang (portable)" -ForegroundColor White
    Write-Host "  clang++-win   - Windows Clang++ (portable)" -ForegroundColor White
}
if (Get-Command clang-msys -ErrorAction SilentlyContinue) {
    Write-Host "  clang-msys    - MSYS2 Clang" -ForegroundColor White
    Write-Host "  clang++-msys  - MSYS2 Clang++" -ForegroundColor White
}

Write-Host "`nAvailable build tools:" -ForegroundColor Yellow
$buildTools = @('make', 'mingw32-make', 'cmake', 'ninja', 'gcc', 'g++', 'clang', 'clang++', 'cl')
foreach ($tool in $buildTools) {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "  ✓ $tool" -ForegroundColor Green
    }
}

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host ""
