$MaximumHistoryCount = 10000  # or whatever limit you want
# =====================================================
# Base Path Configuration
# =====================================================
$msvcRoot = "D:\dev\msvc"
$clangRoot = "D:\Programs\clang"
$cmakeRoot = "D:\Programs\cmake"
$msys64Root = "D:\Programs\msys64"
$nodejsRoot = "D:\Programs\nodejs"

# Auto-detect Python 3.14 installation path
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

# Fallback: search using py launcher
if (-not $pythonRoot) {
    try {
        $pyPath = & py -3.14 -c "import sys; print(sys.executable)" 2>$null
        if ($pyPath -and (Test-Path $pyPath)) {
            $pythonRoot = Split-Path -Parent $pyPath
        }
    } catch {
        Write-Warning "Python 3.14 not found. Python paths will be skipped."
    }
}

$vcToolsVersion = "14.50.35717"
$windowsSDKVersion = "10.0.26100.0"
$hostArch = "x64"
$targetArch = "x64"

# =====================================================
# MSVC Environment Setup
# =====================================================
$env:VSCMD_ARG_HOST_ARCH = $hostArch
$env:VSCMD_ARG_TGT_ARCH = $targetArch
$env:VCToolsVersion = $vcToolsVersion
$env:WindowsSDKVersion = "$windowsSDKVersion\"
$env:VCToolsInstallDir = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
$env:WindowsSdkBinPath = "$msvcRoot\Windows Kits\10\bin\"
$env:WindowsSDKDir = "$msvcRoot\Windows Kits\10"
$env:DISTUTILS_USE_SDK = "1"
$env:MSSdk = "1"

# =====================================================
# INCLUDE Paths (MSVC, Windows SDK, Clang, GCC)
# =====================================================
$includePaths = @(
    "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include"
    "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\ucrt"
    "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\shared"
    "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\um"
    "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\winrt"
    "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\cppwinrt"
    "$clangRoot\include"
    "$msys64Root\ucrt64\include"
)
$env:INCLUDE = $includePaths -join ";"

# =====================================================
# LIB Paths (MSVC, Windows SDK, Clang, GCC)
# =====================================================
$libPaths = @(
    "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\$targetArch"
    "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\ucrt\$targetArch"
    "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\um\$targetArch"
    "$clangRoot\lib"
    "$msys64Root\ucrt64\lib"
)
$env:LIB = $libPaths -join ";"


# =====================================================
# PATH Setup - NODEJS & PYTHON FIRST, then compilers
# =====================================================
# Node.js paths (HIGHEST PRIORITY)
$nodejsPaths = @()
if (Test-Path "$nodejsRoot\node.exe") {
    $nodejsPaths = @(
        "$nodejsRoot"
    )
}

# Python paths (HIGH PRIORITY)
$pythonPaths = @()
if ($pythonRoot) {
    $pythonPaths = @(
        "$pythonRoot"
        "$pythonRoot\Scripts"
    )
}

# CMake path (MEDIUM-HIGH PRIORITY - Windows CMake before compilers)
$cmakePaths = @()
if (Test-Path "$cmakeRoot\bin\cmake.exe") {
    $cmakePaths = @(
        "$cmakeRoot\bin"
    )
}

# Compiler paths (medium priority)
$msvcBinPath = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\bin\Host$hostArch\$targetArch"
$compilerPaths = @(
    "$clangRoot\bin"
    "$msvcBinPath"
    "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch"
    "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch\ucrt"
)

# MSYS2 paths (LOWEST PRIORITY - these go LAST)
$msys2Paths = @(
    "$msys64Root\ucrt64\bin"
    "$msys64Root\usr\bin"
)

