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
$msvcRoot    = "D:\dev\msvc"
$clangRoot   = "D:\Programs\clang"
$cmakeRoot   = "D:\Programs\cmake"
$msys64Root  = "D:\Programs\msys64"
$nodejsRoot  = "D:\Programs\nodejs"
$perlRoot    = "D:\Programs\Perl"
$nasmRoot    = "D:\Programs\nasm"
$opensslRoot = "D:\Programs\OpenSSL"
$mysqlRoot   = "D:\Programs\mysql"
$postgresRoot = "D:\Programs\postgre"
$sqliteRoot = "D:\Programs\sqlite"
$bisonRoot = "D:\Programs\winflexbison"

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

$hostArch   = "x64"
$targetArch = "x64"

# Auto-detect MSVC tools version (highest installed)
$vcToolsVersion = Get-ChildItem "$msvcRoot\VC\Tools\MSVC" -Directory -ErrorAction SilentlyContinue |
                  Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name
if (-not $vcToolsVersion) { $vcToolsVersion = "14.52.36510" }  # fallback

# Auto-detect Windows Kits root (11 takes priority over 10)
$windowsKitsRoot = $null
foreach ($kv in @("11","10")) {
    if (Test-Path "$msvcRoot\Windows Kits\$kv\bin") {
        $windowsKitsRoot = "$msvcRoot\Windows Kits\$kv"
        break
    }
}
if (-not $windowsKitsRoot) { $windowsKitsRoot = "$msvcRoot\Windows Kits\10" }  # fallback

# =====================================================
# Windows Kits Registry Check (required by winres/cargo)
# =====================================================
$kitsRegKey = "HKLM:\SOFTWARE\Microsoft\Windows Kits\Installed Roots"
$kitsRegValue = "KitsRoot10"
$expectedKitsPath = "$windowsKitsRoot\"

$current = (Get-ItemProperty -Path $kitsRegKey -Name $kitsRegValue -ErrorAction SilentlyContinue).$kitsRegValue
if ($current -ne $expectedKitsPath) {
    $isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($isAdmin) {
        New-Item -Path $kitsRegKey -Force | Out-Null
        Set-ItemProperty -Path $kitsRegKey -Name $kitsRegValue -Value $expectedKitsPath
        Write-Host "  ✓ Windows Kits registry key auto-fixed" -ForegroundColor Green
    } else {
        Write-Warning "Windows Kits registry missing — winres/cargo builds may fail!"
        Write-Warning "Run PowerShell as admin once to auto-fix, or run:"
        Write-Warning "  reg add `"HKLM\SOFTWARE\Microsoft\Windows Kits\Installed Roots`" /v KitsRoot10 /t REG_SZ /d `"$expectedKitsPath`" /f /reg:32"
    }
}

# Auto-detect SDK version (highest subfolder under bin\)
$windowsSDKVersion = Get-ChildItem "$windowsKitsRoot\bin" -Directory -ErrorAction SilentlyContinue |
                     Where-Object { $_.Name -match '^\d+\.\d+\.\d+\.\d+$' } |
                     Sort-Object { [version]$_.Name } -Descending |
                     Select-Object -First 1 -ExpandProperty Name
if (-not $windowsSDKVersion) { $windowsSDKVersion = "10.0.26100.0" }  # fallback

$msvcBinPath = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\bin\Host$hostArch\$targetArch"

# =====================================================
# BASE PATH - Universal tools always in PATH
# =====================================================
$basePaths = @()

if (Test-Path "$nasmRoot\nasm.exe") {
    $basePaths += $nasmRoot
}

if (Test-Path "$bisonRoot\win_bison.exe") {
    $basePaths += $bisonRoot
}

# Make nmake always available for cargo build scripts (e.g. openssl-src)
if (Test-Path "$msvcBinPath\nmake.exe") {
    $env:NMAKE = "$msvcBinPath\nmake.exe"
    $basePaths += $msvcBinPath
}

