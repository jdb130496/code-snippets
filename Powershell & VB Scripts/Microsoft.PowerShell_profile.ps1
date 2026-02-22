# =====================================================
# PowerShell Profile - All 4 Toolchains with Explicit Aliases
# =====================================================
# Philosophy: 
# 1. Set PATH correctly per toolchain switch (use-msvc, use-gcc, etc.)
# 2. Create explicit aliases so you can call ANY compiler anytime
#    Example: clang-msys, gcc-msys, cl-msvc, clang-win, etc.

$MaximumHistoryCount = 10000

# =====================================================
# Base Path Configuration (Tool Locations)
# =====================================================
$msvcRoot = "D:\dev\msvc"
$clangRoot = "D:\Programs\clang"
$cmakeRoot = "D:\Programs\cmake"
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
        Write-Warning "Python 3.14 not found."
    }
}

$vcToolsVersion = "14.51.36014"
$windowsSDKVersion = "10.0.26100.0"
$hostArch = "x64"
$targetArch = "x64"
$msvcBinPath = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\bin\Host$hostArch\$targetArch"

# =====================================================
# BASE PATH - Only Node.js and Python (universal tools)
# =====================================================
$basePaths = @()

if (Test-Path "$nodejsRoot\node.exe") {
    $basePaths += $nodejsRoot
    # Unblock npm/npx PowerShell wrappers so they run under RemoteSigned policy
    Get-ChildItem "$nodejsRoot\*.ps1" -ErrorAction SilentlyContinue | ForEach-Object {
        Unblock-File $_.FullName -ErrorAction SilentlyContinue
    }
}

if ($pythonRoot) {
    $basePaths += @(
        $pythonRoot,
        "$pythonRoot\Scripts"
    )
}

$env:PATH = ($basePaths -join ";") + ";$env:PATH"

# =====================================================
# EXPLICIT TOOL ALIASES - All 4 Toolchains
# =====================================================

# --- MSVC Toolchain Aliases ---
if (Test-Path "$msvcBinPath\cl.exe") {
    Set-Alias -Name cl-msvc -Value "$msvcBinPath\cl.exe" -Force
    Set-Alias -Name link-msvc -Value "$msvcBinPath\link.exe" -Force
    Set-Alias -Name lib-msvc -Value "$msvcBinPath\lib.exe" -Force
    Set-Alias -Name nmake-msvc -Value "$msvcBinPath\nmake.exe" -Force
}

# --- MSYS2 GCC Toolchain Aliases ---
if (Test-Path "$msys64Root\ucrt64\bin\gcc.exe") {
    Set-Alias -Name gcc-msys -Value "$msys64Root\ucrt64\bin\gcc.exe" -Force
    Set-Alias -Name g++-msys -Value "$msys64Root\ucrt64\bin\g++.exe" -Force
    Set-Alias -Name ld-msys -Value "$msys64Root\ucrt64\bin\ld.exe" -Force
    Set-Alias -Name ar-msys -Value "$msys64Root\ucrt64\bin\ar.exe" -Force
}

# --- MSYS2 Clang Toolchain Aliases ---
if (Test-Path "$msys64Root\ucrt64\bin\clang.exe") {
    Set-Alias -Name clang-msys -Value "$msys64Root\ucrt64\bin\clang.exe" -Force
    Set-Alias -Name clang++-msys -Value "$msys64Root\ucrt64\bin\clang++.exe" -Force
    Set-Alias -Name lld-msys -Value "$msys64Root\ucrt64\bin\lld.exe" -Force
}

# --- Windows Clang Toolchain Aliases ---
if (Test-Path "$clangRoot\bin\clang.exe") {
    Set-Alias -Name clang-win -Value "$clangRoot\bin\clang.exe" -Force
    Set-Alias -Name clang++-win -Value "$clangRoot\bin\clang++.exe" -Force
    Set-Alias -Name clang-cl-win -Value "$clangRoot\bin\clang-cl.exe" -Force
    Set-Alias -Name lld-link-win -Value "$clangRoot\bin\lld-link.exe" -Force
}

# --- CMake Aliases ---
if (Test-Path "$cmakeRoot\bin\cmake.exe") {
    Set-Alias -Name cmake-win -Value "$cmakeRoot\bin\cmake.exe" -Force
}
if (Test-Path "$msys64Root\ucrt64\bin\cmake.exe") {
    Set-Alias -Name cmake-msys -Value "$msys64Root\ucrt64\bin\cmake.exe" -Force
}