# Remove any existing instances of these paths from PATH to avoid duplicates
$pathsToClean = $nodejsPaths + $pythonPaths + $cmakePaths + $compilerPaths + $msys2Paths
$currentPathArray = $env:PATH -split ';'
$cleanedPath = $currentPathArray | Where-Object { 
    $currentItem = $_
    -not ($pathsToClean | Where-Object { $currentItem -eq $_ })
}
$env:PATH = $cleanedPath -join ';'

# Add paths in correct priority order: Node.js → Python → CMake → Compilers → MSYS2
foreach ($path in $nodejsPaths) {
    if (Test-Path $path) {
        $env:PATH = "$path;$env:PATH"
    }
}

foreach ($path in $pythonPaths) {
    if (Test-Path $path) {
        $env:PATH = "$path;$env:PATH"
    }
}

foreach ($path in $cmakePaths) {
    if (Test-Path $path) {
        $env:PATH = "$path;$env:PATH"
    }
}

foreach ($path in $compilerPaths) {
    if (Test-Path $path) {
        $env:PATH = "$env:PATH;$path"
    }
}

foreach ($path in $msys2Paths) {
    if (Test-Path $path) {
        $env:PATH = "$env:PATH;$path"
    }
}

# =====================================================
# Detect Windows Ninja
# =====================================================
$windowsNinja = $null
$ninjaPossiblePaths = @(
    "$cmakeRoot\bin\ninja.exe"       # Ninja bundled with CMake
    "$clangRoot\bin\ninja.exe"       # Ninja bundled with LLVM/Clang
)

foreach ($ninjaPath in $ninjaPossiblePaths) {
    if (Test-Path $ninjaPath) {
        $windowsNinja = $ninjaPath
        break
    }
}

# =====================================================
# Build System Configuration for Windows MSVC (Cargo)
# =====================================================

# Default to Ninja for general use
$env:CMAKE_GENERATOR = "Ninja"

# CRITICAL: Use Windows Ninja for MSVC builds (for Cargo)
# If Windows Ninja not found, warn user and fall back to NMake
if ($windowsNinja) {
    $env:CMAKE_MAKE_PROGRAM = $windowsNinja
} else {
    Write-Warning "Windows Ninja not found! Cargo builds will use NMake instead."
    Write-Warning "For better performance, download ninja.exe from https://github.com/ninja-build/ninja/releases"
    Write-Warning "and place it in $cmakeRoot\bin\ninja.exe"
    $env:CMAKE_GENERATOR = "NMake Makefiles"
    $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
}

# =====================================================
# Cargo/Rust Build Environment (for C/C++ dependencies)
# =====================================================

# These environment variables are inherited by all cargo subprocesses

# This ensures cargo can find MSVC tools when building crates with C/C++ dependencies

# Tell cargo's cmake/cc crates where to find MSVC tools
$env:CC = "$msvcBinPath\cl.exe"
$env:CXX = "$msvcBinPath\cl.exe"
$env:AR = "$msvcBinPath\lib.exe"
#$env:LINK = "$msvcBinPath\link.exe"

# Ensure cargo can find nmake (some build scripts check for it)
$env:NMAKE = "$msvcBinPath\nmake.exe"

# Critical MSVC environment variables for cargo's cc/cmake crates
$env:VCINSTALLDIR = "$msvcRoot\VC\"
$env:VCToolsInstallDir = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
$env:WindowsSdkDir = "$msvcRoot\Windows Kits\10\"

# Tell cargo's cmake builds to use MSVC
$env:CMAKE_C_COMPILER = "$msvcBinPath\cl.exe"
$env:CMAKE_CXX_COMPILER = "$msvcBinPath\cl.exe"

# =====================================================
# Force Rust to use our MSVC (not old BuildTools)
# =====================================================

# Override Visual Studio detection - point to our custom MSVC location
$env:VSINSTALLDIR = "$msvcRoot\"
$env:VCTOOLSINSTALLDIR = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"

# Explicitly tell Rust's linker where to find the correct link.exe
$env:RUSTFLAGS = "-C linker=$msvcBinPath\link.exe"
$env:CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER = "$msvcBinPath\link.exe"