if (Test-Path "$nodejsRoot\node.exe") {
    $basePaths += $nodejsRoot
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

# OpenSSL
if (Test-Path "$opensslRoot\include\openssl\ssl.h") {
    $env:OPENSSL_DIR         = $opensslRoot
    $env:OPENSSL_NO_VENDOR   = "1"
    $env:OPENSSL_INCLUDE_DIR = "$opensslRoot\include"
    $env:OPENSSL_LIB_DIR     = "$opensslRoot\lib\VC\x64\MD"
    $env:WITH_SSL            = $opensslRoot
    $env:CMAKE_PREFIX_PATH   = $opensslRoot
    $basePaths += "$opensslRoot\bin"    # <-- this line is missing
}

if (Test-Path "$perlRoot\perl\bin\perl.exe") {
    $basePaths += @(
        "$perlRoot\perl\bin",
        "$perlRoot\c\bin"
    )
}

# MySQL - official Oracle connector
if (Test-Path "$mysqlRoot\lib\libmysql.lib") {
    $basePaths += "$mysqlRoot\bin"
    $env:MYSQLCLIENT_LIB_DIR  = "$mysqlRoot\lib"
    $env:MYSQLCLIENT_LIB_NAME = "libmysql"
    $env:MYSQLCLIENT_VERSION  = "9.0.0"
    $env:MYSQLCLIENT_NO_PKG_CONFIG = "1"
    $env:MYSQL_INCLUDE_DIR    = "$mysqlRoot\include"
}

# PostgreSQL
if (Test-Path "$postgresRoot\lib\libpq.lib") {
    $basePaths += "$postgresRoot\bin"
    $env:PQ_LIB_DIR    = "$postgresRoot\lib"
    $env:PQ_LIB_STATIC = "0"
}



if (Test-Path "$sqliteRoot\sqlite3.lib") {
    $env:SQLITE3_LIB_DIR  = $sqliteRoot
    $env:SQLITE3_LIB_NAME = "sqlite3"
    $basePaths += $sqliteRoot
}

# libclang for bindgen (required by libsqlite3-sys, librocksdb-sys, etc.)
if (Test-Path "$clangRoot\bin\libclang.dll") {
    $env:LIBCLANG_PATH = "$clangRoot\bin"
} elseif (Test-Path "$msys64Root\ucrt64\bin\libclang.dll") {
    $env:LIBCLANG_PATH = "$msys64Root\ucrt64\bin"
}

# MSYS2 bash only - needed for packages that require bash to build from source (e.g. pythonmonkey/SpiderMonkey)
# WARNING: usr\bin contains GNU coreutils that may shadow Windows commands (e.g. find, sort, link)
# link.exe conflict is mitigated by $msvcBinPath being prepended earlier in $basePaths
if (Test-Path "$msys64Root\usr\bin\bash.exe") {
    $basePaths += "$msys64Root\usr\bin"
}

$env:PATH = ($basePaths -join ";") + ";$env:PATH"

# =====================================================
# EXPLICIT TOOL ALIASES - All 4 Toolchains
# =====================================================

# --- MSVC Toolchain Aliases ---
if (Test-Path "$msvcBinPath\cl.exe") {
    Set-Alias -Name cl-msvc    -Value "$msvcBinPath\cl.exe"    -Force
    Set-Alias -Name link-msvc  -Value "$msvcBinPath\link.exe"  -Force
    Set-Alias -Name lib-msvc   -Value "$msvcBinPath\lib.exe"   -Force
    Set-Alias -Name nmake-msvc -Value "$msvcBinPath\nmake.exe" -Force
}

# --- MSYS2 GCC Toolchain Aliases ---
if (Test-Path "$msys64Root\ucrt64\bin\gcc.exe") {
    Set-Alias -Name gcc-msys -Value "$msys64Root\ucrt64\bin\gcc.exe"  -Force
    Set-Alias -Name g++-msys -Value "$msys64Root\ucrt64\bin\g++.exe"  -Force
    Set-Alias -Name ld-msys  -Value "$msys64Root\ucrt64\bin\ld.exe"   -Force
    Set-Alias -Name ar-msys  -Value "$msys64Root\ucrt64\bin\ar.exe"   -Force
}

# --- MSYS2 Clang Toolchain Aliases ---
if (Test-Path "$msys64Root\ucrt64\bin\clang.exe") {
    Set-Alias -Name clang-msys   -Value "$msys64Root\ucrt64\bin\clang.exe"   -Force
    Set-Alias -Name clang++-msys -Value "$msys64Root\ucrt64\bin\clang++.exe" -Force
    Set-Alias -Name lld-msys     -Value "$msys64Root\ucrt64\bin\lld.exe"     -Force
}

# --- Windows Clang Toolchain Aliases ---
if (Test-Path "$clangRoot\bin\clang.exe") {
    Set-Alias -Name clang-win     -Value "$clangRoot\bin\clang.exe"    -Force
    Set-Alias -Name clang++-win   -Value "$clangRoot\bin\clang++.exe"  -Force
    Set-Alias -Name clang-cl-win  -Value "$clangRoot\bin\clang-cl.exe" -Force
    Set-Alias -Name lld-link-win  -Value "$clangRoot\bin\lld-link.exe" -Force
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
    Set-Alias -Name python314 -Value "$pythonRoot\python.exe"        -Force
    Set-Alias -Name py314     -Value "$pythonRoot\python.exe"        -Force
    Set-Alias -Name pip314    -Value "$pythonRoot\Scripts\pip.exe"   -Force
}
if (Test-Path "$msys64Root\ucrt64\bin\python.exe") {
    Set-Alias -Name python-msys -Value "$msys64Root\ucrt64\bin\python.exe" -Force
    Set-Alias -Name pip-msys    -Value "$msys64Root\ucrt64\bin\pip.exe"    -Force
}

# --- Perl Alias ---
if (Test-Path "$perlRoot\perl\bin\perl.exe") {
    Set-Alias -Name perl-win -Value "$perlRoot\perl\bin\perl.exe" -Force
}

# --- NASM Alias ---
if (Test-Path "$nasmRoot\nasm.exe") {
    Set-Alias -Name nasm-win -Value "$nasmRoot\nasm.exe" -Force
}

if (Test-Path "$bisonRoot\win_bison.exe") {
    Set-Alias -Name bison-win -Value "$bisonRoot\win_bison.exe" -Force
    Set-Alias -Name flex-win  -Value "$bisonRoot\win_flex.exe"  -Force
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

function Reset-Toolchain {
    Write-Host "`n==> Resetting to default (no toolchain active)..." -ForegroundColor Cyan
    Remove-ToolchainPaths
    $varsToClear = @(
        'CC','CXX','CMAKE_C_COMPILER','CMAKE_CXX_COMPILER',
        'CMAKE_GENERATOR','CMAKE_MAKE_PROGRAM','CMAKE_LINKER',
        'INCLUDE','LIB','LINKER','LINK',
        'VCToolsInstallDir','VCToolsVersion','WindowsSDKVersion',
        'WindowsSdkBinPath','WindowsSDKDir',
        'VSCMD_ARG_HOST_ARCH','VSCMD_ARG_TGT_ARCH'
    )
    foreach ($v in $varsToClear) {
        Remove-Item "Env:\$v" -ErrorAction SilentlyContinue
    }
    Write-Host "✓ No toolchain active — same state as a fresh PowerShell window" -ForegroundColor Green
}
Set-Alias -Name use-none -Value Reset-Toolchain

# =====================================================
# Toolchain 1: Windows MSVC
# =====================================================
function Use-WindowsMSVC {
    Write-Host "`n==> Switching to Windows MSVC toolchain..." -ForegroundColor Cyan
    Write-Host "  MSVC: $vcToolsVersion  SDK: $windowsSDKVersion" -ForegroundColor Gray
    Remove-ToolchainPaths
    $msvcPaths = @(
        "$cmakeRoot\bin",
        "$msvcBinPath",
        "$windowsKitsRoot\bin\$windowsSDKVersion\$targetArch"
    )
    foreach ($path in $msvcPaths) {
        if (Test-Path $path) { $env:PATH = "$path;$env:PATH" }
    }
    $env:VSCMD_ARG_HOST_ARCH  = $hostArch
    $env:VSCMD_ARG_TGT_ARCH   = $targetArch
    $env:VCToolsVersion       = $vcToolsVersion
    $env:WindowsSDKVersion    = "$windowsSDKVersion\"
    $env:VCToolsInstallDir    = "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
    $env:WindowsSdkBinPath    = "$windowsKitsRoot\bin\"
    $env:WindowsSDKDir        = $windowsKitsRoot
    $env:INCLUDE = @(
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include",
        "$windowsKitsRoot\Include\$windowsSDKVersion\ucrt",
        "$windowsKitsRoot\Include\$windowsSDKVersion\shared",
        "$windowsKitsRoot\Include\$windowsSDKVersion\um",
        "$windowsKitsRoot\Include\$windowsSDKVersion\winrt"
    ) -join ";"
    $env:LIB = @(
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\$targetArch",
        "$windowsKitsRoot\Lib\$windowsSDKVersion\ucrt\$targetArch",
        "$windowsKitsRoot\Lib\$windowsSDKVersion\um\$targetArch"
    ) -join ";"
    $env:CMAKE_GENERATOR = "Ninja"
    $windowsNinja = "$cmakeRoot\bin\ninja.exe"
    if (Test-Path $windowsNinja) {
        $env:CMAKE_MAKE_PROGRAM = $windowsNinja
    } else {
        $env:CMAKE_GENERATOR    = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }
    $env:CC                = "$msvcBinPath\cl.exe"
    $env:CXX               = "$msvcBinPath\cl.exe"
    $env:CMAKE_C_COMPILER  = "$msvcBinPath\cl.exe"
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
    $msys2Paths = @( "$msys64Root\ucrt64\bin" )
    foreach ($path in $msys2Paths) {
        if (Test-Path $path) { $env:PATH = "$path;$env:PATH" }
    }
    $env:INCLUDE = "$msys64Root\ucrt64\include"
    $env:LIB     = "$msys64Root\ucrt64\lib"
    $env:CMAKE_GENERATOR    = "Ninja"
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
    $env:CC                 = "$msys64Root\ucrt64\bin\gcc.exe"
    $env:CXX                = "$msys64Root\ucrt64\bin\g++.exe"
    $env:CMAKE_C_COMPILER   = "$msys64Root\ucrt64\bin\gcc.exe"
    $env:CMAKE_CXX_COMPILER = "$msys64Root\ucrt64\bin\g++.exe"
    Remove-Item Env:\LINKER          -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK            -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER    -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Remove-Item Env:\WindowsSDKDir   -ErrorAction SilentlyContinue
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
    $msys2Paths = @( "$msys64Root\ucrt64\bin" )
    foreach ($path in $msys2Paths) {
        if (Test-Path $path) { $env:PATH = "$path;$env:PATH" }
    }
    $env:INCLUDE = "$msys64Root\ucrt64\include"
    $env:LIB     = "$msys64Root\ucrt64\lib"
    $env:CMAKE_GENERATOR    = "Ninja"
    $env:CMAKE_MAKE_PROGRAM = "$msys64Root\ucrt64\bin\ninja.exe"
    $env:CC                 = "$msys64Root\ucrt64\bin\clang.exe"
    $env:CXX                = "$msys64Root\ucrt64\bin\clang++.exe"
    $env:CMAKE_C_COMPILER   = "$msys64Root\ucrt64\bin\clang.exe"
    $env:CMAKE_CXX_COMPILER = "$msys64Root\ucrt64\bin\clang++.exe"
    Remove-Item Env:\LINKER          -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK            -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER    -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Remove-Item Env:\WindowsSDKDir   -ErrorAction SilentlyContinue
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
    $clangPaths = @(
        "$cmakeRoot\bin",
        "$clangRoot\bin",
        "$windowsKitsRoot\bin\$windowsSDKVersion\$targetArch"
    )
    foreach ($path in $clangPaths) {
        if (Test-Path $path) { $env:PATH = "$path;$env:PATH" }
    }
    $env:WindowsSDKVersion = "$windowsSDKVersion\"
    $env:WindowsSDKDir     = $windowsKitsRoot
    $env:INCLUDE = @(
        "$clangRoot\include",
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include",
        "$windowsKitsRoot\Include\$windowsSDKVersion\ucrt",
        "$windowsKitsRoot\Include\$windowsSDKVersion\shared",
        "$windowsKitsRoot\Include\$windowsSDKVersion\um"
    ) -join ";"
    $env:LIB = @(
        "$clangRoot\lib",
        "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\$targetArch",
        "$windowsKitsRoot\Lib\$windowsSDKVersion\ucrt\$targetArch",
        "$windowsKitsRoot\Lib\$windowsSDKVersion\um\$targetArch"
    ) -join ";"
    $env:CMAKE_GENERATOR    = "Ninja"
    $windowsNinja = "$cmakeRoot\bin\ninja.exe"
    if (Test-Path $windowsNinja) {
        $env:CMAKE_MAKE_PROGRAM = $windowsNinja
    } else {
        $env:CMAKE_GENERATOR    = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }
    $env:CC                  = "$clangRoot\bin\clang-cl.exe"
    $env:CXX                 = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_C_COMPILER    = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_CXX_COMPILER  = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_LINKER        = "$clangRoot\bin\lld-link.exe"
    Remove-Item Env:\LINKER          -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK            -ErrorAction SilentlyContinue
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
Set-Alias -Name use-msvc       -Value Use-WindowsMSVC
Set-Alias -Name use-gcc        -Value Use-MSYS2GCC
Set-Alias -Name use-clang-msys -Value Use-MSYS2Clang
Set-Alias -Name use-clang-win  -Value Use-WindowsClang

# =====================================================
# Rust/Cargo Update Function
# =====================================================
function Update-Cargo {
    $customPackages = @{
        'ripgrep' = @{ flags = '-C target-cpu=native'; features = '--all-features' }
        'xh'      = @{ flags = '--cfg reqwest_unstable'; features = '--all-features' }
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
        $oldRustFlags  = $env:RUSTFLAGS
        $env:RUSTFLAGS = $flags
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
# MysqlclientSrc Patch Function
# =====================================================

function Patch-MysqlclientSrc {
    $registryBase = "D:\Programs\cargo\registry\src"
    $opensslPath  = "D:/Programs/OpenSSL"
    $marker       = "PATCH5-OPENSSL4-PATH-FORCED"

    $srcDir = Get-ChildItem $registryBase -Depth 1 -Directory |
        Where-Object { $_.Name -like "mysqlclient-src-*" } |
        Select-Object -First 1

    if (-not $srcDir) {
        Write-Host "✗ mysqlclient-src not found in registry." -ForegroundColor Red
        Write-Host "  Run: cargo install diesel_cli --force --all-features (let it fail once)" -ForegroundColor Yellow
        return
    }
    Write-Host "  Found: $($srcDir.FullName)" -ForegroundColor Gray

    # ════════════════════════════════════════════════════════════════════
    # Patch 1 — build.rs: stop looking in Release\ subfolder for .lib
    # ════════════════════════════════════════════════════════════════════
    $buildRs = Get-ChildItem $srcDir.FullName -Recurse -Filter "build.rs" |
        Select-Object -First 1

    if (-not $buildRs) {
        Write-Host "  ⚠ Patch 1: build.rs not found" -ForegroundColor Yellow
    } else {
        attrib -r $buildRs.FullName 2>$null
        $content = Get-Content $buildRs.FullName -Raw
        if ($content -match [regex]::Escape('dst.push("Release");')) {
            $old1 = "    // on windows the library is in a different folder`n    if std::env::var(""CARGO_CFG_TARGET_ENV"").as_deref() == Ok(""msvc"") {`n        dst.push(""Release"");`n    }"
            $new1 = "    // on windows the library is in a different folder`n    // PATCH1: mysqlclient.lib lands directly in archive_output_directory`n    // if std::env::var(""CARGO_CFG_TARGET_ENV"").as_deref() == Ok(""msvc"") {`n    //     dst.push(""Release"");`n    // }"
            $content = $content.Replace($old1, $new1)
            [System.IO.File]::WriteAllText($buildRs.FullName, $content, [System.Text.Encoding]::UTF8)
            Write-Host "  ✓ Patch 1: build.rs Release\ path removed" -ForegroundColor Green
        } else {
            Write-Host "  ✓ Patch 1: Already applied (build.rs)" -ForegroundColor Cyan
        }
    }

    # ════════════════════════════════════════════════════════════════════
    # Patches 2-5 — ssl.cmake  (LF-only file, spaces not tabs)
    # ════════════════════════════════════════════════════════════════════
    $sslCmake = Get-ChildItem $srcDir.FullName -Recurse -Filter "ssl.cmake" |
        Select-Object -First 1

    if (-not $sslCmake) {
        Write-Host "  ⚠ ssl.cmake not found" -ForegroundColor Yellow
        return
    }

    attrib -r $sslCmake.FullName 2>$null
    # Read as bytes and decode as UTF8 to preserve LF-only line endings
    $bytes   = [System.IO.File]::ReadAllBytes($sslCmake.FullName)
    $content = [System.Text.Encoding]::UTF8.GetString($bytes)
    $changed = $false
    $LF      = "`n"   # single LF — matches the file's actual line endings

    # ── Patch 2: version gate accepts OpenSSL major=4 ────────────────────
    $old2 = "IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3)"
    $new2 = "IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3 OR OPENSSL_VERSION_MAJOR VERSION_EQUAL 4)"
    if ($content -match [regex]::Escape($old2)) {
        $content = $content.Replace($old2, $new2)
        $changed = $true
        Write-Host "  ✓ Patch 2: Version gate extended to OpenSSL major=4" -ForegroundColor Green
    } else {
        Write-Host "  ✓ Patch 2: Already applied" -ForegroundColor Cyan
    }

    # ── Patch 3: FIND_OPENSSL_VERSION — fix for OpenSSL 4.x header ───────
    # File uses LF only. Indentation: 2 spaces outer, 4 spaces inner, 6 deep.
    $old3 = "MACRO(FIND_OPENSSL_VERSION)${LF}  FOREACH(version_part${LF}      OPENSSL_VERSION_MAJOR${LF}      OPENSSL_VERSION_MINOR${LF}      OPENSSL_VERSION_PATCH${LF}      )${LF}    FILE(STRINGS `"`${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h`" `${version_part}${LF}      REGEX `"^#[\t ]*define[\t ]+`${version_part}[\t ]+([0-9]+).*`")${LF}    STRING(REGEX REPLACE${LF}      `"^.*`${version_part}[\t ]+([0-9]+).*`" `"\\1`"${LF}      `${version_part} `"`${`${version_part}}`")${LF}  ENDFOREACH()"
    $new3 = "MACRO(FIND_OPENSSL_VERSION)${LF}  # PATCH3: handle OpenSSL 4.x '# define NAME  VALUE' format${LF}  FOREACH(version_part${LF}      OPENSSL_VERSION_MAJOR${LF}      OPENSSL_VERSION_MINOR${LF}      OPENSSL_VERSION_PATCH${LF}      )${LF}    FILE(STRINGS `"`${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h`" _version_line${LF}      REGEX `"^#[ \t]*define[ \t]+`${version_part}[ \t]+[0-9]+`")${LF}    IF(_version_line)${LF}      STRING(REGEX REPLACE${LF}        `"^.*define[ \t]+`${version_part}[ \t]+([0-9]+).*$`" `"\\1`"${LF}        `${version_part} `"`${_version_line}`")${LF}    ELSE()${LF}      SET(`${version_part} `"0`")${LF}    ENDIF()${LF}  ENDFOREACH()"

    if ($content -match 'PATCH3') {
        Write-Host "  ✓ Patch 3: Already applied (FIND_OPENSSL_VERSION)" -ForegroundColor Cyan
    } elseif ($content.Contains($old3)) {
        $content = $content.Replace($old3, $new3)
        $changed = $true
        Write-Host "  ✓ Patch 3: FIND_OPENSSL_VERSION fixed for OpenSSL 4.x" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Patch 3: block not matched — trying alternate approach" -ForegroundColor Yellow
        # Alternate: use regex replace on the FOREACH block directly
        $pattern3 = '(?s)(MACRO\(FIND_OPENSSL_VERSION\)\n  FOREACH\(version_part.*?ENDFOREACH\(\))'
        if ($content -match $pattern3) {
            $old3block = $Matches[1]
            $new3block = $old3block `
                -replace 'FILE\(STRINGS "\$\{OPENSSL_INCLUDE_DIR\}/openssl/opensslv\.h" \$\{version_part\}\n      REGEX "\^#\[\\t \]\*define\[\\t \]\+\$\{version_part\}\[\\t \]\+\(\[0-9\]\+\)\.\*"\)', `
                         "FILE(STRINGS `"`${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h`" _version_line${LF}      REGEX `"^#[ \t]*define[ \t]+`${version_part}[ \t]+[0-9]+`")" `
                -replace 'STRING\(REGEX REPLACE\n      "\^\.\*\$\{version_part\}\[\\t \]\+\(\[0-9\]\+\)\.\*" "\\\\1"\n      \$\{version_part\} "\$\{\$\{version_part\}\}"\)', `
                         "IF(_version_line)${LF}      STRING(REGEX REPLACE${LF}        `"^.*define[ \t]+`${version_part}[ \t]+([0-9]+).*$`" `"\\1`"${LF}        `${version_part} `"`${_version_line}`")${LF}    ELSE()${LF}      SET(`${version_part} `"0`")${LF}    ENDIF()"
            if ($old3block -ne $new3block) {
                $content = $content.Replace($old3block, $new3block)
                $changed = $true
                Write-Host "  ✓ Patch 3: Applied via regex alternate" -ForegroundColor Green
            } else {
                Write-Host "  ✗ Patch 3: Could not apply — manual edit required" -ForegroundColor Red
            }
        }
    }

    # ── Patch 4: DLL suffix -4-x64 for OpenSSL 4.x ───────────────────────
    # Actual indentation from file: 6 spaces before IF, 8 spaces before SET
    $old4 = "      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 1 AND${LF}         OPENSSL_VERSION_MINOR VERSION_EQUAL 1)${LF}        SET(SSL_MSVC_VERSION_SUFFIX `"-1_1`")${LF}        SET(SSL_MSVC_ARCH_SUFFIX `"-x64`")${LF}      ENDIF()"
    $new4 = "      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 1 AND${LF}         OPENSSL_VERSION_MINOR VERSION_EQUAL 1)${LF}        SET(SSL_MSVC_VERSION_SUFFIX `"-1_1`")${LF}        SET(SSL_MSVC_ARCH_SUFFIX `"-x64`")${LF}      ENDIF()${LF}      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3)${LF}        SET(SSL_MSVC_VERSION_SUFFIX `"-3`")${LF}        SET(SSL_MSVC_ARCH_SUFFIX `"-x64`")${LF}      ENDIF()${LF}      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 4)${LF}        SET(SSL_MSVC_VERSION_SUFFIX `"-4`")${LF}        SET(SSL_MSVC_ARCH_SUFFIX `"-x64`")${LF}      ENDIF()"

    if ($content -match 'VERSION_SUFFIX "-4"') {
        Write-Host "  ✓ Patch 4: Already applied (DLL suffix -4-x64)" -ForegroundColor Cyan
    } elseif ($content.Contains($old4)) {
        $content = $content.Replace($old4, $new4)
        $changed = $true
        Write-Host "  ✓ Patch 4: DLL suffix -4-x64 added" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Patch 4: block not matched" -ForegroundColor Yellow
    }

    # ── Patch 5: Force OPENSSL_ROOT_DIR in FIND_CUSTOM_OPENSSL ───────────
    # Inject at top of function, before WITH_SSL_PATH block
    # Exact text from raw dump: FUNCTION(FIND_CUSTOM_OPENSSL)[LF][LF][SP][SP]IF(WITH_SSL_PATH)
    if ($content -match [regex]::Escape($marker)) {
        Write-Host "  ✓ Patch 5: Already applied (OPENSSL_ROOT_DIR forced)" -ForegroundColor Cyan
    } else {
        $old5 = "FUNCTION(FIND_CUSTOM_OPENSSL)${LF}${LF}  IF(WITH_SSL_PATH)"
        $new5 = "FUNCTION(FIND_CUSTOM_OPENSSL)${LF}  # ${marker}${LF}  SET(OPENSSL_ROOT_DIR `"${opensslPath}`" CACHE PATH `"Forced portable OpenSSL 4.x`" FORCE)${LF}  SET(WITH_SSL_PATH `"${opensslPath}`" CACHE PATH `"Forced portable OpenSSL 4.x`" FORCE)${LF}${LF}  IF(WITH_SSL_PATH)"
        if ($content.Contains($old5)) {
            $content = $content.Replace($old5, $new5)
            $changed = $true
            Write-Host "  ✓ Patch 5: OPENSSL_ROOT_DIR forced to $opensslPath" -ForegroundColor Green
        } else {
            Write-Host "  ⚠ Patch 5: FIND_CUSTOM_OPENSSL opening not matched" -ForegroundColor Yellow
        }
    }

    if ($changed) {
        $outBytes = [System.Text.Encoding]::UTF8.GetBytes($content)
        [System.IO.File]::WriteAllBytes($sslCmake.FullName, $outBytes)
        Write-Host "✓ ssl.cmake written: $($sslCmake.FullName)" -ForegroundColor Green
    } else {
        Write-Host "✓ ssl.cmake: All patches already applied, no changes written" -ForegroundColor Cyan
    }

    Write-Host ""
    Write-Host "Now run: cargo install diesel_cli --force --all-features" -ForegroundColor Yellow
}



# =====================================================
# npm Global Package Update Function
# =====================================================

# Packages with install scripts that are safe to auto-approve
$npmSafeScriptPackages = @("yarn", "node-gyp", "esbuild", "pnpm")

function Update-GlobalNpm {
    # 1. Pre-flight: Unblock npm/npx PowerShell wrappers only
    if (Test-Path $nodejsRoot) {
        Write-Host "Checking for blocked scripts in $nodejsRoot..." -ForegroundColor Gray
        Get-ChildItem -Path $nodejsRoot -Filter "*.ps1" -ErrorAction SilentlyContinue | Unblock-File
        Get-ChildItem -Path $nodejsRoot -Filter "*.cmd" -ErrorAction SilentlyContinue | Unblock-File
    }

    if (Get-Command npm -ErrorAction SilentlyContinue) {
        Write-Host "`nUpdating global npm packages..." -ForegroundColor Cyan
        try {
            npm config set prefix $nodejsRoot
            $json = npm list -g --depth=0 --json 2>$null | ConvertFrom-Json
            if ($json.dependencies) {
                $pkgs = $json.dependencies.PSObject.Properties.Name
            } elseif ($json.node_modules) {
                $pkgs = $json.node_modules.PSObject.Properties.Name
            } else {
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
            $pkgs | Out-File "$env:USERPROFILE\npm-global-packages.txt" -Force
            Write-Host "  Package list saved to npm-global-packages.txt" -ForegroundColor Gray
            foreach ($pkg in $pkgs) {
                if ($pkg -in @("npm", "npx", "corepack")) {
                    Write-Host "  Skipping $pkg (managed by Node.js installer)" -ForegroundColor Gray
                    continue
                }
                Write-Host "  Updating $pkg..." -ForegroundColor Yellow
                npm install -g "$pkg@latest"
            }

            # 2. Post-install: auto-approve install scripts for known-safe packages
            Write-Host "`nChecking for pending install scripts..." -ForegroundColor Gray
            $pendingRaw = npm approve-scripts --allow-scripts-pending 2>&1
            $pendingPkgs = $pendingRaw | Select-String '^\s+(\S+@\S+)' | ForEach-Object {
                $_.Matches[0].Groups[1].Value -replace '@[\d.]+.*$', ''
            } | Sort-Object -Unique

            foreach ($pending in $pendingPkgs) {
                # Strip version suffix for comparison (e.g. "yarn" from "yarn@1.22.22")
                $baseName = $pending -replace '@.*$', ''
                if ($baseName -in $npmSafeScriptPackages) {
                    Write-Host "  Auto-approving install script for: $pending" -ForegroundColor Yellow
                    npm approve-scripts $baseName
                    Write-Host "  ✓ Approved: $pending" -ForegroundColor Green
                } else {
                    Write-Host "  ⚠ Skipped (not in safe list): $pending" -ForegroundColor DarkYellow
                    Write-Host "    Run manually: npm approve-scripts $baseName" -ForegroundColor Gray
                }
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
    Write-Host "  ✓ Node.js:    $nodeVer" -ForegroundColor Green
}
if ($pythonRoot) {
    $pythonVer = & python --version 2>&1
    Write-Host "  ✓ Python:     $pythonVer" -ForegroundColor Green
}
if (Test-Path "$perlRoot\perl\bin\perl.exe") {
    $perlVer = & "$perlRoot\perl\bin\perl.exe" --version 2>&1 | Select-String "v\d+\.\d+\.\d+"
    Write-Host "  ✓ Perl:       $perlVer" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Perl:       not found at $perlRoot" -ForegroundColor Red
}
if (Test-Path "$nasmRoot\nasm.exe") {
    $nasmVer = & "$nasmRoot\nasm.exe" --version 2>&1
    Write-Host "  ✓ NASM:       $nasmVer" -ForegroundColor Green
} else {
    Write-Host "  ⚠ NASM:       not found at $nasmRoot" -ForegroundColor Red
}

if (Test-Path "$bisonRoot\win_bison.exe") {
    $bisonVer = & "$bisonRoot\win_bison.exe" --version 2>&1 | Select-Object -First 1
    Write-Host "  ✓ Bison:   $bisonVer" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Bison:   not found at $bisonRoot" -ForegroundColor Red
}

if (Test-Path "$opensslRoot\include\openssl\ssl.h") {
    $opensslVer = (Get-Content "$opensslRoot\include\openssl\opensslv.h" -ErrorAction SilentlyContinue |
                   Select-String 'OPENSSL_VERSION_STR') -replace '.*"(.*)".*', '$1'
    Write-Host "  ✓ OpenSSL:    $opensslVer" -ForegroundColor Green
} else {
    Write-Host "  ⚠ OpenSSL:    not found at $opensslRoot" -ForegroundColor Red
}
if (Test-Path "$mysqlRoot\lib\libmysql.lib") {
    Write-Host "  ✓ MySQL:      client at $mysqlRoot" -ForegroundColor Green
} else {
    Write-Host "  ⚠ MySQL:      not found at $mysqlRoot" -ForegroundColor Red
}
if (Test-Path "$postgresRoot\lib\libpq.lib") {
    Write-Host "  ✓ PostgreSQL: client at $postgresRoot" -ForegroundColor Green
} else {
    Write-Host "  ⚠ PostgreSQL: not found at $postgresRoot" -ForegroundColor Red
}

Write-Host "`nToolchain Switching (sets PATH + environment):" -ForegroundColor Yellow
Write-Host "  use-msvc         → MSVC (D:\dev\msvc\...)" -ForegroundColor White
Write-Host "  use-gcc          → MSYS2 GCC (D:\Programs\msys64\ucrt64\...)" -ForegroundColor White
Write-Host "  use-clang-msys   → MSYS2 Clang (D:\Programs\msys64\ucrt64\...)" -ForegroundColor White
Write-Host "  use-clang-win    → Windows Clang (D:\Programs\clang\... + D:\Programs\cmake\...)" -ForegroundColor White

Write-Host "`nUpdate Commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo     → Update Rust/Cargo packages" -ForegroundColor White
Write-Host "  Patch-MysqlclientSrc  → Patch mysqlclient-src build.rs for Windows MSVC" -ForegroundColor White
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
Write-Host "  Perl:" -ForegroundColor Cyan
Write-Host "    perl-win" -ForegroundColor White
Write-Host "  NASM:" -ForegroundColor Cyan
Write-Host "    nasm-win" -ForegroundColor White
Write-Host "  Bison/Flex:" -ForegroundColor Cyan
Write-Host "    bison-win, flex-win" -ForegroundColor White
Write-Host "`nUsage Examples:" -ForegroundColor Yellow
Write-Host "  # Switch toolchain then build normally" -ForegroundColor Cyan
Write-Host "  use-msvc" -ForegroundColor White
Write-Host "  cmake -B build && cmake --build build" -ForegroundColor White
Write-Host ""
Write-Host "  # Or use explicit alias without switching" -ForegroundColor Cyan
Write-Host "  clang-msys++ -o test test.cpp" -ForegroundColor White

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host ""