# --- Ninja Aliases ---
if (Test-Path "$cmakeRoot\bin\ninja.exe") {
    Set-Alias -Name ninja-win -Value "$cmakeRoot\bin\ninja.exe" -Force
}
if (Test-Path "$msys64Root\ucrt64\bin\ninja.exe") {
    Set-Alias -Name ninja-msys -Value "$msys64Root\ucrt64\bin\ninja.exe" -Force
}

# --- Make Aliases ---
if (Test-Path "$msys64Root\ucrt64\bin\make.exe") {
    Set-Alias -Name make-msys -Value "$msys64Root\ucrt64\bin\make.exe" -Force
}

# --- Python Aliases ---
if ($pythonRoot -and (Test-Path "$pythonRoot\python.exe")) {
    Set-Alias -Name python314 -Value "$pythonRoot\python.exe" -Force
    Set-Alias -Name py314 -Value "$pythonRoot\python.exe" -Force
    Set-Alias -Name pip314 -Value "$pythonRoot\Scripts\pip.exe" -Force
}
if (Test-Path "$msys64Root\ucrt64\bin\python.exe") {
    Set-Alias -Name python-msys -Value "$msys64Root\ucrt64\bin\python.exe" -Force
    Set-Alias -Name pip-msys -Value "$msys64Root\ucrt64\bin\pip.exe" -Force
}

# =====================================================
# Helper Function: Clean Toolchain Paths
# =====================================================
function Remove-ToolchainPaths {
    $pathsToRemove = @(
        "*\cmake\bin*",
        "*\clang\bin*",
        "*\msvc\*\bin*",
        "*\msys64\ucrt64\bin*",
        "*\msys64\usr\bin*",
        "*Windows Kits*\bin*"
    )
    
    $currentPath = $env:PATH -split ';'
    $cleanPath = $currentPath | Where-Object {
        $item = $_
        $shouldRemove = $false
        foreach ($pattern in $pathsToRemove) {
            if ($item -like $pattern) {
                $shouldRemove = $true
                break
            }
        }
        -not $shouldRemove
    }
    
    $env:PATH = $cleanPath -join ';'
}

# =====================================================
# Toolchain 1: Windows MSVC
# =====================================================
function Use-WindowsMSVC {
    Write-Host "`n==> Switching to Windows MSVC toolchain..." -ForegroundColor Cyan
    
    Remove-ToolchainPaths
    
    # MSVC paths: D:\dev\msvc\VC\Tools\MSVC\14.51.36014\bin\Hostx64\x64
    #             D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64
    $msvcPaths = @(
        "$cmakeRoot\bin",  # D:\Programs\cmake\bin (Windows CMake + Ninja)
        "$msvcBinPath",
        "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch"
    )
    
    foreach ($path in $msvcPaths) {
        if (Test-Path $path) {
            $env:PATH = "$path;$env:PATH"
        }
    }
    
    # MSVC environment variables
    $env:VSCMD_ARG_HOST_ARCH = $hostArch
    $env:VSCMD_ARG_TGT_ARCH = $targetArch
    $env:VCToolsVersion = $vcToolsVersion
    $env:WindowsSDKVersion = "$windowsSDKVersion\"
    $env:VCToolsInstallDir = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
    $env:WindowsSdkBinPath = "$msvcRoot\Windows Kits\10\bin\"
    $env:WindowsSDKDir = "$msvcRoot\Windows Kits\10"
    
    # INCLUDE and LIB
    $env:INCLUDE = @(
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\ucrt",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\shared",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\um",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\winrt"
    ) -join ";"
    
    $env:LIB = @(
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\$targetArch",
        "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\ucrt\$targetArch",
        "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\um\$targetArch"
    ) -join ";"
    
    # CMake configuration
    $env:CMAKE_GENERATOR = "Ninja"
    $windowsNinja = "$cmakeRoot\bin\ninja.exe"
    if (Test-Path $windowsNinja) {
        $env:CMAKE_MAKE_PROGRAM = $windowsNinja
    } else {
        $env:CMAKE_GENERATOR = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }
    
    # Compiler selection
    $env:CC = "$msvcBinPath\cl.exe"
    $env:CXX = "$msvcBinPath\cl.exe"
    $env:CMAKE_C_COMPILER = "$msvcBinPath\cl.exe"
    $env:CMAKE_CXX_COMPILER = "$msvcBinPath\cl.exe"
    
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    
    Write-Host "✓ MSVC toolchain active" -ForegroundColor Green
    Write-Host "  Compiler:  $msvcBinPath\cl.exe" -ForegroundColor White
    Write-Host "  Linker:    $msvcBinPath\link.exe" -ForegroundColor White
    Write-Host "  CMake:     $cmakeRoot\bin\cmake.exe" -ForegroundColor White
    Write-Host "  Ninja:     $cmakeRoot\bin\ninja.exe" -ForegroundColor White
}