# Tell cargo to use MSVC CRT (not mingw)
$env:CC_x86_64_pc_windows_msvc = "$msvcBinPath\cl.exe"
$env:CXX_x86_64_pc_windows_msvc = "$msvcBinPath\cl.exe"
$env:AR_x86_64_pc_windows_msvc = "$msvcBinPath\lib.exe"

# Ensure cargo's cc crate finds MSVC libs
$env:CFLAGS_x86_64_pc_windows_msvc = "/I$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include"

# =====================================================
# MSYS2 Tool Aliases (for explicit MSYS2 tool usage)
# =====================================================
$ucrt64Tools = @{
    'make' = "$msys64Root\ucrt64\bin\make.exe"
    'mingw32-make' = "$msys64Root\ucrt64\bin\mingw32-make.exe"
}

foreach ($tool in $ucrt64Tools.Keys) {
    $exePath = $ucrt64Tools[$tool]
    if (Test-Path $exePath) {
        Set-Alias -Name $tool -Value $exePath -Force -Option AllScope
        Write-Verbose "Aliased $tool -> $exePath"
    }
}

# =====================================================
# Python Aliases (explicit versions)
# =====================================================
if ($pythonRoot) {
    $python314Exe = "$pythonRoot\python.exe"
    $pip314Exe = "$pythonRoot\Scripts\pip.exe"

    if (Test-Path $python314Exe) {
        Set-Alias -Name python314 -Value $python314Exe -Force -Option AllScope
        Set-Alias -Name py314 -Value $python314Exe -Force -Option AllScope
    }

    if (Test-Path $pip314Exe) {
        Set-Alias -Name pip314 -Value $pip314Exe -Force -Option AllScope
    }
}

# MSYS2 Python aliases (for when you specifically need MSYS2 Python)
$pythonMsysExe = "$msys64Root\ucrt64\bin\python.exe"
if (Test-Path $pythonMsysExe) {
    Set-Alias -Name python-msys -Value $pythonMsysExe -Force -Option AllScope
    Set-Alias -Name pip-msys -Value "$msys64Root\ucrt64\bin\pip.exe" -Force -Option AllScope
}

# =====================================================
# Compiler Aliases (Windows vs MSYS2)
# =====================================================
$clangExe = "$clangRoot\bin\clang.exe"
$clangPlusPlusExe = "$clangRoot\bin\clang++.exe"
$clangMsysExe = "$msys64Root\ucrt64\bin\clang.exe"
$clangPlusPlusMsysExe = "$msys64Root\ucrt64\bin\clang++.exe"

if (Test-Path $clangExe) {
    Set-Alias -Name clang-win -Value $clangExe -Force -Option AllScope
    Set-Alias -Name clang++-win -Value $clangPlusPlusExe -Force -Option AllScope
}

if (Test-Path $clangMsysExe) {
    Set-Alias -Name clang-msys -Value $clangMsysExe -Force -Option AllScope
    Set-Alias -Name clang++-msys -Value $clangPlusPlusMsysExe -Force -Option AllScope
}

# =====================================================
# CMake Aliases (Windows vs MSYS2)
# =====================================================
$cmakeWinExe = "$cmakeRoot\bin\cmake.exe"
$cmakeMsysExe = "$msys64Root\ucrt64\bin\cmake.exe"

if (Test-Path $cmakeWinExe) {
    # cmake-win is the Windows native CMake (default, already in PATH first)
    Set-Alias -Name cmake-win -Value $cmakeWinExe -Force -Option AllScope
}

if (Test-Path $cmakeMsysExe) {
    # cmake-msys is the MSYS2 CMake (for bash/MSYS2 environment builds)
    Set-Alias -Name cmake-msys -Value $cmakeMsysExe -Force -Option AllScope
}

