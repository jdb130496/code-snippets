$MaximumHistoryCount = 10000

# =====================================================
# MSVC Setup - MUST BE FIRST IN PATH
# =====================================================
$msvcRoot = "D:\dev\msvc"
$vcToolsVersion = "14.50.35717"
$windowsSDKVersion = "10.0.26100.0"

$env:VSCMD_ARG_HOST_ARCH = "x64"
$env:VSCMD_ARG_TGT_ARCH = "x64"
$env:VCToolsVersion = $vcToolsVersion
$env:WindowsSDKVersion = "$windowsSDKVersion\"

$env:VCToolsInstallDir = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
$env:WindowsSdkBinPath = "$msvcRoot\Windows Kits\10\bin\"

# CRITICAL: Start with MSVC at the BEGINNING of PATH
$env:PATH = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\bin\Hostx64\x64;$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\x64;$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\x64\ucrt;$env:PATH"

$env:INCLUDE = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include;$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\ucrt;$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\shared;$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\um;$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\winrt;$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\cppwinrt"

$env:LIB = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\x64;$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\ucrt\x64;$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\um\x64"

# =====================================================
# Additional Tool Paths
# =====================================================
$clangRoot = "D:\Programs\clang"
$msys64Root = "D:\Programs\msys64"
$nodejsRoot = "D:\Programs\nodejs"

# Auto-detect Python 3.14
$pythonRoot = $null
$possiblePaths = @(
    "D:\Programs\Python314",
    "D:\Programs\Python\Python314",
    "C:\Program Files\Python314",
    "$env:LOCALAPPDATA\Programs\Python\Python314"
)

foreach ($path in $possiblePaths) {
    if (Test-Path "$path\python.exe") {
        $version = & "$path\python.exe" --version 2>&1
        if ($version -match "3\.14") {
            $pythonRoot = $path
            break
        }
    }
}

if (-not $pythonRoot) {
    try {
        $pyPath = & py -3.14 -c "import sys; print(sys.executable)" 2>$null
        if ($pyPath -and (Test-Path $pyPath)) {
            $pythonRoot = Split-Path -Parent $pyPath
        }
    } catch {
        # Python 3.14 not found
    }
}

# =====================================================
# Add Additional Tools to PATH (AFTER MSVC)
# Order: MSVC (already first) → Node → Python → Clang → MSYS2
# This ensures MSVC link.exe is found first by cargo
# =====================================================

# Node.js
if (Test-Path "$nodejsRoot\node.exe") {
    $env:PATH = "$env:PATH;$nodejsRoot"
}

# Python
if ($pythonRoot) {
    $env:PATH = "$env:PATH;$pythonRoot;$pythonRoot\Scripts"
}

# Windows Clang (standalone)
if (Test-Path "$clangRoot\bin") {
    $env:PATH = "$env:PATH;$clangRoot\bin"
}

# MSYS2 (LAST - gives access to gcc, g++, clang, make, etc.)
if (Test-Path "$msys64Root\ucrt64\bin") {
    $env:PATH = "$env:PATH;$msys64Root\ucrt64\bin;$msys64Root\usr\bin"
}

# =====================================================
# Extended INCLUDE and LIB (for non-cargo projects)
# =====================================================
if (Test-Path "$clangRoot\include") {
    $env:INCLUDE = "$env:INCLUDE;$clangRoot\include"
}
if (Test-Path "$msys64Root\ucrt64\include") {
    $env:INCLUDE = "$env:INCLUDE;$msys64Root\ucrt64\include"
}

if (Test-Path "$clangRoot\lib") {
    $env:LIB = "$env:LIB;$clangRoot\lib"
}
if (Test-Path "$msys64Root\ucrt64\lib") {
    $env:LIB = "$env:LIB;$msys64Root\ucrt64\lib"
}

# =====================================================
# Optional Environment Variables
# =====================================================
$env:WindowsSDKDir = "$msvcRoot\Windows Kits\10"
$env:DISTUTILS_USE_SDK = "1"
$env:MSSdk = "1"

# Build system defaults
$env:CMAKE_GENERATOR = "Ninja"
if (Test-Path "$msys64Root\ucrt64\bin\ninja.exe") {
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
}

# =====================================================
# Tool Aliases for Disambiguation
# =====================================================

# Explicit MSYS2 tool aliases (when you need to be specific)
if (Test-Path "$msys64Root\ucrt64\bin\ninja.exe") {
    Set-Alias -Name ninja-msys -Value "$msys64Root\ucrt64\bin\ninja.exe" -Force -Option AllScope
}
if (Test-Path "$msys64Root\ucrt64\bin\meson.exe") {
    Set-Alias -Name meson-msys -Value "$msys64Root\ucrt64\bin\meson.exe" -Force -Option AllScope
}
if (Test-Path "$msys64Root\ucrt64\bin\pkgconf.exe") {
    Set-Alias -Name pkgconf-msys -Value "$msys64Root\ucrt64\bin\pkgconf.exe" -Force -Option AllScope
}