# =====================================================
# Toolchain 2: MSYS2 GCC
# =====================================================
function Use-MSYS2GCC {
    Write-Host "`n==> Switching to MSYS2 GCC toolchain..." -ForegroundColor Cyan
    
    Remove-ToolchainPaths
    
    # MSYS2 paths: D:\Programs\msys64\ucrt64\bin ONLY
    # DO NOT add \usr\bin - it has duplicate ninja that breaks CMAKE_MAKE_PROGRAM
    $msys2Paths = @(
        "$msys64Root\ucrt64\bin"  # GCC, CMake, Ninja all here
    )
    
    foreach ($path in $msys2Paths) {
        if (Test-Path $path) {
            $env:PATH = "$path;$env:PATH"
        }
    }
    
    $env:INCLUDE = "$msys64Root\ucrt64\include"
    $env:LIB = "$msys64Root\ucrt64\lib"
    
    # CMake configuration
    $env:CMAKE_GENERATOR = "Ninja"
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
    
    # Compiler selection
    $env:CC = "$msys64Root\ucrt64\bin\gcc.exe"
    $env:CXX = "$msys64Root\ucrt64\bin\g++.exe"
    $env:CMAKE_C_COMPILER = "$msys64Root\ucrt64\bin\gcc.exe"
    $env:CMAKE_CXX_COMPILER = "$msys64Root\ucrt64\bin\g++.exe"
    
    # Clear Windows-specific variables
    Remove-Item Env:\LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Remove-Item Env:\WindowsSDKDir -ErrorAction SilentlyContinue
    
    Write-Host "✓ MSYS2 GCC toolchain active" -ForegroundColor Green
    Write-Host "  Compiler:  $msys64Root\ucrt64\bin\gcc.exe" -ForegroundColor White
    Write-Host "  Linker:    $msys64Root\ucrt64\bin\ld.exe (GNU ld)" -ForegroundColor White
    Write-Host "  CMake:     $msys64Root\ucrt64\bin\cmake.exe" -ForegroundColor White
    Write-Host "  Ninja:     $msys64Root\ucrt64\bin\ninja.exe" -ForegroundColor White
}

# =====================================================
# Toolchain 3: MSYS2 Clang
# =====================================================
function Use-MSYS2Clang {
    Write-Host "`n==> Switching to MSYS2 Clang toolchain..." -ForegroundColor Cyan
    
    Remove-ToolchainPaths
    
    # MSYS2 paths: D:\Programs\msys64\ucrt64\bin ONLY
    # DO NOT add \usr\bin - it has duplicate ninja that breaks CMAKE_MAKE_PROGRAM
    $msys2Paths = @(
        "$msys64Root\ucrt64\bin"  # Clang, CMake, Ninja all here
    )
    
    foreach ($path in $msys2Paths) {
        if (Test-Path $path) {
            $env:PATH = "$path;$env:PATH"
        }
    }
    
    $env:INCLUDE = "$msys64Root\ucrt64\include"
    $env:LIB = "$msys64Root\ucrt64\lib"
    
    # CMake configuration
    $env:CMAKE_GENERATOR = "Ninja"
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
    
    # Compiler selection
    $env:CC = "$msys64Root\ucrt64\bin\clang.exe"
    $env:CXX = "$msys64Root\ucrt64\bin\clang++.exe"
    $env:CMAKE_C_COMPILER = "$msys64Root\ucrt64\bin\clang.exe"
    $env:CMAKE_CXX_COMPILER = "$msys64Root\ucrt64\bin\clang++.exe"
    
    # Clear Windows-specific variables
    Remove-Item Env:\LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Remove-Item Env:\WindowsSDKDir -ErrorAction SilentlyContinue
    
    Write-Host "✓ MSYS2 Clang toolchain active" -ForegroundColor Green
    Write-Host "  Compiler:  $msys64Root\ucrt64\bin\clang++.exe" -ForegroundColor White
    Write-Host "  Linker:    $msys64Root\ucrt64\bin\lld.exe (LLVM lld)" -ForegroundColor White
    Write-Host "  CMake:     $msys64Root\ucrt64\bin\cmake.exe" -ForegroundColor White
    Write-Host "  Ninja:     $msys64Root\ucrt64\bin\ninja.exe" -ForegroundColor White
}