# Note: 'cmake' without suffix will use cmake-win by default since 
# D:\Programs\cmake\bin is earlier in PATH than MSYS2 paths

# =====================================================
# Ninja Aliases (Windows vs MSYS2)
# =====================================================
$ninjaMsysExe = "$msys64Root\ucrt64\bin\ninja.exe"

# Set ninja-msys alias (MSYS2 Ninja for MSYS2/GCC builds)
if (Test-Path $ninjaMsysExe) {
    Set-Alias -Name ninja-msys -Value $ninjaMsysExe -Force -Option AllScope
}

# Set ninja-win alias (Windows Ninja for MSVC builds)
if ($windowsNinja -and (Test-Path $windowsNinja)) {
    Set-Alias -Name ninja-win -Value $windowsNinja -Force -Option AllScope
}

# =====================================================
# Build Environment Switching Functions
# =====================================================

# Switch to Windows MSVC build environment (for manual builds)
function Use-WindowsMSVC {
    Write-Host "Switching to Windows MSVC build environment..." -ForegroundColor Cyan
    
    $env:CMAKE_GENERATOR = "Ninja"
    if ($windowsNinja) {
        $env:CMAKE_MAKE_PROGRAM = $windowsNinja
        Write-Host "  CMake: $cmakeRoot\bin\cmake.exe" -ForegroundColor Green
        Write-Host "  Ninja: $windowsNinja" -ForegroundColor Green
    } else {
        $env:CMAKE_GENERATOR = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
        Write-Host "  CMake: $cmakeRoot\bin\cmake.exe" -ForegroundColor Green
        Write-Host "  NMake: $msvcBinPath\nmake.exe" -ForegroundColor Green
    }
    
    # MSVC toolchain
    $env:CC = "$msvcBinPath\cl.exe"
    $env:CXX = "$msvcBinPath\cl.exe"
    $env:LINKER = "$msvcBinPath\link.exe"
    
    # Clear any Clang-specific variables
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    
    Write-Host "  Compiler: MSVC cl.exe" -ForegroundColor Green
    Write-Host "  Linker: $msvcBinPath\link.exe" -ForegroundColor Green
}

# Switch to MSYS2/GCC build environment (for manual builds)
function Use-MSYS2GCC {
    Write-Host "Switching to MSYS2/GCC build environment..." -ForegroundColor Cyan
    
    $env:CMAKE_GENERATOR = "Ninja"
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
    
    # GCC toolchain
    $env:CC = "$msys64Root\ucrt64\bin\gcc.exe"
    $env:CXX = "$msys64Root\ucrt64\bin\g++.exe"
    
    # Clear Windows-specific linker variables
    Remove-Item Env:\LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    
    Write-Host "  CMake: $msys64Root\ucrt64\bin\cmake.exe" -ForegroundColor Green
    Write-Host "  Ninja: $msys64Root\ucrt64\bin\ninja.exe" -ForegroundColor Green
    Write-Host "  Compiler: $msys64Root\ucrt64\bin\gcc.exe" -ForegroundColor Green
    Write-Host "  Linker: GNU ld (auto-detected by GCC)" -ForegroundColor Green
}

# Switch to MSYS2/Clang build environment (for manual builds)
function Use-MSYS2Clang {
    Write-Host "Switching to MSYS2/Clang build environment..." -ForegroundColor Cyan
    
    $env:CMAKE_GENERATOR = "Ninja"
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
    
    # MSYS2 Clang toolchain
    $env:CC = "$msys64Root\ucrt64\bin\clang.exe"
    $env:CXX = "$msys64Root\ucrt64\bin\clang++.exe"
    
    # Clear Windows-specific linker variables
    Remove-Item Env:\LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    
    Write-Host "  CMake: $msys64Root\ucrt64\bin\cmake.exe" -ForegroundColor Green
    Write-Host "  Ninja: $msys64Root\ucrt64\bin\ninja.exe" -ForegroundColor Green
    Write-Host "  Compiler: $msys64Root\ucrt64\bin\clang.exe" -ForegroundColor Green
    Write-Host "  Linker: LLVM lld (auto-detected by Clang)" -ForegroundColor Green
}