# Python aliases
if ($pythonRoot) {
    if (Test-Path "$pythonRoot\python.exe") {
        Set-Alias -Name python314 -Value "$pythonRoot\python.exe" -Force -Option AllScope
        Set-Alias -Name py314 -Value "$pythonRoot\python.exe" -Force -Option AllScope
    }
    if (Test-Path "$pythonRoot\Scripts\pip.exe") {
        Set-Alias -Name pip314 -Value "$pythonRoot\Scripts\pip.exe" -Force -Option AllScope
    }
}

if (Test-Path "$msys64Root\ucrt64\bin\python.exe") {
    Set-Alias -Name python-msys -Value "$msys64Root\ucrt64\bin\python.exe" -Force -Option AllScope
    Set-Alias -Name pip-msys -Value "$msys64Root\ucrt64\bin\pip.exe" -Force -Option AllScope
}

# Compiler aliases for disambiguation
if (Test-Path "$clangRoot\bin\clang.exe") {
    Set-Alias -Name clang-win -Value "$clangRoot\bin\clang.exe" -Force -Option AllScope
    Set-Alias -Name clang++-win -Value "$clangRoot\bin\clang++.exe" -Force -Option AllScope
}

if (Test-Path "$msys64Root\ucrt64\bin\clang.exe") {
    Set-Alias -Name clang-msys -Value "$msys64Root\ucrt64\bin\clang.exe" -Force -Option AllScope
    Set-Alias -Name clang++-msys -Value "$msys64Root\ucrt64\bin\clang++.exe" -Force -Option AllScope
}

if (Test-Path "$msys64Root\ucrt64\bin\gcc.exe") {
    Set-Alias -Name gcc-msys -Value "$msys64Root\ucrt64\bin\gcc.exe" -Force -Option AllScope
    Set-Alias -Name g++-msys -Value "$msys64Root\ucrt64\bin\g++.exe" -Force -Option AllScope
}

# =====================================================
# Custom Functions
# =====================================================

function Update-Cargo {
    $customPackages = @{
        'ripgrep' = @{
            flags = '-C target-cpu=native'
            features = '--all-features'
        }
        'xh' = @{
            flags = '--cfg reqwest_unstable'
            features = '--all-features'
        }
    }
    
    Write-Host "Checking cargo-binstall..." -ForegroundColor Cyan
    cargo install cargo-binstall
    
    Write-Host "`nUpdating custom-compiled packages..." -ForegroundColor Cyan
    foreach ($pkg in $customPackages.Keys) {
        Write-Host "  Updating $pkg with custom flags..." -ForegroundColor Yellow
        $flags = $customPackages[$pkg].flags
        $featuresArg = $customPackages[$pkg].features
        
        # Temporarily set RUSTFLAGS for this package only
        $oldRustFlags = $env:RUSTFLAGS
        $env:RUSTFLAGS = $flags
        
        if ($featuresArg) {
            & cargo install $pkg $featuresArg.Split(' ')
        } else {
            & cargo install $pkg
        }
        
        # Restore original RUSTFLAGS
        if ($oldRustFlags) {
            $env:RUSTFLAGS = $oldRustFlags
        } else {
            Remove-Item Env:\RUSTFLAGS -ErrorAction SilentlyContinue
        }
    }
    
    Write-Host "`nUpdating remaining cargo packages..." -ForegroundColor Cyan
    cargo install-update -a
    
    Write-Host "`nAll updates complete!" -ForegroundColor Green
}

function Update-GlobalNpm {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        npm list -g --depth=0 --parseable | Select-Object -Skip 1 | ForEach-Object { 
            npm install -g "$(Split-Path $_ -Leaf)@latest" 
        }
    } else {
        Write-Host "npm not found in PATH" -ForegroundColor Red
    }
}

function Setup-MSVC {
    Write-Host "`nMSVC Configuration:" -ForegroundColor Green
    Write-Host "  Version:  $env:VCToolsVersion" -ForegroundColor Cyan
    Write-Host "  Root:     $msvcRoot" -ForegroundColor Cyan
    $linkCmd = Get-Command link.exe -ErrorAction SilentlyContinue
    if ($linkCmd) {
        Write-Host "  link.exe: $($linkCmd.Source)" -ForegroundColor Cyan
    }
}

function Setup-GCC {
    if (Get-Command gcc -ErrorAction SilentlyContinue) {
        Write-Host "`nGCC available from MSYS2:" -ForegroundColor Green
        & gcc --version | Select-Object -First 1
    } else {
        Write-Host "GCC not found in PATH" -ForegroundColor Red
    }
}

