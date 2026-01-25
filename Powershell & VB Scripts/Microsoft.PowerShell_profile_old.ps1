# =====================================================
# Base Path Configuration
# =====================================================
$msvcRoot = "D:\dev\msvc"
$clangRoot = "D:\Programs\clang"
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

# Compiler paths (medium priority)
$compilerPaths = @(
    "$clangRoot\bin"
    "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\bin\Host$hostArch\$targetArch"
    "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch"
    "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch\ucrt"
)

# MSYS2 paths (LOWEST PRIORITY - these go LAST)
$msys2Paths = @(
    "$msys64Root\ucrt64\bin"
    "$msys64Root\usr\bin"
)

# Remove any existing instances of these paths from PATH to avoid duplicates
$pathsToClean = $nodejsPaths + $pythonPaths + $compilerPaths + $msys2Paths
$currentPathArray = $env:PATH -split ';'
$cleanedPath = $currentPathArray | Where-Object { 
    $currentItem = $_
    -not ($pathsToClean | Where-Object { $currentItem -eq $_ })
}
$env:PATH = $cleanedPath -join ';'

# Add paths in correct priority order: Node.js → Python → Compilers → MSYS2
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
# Auto-alias .exe versions over scripts (MSYS2 tools only)
# =====================================================
$ucrt64Tools = @('meson', 'ninja', 'pkgconf')

foreach ($tool in $ucrt64Tools) {
    $exePath = "$msys64Root\ucrt64\bin\$tool.exe"
    if (Test-Path $exePath) {
        Set-Alias -Name $tool -Value $exePath -Force -Option AllScope
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
# Compiler Aliases
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

Write-Host "`nAvailable custom commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo  - Update Rust/Cargo packages" -ForegroundColor White

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