# Switch to Windows Clang with LLVM linker (for manual builds)
function Use-WindowsClangMSVC {
    Write-Host "Switching to Windows Clang-cl (MSVC backend) build environment..." -ForegroundColor Cyan
    
    $env:CMAKE_GENERATOR = "Ninja"
    if ($windowsNinja) {
        $env:CMAKE_MAKE_PROGRAM = $windowsNinja
    } else {
        $env:CMAKE_GENERATOR = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }
    
    # Windows Clang toolchain with LLD linker
    $env:CC = "$clangRoot\bin\clang-cl.exe"
    $env:CXX = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_LINKER = "$clangRoot\bin\lld-link.exe"
    
    # Clear MSVC linker variables to avoid confusion
    Remove-Item Env:\LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK -ErrorAction SilentlyContinue
    
    Write-Host "  CMake: $cmakeRoot\bin\cmake.exe" -ForegroundColor Green
    if ($windowsNinja) {
        Write-Host "  Ninja: $windowsNinja" -ForegroundColor Green
    } else {
        Write-Host "  NMake: $msvcBinPath\nmake.exe" -ForegroundColor Green
    }
    Write-Host "  Compiler: $clangRoot\bin\clang-cl.exe (MSVC-compatible)" -ForegroundColor Green
    Write-Host "  Linker: $clangRoot\bin\lld-link.exe" -ForegroundColor Green
}

Set-Alias -Name use-msvc -Value Use-WindowsMSVC
Set-Alias -Name use-gcc -Value Use-MSYS2GCC
Set-Alias -Name use-clang-msys -Value Use-MSYS2Clang
Set-Alias -Name use-clang-win -Value Use-WindowsClangMSVC

# =====================================================
# Rust/Cargo Functions
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
        
        # Set RUSTFLAGS and install
        $env:RUSTFLAGS = $flags
        
        # Only add features argument if it's not empty
        if ($featuresArg) {
            & cargo install $pkg $featuresArg.Split(' ')
        } else {
            & cargo install $pkg
        }
        
        Remove-Item Env:\RUSTFLAGS -ErrorAction SilentlyContinue
    }
    
    Write-Host "`nUpdating remaining cargo packages..." -ForegroundColor Cyan
    cargo install-update -a
    
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

function Update-GlobalNpm {
    npm list -g --depth=0 --parseable | Select-Object -Skip 1 | ForEach-Object { npm install -g "$(Split-Path $_ -Leaf)@latest" }
}

Set-Alias -Name setupmsvc -Value Setup-MSVC
Set-Alias -Name setupgcc -Value Setup-GCC
Set-Alias -Name setupclang -Value Setup-Clang
Set-Alias -Name setupcc -Value Setup-AllCompilers
Set-Alias -Name npmupdate -Value Update-GlobalNpm

# =====================================================
# Profile Load Message
# =====================================================
Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  PowerShell Profile Loaded!" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`nNode.js Configuration:" -ForegroundColor Yellow
if (Test-Path "$nodejsRoot\node.exe") {
    $nodeCmd = Get-Command node -ErrorAction SilentlyContinue
    if ($nodeCmd) {
        $nodeVer = & node --version 2>&1
        Write-Host "  ✓ node:    $nodeVer" -ForegroundColor Green
        Write-Host "             $($nodeCmd.Source)" -ForegroundColor DarkGray
    }
    $npmCmd = Get-Command npm -ErrorAction SilentlyContinue
if ($npmCmd) {
    try {
        $npmVer = (powershell -ExecutionPolicy Bypass -Command "npm --version" 2>&1 | Select-String "^\d+\.\d+\.\d+$").Matches.Value
        if ($npmVer) {
            Write-Host "  ✓ npm:     v$npmVer" -ForegroundColor Green
        } else {
            Write-Host "  ✓ npm:     installed" -ForegroundColor Green
        }
    } catch {
        Write-Host "  ✓ npm:     installed" -ForegroundColor Green
    }
}
} else {
    Write-Host "  ⚠ Node.js not found at $nodejsRoot" -ForegroundColor Red
}