function Setup-Clang {
    Write-Host "`nClang Configuration:" -ForegroundColor Green
    if (Get-Command clang-win -ErrorAction SilentlyContinue) {
        Write-Host "  Windows Clang: Available (use 'clang-win')" -ForegroundColor Cyan
    }
    if (Get-Command clang-msys -ErrorAction SilentlyContinue) {
        Write-Host "  MSYS2 Clang:   Available (use 'clang-msys')" -ForegroundColor Cyan
    }
    if (Get-Command clang -ErrorAction SilentlyContinue) {
        Write-Host "  Default 'clang' resolves to:" -ForegroundColor Yellow
        Write-Host "    $((Get-Command clang).Source)" -ForegroundColor DarkGray
    }
}

function Setup-AllCompilers {
    Setup-MSVC
    Setup-GCC
    Setup-Clang
}

# Function aliases
Set-Alias -Name setupmsvc -Value Setup-MSVC
Set-Alias -Name setupgcc -Value Setup-GCC
Set-Alias -Name setupclang -Value Setup-Clang
Set-Alias -Name setupcc -Value Setup-AllCompilers
Set-Alias -Name npmupdate -Value Update-GlobalNpm

# =====================================================
# Startup Messages
# =====================================================

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  PowerShell Profile Loaded!" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`nMSVC environment configured for x64 from $msvcRoot" -ForegroundColor Green

# Verify link.exe (CRITICAL for cargo)
if (Get-Command link.exe -ErrorAction SilentlyContinue) {
    Write-Host "✓ link.exe found at: $((Get-Command link.exe).Source)" -ForegroundColor Green
} else {
    Write-Host "✗ link.exe NOT found in PATH!" -ForegroundColor Red
}

# Show available compilers
Write-Host "`nAvailable Compilers:" -ForegroundColor Yellow
$compilers = @('cl', 'gcc', 'g++', 'clang', 'clang++')
foreach ($compiler in $compilers) {
    $cmd = Get-Command $compiler -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "  ✓ $compiler" -ForegroundColor Green
    }
}

# Show available build tools
Write-Host "`nAvailable Build Tools:" -ForegroundColor Yellow
$buildTools = @('make', 'cmake', 'ninja', 'meson')
foreach ($tool in $buildTools) {
    $cmd = Get-Command $tool -ErrorAction SilentlyContinue
    if ($cmd) {
        Write-Host "  ✓ $tool" -ForegroundColor Green
    }
}

Write-Host "`nAvailable Commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo  - Update Rust/Cargo packages with custom flags" -ForegroundColor White
Write-Host "  npmupdate     - Update global npm packages" -ForegroundColor White
Write-Host "  setupmsvc     - Show MSVC configuration" -ForegroundColor White
Write-Host "  setupgcc      - Show GCC configuration" -ForegroundColor White
Write-Host "  setupclang    - Show Clang configuration" -ForegroundColor White
Write-Host "  setupcc       - Show all compiler configurations" -ForegroundColor White

if ($pythonRoot -or (Test-Path "$msys64Root\ucrt64\bin\python.exe")) {
    Write-Host "`nPython Aliases:" -ForegroundColor Yellow
    if (Get-Command python314 -ErrorAction SilentlyContinue) {
        Write-Host "  python314 / py314  - Windows Python 3.14 (explicit)" -ForegroundColor White
        Write-Host "  pip314             - Windows pip for Python 3.14" -ForegroundColor White
    }
    if (Get-Command python-msys -ErrorAction SilentlyContinue) {
        Write-Host "  python-msys        - MSYS2 Python" -ForegroundColor White
        Write-Host "  pip-msys           - MSYS2 pip" -ForegroundColor White
    }
}

Write-Host "`nCompiler Aliases:" -ForegroundColor Yellow
if (Get-Command clang-win -ErrorAction SilentlyContinue) {
    Write-Host "  clang-win / clang++-win    - Windows Clang (portable)" -ForegroundColor White
}
if (Get-Command clang-msys -ErrorAction SilentlyContinue) {
    Write-Host "  clang-msys / clang++-msys  - MSYS2 Clang" -ForegroundColor White
}
if (Get-Command gcc-msys -ErrorAction SilentlyContinue) {
    Write-Host "  gcc-msys / g++-msys        - MSYS2 GCC" -ForegroundColor White
}

Write-Host "`nNOTE: 'gcc', 'g++', 'clang', 'make' are available directly" -ForegroundColor DarkGray
Write-Host "      Use aliases (e.g., 'clang-win', 'clang-msys') when you need specific versions" -ForegroundColor DarkGray

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host ""