# =====================================================
# Toolchain 4: Windows Clang (clang-cl)
# =====================================================
function Use-WindowsClang {
    Write-Host "`n==> Switching to Windows Clang-cl toolchain..." -ForegroundColor Cyan
    
    Remove-ToolchainPaths
    
    # Windows Clang paths: D:\Programs\clang\bin
    #                      D:\Programs\cmake\bin
    $clangPaths = @(
        "$cmakeRoot\bin",  # D:\Programs\cmake\bin (Windows CMake + Ninja)
        "$clangRoot\bin",  # D:\Programs\clang\bin
        "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch"
    )
    
    foreach ($path in $clangPaths) {
        if (Test-Path $path) {
            $env:PATH = "$path;$env:PATH"
        }
    }
    
    # Windows SDK environment
    $env:WindowsSDKVersion = "$windowsSDKVersion\"
    $env:WindowsSDKDir = "$msvcRoot\Windows Kits\10"
    
    # INCLUDE and LIB
    $env:INCLUDE = @(
        "$clangRoot\include",
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\ucrt",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\shared",
        "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\um"
    ) -join ";"
    
    $env:LIB = @(
        "$clangRoot\lib",
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\$targetArch",
        "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\ucrt\$targetArch",
        "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\um\$targetArch"
    ) -join ";"
    
    # CMake configuration
    $env:CMAKE_GENERATOR = "Ninja"
    $windowsNinja = "$cmakeRoot\bin\ninja.exe"
    if (Test-Path $windowsNinja) {
        $env:CMAKE_MAKE_PROGRAM = $windowsNinja
    } else {
        $env:CMAKE_GENERATOR = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }
    
    # Compiler selection
    $env:CC = "$clangRoot\bin\clang-cl.exe"
    $env:CXX = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_C_COMPILER = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_CXX_COMPILER = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_LINKER = "$clangRoot\bin\lld-link.exe"
    
    Remove-Item Env:\LINKER -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    
    Write-Host "✓ Windows Clang-cl toolchain active" -ForegroundColor Green
    Write-Host "  Compiler:  $clangRoot\bin\clang-cl.exe" -ForegroundColor White
    Write-Host "  Linker:    $clangRoot\bin\lld-link.exe" -ForegroundColor White
    Write-Host "  CMake:     $cmakeRoot\bin\cmake.exe" -ForegroundColor White
    Write-Host "  Ninja:     $cmakeRoot\bin\ninja.exe" -ForegroundColor White
}

# =====================================================
# Convenient Aliases
# =====================================================
Set-Alias -Name use-msvc -Value Use-WindowsMSVC
Set-Alias -Name use-gcc -Value Use-MSYS2GCC
Set-Alias -Name use-clang-msys -Value Use-MSYS2Clang
Set-Alias -Name use-clang-win -Value Use-WindowsClang

# =====================================================
# Rust/Cargo Update Function
# =====================================================
function Update-Cargo {
    # Packages that need custom RUSTFLAGS or feature flags when built from source
    $customPackages = @{
        'ripgrep' = @{
            flags    = '-C target-cpu=native'
            features = '--all-features'
        }
        'xh' = @{
            flags    = '--cfg reqwest_unstable'
            features = '--all-features'
        }
    }

    Write-Host "`nSwitching to MSVC for Cargo builds..." -ForegroundColor Cyan
    Use-WindowsMSVC

    Write-Host "`nChecking cargo-binstall..." -ForegroundColor Cyan
    cargo install cargo-binstall

    Write-Host "`nUpdating custom-compiled packages..." -ForegroundColor Cyan
    foreach ($pkg in $customPackages.Keys) {
        Write-Host "  Updating $pkg with custom flags..." -ForegroundColor Yellow
        $flags       = $customPackages[$pkg].flags
        $featuresArg = $customPackages[$pkg].features

        $oldRustFlags    = $env:RUSTFLAGS
        $env:RUSTFLAGS   = $flags

        if ($featuresArg) {
            & cargo install $pkg $featuresArg.Split(' ')
        } else {
            & cargo install $pkg
        }

        if ($oldRustFlags) {
            $env:RUSTFLAGS = $oldRustFlags
        } else {
            Remove-Item Env:\RUSTFLAGS -ErrorAction SilentlyContinue
        }
    }

    Write-Host "`nUpdating remaining cargo packages..." -ForegroundColor Cyan
    cargo install-update -a

    Write-Host "`nAll Cargo updates complete!" -ForegroundColor Green
}