Write-Host "`nPython Configuration:" -ForegroundColor Yellow
if ($pythonRoot) {
    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    $pipCmd = Get-Command pip -ErrorAction SilentlyContinue
    if ($pythonCmd) {
        $pythonVer = & python --version 2>&1
        Write-Host "  ✓ python:  $pythonVer" -ForegroundColor Green
        Write-Host "             $($pythonCmd.Source)" -ForegroundColor DarkGray
    }
    if ($pipCmd) {
        $pipVer = (& pip --version 2>&1) -split "`n" | Select-Object -First 1
        Write-Host "  ✓ pip:     $pipVer" -ForegroundColor Green
    }
    
    # Check for MSYS2 Python conflict
    $msysPython = "$msys64Root\ucrt64\bin\python.exe"
    if (Test-Path $msysPython) {
        $msysPyVer = & $msysPython --version 2>&1
        Write-Host "  ℹ MSYS2:   $msysPyVer (use 'python-msys' alias)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ⚠ Python 3.14 not found!" -ForegroundColor Red
    Write-Host "    Install from: https://www.python.org/downloads/" -ForegroundColor Yellow
}

Write-Host "`nCMake Configuration:" -ForegroundColor Yellow
$cmakeCmd = Get-Command cmake -ErrorAction SilentlyContinue
if ($cmakeCmd) {
    $cmakeVer = & cmake --version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ cmake:   $cmakeVer" -ForegroundColor Green
    Write-Host "             $($cmakeCmd.Source)" -ForegroundColor DarkGray
    
    # Check for MSYS2 CMake
    if (Test-Path "$msys64Root\ucrt64\bin\cmake.exe") {
        $cmakeMsysVer = & "$msys64Root\ucrt64\bin\cmake.exe" --version 2>&1 | Select-Object -First 1
        Write-Host "  ℹ MSYS2:   $cmakeMsysVer (use 'cmake-msys' alias)" -ForegroundColor Cyan
    }
} else {
    Write-Host "  ⚠ CMake not found!" -ForegroundColor Red
}

Write-Host "`nNinja Configuration:" -ForegroundColor Yellow
if ($windowsNinja) {
    $ninjaVer = & $windowsNinja --version 2>&1
    Write-Host "  ✓ ninja:   v$ninjaVer (Windows)" -ForegroundColor Green
    Write-Host "             $windowsNinja" -ForegroundColor DarkGray
} else {
    Write-Host "  ⚠ Windows Ninja not found!" -ForegroundColor Red
    Write-Host "    Download from: https://github.com/ninja-build/ninja/releases" -ForegroundColor Yellow
    Write-Host "    Place ninja.exe in: $cmakeRoot\bin\" -ForegroundColor Yellow
}

if (Test-Path "$msys64Root\ucrt64\bin\ninja.exe") {
    $ninjaMsysVer = & "$msys64Root\ucrt64\bin\ninja.exe" --version 2>&1
    Write-Host "  ℹ MSYS2:   v$ninjaMsysVer (use 'ninja-msys' alias)" -ForegroundColor Cyan
}

Write-Host "`nDefault Build Environment (for Cargo):" -ForegroundColor Yellow

# Get CMake version dynamically
$cmakeVersionDisplay = "CMake (not found)"
if (Test-Path "$cmakeRoot\bin\cmake.exe") {
    try {
        $cmakeVer = & "$cmakeRoot\bin\cmake.exe" --version 2>&1 | Select-Object -First 1
        if ($cmakeVer) {
            $cmakeVersionDisplay = $cmakeVer.Trim()
        }
    } catch {
        $cmakeVersionDisplay = "Windows CMake (version detection failed)"
    }
}
Write-Host "  CMake:     $cmakeVersionDisplay" -ForegroundColor Green

if ($windowsNinja) {
    Write-Host "  Generator: Ninja (Windows)" -ForegroundColor Green
} else {
    Write-Host "  Generator: NMake Makefiles" -ForegroundColor Yellow
}
Write-Host "  Compiler:  $msvcBinPath\cl.exe" -ForegroundColor Green
Write-Host "  Linker:    $msvcBinPath\link.exe" -ForegroundColor Green

Write-Host "`nAvailable custom commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo  - Update Rust/Cargo packages" -ForegroundColor White

Write-Host "`nBuild environment switching:" -ForegroundColor Yellow
Write-Host "  use-msvc         - Windows MSVC (cl.exe + MSVC link.exe)" -ForegroundColor White
Write-Host "  use-clang-win    - Windows Clang-cl (clang-cl.exe + LLVM lld-link.exe)" -ForegroundColor White
Write-Host "  use-gcc          - MSYS2 GCC (gcc.exe + GNU ld)" -ForegroundColor White
Write-Host "  use-clang-msys   - MSYS2 Clang (clang.exe + LLVM lld)" -ForegroundColor White

Write-Host "`nCompiler setup commands:" -ForegroundColor Yellow
Write-Host "  setupcc       - All compilers already loaded" -ForegroundColor White
Write-Host "  setupmsvc     - MSVC already loaded" -ForegroundColor White
Write-Host "  setupgcc      - GCC already loaded" -ForegroundColor White
Write-Host "  setupclang    - Clang already loaded" -ForegroundColor White

Write-Host "`nPython aliases:" -ForegroundColor Yellow
if (Get-Command python314 -ErrorAction SilentlyContinue) {
    Write-Host "  python314 / py314  - Windows Python 3.14 (explicit)" -ForegroundColor White
    Write-Host "  pip314             - Windows pip for Python 3.14" -ForegroundColor White
}
if (Get-Command python-msys -ErrorAction SilentlyContinue) {
    Write-Host "  python-msys        - MSYS2 Python" -ForegroundColor White
    Write-Host "  pip-msys           - MSYS2 pip" -ForegroundColor White
}

Write-Host "`nCompiler aliases:" -ForegroundColor Yellow
if (Get-Command clang-win -ErrorAction SilentlyContinue) {
    Write-Host "  clang-win     - Windows Clang (portable)" -ForegroundColor White
    Write-Host "  clang++-win   - Windows Clang++ (portable)" -ForegroundColor White
}
if (Get-Command clang-msys -ErrorAction SilentlyContinue) {
    Write-Host "  clang-msys    - MSYS2 Clang" -ForegroundColor White
    Write-Host "  clang++-msys  - MSYS2 Clang++" -ForegroundColor White
}

Write-Host "`nCMake aliases:" -ForegroundColor Yellow
if (Get-Command cmake-win -ErrorAction SilentlyContinue) {
    Write-Host "  cmake-win     - Windows CMake 4.2.3 (default)" -ForegroundColor White
}
if (Get-Command cmake-msys -ErrorAction SilentlyContinue) {
    Write-Host "  cmake-msys    - MSYS2 CMake (for MSYS2 builds)" -ForegroundColor White
}

Write-Host "`nNinja aliases:" -ForegroundColor Yellow
if (Get-Command ninja-win -ErrorAction SilentlyContinue) {
    Write-Host "  ninja-win     - Windows Ninja (for MSVC builds)" -ForegroundColor White
}
if (Get-Command ninja-msys -ErrorAction SilentlyContinue) {
    Write-Host "  ninja-msys    - MSYS2 Ninja (for MSYS2 builds)" -ForegroundColor White
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