# =====================================================
# npm Global Package Update Function
# =====================================================
function Update-GlobalNpm {
    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "`nUpdating global npm packages..." -ForegroundColor Cyan
        try {
            # Force the global prefix to match where packages are actually installed.
            # This overrides any misconfigured npm prefix (e.g. AppData) and ensures
            # list and install both operate on the same location.
            npm config set prefix $nodejsRoot

            $json = npm list -g --depth=0 --json 2>$null | ConvertFrom-Json

            # npm may use either .dependencies or .node_modules depending on version/prefix
            if ($json.dependencies) {
                $pkgs = $json.dependencies.PSObject.Properties.Name
            } elseif ($json.node_modules) {
                $pkgs = $json.node_modules.PSObject.Properties.Name
            } else {
                # Last resort: read package folders directly from disk
                $pkgs = Get-ChildItem "$nodejsRoot\node_modules" -Directory -ErrorAction SilentlyContinue |
                         Where-Object { $_.Name -notmatch '^.npm$' -and $_.Name -notlike '.bin*' } |
                         ForEach-Object {
                             if ($_.Name.StartsWith("@")) {
                                 Get-ChildItem $_.FullName -Directory | ForEach-Object { "$($_.Parent.Name)/$($_.Name)" }
                             } else { $_.Name }
                         }
            }

            if (-not $pkgs) {
                Write-Host "No global npm packages found under $nodejsRoot." -ForegroundColor Yellow
                return
            }
            foreach ($pkg in $pkgs) {
                Write-Host "  Updating $pkg..." -ForegroundColor Yellow
                npm install -g "$pkg@latest"
            }
            Write-Host "`nAll npm global packages updated!" -ForegroundColor Green
        } catch {
            Write-Host "Failed to list npm packages: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "npm not found in PATH" -ForegroundColor Red
    }
}

Set-Alias -Name npmupdate -Value Update-GlobalNpm

# =====================================================
# Profile Load Message
# =====================================================
Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  PowerShell Profile - 4 Toolchains with Aliases" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

Write-Host "`nUniversal Tools:" -ForegroundColor Yellow
if (Test-Path "$nodejsRoot\node.exe") {
    $nodeVer = & node --version 2>&1
    Write-Host "  ✓ Node.js: $nodeVer" -ForegroundColor Green
}
if ($pythonRoot) {
    $pythonVer = & python --version 2>&1
    Write-Host "  ✓ Python:  $pythonVer" -ForegroundColor Green
}

Write-Host "`nToolchain Switching (sets PATH + environment):" -ForegroundColor Yellow
Write-Host "  use-msvc         → MSVC (D:\dev\msvc\...)" -ForegroundColor White
Write-Host "  use-gcc          → MSYS2 GCC (D:\Programs\msys64\ucrt64\...)" -ForegroundColor White
Write-Host "  use-clang-msys   → MSYS2 Clang (D:\Programs\msys64\ucrt64\...)" -ForegroundColor White
Write-Host "  use-clang-win    → Windows Clang (D:\Programs\clang\... + D:\Programs\cmake\...)" -ForegroundColor White

Write-Host "`nUpdate Commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo     → Update Rust/Cargo packages (ripgrep, xh with custom flags + rest via install-update)" -ForegroundColor White
Write-Host "  npmupdate        → Update all global npm packages to @latest" -ForegroundColor White

Write-Host "`nExplicit Aliases (always available):" -ForegroundColor Yellow
Write-Host "  Compilers:" -ForegroundColor Cyan
Write-Host "    cl-msvc, link-msvc, lib-msvc, nmake-msvc" -ForegroundColor White
Write-Host "    gcc-msys, g++-msys, ld-msys, ar-msys" -ForegroundColor White
Write-Host "    clang-msys, clang++-msys, lld-msys" -ForegroundColor White
Write-Host "    clang-win, clang++-win, clang-cl-win, lld-link-win" -ForegroundColor White

Write-Host "  Build Tools:" -ForegroundColor Cyan
Write-Host "    cmake-win, cmake-msys" -ForegroundColor White
Write-Host "    ninja-win, ninja-msys" -ForegroundColor White
Write-Host "    make-msys" -ForegroundColor White

Write-Host "  Python:" -ForegroundColor Cyan
Write-Host "    python314, py314, pip314" -ForegroundColor White
Write-Host "    python-msys, pip-msys" -ForegroundColor White

Write-Host "`nUsage Examples:" -ForegroundColor Yellow
Write-Host "  # Switch toolchain then build normally" -ForegroundColor Cyan
Write-Host "  use-msvc" -ForegroundColor White
Write-Host "  cmake -B build && cmake --build build" -ForegroundColor White
Write-Host ""
Write-Host "  # Or use explicit alias without switching" -ForegroundColor Cyan
Write-Host "  clang-msys++ -o test test.cpp" -ForegroundColor White

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host ""
