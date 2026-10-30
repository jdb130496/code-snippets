# Added: $cmakeRoot\bin added to $basePaths (before Python Scripts to prevent pip cmake shadowing)
# Added: Update-WinCmake — builds cmake from source via clang-win + WARP; handles fresh/broken/update automatically
# Added: $ninjaRoot  = "D:\Programs\ninja"
# Added: $mesonRoot  = "D:\Programs\meson"
# Changed: use-msvc, use-clang-win now prefer standalone ninja over cmake-bundled ninja
# Changed: meson-win alias resolves standalone meson first, pip meson as fallback
# Changed: Remove-ToolchainPaths now also strips ninjaRoot from PATH on switch
# Changed: ninja-win alias now points to standalone ninja (D:\Programs\ninja\ninja.exe)
#          ninja-cmake alias added for cmake-bundled ninja (D:\Programs\cmake\bin\ninja.exe)
#
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
$ninjaRoot   = "D:\Programs\ninja"
$mesonRoot   = "D:\Programs\meson"
$msys64Root  = "D:\Programs\msys64"
$nodejsRoot  = "D:\Programs\nodejs"
$perlRoot    = "D:\Programs\Perl"
$nasmRoot    = "D:\Programs\nasm"
$opensslRoot = "D:\Programs\OpenSSL"
$mysqlRoot   = "D:\Programs\mysql"
$postgresRoot = "D:\Programs\postgre"
$sqliteRoot  = "D:\Programs\sqlite"
$bisonRoot   = "D:\Programs\winflexbison"
$jomRoot     = "D:\Programs\jom"
$mingitRoot  = "D:\Programs\MinGit"
$rustRoot  = "D:\Programs\rustup"
$cargoRoot = "D:\Programs\cargo"
$bzip2Root   = "D:\Programs\bzip2"
$zlibRoot    = "D:\Programs\zlib"
$popplerRoot = "D:\Programs\poppler"
$pandocRoot = "D:\Programs\pandoc"

# =====================================================
# Python - Direct path
# =====================================================
$pythonRoot = "D:\Programs\Python"
$hostArch   = "x64"
$targetArch = "x64"

# =====================================================
# Git SSL - point MinGit to Python's certifi CA bundle
# =====================================================
$_certCacheFile = "$env:TEMP\ps_certifi_path.txt"
if (Test-Path $_certCacheFile) {
    $_certBundle = (Get-Content $_certCacheFile -Raw).Trim()
} else {
    $_certBundle = & "$pythonRoot\python.exe" -c "import certifi; print(certifi.where())" 2>$null
    if ($_certBundle) { $_certBundle | Set-Content $_certCacheFile }
}
if ($_certBundle -and (Test-Path $_certBundle)) {
    $env:GIT_SSL_CAINFO = $_certBundle
}

# =====================================================
# Rustup mirror - auto-select based on WARP state
# =====================================================
$_warpTrace = & curl.exe -s --max-time 3 https://www.cloudflare.com/cdn-cgi/trace 2>&1
if ($_warpTrace -match "warp=on") {
    $env:RUSTUP_DIST_SERVER = "https://static.rust-lang.org"             # Cloudflare CDN — WARP helps
} else {
    $env:RUSTUP_DIST_SERVER = "https://cloudfront-static.rust-lang.org"  # AWS CloudFront — faster without WARP
}

# Auto-detect MSVC tools version (highest installed)
$vcToolsVersion = Get-ChildItem "$msvcRoot\VC\Tools\MSVC" -Directory -ErrorAction SilentlyContinue |
                  Sort-Object Name -Descending | Select-Object -First 1 -ExpandProperty Name
if (-not $vcToolsVersion) { $vcToolsVersion = "14.53.36911" }  # fallback

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
# Resolve preferred standalone ninja path for Windows toolchains
# Priority: standalone D:\Programs\ninja > cmake-bundled D:\Programs\cmake\bin
# MSYS2 toolchains always use their own ucrt64\bin\ninja.exe (unchanged)
# =====================================================

function Update-WinNinja {
    $savedPath    = $env:PATH
    $savedCC      = $env:CC
    $savedCXX     = $env:CXX
    $savedINCLUDE = $env:INCLUDE
    $savedLIB     = $env:LIB
    $savedCMakeC  = $env:CMAKE_C_COMPILER
    $savedCMakeCX = $env:CMAKE_CXX_COMPILER
    $savedCMakeG  = $env:CMAKE_GENERATOR
    $savedCMakeMk = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn = $env:CMAKE_LINKER
    $savedLocation = Get-Location

    try {
        use-clang-win

        $ninjaRepo = "$env:USERPROFILE\dev\ninja-src"

        if (Test-Path "$ninjaRepo\.git") {
            Write-Host "==> Updating ninja source..." -ForegroundColor Cyan
            git -C $ninjaRepo pull
            if ($LASTEXITCODE -ne 0) {
                Write-Host "✗ git pull failed" -ForegroundColor Red
                return
            }
        } else {
            if (Test-Path $ninjaRepo) {
                Write-Host "==> Removing invalid ninja source directory..." -ForegroundColor Yellow
                Remove-Item $ninjaRepo -Recurse -Force
            }
            Write-Host "==> Cloning ninja source..." -ForegroundColor Cyan
            git clone https://github.com/ninja-build/ninja.git $ninjaRepo
            if ($LASTEXITCODE -ne 0) {
                Write-Host "✗ git clone failed" -ForegroundColor Red
                return
            }
        }

        # Clean previous build directory
        if (Test-Path "$ninjaRepo\build") {
            Write-Host "==> Cleaning previous build..." -ForegroundColor Yellow
            Remove-Item "$ninjaRepo\build" -Recurse -Force
        }

        Write-Host "==> Configuring..." -ForegroundColor Cyan
        cmake -B "$ninjaRepo\build" -S $ninjaRepo -G Ninja `
            -DCMAKE_BUILD_TYPE=Release `
            -DCMAKE_C_COMPILER="$clangRoot\bin\clang-cl.exe" `
            -DCMAKE_CXX_COMPILER="$clangRoot\bin\clang-cl.exe" `
            -DCMAKE_LINKER="$clangRoot\bin\lld-link.exe"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake configure failed" -ForegroundColor Red
            return
        }

        Write-Host "==> Building..." -ForegroundColor Cyan
        cmake --build "$ninjaRepo\build" --config Release

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake build failed" -ForegroundColor Red
            return
        }

        $builtExe = "$ninjaRepo\build\ninja.exe"
        if (Test-Path $builtExe) {
            New-Item -ItemType Directory -Force -Path "$ninjaRoot\bin" | Out-Null
            Copy-Item $builtExe "$ninjaRoot\bin\ninja.exe" -Force
            Write-Host "✓ Ninja $(& "$ninjaRoot\bin\ninja.exe" --version) installed to $ninjaRoot\bin\ninja.exe" -ForegroundColor Green
        } else {
            Write-Host "✗ ninja.exe not found at $builtExe after build" -ForegroundColor Red
        }

    } finally {
        $env:PATH               = $savedPath
        $env:CC                 = $savedCC
        $env:CXX                = $savedCXX
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_C_COMPILER   = $savedCMakeC
        $env:CMAKE_CXX_COMPILER = $savedCMakeCX
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCMakeLn) { $env:CMAKE_LINKER = $savedCMakeLn }
        else { Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue }
        Set-Location $savedLocation
    }
}

# Resolve preferred meson path
# Priority: standalone D:\Programs\meson > pip D:\Programs\Python\Scripts

function Update-WinMeson {
    param([switch]$Update)
    if ($Update) {
        # Point git to Python's certifi CA bundle to fix TLS on MinGit
        $certBundle = & "$pythonRoot\python.exe" -c "import certifi; print(certifi.where())" 2>$null
        if ($certBundle -and (Test-Path $certBundle)) { $env:GIT_SSL_CAINFO = $certBundle }

        Set-Location D:\dev\meson-src
        git pull
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "git pull failed (exit $LASTEXITCODE) — meson.pyz will NOT be updated"
            Set-Location D:\
            return
        }
        & "$pythonRoot\python.exe" packaging\create_zipapp.py --outfile "$mesonRoot\meson.pyz" --compress
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "create_zipapp.py failed — meson.pyz NOT updated"
            Set-Location D:\
            return
        }
        Write-Host "✓ Meson updated to $(& "$pythonRoot\python.exe" "$mesonRoot\meson.pyz" --version)" -ForegroundColor Green
        Set-Location D:\

        # Rebuild shim exe after update so it stays in sync
        Remove-Item "$mesonRoot\meson.exe" -Force -ErrorAction SilentlyContinue
        if (Test-Path "$mesonRoot\meson.exe") {
            Write-Warning "meson.exe is in use and could not be replaced — close any running meson/pip and retry"
        }
    }

    # Create meson.exe shim if it doesn't exist.
    # The shim runs meson.pyz but tells Meson that *meson.exe* is the launcher, so build.ninja
    # records a real Windows executable (a .pyz cannot be started by CreateProcess).
    if (-not (Test-Path "$mesonRoot\meson.exe")) {
        $shimScript = "$env:TEMP\meson_shim.py"
        Set-Content $shimScript @"
import sys, subprocess

SELF = r'$mesonRoot\meson.exe'
PYZ  = r'$mesonRoot\meson.pyz'
PY   = r'$pythonRoot\python.exe'

code = (
    "import sys; sys.path.insert(0, sys.argv[1]); "
    "from mesonbuild import mesonmain; "
    "sys.exit(mesonmain.run(sys.argv[3:], sys.argv[2]))"
)
result = subprocess.run([PY, '-c', code, PYZ, SELF] + sys.argv[1:], check=False)
sys.exit(result.returncode)
"@
        $shimLog = "$env:TEMP\meson_shim_build.log"
        & "$pythonRoot\python.exe" -m PyInstaller --onefile --name meson_git $shimScript `
            --distpath "$mesonRoot" --workpath "$env:TEMP\meson_shim_build" --specpath "$env:TEMP" -y *> $shimLog

        if (Test-Path "$mesonRoot\meson_git.exe") {
            Rename-Item "$mesonRoot\meson_git.exe" "$mesonRoot\meson.exe" -Force
            $ver = & "$mesonRoot\meson.exe" --version 2>&1
            if ($LASTEXITCODE -eq 0) {
                Write-Host "✓ meson.exe shim created (reports $ver)" -ForegroundColor Green
            } else {
                Write-Warning "meson.exe shim built but '--version' failed: $ver"
            }
        } else {
            Write-Warning "PyInstaller failed — meson.exe NOT created. See $shimLog"
        }
    }

    if (Test-Path "$mesonRoot\meson.exe") { return "$mesonRoot\meson.exe" }
    if (Test-Path "$mesonRoot\meson.cmd") { return "$mesonRoot\meson.cmd" }
    if (Test-Path "$mesonRoot\meson.pyz") { return "$mesonRoot\meson.pyz" }
    if (Test-Path "$pythonRoot\Scripts\meson.exe") { return "$pythonRoot\Scripts\meson.exe" }
    return $null
}

# =====================================================
# Added: Update-WinCmake function to build cmake from source via clang-win
# Added: cmake-src expected at D:\dev\cmake-src (git clone https://gitlab.kitware.com/cmake/cmake)
# Changed: cmake --install targets $cmakeRoot (D:\Programs\cmake) — overwrites in place
# =====================================================

function Update-WinCmake {
    $warpCli = "C:\Program Files\Cloudflare\Cloudflare WARP\warp-cli.exe"
    $warpWasConnected = $false
    if (Test-Path $warpCli) {
        $trace = & curl.exe -s --max-time 3 https://www.cloudflare.com/cdn-cgi/trace 2>&1
        if ($trace -match "warp=on") {
            $warpWasConnected = $true
            Write-Host "  WARP already active (confirmed warp=on)" -ForegroundColor Cyan
        } else {
            & $warpCli disconnect | Out-Null
            Start-Sleep -Seconds 1
            & $warpCli connect | Out-Null
            Write-Host "  WARP connecting..." -ForegroundColor Cyan
            $elapsed = 0
            do {
                Start-Sleep -Seconds 1
                $elapsed++
                $trace = & curl.exe -s --max-time 3 https://www.cloudflare.com/cdn-cgi/trace 2>&1
            } until (($trace -match "warp=on") -or ($elapsed -ge 15))
            if ($trace -match "warp=on") {
                Write-Host "  ✓ WARP tunnel confirmed (warp=on)" -ForegroundColor Green
            } else {
                Write-Warning "WARP tunnel not confirmed after 15s — proceeding anyway"
            }
        }
    } else {
        Write-Warning "warp-cli not found at $warpCli"
    }

    $savedPath    = $env:PATH
    $savedCC      = $env:CC
    $savedCXX     = $env:CXX
    $savedINCLUDE = $env:INCLUDE
    $savedLIB     = $env:LIB
    $savedCMakeG  = $env:CMAKE_GENERATOR
    $savedCMakeMk = $env:CMAKE_MAKE_PROGRAM

    try {
        if (-not (Test-Path D:\dev\cmake-src)) {
            Write-Host "  No existing repo found — cloning fresh..." -ForegroundColor Cyan
            git clone https://gitlab.kitware.com/cmake/cmake D:\dev\cmake-src
        } else {
            $isValidRepo = & git -C D:\dev\cmake-src rev-parse --git-dir 2>&1
            if ($LASTEXITCODE -ne 0) {
                Write-Host "  Incomplete clone detected — removing and re-cloning..." -ForegroundColor Yellow
                Remove-Item D:\dev\cmake-src -Recurse -Force
                git clone https://gitlab.kitware.com/cmake/cmake D:\dev\cmake-src
            } else {
                Write-Host "  Existing repo found — pulling latest..." -ForegroundColor Cyan
                git -C D:\dev\cmake-src pull
            }
        }

        use-clang-win
        Set-Location D:\dev\cmake-src

        cmake -B build -G Ninja `
          -DCMAKE_BUILD_TYPE=Release `
          -DCMAKE_C_COMPILER="$clangRoot\bin\clang-cl.exe" `
          -DCMAKE_CXX_COMPILER="$clangRoot\bin\clang-cl.exe" `
          -DCMAKE_LINKER="$clangRoot\bin\lld-link.exe" `
          -DCMAKE_INSTALL_PREFIX="D:\Programs\cmake"
        cmake --build build --config Release --parallel
        # Rename old binaries to avoid lock conflicts during install
        foreach ($exe in @("cmake.exe", "ctest.exe", "cpack.exe", "cmake-gui.exe")) {
            $target = "$cmakeRoot\bin\$exe"
            if (Test-Path $target) {
                Rename-Item $target "$target.bak" -Force -ErrorAction SilentlyContinue
            }
        }
        cmake --install build
        # Remove backups if install succeeded
        foreach ($exe in @("cmake.exe", "ctest.exe", "cpack.exe", "cmake-gui.exe")) {
            $bak = "$cmakeRoot\bin\$exe.bak"
            if (Test-Path $bak) { Remove-Item $bak -Force -ErrorAction SilentlyContinue }
        }

        Write-Host "✓ CMake built and installed to $cmakeRoot" -ForegroundColor Green
        Write-Host "  Version: $(& "$cmakeRoot\bin\cmake.exe" --version | Select-Object -First 1)" -ForegroundColor Green
    } finally {
        $env:PATH               = $savedPath
        $env:CC                 = $savedCC
        $env:CXX                = $savedCXX
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk

        if ((Test-Path $warpCli) -and -not $warpWasConnected) {
            & $warpCli disconnect | Out-Null
            Write-Host "  WARP disconnected." -ForegroundColor Cyan
        }

        Set-Location D:\
    }
}

#======================================================
#Mingit Building From Source
#======================================================
function Update-WinGit {
    param([switch]$Update)
    if ($Update) {
        $release = Invoke-RestMethod "https://api.github.com/repos/git-for-windows/git/releases/latest"
        $asset = $release.assets | Where-Object { $_.name -like "*MinGit*64-bit*" } | Select-Object -First 1
        if ($asset) {
            $zip     = "$env:TEMP\mingit.zip"
            $tempDir = "$env:TEMP\mingit-extract"
            $destDir = "D:\Programs\MinGit"

            Get-Process -Name "git", "git-remote-https" -ErrorAction SilentlyContinue | Stop-Process -Force

            Invoke-WebRequest $asset.browser_download_url -OutFile $zip

            if (Test-Path $tempDir) { Remove-Item $tempDir -Recurse -Force }
            Expand-Archive $zip -DestinationPath $tempDir -Force
            Remove-Item $zip

            robocopy $tempDir $destDir /E /IS /IT /IM /MOVE /NP /NFL /NDL /NJH /NJS | Out-Null

            # Replant libpcre2-8-0.dll which MinGit zip does not include
            $pcre2Usr  = "D:\Programs\msys64\usr\bin\libpcre2-8-0.dll"
            $pcre2Ucrt = "D:\Programs\msys64\ucrt64\bin\libpcre2-8-0.dll"
            if (Test-Path $pcre2Usr) {
                Copy-Item $pcre2Usr "$destDir\bin\libpcre2-8-0.dll" -Force
                Write-Host "  ✓ Planted libpcre2-8-0.dll into MinGit\bin" -ForegroundColor Green
            }
            if (Test-Path $pcre2Ucrt) {
                Copy-Item $pcre2Ucrt "$destDir\libexec\git-core\libpcre2-8-0.dll" -Force
                Write-Host "  ✓ Planted libpcre2-8-0.dll into MinGit\libexec\git-core" -ForegroundColor Green
            }

            Write-Host "✓ MinGit updated to $(& "$destDir\cmd\git.exe" --version)" -ForegroundColor Green
        } else {
            Write-Host "⚠ No MinGit asset found in latest release" -ForegroundColor Red
        }
    }
    if (Test-Path "D:\Programs\MinGit\cmd\git.exe") { return "D:\Programs\MinGit\cmd\git.exe" }
    if (Get-Command git -ErrorAction SilentlyContinue) { return (Get-Command git).Source }
    return $null
}

function Update-WinGit-Msys {
    $log      = "D:\dev\build-git.log"
    $stageDir = "D:\dev\git-stage"

    Write-Host "Building git via MSYS2 ucrt64 (clang)..." -ForegroundColor Cyan

    # Backup existing install — bin\* AND libexec\git-core\*
    $backupDir     = "$mingitRoot-backup"
    $backupVersion = $null
    if (Test-Path "$mingitRoot\bin\git.exe") {
        New-Item -ItemType Directory -Force $backupDir | Out-Null
        New-Item -ItemType Directory -Force "$backupDir\libexec\git-core" | Out-Null
        Copy-Item "$mingitRoot\bin\*"              "$backupDir\"                  -Force
        Copy-Item "$mingitRoot\cmd\git.exe"        "$backupDir\git-cmd.exe"       -Force
        Copy-Item "$mingitRoot\libexec\git-core\*" "$backupDir\libexec\git-core\" -Force -ErrorAction SilentlyContinue
        try   { $backupVersion = & "$backupDir\git.exe" --version 2>$null }
        catch { $backupVersion = "(could not read version)" }
        $backupCommit = & "$backupDir\git.exe" -c core.longpaths=true `
            --exec-path 2>$null
        # git.exe itself reports its commit via --build-options
        $backupCommitRaw = & "$backupDir\git.exe" version --build-options 2>$null |
            Select-String "commit:" | ForEach-Object { ($_ -split "commit:\s*")[1].Trim().Substring(0,10) }
        if ($backupCommitRaw) { $backupCommit = $backupCommitRaw }
        else { $backupCommit = "(unknown)" }
        Write-Host "  Backed up: $backupVersion" -ForegroundColor Yellow
    }

    # Kill git processes that would lock files
    Get-Process -Name "git","git-remote-https" -ErrorAction SilentlyContinue | Stop-Process -Force

    # Save and wipe env vars that could poison MSYS2
    $savedVars = @{}
    foreach ($v in @("MAKEFLAGS","MFLAGS","MAKELEVEL","CARGO_MAKEFLAGS",
                     "MSYS","MSYS2_PATH_TYPE","CC","CXX","CFLAGS","CXXFLAGS")) {
        $savedVars[$v] = [System.Environment]::GetEnvironmentVariable($v)
        [System.Environment]::SetEnvironmentVariable($v, $null)
    }

    # Launch bash and tee output to both console and log file in real time
    Write-Host "  Running build-git.sh..." -ForegroundColor Cyan
    & "$msys64Root\usr\bin\env.exe" MSYSTEM=UCRT64 MSYS2_PATH_TYPE=minimal `
        "$msys64Root\usr\bin\bash.exe" -c `
        "unset MAKEFLAGS MFLAGS MAKELEVEL CARGO_MAKEFLAGS; source /etc/profile; exec bash /d/dev/build-git.sh" `
        2>&1 | Tee-Object -FilePath $log
    $buildExit = $LASTEXITCODE

    # Restore env vars
    foreach ($v in $savedVars.Keys) {
        if ($savedVars[$v]) { [System.Environment]::SetEnvironmentVariable($v, $savedVars[$v]) }
        else                 { [System.Environment]::SetEnvironmentVariable($v, $null) }
    }

    if ($buildExit -eq 0) {
        $ucrt64Root    = "$msys64Root\ucrt64"
        $ucrt64BinPath = "$ucrt64Root\bin"   # local, always set, used with -LiteralPath
        Write-Host "  Staging to $mingitRoot..." -ForegroundColor Cyan

        foreach ($d in @("bin","cmd","libexec\git-core","share\git-core\templates","share\git")) {
            New-Item -ItemType Directory -Force "$mingitRoot\$d" | Out-Null
        }

        # Copy stage tree first — DLL planting always happens after so robocopy
        # can never clobber what we plant
        robocopy "$stageDir\bin"     "$mingitRoot\bin"     /E /IS /IT /IM /NP /NFL /NDL /NJH /NJS | Out-Null
        robocopy "$stageDir\cmd"     "$mingitRoot\cmd"     /E /IS /IT /IM /NP /NFL /NDL /NJH /NJS | Out-Null
        robocopy "$stageDir\libexec" "$mingitRoot\libexec" /E /IS /IT /IM /NP /NFL /NDL /NJH /NJS | Out-Null
        robocopy "$stageDir\share"   "$mingitRoot\share"   /E /IS /IT /IM /NP /NFL /NDL /NJH /NJS | Out-Null

        # Build a single deduplicated DLL set from two sources:
        #   A) ldd import-table scan across every stage exe
        #   B) hardcoded list of DLLs loaded at runtime via LoadLibraryExW
        #      (invisible to ldd — libcurl and its full dep chain)
        # Everything goes into BOTH bin\ and libexec\git-core\.

        $dllNames = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::OrdinalIgnoreCase)

        # A) ldd scan — all stage exes
        # FIX: use single-quoted string so PowerShell does not interpret $PATH or $3.
        # '' inside a single-quoted PS string is an escaped literal single-quote,
        # which produces the surrounding quotes awk needs around the pattern.
        Write-Host "  Discovering import-table DLLs via ldd..." -ForegroundColor Cyan
        $lddLines = & "$msys64Root\usr\bin\env.exe" MSYSTEM=UCRT64 `
            "$msys64Root\usr\bin\bash.exe" -c `
            'export PATH=/ucrt64/bin:$PATH; find /d/dev/git-stage -name "*.exe" -print0 | xargs -0 ldd 2>/dev/null | awk ''/\/ucrt64\//{print $3}'' | sort -u'

        foreach ($msysPath in ($lddLines -split "`n" | Where-Object { $_ -match '\.dll$' })) {
            $dllNames.Add((Split-Path $msysPath.Trim() -Leaf)) | Out-Null
        }

        # B) Runtime-loaded (LoadLibraryExW) DLLs — libcurl and its full transitive dep
        #    chain. These are invisible to ldd. Both ngtcp2 crypto variants are included;
        #    whichever is absent on disk is skipped silently by the -LiteralPath Test-Path.
        $runtimeDlls = @(
            "libcurl-4.dll",
            "libcrypto-3-x64.dll",
            "libssl-3-x64.dll",
            "libnghttp2-14.dll",
            "libnghttp3-9.dll",
            "libngtcp2-16.dll",
            "libngtcp2_crypto_ossl-0.dll",   # OpenSSL variant — present on this system
            "libngtcp2_crypto_gnutls-8.dll", # GnuTLS variant  — included for completeness
            "libssh2-1.dll",
            "libbrotlidec.dll",
            "libbrotlicommon.dll",
            "libzstd.dll",
            "libidn2-0.dll",
            "libpsl-5.dll",
            "libunistring-5.dll",
            "zlib1.dll",
            "libiconv-2.dll",
            "libintl-8.dll"
        )
        foreach ($name in $runtimeDlls) { $dllNames.Add($name) | Out-Null }

        # Plant every DLL from ucrt64\bin into BOTH bin\ and libexec\git-core\.
        # -LiteralPath prevents PowerShell from misinterpreting special characters
        # (hyphens, underscores) in DLL names as wildcard/range operators.
        $planted = 0; $missing = @()
        Write-Host "  Planting $($dllNames.Count) DLLs (ucrt64\bin → bin\ + libexec\git-core\)..." -ForegroundColor Cyan
        foreach ($name in ($dllNames | Sort-Object)) {
            $src = Join-Path $ucrt64BinPath $name
            if (Test-Path -LiteralPath $src) {
                Copy-Item -LiteralPath $src "$mingitRoot\bin\$name"              -Force
                Copy-Item -LiteralPath $src "$mingitRoot\libexec\git-core\$name" -Force
                Write-Host "    $name" -ForegroundColor DarkGray
                $planted++
            } else {
                $missing += $name
            }
        }
        Write-Host "  Planted: $planted  Skipped (not in ucrt64\bin): $($missing.Count)" -ForegroundColor Cyan
        if ($missing.Count) {
            Write-Host "  Skipped: $($missing -join ', ')" -ForegroundColor DarkGray
        }

        # Read version after exe AND DLLs are both in place
        $builtVersion = & "$mingitRoot\bin\git.exe" --version 2>$null
        if (-not $builtVersion) {
            $builtVersion = & "$mingitRoot\cmd\git.exe" --version 2>$null
        }
        $builtCommit = & "$msys64Root\usr\bin\env.exe" MSYSTEM=UCRT64 `
        "$msys64Root\usr\bin\bash.exe" -c `
            "git -C /d/dev/git-src rev-parse --short HEAD 2>/dev/null" `
            2>$null | Select-Object -Last 1
        Write-Host "✓ Git built and installed to $mingitRoot" -ForegroundColor Green
        Write-Host "  Version:  $builtVersion ($builtCommit)" -ForegroundColor Green
        Write-Host "  Compiler: clang (MSYS2 ucrt64, -march=native)" -ForegroundColor Green
        if ($backupVersion) {
            Write-Host "  Previous: $backupVersion ($backupCommit) (at $backupDir)" -ForegroundColor Yellow
        } else {
            Write-Host "  Previous: (no backup — install dir was already absent)" -ForegroundColor DarkGray
        }

        # Smoke-test HTTPS transport — catches any remaining missing DLL immediately
        Write-Host "  Smoke-testing HTTPS transport..." -ForegroundColor Cyan
        $smokeOut = & "$mingitRoot\bin\git.exe" ls-remote --exit-code `
            https://github.com/git-for-windows/git.git HEAD 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "  ✓ HTTPS transport OK" -ForegroundColor Green
        } else {
            Write-Warning "HTTPS smoke-test failed — git pull in other functions may break"
            Write-Host   "  $smokeOut" -ForegroundColor Red
        }

        $env:PATH = "$mingitRoot\cmd;$mingitRoot\bin;" + `
            ($env:PATH `
                -replace [regex]::Escape("$mingitRoot\cmd;"), '' `
                -replace [regex]::Escape("$mingitRoot\bin;"), '')
        Write-Host "  ✓ MinGit promoted to front of PATH for this session" -ForegroundColor Green

    } else {
        Write-Host "✗ Build failed (exit $buildExit) — restoring backup..." -ForegroundColor Red
        if (Test-Path "$backupDir\git.exe") {
            Copy-Item "$backupDir\*.exe"        "$mingitRoot\bin\"              -Force
            Copy-Item "$backupDir\*.dll"        "$mingitRoot\bin\"              -Force -ErrorAction SilentlyContinue
            Copy-Item "$backupDir\git-cmd.exe"  "$mingitRoot\cmd\git.exe"       -Force
            if (Test-Path "$backupDir\libexec\git-core") {
                Copy-Item "$backupDir\libexec\git-core\*" "$mingitRoot\libexec\git-core\" -Force -ErrorAction SilentlyContinue
            }
            Write-Host "  Restored: $(& "$mingitRoot\cmd\git.exe" --version)" -ForegroundColor Yellow
        }
        Write-Host "  Check $log for details" -ForegroundColor Red
    }
}

#======================================================
#NASM Building From Source
#======================================================

function Update-WinNasm-Clang {
    $nasmMode = "dev"   # "stable" | "dev"

    $savedPath    = $env:PATH
    $savedCC      = $env:CC
    $savedCXX     = $env:CXX
    $savedINCLUDE = $env:INCLUDE
    $savedLIB     = $env:LIB
    $savedCMakeC  = $env:CMAKE_C_COMPILER
    $savedCMakeCX = $env:CMAKE_CXX_COMPILER
    $savedCMakeG  = $env:CMAKE_GENERATOR
    $savedCMakeMk = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn = $env:CMAKE_LINKER

    try {
        if (-not (Test-Path D:\dev\nasm-src)) {
            git clone https://github.com/netwide-assembler/nasm D:\dev\nasm-src
        }

        if ($nasmMode -eq "stable") {
            git -C D:\dev\nasm-src fetch origin
            git -C D:\dev\nasm-src fetch --tags
            git -C D:\dev\nasm-src reset --hard
            git -C D:\dev\nasm-src checkout 4a56d66
            git -C D:\dev\nasm-src clean -fdx
        } else {
            git -C D:\dev\nasm-src fetch origin
            git -C D:\dev\nasm-src fetch --tags
            git -C D:\dev\nasm-src reset --hard origin/master
            git -C D:\dev\nasm-src clean -fdx

            $msvcH = "D:\dev\nasm-src\config\msvc.h"
            if (Test-Path $msvcH) {
                $found = rg --fixed-strings '# define HAVE__BITSCANREVERSE 1' $msvcH
                if ($found) {
                    sd `
                        '#if _MSC_VER >= 1400\r?\n# define HAVE__BITSCANREVERSE 1\r?\n#endif' `
                        '// HAVE__BITSCANREVERSE disabled: corrupts COFF symbol table under clang-cl (e2f38a8)
// #if _MSC_VER >= 1400
// # define HAVE__BITSCANREVERSE 1
// #endif' `
                        $msvcH
                    $stillThere = rg '^# define HAVE__BITSCANREVERSE 1' $msvcH
                    if ($stillThere) {
                        Write-Host "  ✗ Patch FAILED: HAVE__BITSCANREVERSE still present" -ForegroundColor Red
                        return
                    }
                    Write-Host "  ✓ Patch applied: commented out HAVE__BITSCANREVERSE in config/msvc.h" -ForegroundColor Cyan
                } else {
                    Write-Host "  Patch skipped: HAVE__BITSCANREVERSE not present (already fixed upstream)" -ForegroundColor DarkGray
                }
            } else {
                Write-Host "  ✗ config/msvc.h not found — unexpected tree layout" -ForegroundColor Red
                return
            }
        }

        $gitDesc = (git -C D:\dev\nasm-src describe --tags --long --dirty 2>$null)
        if ($gitDesc) {
            $verStr  = $gitDesc -replace '^nasm-', ''
            $verFile = "D:\dev\nasm-src\version"
            [System.IO.File]::WriteAllText($verFile, "$verStr`n")
            Write-Host "  version file patched: $verStr" -ForegroundColor Cyan
        } else {
            Write-Host "  version file not patched: git describe returned nothing" -ForegroundColor Yellow
        }

        use-clang-win
        Set-Location D:\dev\nasm-src

        nmake-msvc /f Mkfiles\msvc.mak clean

        nmake-msvc /f Mkfiles\msvc.mak `
            CC="$clangRoot\bin\clang-cl.exe" `
            AR="$clangRoot\bin\llvm-lib.exe" `
            OPTFLAGS="/O2" `
            LDFLAGS="/opt:ref /opt:icf"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ NASM build failed (exit $LASTEXITCODE)" -ForegroundColor Red
            return
        }

        Copy-Item D:\dev\nasm-src\nasm.exe    D:\Programs\nasm\nasm.exe    -Force
        Copy-Item D:\dev\nasm-src\ndisasm.exe D:\Programs\nasm\ndisasm.exe -Force
        Write-Host "✓ NASM: $(& "$nasmRoot\nasm.exe" --version)" -ForegroundColor Green

    } finally {
        $env:PATH               = $savedPath
        $env:CC                 = $savedCC
        $env:CXX                = $savedCXX
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_C_COMPILER   = $savedCMakeC
        $env:CMAKE_CXX_COMPILER = $savedCMakeCX
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCMakeLn) { $env:CMAKE_LINKER = $savedCMakeLn }
        else { Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue }
        Set-Location D:\
    }
}

function Update-WinNasm-MSVC {
    # Builds NASM from source using MSVC toolchain (cl.exe/nmake).
    # $nasmMode = "stable" : pins to commit 4a56d66 (nasm-3.02 release)
    # $nasmMode = "dev"    : tracks master; applies two patches required for
    #                        OpenSSL compatibility (file.c + outcoff.c).
    $nasmMode = "stable"   # "stable" | "dev"

    $savedPath    = $env:PATH
    $savedCC      = $env:CC
    $savedCXX     = $env:CXX
    $savedINCLUDE = $env:INCLUDE
    $savedLIB     = $env:LIB
    $savedCMakeC  = $env:CMAKE_C_COMPILER
    $savedCMakeCX = $env:CMAKE_CXX_COMPILER
    $savedCMakeG  = $env:CMAKE_GENERATOR
    $savedCMakeMk = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn = $env:CMAKE_LINKER

    try {
        if (-not (Test-Path D:\dev\nasm-src)) {
            git clone https://github.com/netwide-assembler/nasm D:\dev\nasm-src
        }

        if ($nasmMode -eq "stable") {
            git -C D:\dev\nasm-src fetch --tags
            git -C D:\dev\nasm-src reset --hard
            git -C D:\dev\nasm-src checkout 720a326 #4a56d66
            git -C D:\dev\nasm-src clean -fdx
        } else {
            git -C D:\dev\nasm-src fetch --tags
            git -C D:\dev\nasm-src reset --hard
            git -C D:\dev\nasm-src checkout master
            git -C D:\dev\nasm-src pull
            git -C D:\dev\nasm-src clean -fdx
        }

        # Embed git commit hash into the 'version' plain text file that version.pl reads.
        # msvc.mak generates version.h via: perl version.pl h < version > version.h
        # Patching version.h directly is useless — nmake regenerates it from 'version'.
        # stable produces: "3.02-0-g4a56d66"
        # dev produces:    "3.02-50-gfbdc88565-dirty"
        $gitDesc = (git -C D:\dev\nasm-src describe --tags --long --dirty 2>$null)
        if ($gitDesc) {
            $verStr  = $gitDesc -replace '^nasm-', ''
            $verFile = "D:\dev\nasm-src\version"
            [System.IO.File]::WriteAllText($verFile, "$verStr`n")
            Write-Host "  version file patched: $verStr" -ForegroundColor Cyan
        } else {
            Write-Host "  version file not patched: git describe returned nothing" -ForegroundColor Yellow
        }

        use-msvc
        Set-Location D:\dev\nasm-src

        nmake-msvc /f Mkfiles\msvc.mak clean

        nmake-msvc /f Mkfiles\msvc.mak `
            OPTFLAGS="/O2" `
            LDFLAGS="/opt:ref /opt:icf"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ NASM build failed (exit $LASTEXITCODE)" -ForegroundColor Red
            return
        }

        Copy-Item D:\dev\nasm-src\nasm.exe    D:\Programs\nasm\nasm.exe    -Force
        Copy-Item D:\dev\nasm-src\ndisasm.exe D:\Programs\nasm\ndisasm.exe -Force
        Write-Host "✓ NASM: $(& "$nasmRoot\nasm.exe" --version)" -ForegroundColor Green

    } finally {
        $env:PATH               = $savedPath
        $env:CC                 = $savedCC
        $env:CXX                = $savedCXX
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_C_COMPILER   = $savedCMakeC
        $env:CMAKE_CXX_COMPILER = $savedCMakeCX
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCMakeLn) { $env:CMAKE_LINKER = $savedCMakeLn }
        else { Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue }
        Set-Location D:\
    }
}

#======================================================
# OpenSSL — Build from source (MSVC tool chain - use-msvc alias)
#======================================================

function Update-WinOpenSSL-MSVC {
    $savedPath    = $env:PATH
    $savedCC      = $env:CC
    $savedCXX     = $env:CXX
    $savedINCLUDE = $env:INCLUDE
    $savedLIB     = $env:LIB
    $savedCL      = $env:CL

    $env:PATH = "$perlRoot\perl\bin;$nasmRoot;$env:PATH"

    use-msvc

    Set-Location "D:\Downloads\OpenSSL"
    git pull
    nmake-msvc distclean 2>$null   # suppress errors if no Makefile yet

    perl Configure VC-WIN64A no-makedepend `
        --prefix="D:\Programs\OpenSSL" `
        --openssldir="D:\Programs\OpenSSL"

    $jobs = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
    & "$jomRoot\jom.exe" /J $jobs

    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Build failed (exit $LASTEXITCODE)" -ForegroundColor Red
    } else {
        # 20-test_app_ecparam.t has a known CRLF false-failure on Windows
        # (PEM line endings, not a real bug). Skip it and run everything else.
        & "$jomRoot\jom.exe" TESTS="-test_app_ecparam" test

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Tests failed (exit $LASTEXITCODE)" -ForegroundColor Red
        } else {
            & "$jomRoot\jom.exe" install_sw
            $ver = (Get-Content "D:\Programs\OpenSSL\include\openssl\opensslv.h" -ErrorAction SilentlyContinue |
                    Select-String 'OPENSSL_VERSION_STR') -replace '.*"(.*)".*', '$1'
            Write-Host "✓ OpenSSL $ver installed to D:\Programs\OpenSSL" -ForegroundColor Green
        }
    }
    $env:PATH    = $savedPath
    $env:CC      = $savedCC
    $env:CXX     = $savedCXX
    $env:INCLUDE = $savedINCLUDE
    $env:LIB     = $savedLIB
    if ($savedCL) { $env:CL = $savedCL }
    else { Remove-Item Env:\CL -ErrorAction SilentlyContinue }
    Set-Location D:\
}

function Update-WinOpenSSL-Clang {
    # Builds OpenSSL from source using clang-win toolchain.
    # OpenSSL has no VC-CLANG-WIN64A target for x86-64 — clang-cl is passed
    # via CC/LD env vars on top of VC-WIN64A, same pattern as the MSVC build
    # but with clang-cl.exe as compiler and lld-link.exe as linker.
    # nmake distclean runs unconditionally — stale MSVC obj/lib files from a
    # previous build silently block recompilation (same lesson as NASM).
    # jom is used for parallel build identical to the MSVC function.

    $savedPath    = $env:PATH
    $savedCC      = $env:CC
    $savedCXX     = $env:CXX
    $savedINCLUDE = $env:INCLUDE
    $savedLIB     = $env:LIB
    $savedCL      = $env:CL

    try {
        # Perl and NASM must be ahead of everything — OpenSSL Configure needs both
        $env:PATH = "$perlRoot\perl\bin;$nasmRoot;$env:PATH"

        use-clang-win

        # Point OpenSSL's Configure at clang-cl and lld-link via env vars.
        # VC-WIN64A uses CC for the compiler and LD for the linker — these
        # override cl.exe/link.exe without needing a shim directory.
        $env:CC  = "$clangRoot\bin\clang-cl.exe"
        $env:CXX = "$clangRoot\bin\clang-cl.exe"
        $env:LD  = "$clangRoot\bin\lld-link.exe"

        Set-Location "D:\Downloads\OpenSSL"
        git pull

        # distclean unconditionally — nmake tracks timestamps not compiler
        # identity; stale MSVC objects silently prevent recompilation
        nmake-msvc distclean 2>$null   # suppress errors if no Makefile yet

        perl Configure VC-WIN64A no-makedepend `
            --prefix="D:\Programs\OpenSSL" `
            --openssldir="D:\Programs\OpenSSL"

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Configure failed (exit $LASTEXITCODE)" -ForegroundColor Red
            return
        }
        # Replace lib.exe with llvm-lib.exe in generated Makefile
        (Get-Content "D:\Downloads\OpenSSL\Makefile") `
            -replace '^AR="lib"', "AR=`"$clangRoot\bin\llvm-lib.exe`"" |
            Set-Content "D:\Downloads\OpenSSL\Makefile"

        $jobs = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
        & "$jomRoot\jom.exe" /J $jobs

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Build failed (exit $LASTEXITCODE)" -ForegroundColor Red
            return
        }

        # Skip 20-test_app_ecparam.t — known CRLF false-failure on Windows
        & "$jomRoot\jom.exe" TESTS="-test_app_ecparam" test

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ Tests failed (exit $LASTEXITCODE)" -ForegroundColor Red
            return
       }

        & "$jomRoot\jom.exe" install_sw

        $ver = (Get-Content "D:\Programs\OpenSSL\include\openssl\opensslv.h" -ErrorAction SilentlyContinue |
                Select-String 'OPENSSL_VERSION_STR') -replace '.*"(.*)".*', '$1'
        Write-Host "✓ OpenSSL $ver installed to D:\Programs\OpenSSL" -ForegroundColor Green

    } finally {
        $env:PATH    = $savedPath
        $env:CC      = $savedCC
        $env:CXX     = $savedCXX
        $env:INCLUDE = $savedINCLUDE
        $env:LIB     = $savedLIB
        Remove-Item Env:\LD -ErrorAction SilentlyContinue
        if ($savedCL) { $env:CL = $savedCL }
        else { Remove-Item Env:\CL -ErrorAction SilentlyContinue }
        Set-Location D:\
    }
}

#====================================================
# Building BZip2 from source (clang-win)
# Source: https://github.com/libarchive/bzip2  (cmake fork)
# Output: D:\Programs\bzip2\lib\bzip2.lib (static)
#         D:\Programs\bzip2\lib\bzip2dll.lib (import)
#         D:\Programs\bzip2\bin\bzip2.dll
#         D:\Programs\bzip2\include\bzlib.h
#====================================================
function Update-WinBzip2 {
    $srcDir  = "D:\dev\bzip2-src"
    $instDir = $bzip2Root   # D:\Programs\bzip2

    # Git work before toolchain switch
    if (Test-Path "$srcDir\.git") {
        Write-Host "==> Updating bzip2 source..." -ForegroundColor Cyan
        git -C $srcDir pull
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ git pull failed" -ForegroundColor Red
            return
        }
    } else {
        if (Test-Path $srcDir) {
            Write-Host "==> Removing incomplete bzip2 source directory..." -ForegroundColor Yellow
            Remove-Item $srcDir -Recurse -Force
        }
        Write-Host "==> Cloning bzip2 source (libarchive cmake fork)..." -ForegroundColor Cyan
        git clone https://github.com/libarchive/bzip2.git $srcDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ git clone failed" -ForegroundColor Red
            return
        }
    }

    $savedPath      = $env:PATH
    $savedCC        = $env:CC
    $savedCXX       = $env:CXX
    $savedINCLUDE   = $env:INCLUDE
    $savedLIB       = $env:LIB
    $savedCMakeC    = $env:CMAKE_C_COMPILER
    $savedCMakeCX   = $env:CMAKE_CXX_COMPILER
    $savedCMakeG    = $env:CMAKE_GENERATOR
    $savedCMakeMk   = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn   = $env:CMAKE_LINKER
    $savedWinSDKVer = $env:WindowsSDKVersion
    $savedWinSDKDir = $env:WindowsSDKDir
    $savedLocation  = Get-Location

    try {
        use-clang-win

        $cmakeExe = "$cmakeRoot\bin\cmake.exe"
        if (-not (Test-Path $cmakeExe)) {
            Write-Host "✗ Standalone cmake not found at $cmakeExe — run Update-WinCmake first" -ForegroundColor Red
            return
        }

        Set-Location $srcDir

        # Clean previous build dir so cmake cache does not carry stale paths
        if (Test-Path "$srcDir\build") {
            Remove-Item "$srcDir\build" -Recurse -Force
        }

        Write-Host "==> Configuring BZip2..." -ForegroundColor Cyan
        & $cmakeExe -B build -G Ninja `
            -DCMAKE_BUILD_TYPE=Release `
            -DCMAKE_INSTALL_PREFIX="$instDir" `
            -DCMAKE_C_COMPILER="$clangRoot\bin\clang-cl.exe" `
            -DCMAKE_LINKER="$clangRoot\bin\lld-link.exe" `
            -DENABLE_STATIC_LIB=ON `
            -DENABLE_SHARED_LIB=ON `
            -DENABLE_TESTS=OFF `
            -DENABLE_DOCS=OFF

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake configure failed" -ForegroundColor Red
            return
        }

        Write-Host "==> Building BZip2..." -ForegroundColor Cyan
        & $cmakeExe --build build --config Release
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake build failed" -ForegroundColor Red
            return
        }

        Write-Host "==> Installing BZip2 to $instDir..." -ForegroundColor Cyan
        & $cmakeExe --install build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake install failed" -ForegroundColor Red
            return
        }

        # The libarchive fork installs the static lib as bz2_static.lib —
        # rename to bzip2.lib so Update-Pcre2Win's *.lib glob finds it predictably
        $staticSrc = "$instDir\lib\bz2_static.lib"
        $staticDst = "$instDir\lib\bzip2.lib"
        if ((Test-Path $staticSrc) -and (-not (Test-Path $staticDst))) {
            Rename-Item $staticSrc $staticDst
            Write-Host "  Renamed bz2_static.lib → bzip2.lib" -ForegroundColor DarkGray
        }

        # Verify
        $cutoff = (Get-Date).AddMinutes(-5)
        $hdr    = "$instDir\include\bzlib.h"
        $lib    = "$instDir\lib\bzip2.lib"
        $dll    = "$instDir\bin\bzip2.dll"

        if ((Test-Path $hdr) -and (Test-Path $lib)) {
            $ver = (Get-Content $hdr -ErrorAction SilentlyContinue |
                    Select-String 'BZ_VERSION') -replace '.*"(.*)".*', '$1'
            Write-Host "✓ BZip2 $ver installed to $instDir" -ForegroundColor Green
            Write-Host "  Static:  $lib" -ForegroundColor White
            if (Test-Path $dll) {
                Write-Host "  DLL:     $dll" -ForegroundColor White
            }
        } else {
            Write-Host "✗ BZip2 install verification failed — check output above" -ForegroundColor Red
        }

    } finally {
        $env:PATH               = $savedPath
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCC)        { $env:CC                  = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
        if ($savedCXX)       { $env:CXX                 = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
        if ($savedCMakeC)    { $env:CMAKE_C_COMPILER    = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
        if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
        if ($savedCMakeLn)   { $env:CMAKE_LINKER        = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
        if ($savedWinSDKVer) { $env:WindowsSDKVersion   = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
        if ($savedWinSDKDir) { $env:WindowsSDKDir       = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }
        Set-Location $savedLocation
    }
}

#====================================================
# Building ZLib from source (clang-win)
# Source: https://github.com/madler/zlib
# Output: D:\Programs\zlib\lib\zs.lib (static)
#         D:\Programs\zlib\lib\z.lib (import)
#         D:\Programs\zlib\bin\z.dll
#         D:\Programs\zlib\include\zlib.h
#====================================================
function Update-WinZlib {
    $srcDir  = "D:\dev\zlib-src"
    $instDir = $zlibRoot   # D:\Programs\zlib

    # Git work before toolchain switch
    if (Test-Path "$srcDir\.git") {
        Write-Host "==> Updating zlib source..." -ForegroundColor Cyan
        # zlib uses tags for releases and is typically in detached HEAD —
        # fetch all tags then checkout the latest vX.Y.Z release tag.
        git -C $srcDir fetch --tags origin
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ git fetch failed" -ForegroundColor Red
            return
        }
        $latestTag = git -C $srcDir tag -l "v*" |
                     Where-Object { $_ -match '^v\d+\.\d+(\.\d+)?$' } |
                     Sort-Object { [version]($_ -replace '^v','') } |
                     Select-Object -Last 1
        if ($latestTag) {
            Write-Host "  Checking out $latestTag" -ForegroundColor Cyan
            git -C $srcDir checkout $latestTag --quiet
        } else {
            Write-Host "  No versioned tag found — staying on current commit" -ForegroundColor Yellow
        }
    } else {
        if (Test-Path $srcDir) {
            Write-Host "==> Removing incomplete zlib source directory..." -ForegroundColor Yellow
            Remove-Item $srcDir -Recurse -Force
        }
        Write-Host "==> Cloning zlib source..." -ForegroundColor Cyan
        git clone https://github.com/madler/zlib.git $srcDir
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ git clone failed" -ForegroundColor Red
            return
        }
        $latestTag = git -C $srcDir tag -l "v*" |
                     Where-Object { $_ -match '^v\d+\.\d+(\.\d+)?$' } |
                     Sort-Object { [version]($_ -replace '^v','') } |
                     Select-Object -Last 1
        if ($latestTag) {
            Write-Host "  Checking out $latestTag" -ForegroundColor Cyan
            git -C $srcDir checkout $latestTag --quiet
        }
    }

    $savedPath      = $env:PATH
    $savedCC        = $env:CC
    $savedCXX       = $env:CXX
    $savedINCLUDE   = $env:INCLUDE
    $savedLIB       = $env:LIB
    $savedCMakeC    = $env:CMAKE_C_COMPILER
    $savedCMakeCX   = $env:CMAKE_CXX_COMPILER
    $savedCMakeG    = $env:CMAKE_GENERATOR
    $savedCMakeMk   = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn   = $env:CMAKE_LINKER
    $savedWinSDKVer = $env:WindowsSDKVersion
    $savedWinSDKDir = $env:WindowsSDKDir
    $savedLocation  = Get-Location

    try {
        use-clang-win

        $cmakeExe = "$cmakeRoot\bin\cmake.exe"
        if (-not (Test-Path $cmakeExe)) {
            Write-Host "✗ Standalone cmake not found at $cmakeExe — run Update-WinCmake first" -ForegroundColor Red
            return
        }

        Set-Location $srcDir

        # Clean previous build dir
        if (Test-Path "$srcDir\build") {
            Remove-Item "$srcDir\build" -Recurse -Force
        }

        Write-Host "==> Configuring ZLib..." -ForegroundColor Cyan
        & $cmakeExe -B build -G Ninja `
            -DCMAKE_BUILD_TYPE=Release `
            -DCMAKE_INSTALL_PREFIX="$instDir" `
            -DCMAKE_C_COMPILER="$clangRoot\bin\clang-cl.exe" `
            -DCMAKE_LINKER="$clangRoot\bin\lld-link.exe" `
            -DZLIB_BUILD_EXAMPLES=OFF `
            -DZLIB_BUILD_TESTING=OFF `
            -DBUILD_TESTING=OFF

        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake configure failed" -ForegroundColor Red
            return
        }

        Write-Host "==> Building ZLib..." -ForegroundColor Cyan
        & $cmakeExe --build build --config Release
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake build failed" -ForegroundColor Red
            return
        }

        Write-Host "==> Installing ZLib to $instDir..." -ForegroundColor Cyan
        & $cmakeExe --install build
        if ($LASTEXITCODE -ne 0) {
            Write-Host "✗ CMake install failed" -ForegroundColor Red
            return
        }

        # zlib's cmake (madler/zlib, newer) installs:
        #   z.lib  (shared import), zs.lib (static), z.dll — under bin/lib as above.

        # Verify — probe actual filenames the new cmake produces
        $hdr       = "$instDir\include\zlib.h"
        $staticLib = if (Test-Path "$instDir\lib\zs.lib")        { "$instDir\lib\zs.lib"        }
                     elseif (Test-Path "$instDir\lib\zlibstatic.lib") { "$instDir\lib\zlibstatic.lib" }
                     else { $null }
        $importLib = if (Test-Path "$instDir\lib\z.lib")         { "$instDir\lib\z.lib"         }
                     elseif (Test-Path "$instDir\lib\zlib.lib")  { "$instDir\lib\zlib.lib"      }
                     else { $null }
        $dll       = if (Test-Path "$instDir\bin\z.dll")         { "$instDir\bin\z.dll"         }
                     elseif (Test-Path "$instDir\bin\zlib1.dll") { "$instDir\bin\zlib1.dll"     }
                     else { $null }

        if ((Test-Path $hdr) -and ($staticLib -or $importLib)) {
            $ver = (Get-Content $hdr -ErrorAction SilentlyContinue |
                    Select-String '#define ZLIB_VERSION') -replace '.*"(.*)".*', '$1'
            Write-Host "✓ ZLib $ver installed to $instDir" -ForegroundColor Green
            if ($staticLib) { Write-Host "  Static:  $staticLib" -ForegroundColor White }
            if ($importLib) { Write-Host "  Import:  $importLib" -ForegroundColor White }
            if ($dll)       { Write-Host "  DLL:     $dll"       -ForegroundColor White }
        } else {
            Write-Host "✗ ZLib install verification failed — check output above" -ForegroundColor Red
        }

    } finally {
        $env:PATH               = $savedPath
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCC)        { $env:CC                  = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
        if ($savedCXX)       { $env:CXX                 = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
        if ($savedCMakeC)    { $env:CMAKE_C_COMPILER    = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
        if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
        if ($savedCMakeLn)   { $env:CMAKE_LINKER        = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
        if ($savedWinSDKVer) { $env:WindowsSDKVersion   = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
        if ($savedWinSDKDir) { $env:WindowsSDKDir       = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }
        Set-Location $savedLocation
    }
}

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

if (Test-Path "$jomRoot\jom.exe") {
    $basePaths += $jomRoot
}

# Standalone ninja always in PATH (both Windows and MSYS2 toolchains benefit from having it visible)
if (Test-Path "$ninjaRoot\bin\ninja.exe") {
    $basePaths += "$ninjaRoot\bin"
}

# cmake always in PATH — before Python Scripts to avoid pip cmake shadowing
if (Test-Path "$cmakeRoot\bin\cmake.exe") {
    $basePaths += "$cmakeRoot\bin"
}

# Standalone meson always in PATH
if (Test-Path "$mesonRoot\meson.exe") {
    $basePaths += $mesonRoot
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
    $env:OPENSSL_LIB_DIR     = "$opensslRoot\lib"
    $env:WITH_SSL            = $opensslRoot
    $env:CMAKE_PREFIX_PATH   = $opensslRoot
    # CMake 4.x compatibility for legacy vendored CMakeLists.txt (e.g. audiopus_sys/opus)
    $env:CMAKE_POLICY_VERSION_MINIMUM = "3.5"

    # SSE4.1 globally for clang-cl — Opus per-file GCC flags are silently dropped in MSVC mode
    $env:CFLAGS = "-msse4.1"

    # Python 3.15 forward compatibility for pyo3 — suppresses "version newer than max supported"
    # check and builds using the stable ABI. Required until pyo3 0.28+ ships with native 3.15 support.
    $env:PYO3_USE_ABI3_FORWARD_COMPATIBILITY = "1"
    $basePaths += "$opensslRoot\bin"
}

if (Test-Path "$perlRoot\perl\bin\perl.exe") {
    $basePaths += @(
        "$perlRoot\perl\bin",
        "$perlRoot\c\bin"
    )
}

# MySQL - official Oracle connector
if (Test-Path "$mysqlRoot\lib\libmysql.lib") {
    $basePaths += @("$mysqlRoot\bin", "$mysqlRoot\lib")
    $env:MYSQLCLIENT_LIB_DIR       = "$mysqlRoot\lib"
    $env:MYSQLCLIENT_LIBNAME       = "libmysql"
    $env:MYSQLCLIENT_NO_PKG_CONFIG = "1"
    $env:MYSQL_INCLUDE_DIR         = "$mysqlRoot\include"

    # Auto-detect version — primary source: mysql_version.h header
    $mysqlVersionHeader = "$mysqlRoot\include\mysql_version.h"
    $detectedVersion = $null

    if (Test-Path $mysqlVersionHeader) {
        $verLine = Select-String -Path $mysqlVersionHeader -Pattern 'MYSQL_SERVER_VERSION\s+"([\d.][\d.\-\w]*)"'
        if ($verLine) {
            $detectedVersion = $verLine.Matches[0].Groups[1].Value
        }
    }

    # Fallback: ask mysql.exe directly if the header didn't give us a version
    if (-not $detectedVersion -and (Test-Path "$mysqlRoot\bin\mysql.exe")) {
        $verOutput = & "$mysqlRoot\bin\mysql.exe" --version 2>$null
        if ($verOutput -match '(\d+\.\d+\.\d+)') {
            $detectedVersion = $Matches[1]
        }
    }

    if ($detectedVersion) {
        $env:MYSQLCLIENT_VERSION = $detectedVersion
    } else {
        Write-Warning "Could not auto-detect MySQL version from header or mysql.exe — MYSQLCLIENT_VERSION not set"
    }
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

# BZip2 — DLL on PATH for runtime consumers (e.g. pcre2grep when enabled)
if (Test-Path "$bzip2Root\bin") {
    $basePaths += "$bzip2Root\bin"
}

# ZLib — DLL on PATH
if (Test-Path "$zlibRoot\bin") {
    $basePaths += "$zlibRoot\bin"
}

# Rust/Cargo — always in PATH
if (Test-Path "$cargoRoot\bin") {
    $basePaths += "$cargoRoot\bin"
}

if (Test-Path "$rustRoot\bin") {
    $basePaths += "$rustRoot\bin"
}

if (Test-Path "$clangRoot\bin\lld-link.exe") {
    $env:CARGO_HOME  = $cargoRoot
    $env:RUSTUP_HOME = $rustRoot
}

# PCRE2 custom build - DLL needed at runtime by PyPcre and ripgrep
if (Test-Path "D:\Programs\pcre2-clang-win\bin\pcre2-8.dll") {
    $basePaths += "D:\Programs\pcre2-clang-win\bin"
}

# MinGit - prefer over MSYS2 git which gets dragged in via usr\bin below
if (Test-Path "$mingitRoot\cmd\git.exe") {
    $basePaths += "$mingitRoot\bin"    # ← DLLs (libpcre2, libiconv, zlib) findable in PATH
    $basePaths += "$mingitRoot\cmd"
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

# Poppler (pdftotext etc.) — appended so its bundled DLLs don't shadow your custom builds
if (Test-Path "$popplerRoot\Library\bin\pdftotext.exe") {
    $env:PATH = "$env:PATH;$popplerRoot\Library\bin"
}

# Pandoc — single static exe, used by rga for docx/odt/epub
if (Test-Path "$pandocRoot\pandoc.exe") {
    $env:PATH = "$env:PATH;$pandocRoot"
}

# Force MinGit ahead of any MSYS2 git already in PATH (usr\bin was just appended above)
if (Test-Path "$mingitRoot\cmd\git.exe") {
    $env:PATH = "$mingitRoot\cmd;$mingitRoot\bin;" + $env:PATH
}

# Force standalone meson ahead of Python Scripts meson.exe
# (.cmd loses to .exe in PATH resolution even when listed first)
if (Test-Path "$mesonRoot\meson.cmd") {
    $env:PATH = "$mesonRoot;" + $env:PATH
}

# Force cmake ahead of Python Scripts cmake.exe
if (Test-Path "$cmakeRoot\bin\cmake.exe") {
    if (Test-Path "$ninjaRoot\bin\ninja.exe") {
        $env:PATH = "$ninjaRoot\bin;$cmakeRoot\bin;" + $env:PATH
    } else {
        $env:PATH = "$cmakeRoot\bin;" + $env:PATH
    }
}

# Unicode fix for Python on Windows cp1252 terminals
$env:PYTHONUTF8 = "1"

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
# ninja-win  → standalone ninja (D:\Programs\ninja), preferred for Windows toolchains
# ninja-cmake → cmake-bundled ninja (D:\Programs\cmake\bin), explicit fallback alias
# ninja-msys  → MSYS2 ucrt64 ninja, unchanged
if (Test-Path "$ninjaRoot\bin\ninja.exe") {
    Set-Alias -Name ninja-win -Value "$ninjaRoot\bin\ninja.exe" -Force
} elseif (Test-Path "$cmakeRoot\bin\ninja.exe") {
    Set-Alias -Name ninja-win -Value "$cmakeRoot\bin\ninja.exe" -Force
}
if (Test-Path "$cmakeRoot\bin\ninja.exe") {
    Set-Alias -Name ninja-cmake -Value "$cmakeRoot\bin\ninja.exe" -Force
}
if (Test-Path "$msys64Root\ucrt64\bin\ninja.exe") {
    Set-Alias -Name ninja-msys -Value "$msys64Root\ucrt64\bin\ninja.exe" -Force
}

# --- Meson function (wraps .pyz or .exe transparently) ---
# meson-win  → preferred: D:\Programs\meson\meson.pyz (git zipapp) or meson.exe
# meson-pip  → pip-installed meson (D:\Programs\Python\Scripts), explicit fallback
$_mesonExe = Update-WinMeson
if ($_mesonExe) {
    $script:_mesonExePath = $_mesonExe
    function meson-win {
        if ($script:_mesonExePath -like "*.pyz") {
            & "$pythonRoot\python.exe" $script:_mesonExePath @args
        } else {
            & $script:_mesonExePath @args
        }
    }
    if (Test-Path "$mesonRoot\meson.pyz") {
        Set-Alias -Name meson-standalone -Value "$mesonRoot\meson.pyz" -Force -ErrorAction SilentlyContinue
    }
}
if (Test-Path "$pythonRoot\Scripts\meson.exe") {
    Set-Alias -Name meson-pip -Value "$pythonRoot\Scripts\meson.exe" -Force
}

# ~line 1146 area - after meson-win and ninja-win aliases
# ── pip build helper ──────────────────────────────────────────────────────────
# Uses pip meson.exe temporarily so ninja can spawn it as a direct process,
# then restores PATH. Git-built meson stays at priority for everything else.
function Invoke-PipBuild {
    $savedPath = $env:PATH
    $env:PATH = "$pythonRoot\Scripts;" + $env:PATH
    try {
        & pip install . --no-build-isolation @args
    } finally {
        $env:PATH = $savedPath
    }
}
Set-Alias pipbuild Invoke-PipBuild

# --- Make Aliases ---
if (Test-Path "$msys64Root\ucrt64\bin\make.exe") {
    Set-Alias -Name make-msys -Value "$msys64Root\ucrt64\bin\make.exe" -Force
}

# --- Python Aliases ---
if (Test-Path "$pythonRoot\python.exe") {
    Set-Alias -Name python    -Value "$pythonRoot\python.exe"      -Force
    Set-Alias -Name python3   -Value "$pythonRoot\python.exe"      -Force
    Set-Alias -Name python314 -Value "$pythonRoot\python.exe"      -Force
    Set-Alias -Name py        -Value "$pythonRoot\python.exe"      -Force
    Set-Alias -Name py314     -Value "$pythonRoot\python.exe"      -Force
    Set-Alias -Name pip       -Value "$pythonRoot\Scripts\pip.exe" -Force
    Set-Alias -Name pip3      -Value "$pythonRoot\Scripts\pip.exe" -Force
    Set-Alias -Name pip314    -Value "$pythonRoot\Scripts\pip.exe" -Force
}

# --- Perl Alias ---
if (Test-Path "$perlRoot\perl\bin\perl.exe") {
    Set-Alias -Name perl-win -Value "$perlRoot\perl\bin\perl.exe" -Force
}

# --- Perl PCRE2 function (re::engine::PCRE2 10.47) ---
if (Test-Path "$perlRoot\perl\bin\perl.exe") {
    function perl-pcre2 {
        & "$perlRoot\perl\bin\perl.exe" -Mre::engine::PCRE2 @args
    }
}

# --- NASM Alias ---
if (Test-Path "$nasmRoot\nasm.exe") {
    Set-Alias -Name nasm-win -Value "$nasmRoot\nasm.exe" -Force
}

# --- Bison/Flex Aliases ---
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
        "*Windows Kits*\bin*",
        "*\ninja*"           # covers standalone D:\Programs\ninja prepended by toolchain switches
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
    # Prepend standalone ninja on top so it wins over cmake-bundled ninja
    if (Test-Path "$ninjaRoot\ninja.exe") {
        $env:PATH = "$ninjaRoot;$env:PATH"
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
    if (Test-Path "$ninjaRoot\bin\ninja.exe") {
        $env:CMAKE_MAKE_PROGRAM = "$ninjaRoot\bin\ninja.exe"
    } elseif (Test-Path "$cmakeRoot\bin\ninja.exe") {
        $env:CMAKE_MAKE_PROGRAM = "$cmakeRoot\bin\ninja.exe"
    } else {
        $env:CMAKE_GENERATOR    = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }
    $env:CC                  = "$msvcBinPath\cl.exe"
    $env:CXX                 = "$msvcBinPath\cl.exe"
    $env:CMAKE_C_COMPILER    = "$msvcBinPath\cl.exe"
    $env:CMAKE_CXX_COMPILER  = "$msvcBinPath\cl.exe"
    Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
    Write-Host "✓ MSVC toolchain active" -ForegroundColor Green
    Write-Host "  Compiler:  $msvcBinPath\cl.exe" -ForegroundColor White
    Write-Host "  Linker:    $msvcBinPath\link.exe" -ForegroundColor White
    Write-Host "  CMake:     $cmakeRoot\bin\cmake.exe" -ForegroundColor White
    Write-Host "  Ninja:     $($env:CMAKE_MAKE_PROGRAM)" -ForegroundColor White
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
    Remove-Item Env:\LINKER            -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK              -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER      -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Remove-Item Env:\WindowsSDKDir     -ErrorAction SilentlyContinue
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
    Remove-Item Env:\LINKER            -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK              -ErrorAction SilentlyContinue
    Remove-Item Env:\CMAKE_LINKER      -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Remove-Item Env:\WindowsSDKDir     -ErrorAction SilentlyContinue
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
        "$msvcBinPath",
        "$windowsKitsRoot\bin\$windowsSDKVersion\$targetArch",
        "$windowsKitsRoot\bin\$windowsSDKVersion\$targetArch\ucrt"
    )
    foreach ($path in $clangPaths) {
        if (Test-Path $path) { $env:PATH = "$path;$env:PATH" }
    }
    # Prepend standalone ninja — fixed path to bin\ninja.exe
    if (Test-Path "$ninjaRoot\bin\ninja.exe") {
        $env:PATH = "$ninjaRoot\bin;$env:PATH"
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
    $env:CMAKE_GENERATOR = "Ninja"

    # Resolve ninja directly — avoids circular call back into Update-WinNinja
    # which would trigger a second Use-WindowsClang call
    if (Test-Path "$ninjaRoot\bin\ninja.exe") {
        $env:CMAKE_MAKE_PROGRAM = "$ninjaRoot\bin\ninja.exe"
    } elseif (Test-Path "$cmakeRoot\bin\ninja.exe") {
        $env:CMAKE_MAKE_PROGRAM = "$cmakeRoot\bin\ninja.exe"
    } else {
        $env:CMAKE_GENERATOR    = "NMake Makefiles"
        $env:CMAKE_MAKE_PROGRAM = "$msvcBinPath\nmake.exe"
    }

    $env:CC                  = "$clangRoot\bin\clang-cl.exe"
    $env:CXX                 = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_C_COMPILER    = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_CXX_COMPILER  = "$clangRoot\bin\clang-cl.exe"
    $env:CMAKE_LINKER        = "$clangRoot\bin\lld-link.exe"
    $env:DISTUTILS_USE_SDK   = "1"
    $env:MSSdk               = "1"
    Remove-Item Env:\LINKER            -ErrorAction SilentlyContinue
    Remove-Item Env:\LINK              -ErrorAction SilentlyContinue
    Remove-Item Env:\VCToolsInstallDir -ErrorAction SilentlyContinue
    Write-Host "✓ Windows Clang-cl toolchain active" -ForegroundColor Green
    Write-Host "  Compiler:  $clangRoot\bin\clang-cl.exe" -ForegroundColor White
    Write-Host "  Linker:    $clangRoot\bin\lld-link.exe" -ForegroundColor White
    Write-Host "  CMake:     $cmakeRoot\bin\cmake.exe" -ForegroundColor White
    Write-Host "  Ninja:     $($env:CMAKE_MAKE_PROGRAM)" -ForegroundColor White
}

# =====================================================
# Update-RandomgenWin: build randomgen from the PyPI sdist with clang-cl
# Requires (from your profile): $pythonRoot, $mesonRoot, use-clang-win, Update-WinMeson
#   (Update-WinMeson must be the version that builds the meson.exe shim passing its
#    own path to mesonmain.run, so Ninja records meson.exe instead of meson.pyz)
# Usage:
#   Update-RandomgenWin                    # latest on PyPI, skips if already installed
#   Update-RandomgenWin -Version 2.3.0     # specific version
#   Update-RandomgenWin -Force             # rebuild even if the version is installed
# =====================================================
function Update-RandomgenWin {
    param(
        [string]$Version,     # default: latest on PyPI
        [switch]$Force        # rebuild even if this version is already installed
    )

    $py       = "$pythonRoot\python.exe"
    $workDir  = "D:\dev\randomgen-src"
    $buildDir = "D:\dev\randomgen-build"
    $logFile  = "D:\temp\randomgen_build.log"
    New-Item -ItemType Directory (Split-Path $logFile) -Force | Out-Null

    # ── Resolve version + sdist from PyPI ────────────────────────────
    $url = if ($Version) { "https://pypi.org/pypi/randomgen/$Version/json" }
           else          { "https://pypi.org/pypi/randomgen/json" }
    try   { $meta = Invoke-RestMethod $url -ErrorAction Stop }
    catch { Write-Host "✗ Could not query PyPI: $_" -ForegroundColor Red; return }

    $target = $meta.info.version
    $sdist  = $meta.urls | Where-Object packagetype -eq 'sdist' | Select-Object -First 1
    if (-not $sdist) { Write-Host "✗ No sdist for randomgen $target" -ForegroundColor Red; return }

    $installed = & $py -c "import importlib.metadata as m; print(m.version('randomgen'))" 2>$null
    if ($installed -eq $target -and -not $Force) {
        Write-Host "✓ randomgen $target already installed (use -Force to rebuild)" -ForegroundColor Green
        return
    }
    Write-Host "==> Building randomgen $target (installed: $(if ($installed) { $installed } else { 'none' }))" -ForegroundColor Cyan

    # ── Make sure the meson.exe shim exists (Ninja must be able to launch it) ──
    $null = Update-WinMeson
    if (-not (Test-Path "$mesonRoot\meson.exe")) {
        Write-Host "✗ meson.exe shim missing — run Update-WinMeson -Update" -ForegroundColor Red; return
    }

    # ── Build prerequisites for --no-build-isolation ─────────────────
    & $py -c "import mesonpy, numpy, Cython" 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  Installing build prerequisites..." -ForegroundColor Gray
        & $py -m pip install meson-python numpy cython
        if ($LASTEXITCODE -ne 0) { Write-Host "✗ Prerequisite install failed" -ForegroundColor Red; return }
    }

    # ── Download, verify, extract ────────────────────────────────────
    Remove-Item $workDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item -ItemType Directory $workDir -Force | Out-Null
    $tgz = Join-Path $workDir $sdist.filename
    Invoke-WebRequest $sdist.url -OutFile $tgz
    if ((Get-FileHash $tgz -Algorithm SHA256).Hash.ToLower() -ne $sdist.digests.sha256) {
        Write-Host "✗ SHA256 mismatch for $($sdist.filename)" -ForegroundColor Red; return
    }
    & $py -c "import sys,tarfile; tarfile.open(sys.argv[1]).extractall(sys.argv[2], filter='data')" $tgz $workDir
    $src = Get-ChildItem $workDir -Directory | Select-Object -First 1 -ExpandProperty FullName
    if (-not $src) { Write-Host "✗ Extraction failed" -ForegroundColor Red; return }

    # ── Patch: clang-cl defines both __clang__ and _MSC_VER ──────────
    $f   = Join-Path $src "randomgen\src\common\cpu_features.c"
    $old = '#if defined(__clang__) || defined(__GNUC__)'
    $new = '#if (defined(__clang__) || defined(__GNUC__)) && !defined(_MSC_VER)'
    $c   = [System.IO.File]::ReadAllText($f)
    if     ($c.Contains($new)) { Write-Host "✓ cpu_features.c already patched" -ForegroundColor Green }
    elseif ($c.Contains($old)) {
        [System.IO.File]::WriteAllText($f, $c.Replace($old, $new))
        Write-Host "✓ cpu_features.c patched for clang-cl" -ForegroundColor Green
    }
    else { Write-Host "⚠ cpu_features.c pattern not found — upstream may have changed; building unpatched" -ForegroundColor Yellow }

    # ── Snapshot env (restored in finally) ───────────────────────────
    $envNames = 'PATH','CC','CXX','CC_LD','CXX_LD','CCACHE_DISABLE','CFLAGS','CXXFLAGS','INCLUDE','LIB',
                'CMAKE_C_COMPILER','CMAKE_CXX_COMPILER','CMAKE_GENERATOR','CMAKE_MAKE_PROGRAM',
                'CMAKE_LINKER','WindowsSDKVersion','WindowsSDKDir','VCToolsInstallDir','LINKER','LINK'
    $saved = @{}
    foreach ($n in $envNames) { $saved[$n] = [Environment]::GetEnvironmentVariable($n, 'Process') }

    $ok = $false
    try {
        use-clang-win
        $env:CC  = "clang-cl";   $env:CXX  = "clang-cl"
        $env:CC_LD = "lld-link"; $env:CXX_LD = "lld-link"
        $env:CCACHE_DISABLE = "1"                          # avoid Strawberry Perl's ccache
        $env:CFLAGS   = "-msse4.1 -maes -mpclmul"          # clang needs explicit AES-NI / PCLMUL
        $env:CXXFLAGS = $env:CFLAGS

        Remove-Item $buildDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "  Compiling (full log: $logFile)..." -ForegroundColor Gray
        & $py -m pip install $src --no-build-isolation --no-deps --force-reinstall -v `
            "--config-settings=build-dir=$($buildDir -replace '\\','/')" *> $logFile
        $ok = ($LASTEXITCODE -eq 0)
    }
    finally {
        foreach ($n in $envNames) { [Environment]::SetEnvironmentVariable($n, $saved[$n], 'Process') }
        Set-Location D:\
    }

    if (-not $ok) {
        Write-Host "✗ randomgen build failed — first errors:" -ForegroundColor Red
        Select-String -Path $logFile -Pattern 'FAILED:|\): error:|lld-link: error|ninja: fatal|fatal error' -Context 0,6 |
            Select-Object -First 3
        return
    }

    # ── Verify ───────────────────────────────────────────────────────
    & $py -c "import randomgen as r; from randomgen import AESCounter; print('randomgen', r.__version__, '| AESCounter:', AESCounter(1234).random_raw(2))"
    if ($LASTEXITCODE -eq 0) { Write-Host "✓ randomgen $target built with clang-cl and installed" -ForegroundColor Green }
    else { Write-Host "⚠ Built, but the import test failed" -ForegroundColor Yellow }
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

    # ── Snapshot env ──
    $savedPath      = $env:PATH
    $savedCC        = $env:CC
    $savedCXX       = $env:CXX
    $savedINCLUDE   = $env:INCLUDE
    $savedLIB       = $env:LIB
    $savedCMakeC    = $env:CMAKE_C_COMPILER
    $savedCMakeCX   = $env:CMAKE_CXX_COMPILER
    $savedCMakeG    = $env:CMAKE_GENERATOR
    $savedCMakeMk   = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn   = $env:CMAKE_LINKER
    $savedWinSDKVer = $env:WindowsSDKVersion
    $savedWinSDKDir = $env:WindowsSDKDir

    use-clang-win

    try {
        Write-Host "`nChecking cargo-binstall..." -ForegroundColor Cyan
        cargo install cargo-binstall

        Write-Host "`nUpdating custom-compiled packages..." -ForegroundColor Cyan
        foreach ($pkg in $customPackages.Keys) {
            Write-Host "  Updating $pkg with custom flags..." -ForegroundColor Yellow
            $flags       = $customPackages[$pkg].flags
            $featuresArg = $customPackages[$pkg].features
            $oldRustFlags = $env:RUSTFLAGS
            $env:RUSTFLAGS = if ($oldRustFlags) { "$oldRustFlags $flags" } else { $flags }
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

    } finally {
        # ── Restore env ──
        $env:PATH               = $savedPath
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCC)       { $env:CC                 = $savedCC       } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
        if ($savedCXX)      { $env:CXX                = $savedCXX      } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
        if ($savedCMakeC)   { $env:CMAKE_C_COMPILER   = $savedCMakeC   } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
        if ($savedCMakeCX)  { $env:CMAKE_CXX_COMPILER = $savedCMakeCX  } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
        if ($savedCMakeLn)  { $env:CMAKE_LINKER       = $savedCMakeLn  } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
        if ($savedWinSDKVer){ $env:WindowsSDKVersion  = $savedWinSDKVer} else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
        if ($savedWinSDKDir){ $env:WindowsSDKDir      = $savedWinSDKDir} else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }
    }
}

# =====================================================
# Rust Toolchain Switching
# =====================================================

function Use-RustNightly {
    Remove-Item Env:\RUSTUP_TOOLCHAIN -ErrorAction SilentlyContinue
    rustup default nightly-x86_64-pc-windows-msvc
    Write-Host "✓ Rust toolchain → nightly (default)" -ForegroundColor Green
}

function Use-RustStable {
    Remove-Item Env:\RUSTUP_TOOLCHAIN -ErrorAction SilentlyContinue
    rustup default stable-x86_64-pc-windows-msvc
    Write-Host "✓ Rust toolchain → stable (default)" -ForegroundColor Green
}

function Get-RustToolchain {
    $active = rustup show active-toolchain 2>$null
    Write-Host "  Active: $active" -ForegroundColor Cyan
    Write-Host "  Installed:" -ForegroundColor Cyan
    rustup toolchain list
}

Set-Alias -Name use-rust-stable   -Value Use-RustStable
Set-Alias -Name use-rust-nightly  -Value Use-RustNightly
Set-Alias -Name rust-toolchain    -Value Get-RustToolchain


# =====================================================
# MysqlclientSrc Patch Function
# =====================================================
function Patch-MysqlclientSrc {
    # ── Patch 1: build.rs (Release folder path fix) ──────────────────
    $buildRs = Get-ChildItem "D:\Programs\cargo\registry\src" -Recurse -Filter "build.rs" |
        Where-Object { $_.FullName -like "*mysqlclient-src*" } |
        Select-Object -First 1

    if (-not $buildRs) {
        Write-Host "mysqlclient-src build.rs not found - may not be downloaded yet" -ForegroundColor Red
        Write-Host "Run: cargo install diesel_cli --all-features (let it fail once first)" -ForegroundColor Yellow
    } else {
        $content = Get-Content $buildRs.FullName -Raw
        if ($content -match 'dst\.push\("Release"\);') {
            $old = "    // on windows the library is in a different folder`n    if std::env::var(""CARGO_CFG_TARGET_ENV"").as_deref() == Ok(""msvc"") {`n        dst.push(""Release"");`n    }"
            $new = "    // on windows the library is in a different folder`n    // NOTE: patched - mysqlclient.lib lands directly in archive_output_directory`n    // if std::env::var(""CARGO_CFG_TARGET_ENV"").as_deref() == Ok(""msvc"") {`n    //     dst.push(""Release"");`n    // }"
            $content = $content.Replace($old, $new)
            [System.IO.File]::WriteAllText($buildRs.FullName, $content, [System.Text.Encoding]::UTF8)
            Write-Host "✓ Patched build.rs: $($buildRs.FullName)" -ForegroundColor Green
        } else {
            Write-Host "✓ Already patched build.rs: $($buildRs.FullName)" -ForegroundColor Cyan
        }
    }

    # ── Patch 2: ssl.cmake (OpenSSL 4.x support) ─────────────────────
    $sslCmake = Get-ChildItem "D:\Programs\cargo\registry\src" -Recurse -Filter "ssl.cmake" |
        Where-Object { $_.FullName -like "*mysqlclient-src*" } |
        Select-Object -First 1

    if (-not $sslCmake) {
        Write-Host "ssl.cmake not found - may not be downloaded yet" -ForegroundColor Red
        Write-Host "Run: cargo install diesel_cli --all-features (let it fail once first)" -ForegroundColor Yellow
        return
    }

    attrib -r $sslCmake.FullName
    $content = Get-Content $sslCmake.FullName -Raw

    if ($content -match 'VERSION_EQUAL 4') {
        Write-Host "✓ Already patched ssl.cmake: $($sslCmake.FullName)" -ForegroundColor Cyan
        return
    }

    # Patch 2a: Version detection in FIND_OPENSSL_VERSION macro
    $old2a = 'IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3)'
    $new2a = 'IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3 OR OPENSSL_VERSION_MAJOR VERSION_EQUAL 4)'
    $content = $content.Replace($old2a, $new2a)

    # Patch 2b: DLL naming in MYSQL_CHECK_SSL_DLLS macro
    $old2b = '      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3)
        SET(SSL_MSVC_VERSION_SUFFIX "-3")
        SET(SSL_MSVC_ARCH_SUFFIX "-x64")
      ENDIF()'
    $new2b = '      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 3)
        SET(SSL_MSVC_VERSION_SUFFIX "-3")
        SET(SSL_MSVC_ARCH_SUFFIX "-x64")
      ENDIF()
      IF(OPENSSL_VERSION_MAJOR VERSION_EQUAL 4)
        SET(SSL_MSVC_VERSION_SUFFIX "-4")
        SET(SSL_MSVC_ARCH_SUFFIX "-x64")
      ENDIF()'
    $content = $content.Replace($old2b, $new2b)

    # Patch 2c: Fix OPENSSL_FIX_VERSION extraction for OpenSSL 3.x/4.x+
    # (OPENSSL_VERSION_PATCH macro no longer exists; parse from OPENSSL_VERSION_STR instead)
    $oldFix = 'SET(OPENSSL_FIX_VERSION "${OPENSSL_VERSION_PATCH}")'
    $newFix = 'FILE(STRINGS "${OPENSSL_INCLUDE_DIR}/openssl/opensslv.h" OPENSSL_VERSION_STR_LINE REGEX "^#[\t ]*define[\t ]+OPENSSL_VERSION_STR[\t ]+\"[0-9]+\.[0-9]+\.[0-9]+\"")
    STRING(REGEX REPLACE "^.*OPENSSL_VERSION_STR[\t ]+\"[0-9]+\.[0-9]+\.([0-9]+)\".*$" "\\1" OPENSSL_FIX_VERSION "${OPENSSL_VERSION_STR_LINE}")'
    $content = $content.Replace($oldFix, $newFix)

    [System.IO.File]::WriteAllText($sslCmake.FullName, $content, [System.Text.Encoding]::UTF8)
    Write-Host "✓ Patched ssl.cmake: $($sslCmake.FullName)" -ForegroundColor Green
}

# =====================================================
# Patch-MysqlclientSysVersionCheck Patch Function
# =====================================================
function Patch-MysqlclientSysVersionCheck {
    $buildRs = Get-ChildItem "D:\Programs\cargo\registry\src" -Recurse -Filter "build.rs" |
        Where-Object { $_.FullName -like "*mysqlclient-sys-*" } |
        Select-Object -First 1

    if (-not $buildRs) {
        Write-Host "mysqlclient-sys build.rs not found - may not be downloaded yet" -ForegroundColor Red
        Write-Host "Run: cargo install diesel_cli --features mysql (let it fail once first)" -ForegroundColor Yellow
        return
    }

    $content = Get-Content $buildRs.FullName -Raw
    $changed = $false

    # --- Patch A: explicit 9.x fallback (9.6, 9.7, 9.8, ...) -> 9.5.x bindings ---
    if ($content -notmatch 'PATCHED: any MySQL 9\.x newer than 9\.5') {
        $oldA = "        } else if version.starts_with(`"9.5`") {`n            Some(Self::Mysql95)`n        } else if version.starts_with(`"3.1`")"
        $newA = "        } else if version.starts_with(`"9.5`") {`n            Some(Self::Mysql95)`n        } else if version.starts_with(`"9.`") {`n            // PATCHED: any MySQL 9.x newer than 9.5 (9.6, 9.7, 9.8, ...) falls back`n            // to the 9.5.x bindings. The libmysqlclient C ABI is stable across 9.x`n            // minors, so this holds until mysqlclient-sys ships real bindings for them.`n            Some(Self::Mysql95)`n        } else if version.starts_with(`"3.1`")"

        if ($content -match [regex]::Escape($oldA)) {
            $content = $content.Replace($oldA, $newA)
            Write-Host "✓ Applied patch A (explicit 9.x fallback)" -ForegroundColor Green
            $changed = $true
        } else {
            Write-Host "⚠ Anchor for patch A not found — skipping (may already differ)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✓ Patch A already applied" -ForegroundColor Cyan
    }

    # --- Patch B: universal fallback for anything unrecognized (26.x, future schemes, ...) ---
    if ($content -notmatch 'PATCHED: unrecognized version') {
        $oldB = "        } else if version.starts_with(`"3.4`") || version.starts_with(`"11`") {`n            Some(Self::MariaDb34)`n        } else {`n            None`n        }`n    }"
        $newB = "        } else if version.starts_with(`"3.4`") || version.starts_with(`"11`") {`n            Some(Self::MariaDb34)`n        } else {`n            // PATCHED: unrecognized version (e.g. a new MySQL numbering scheme like`n            // 26.x, or a future MariaDB release) - fall back to the newest known`n            // MySQL bindings rather than panicking.`n            Some(Self::Mysql95)`n        }`n    }"

        if ($content -match [regex]::Escape($oldB)) {
            $content = $content.Replace($oldB, $newB)
            Write-Host "✓ Applied patch B (universal fallback)" -ForegroundColor Green
            $changed = $true
        } else {
            Write-Host "⚠ Anchor for patch B not found — skipping (may already differ)" -ForegroundColor Yellow
        }
    } else {
        Write-Host "✓ Patch B already applied" -ForegroundColor Cyan
    }

    if ($changed) {
        [System.IO.File]::WriteAllText($buildRs.FullName, $content, [System.Text.Encoding]::UTF8)
        Write-Host "`n✓ build.rs updated: $($buildRs.FullName)" -ForegroundColor Green
    } else {
        Write-Host "`nNo changes made — already patched or anchors not found." -ForegroundColor Gray
    }
}
Set-Alias -Name patch-mysqlsys -Value Patch-MysqlclientSysVersionCheck

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

#======================================================
# Update-Pcre from source: https://github.com/ModelCloud/PyPcre (using meson build system)
#======================================================

function Update-PyPcre {
    $originalLocation = Get-Location
    Set-Location D:\dev\PyPcre

    # ── Files that are YOURS — never overwritten by upstream ──
    $forkFiles = @(
        "README.md",
        "meson.build",
        "meson.options",
        "pyproject.toml"
        # add setup.py, setup.cfg etc. if upstream ever ships them
    )

    # ── 1. Fetch upstream ──
    Write-Host "Fetching upstream (ModelCloud/PyPcre)..." -ForegroundColor Cyan
    git fetch upstream
    if ($LASTEXITCODE -ne 0) { Write-Warning "git fetch upstream failed"; Set-Location $originalLocation; return }

    # ── 2. Stash your fork files to a temp folder ──
    $tmpDir = Join-Path $env:TEMP "pypcre_fork_files"
    Remove-Item $tmpDir -Recurse -Force -ErrorAction SilentlyContinue
    New-Item $tmpDir -ItemType Directory | Out-Null

    foreach ($f in $forkFiles) {
        if (Test-Path $f) {
            Copy-Item $f (Join-Path $tmpDir $f)
            Write-Host "  Saved: $f" -ForegroundColor DarkGray
        }
    }

    # ── 3. Hard reset local to upstream/main (becomes identical to ModelCloud) ──
    git reset --hard upstream/main
    if ($LASTEXITCODE -ne 0) { Write-Warning "git reset --hard upstream/main failed"; Set-Location $originalLocation; return }
    Write-Host "  ✓ Local reset to upstream/main" -ForegroundColor Green

    # ── 4. Restore your fork files on top ──
    $restored = @()
    foreach ($f in $forkFiles) {
        $saved = Join-Path $tmpDir $f
        if (Test-Path $saved) {
            Copy-Item $saved $f -Force
            git add $f
            $restored += $f
        }
    }

    if ($restored.Count -gt 0) {
        $msg = "chore: sync upstream/main, retain fork files [$(($restored) -join ', ')]"
        git diff --cached --quiet
        if ($LASTEXITCODE -ne 0) {
            git commit -m $msg
            Write-Host "  ✓ Fork files restored and committed" -ForegroundColor Green
        } else {
            Write-Host "  ✓ Fork files unchanged vs upstream — no commit needed" -ForegroundColor Green
        }
    }

    # ── 5. Push to your fork ──
    $pushOut = git push origin main --force 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git push to your fork failed:"
        Write-Host ($pushOut | Out-String).Trim() -ForegroundColor Red
        Set-Location $originalLocation; return
    }
    Write-Host "  ✓ Your fork (jdb130496/PyPcre) synced" -ForegroundColor Green

    # ── Snapshot env ──
    $savedPath      = $env:PATH
    $savedCC        = $env:CC
    $savedCXX       = $env:CXX
    $savedINCLUDE   = $env:INCLUDE
    $savedLIB       = $env:LIB
    $savedCMakeC    = $env:CMAKE_C_COMPILER
    $savedCMakeCX   = $env:CMAKE_CXX_COMPILER
    $savedCMakeG    = $env:CMAKE_GENERATOR
    $savedCMakeMk   = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn   = $env:CMAKE_LINKER
    $savedWinSDKVer = $env:WindowsSDKVersion
    $savedWinSDKDir = $env:WindowsSDKDir

    use-clang-win

    # ── 6. Build & install ──
    pip install . --no-build-isolation --no-cache-dir --force-reinstall `
      --config-settings=setup-args="-Dpcre2_include_dir=D:\Programs\pcre2-clang-win\include" `
      --config-settings=setup-args="-Dpcre2_library=D:\Programs\pcre2-clang-win\lib\pcre2-8.lib"

    # ── Restore env ──
    $env:PATH               = $savedPath
    $env:INCLUDE            = $savedINCLUDE
    $env:LIB                = $savedLIB
    $env:CMAKE_GENERATOR    = $savedCMakeG
    $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
    if ($savedCC)        { $env:CC                 = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
    if ($savedCXX)       { $env:CXX                = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
    if ($savedCMakeC)    { $env:CMAKE_C_COMPILER   = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
    if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
    if ($savedCMakeLn)   { $env:CMAKE_LINKER       = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
    if ($savedWinSDKVer) { $env:WindowsSDKVersion  = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
    if ($savedWinSDKDir) { $env:WindowsSDKDir      = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }

    Set-Location $originalLocation

    $pth = "D:\Programs\Python\Lib\site-packages\pcre2-clang-win.pth"
    if (-not (Test-Path $pth)) {
        @"
import os; os.add_dll_directory(r'D:\Programs\pcre2-clang-win\bin')
"@ | Set-Content $pth -Encoding UTF8
        Write-Host "✓ Created DLL search path: $pth" -ForegroundColor Green
    }
    python -c "import pcre_ext_c; import pcre; print('PyPcre Python:', pcre.__version__, '| PCRE2 C:', pcre_ext_c.get_library_version())"
}

#====================================================
# Build ripgrep from source, linked against custom
# PCRE2 at D:\Programs\pcre2-clang-win
# Output: D:\dev\ripgrep\target\release\rg.exe
#          D:\Programs\cargo\bin\rg.exe (system-wide)
# Requires: Update-Pcre2Win to have run first
#====================================================
function Update-RipgrepWin {
    # All git work BEFORE toolchain switch
    Set-Location D:\dev\ripgrep
    git pull
    git submodule update --init --recursive

    # Dynamically find whichever pcre2-sys version is in the registry
    $pcre2SysDir = Get-ChildItem "D:\Programs\cargo\registry\src\index.crates.io-1949cf8c6b5b557f" `
        -Directory | Where-Object { $_.Name -like "pcre2-sys-*" } |
        Sort-Object Name -Descending | Select-Object -First 1
    if (-not $pcre2SysDir) {
        Write-Host "✗ pcre2-sys not found in registry — run: cargo build --features pcre2 once to download it" -ForegroundColor Red
        return
    }
    $buildRs = "$($pcre2SysDir.FullName)\build.rs"
    Write-Host "  pcre2-sys: $($pcre2SysDir.Name)" -ForegroundColor Gray

    attrib -r $buildRs

    # Patch build.rs to link against our custom PCRE2 instead of bundled upstream
    $content = Get-Content $buildRs -Raw
    if ($content -notmatch 'PATCHED') {
        $old = 'fn main() {
    println!("cargo:rerun-if-env-changed=PCRE2_SYS_STATIC");'
        $new = 'fn main() {
    // PATCHED: link against custom clang-win PCRE2 build instead of bundled
    println!("cargo:rerun-if-env-changed=PCRE2_SYS_STATIC");
    println!("cargo:rustc-link-search=native=D:\\Programs\\pcre2-clang-win\\lib");
    println!("cargo:rustc-link-lib=static=pcre2-8-static");
    return;'
        $content = $content.Replace($old, $new)
        [System.IO.File]::WriteAllText($buildRs, $content, [System.Text.Encoding]::UTF8)
        Write-Host "✓ Patched pcre2-sys build.rs" -ForegroundColor Green
    } else {
        Write-Host "✓ pcre2-sys build.rs already patched" -ForegroundColor Cyan
    }

    # Ensure .cargo\config.toml has lld-link as linker
    # Re-applied after every git pull in case upstream overwrites it
    $cargoConfig = "D:\dev\ripgrep\.cargo\config.toml"
    $configContent = Get-Content $cargoConfig -Raw
    if ($configContent -notmatch 'lld-link') {
        $old = '[target.x86_64-pc-windows-msvc]
rustflags = ["-C", "target-feature=+crt-static"]'
        $new = '[target.x86_64-pc-windows-msvc]
linker = "D:\\Programs\\clang\\bin\\lld-link.exe"
rustflags = ["-C", "target-feature=+crt-static"]'
        $configContent = $configContent.Replace($old, $new)
        [System.IO.File]::WriteAllText($cargoConfig, $configContent, [System.Text.Encoding]::UTF8)
        Write-Host "✓ Patched .cargo\config.toml with lld-link" -ForegroundColor Green
    } else {
        Write-Host "✓ .cargo\config.toml already has lld-link" -ForegroundColor Cyan
    }

    # Read actual PCRE2 version from source so verification is always current
    $pcre2Version = $null
    $configAc = "D:\dev\pcre2\configure.ac"
    if (Test-Path $configAc) {
        $major = (Select-String 'pcre2_major,\s*\[(\d+)\]' $configAc).Matches[0].Groups[1].Value
        $minor = (Select-String 'pcre2_minor,\s*\[(\d+)\]' $configAc).Matches[0].Groups[1].Value
        $pcre2Version = "$major\.$minor"
    }

    # Snapshot env
    $savedPath       = $env:PATH
    $savedCC         = $env:CC
    $savedCXX        = $env:CXX
    $savedINCLUDE    = $env:INCLUDE
    $savedLIB        = $env:LIB
    $savedCMakeC     = $env:CMAKE_C_COMPILER
    $savedCMakeCX    = $env:CMAKE_CXX_COMPILER
    $savedCMakeG     = $env:CMAKE_GENERATOR
    $savedCMakeMk    = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn    = $env:CMAKE_LINKER
    $savedWinSDKVer  = $env:WindowsSDKVersion
    $savedWinSDKDir  = $env:WindowsSDKDir
    $savedCargoHome  = $env:CARGO_HOME
    $savedRustupHome = $env:RUSTUP_HOME

    use-clang-win

    $env:CARGO_HOME  = "D:\Programs\cargo"
    $env:RUSTUP_HOME = "D:\Programs\rustup"

    # Clean previous artifacts so patched build.rs is guaranteed to re-run
    cargo clean

    cargo build --release --features pcre2

    # Restore env
    $env:PATH               = $savedPath
    $env:INCLUDE            = $savedINCLUDE
    $env:LIB                = $savedLIB
    $env:CMAKE_GENERATOR    = $savedCMakeG
    $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
    if ($savedCC)         { $env:CC                  = $savedCC         } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
    if ($savedCXX)        { $env:CXX                 = $savedCXX        } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
    if ($savedCMakeC)     { $env:CMAKE_C_COMPILER    = $savedCMakeC     } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
    if ($savedCMakeCX)    { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX    } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
    if ($savedCMakeLn)    { $env:CMAKE_LINKER        = $savedCMakeLn    } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
    if ($savedWinSDKVer)  { $env:WindowsSDKVersion   = $savedWinSDKVer  } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
    if ($savedWinSDKDir)  { $env:WindowsSDKDir       = $savedWinSDKDir  } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }
    if ($savedCargoHome)  { $env:CARGO_HOME          = $savedCargoHome  } else { Remove-Item Env:\CARGO_HOME          -ErrorAction SilentlyContinue }
    if ($savedRustupHome) { $env:RUSTUP_HOME         = $savedRustupHome } else { Remove-Item Env:\RUSTUP_HOME         -ErrorAction SilentlyContinue }

    Set-Location D:\

    # Confirm binary is fresh, install system-wide, verify PCRE2 version
    $rg     = "D:\dev\ripgrep\target\release\rg.exe"
    $dest   = "D:\Programs\cargo\bin\rg.exe"
    $cutoff = (Get-Date).AddMinutes(-5)

    if ((Test-Path $rg) -and ((Get-Item $rg).LastWriteTime -gt $cutoff)) {
        Write-Host "✓ ripgrep built: $rg" -ForegroundColor Green

        # Install to cargo bin so rg is available system-wide in PATH
        Copy-Item $rg $dest -Force
        if (Test-Path $dest) {
            Write-Host "✓ Installed to: $dest" -ForegroundColor Green
        } else {
            Write-Host "✗ Failed to copy to $dest" -ForegroundColor Red
        }

        & $dest --version

        # Confirm our custom PCRE2 is baked in using dynamic version from source
        if ($pcre2Version) {
            $bytes = [System.IO.File]::ReadAllBytes($dest)
            $text  = [System.Text.Encoding]::ASCII.GetString($bytes)
            $match = [regex]::Match($text, "$pcre2Version[\x20-\x7E]{0,15}")
            if ($match.Success) {
                Write-Host "✓ PCRE2 $($major).$($minor)-DEV confirmed inside rg.exe: $($match.Value)" -ForegroundColor Green
            } else {
                Write-Host "⚠ PCRE2 $($major).$($minor)-DEV string not found in binary — check patch" -ForegroundColor Yellow
            }
        }
    } else {
        Write-Host "✗ Build failed — rg.exe not found or not updated" -ForegroundColor Red
    }
}

function Update-RgaWin {
    $rgaDir  = "D:\dev\ripgrep-all"
    $destDir = "D:\Programs\cargo\bin"

    # ── Clone if missing, then update ────────────────────────────────
    if (-not (Test-Path $rgaDir)) {
        Write-Host "  Cloning ripgrep-all..." -ForegroundColor Gray
        git clone https://github.com/phiresky/ripgrep-all $rgaDir
        if (-not (Test-Path "$rgaDir\Cargo.toml")) {
            Write-Host "✗ Clone failed — aborting" -ForegroundColor Red
            return
        }
    }

    try { Set-Location $rgaDir -ErrorAction Stop }
    catch { Write-Host "✗ Could not cd to $rgaDir — aborting" -ForegroundColor Red; return }

    git pull
    git submodule update --init --recursive

    # ── Snapshot env (restored in finally) ───────────────────────────
    $envNames = 'PATH','CC','CXX','INCLUDE','LIB','CMAKE_C_COMPILER','CMAKE_CXX_COMPILER',
                'CMAKE_GENERATOR','CMAKE_MAKE_PROGRAM','CMAKE_LINKER','WindowsSDKVersion',
                'WindowsSDKDir','CARGO_HOME','RUSTUP_HOME','DISTUTILS_USE_SDK','MSSdk',
                'LINKER','LINK','VCToolsInstallDir'
    $saved = @{}
    foreach ($n in $envNames) { $saved[$n] = [Environment]::GetEnvironmentVariable($n, 'Process') }

    $buildOk = $false
    try {
        use-clang-win
        $env:CARGO_HOME  = "D:\Programs\cargo"
        $env:RUSTUP_HOME = "D:\Programs\rustup"

        # rga has no pcre2 feature and no pcre2-sys dependency — it shells out to rg.
        cargo clean
        cargo build --release
        $buildOk = ($LASTEXITCODE -eq 0)
    }
    finally {
        foreach ($n in $envNames) {
            [Environment]::SetEnvironmentVariable($n, $saved[$n], 'Process')
        }
        Set-Location D:\
    }

    if (-not $buildOk) {
        Write-Host "✗ cargo build failed — see output above" -ForegroundColor Red
        return
    }

    # ── Install binaries ─────────────────────────────────────────────
    foreach ($name in @("rga", "rga-fzf")) {
        $src  = "$rgaDir\target\release\$name.exe"
        $dest = "$destDir\$name.exe"
        if (Test-Path $src) {
            Copy-Item $src $dest -Force
            Write-Host "✓ $name installed: $dest" -ForegroundColor Green
        } else {
            Write-Host "⚠ $name.exe not produced by this build" -ForegroundColor Yellow
        }
    }

    & "$destDir\rga.exe" --version

    # ── Confirm the rg that rga will call has your custom PCRE2 ──────
    $rgCmd = Get-Command rg -ErrorAction SilentlyContinue
    if ($rgCmd) {
        Write-Host "  rga will use: $($rgCmd.Source)" -ForegroundColor Gray
        & rg --pcre2-version
    } else {
        Write-Host "⚠ rg not found in PATH — rga needs it at runtime" -ForegroundColor Yellow
    }
}

#====================================================
# Building PCRE2 C static lnd dll lib from source (clang-win)
# Output: D:\Programs\pcre2-clang-win\lib\pcre2-8-static.lib
#====================================================
function Update-Pcre2Win {
    # All git work BEFORE toolchain switch
    Set-Location D:\dev\pcre2
    git pull
    git submodule update --init --recursive

    # Snapshot env
    $savedPath      = $env:PATH
    $savedCC        = $env:CC
    $savedCXX       = $env:CXX
    $savedINCLUDE   = $env:INCLUDE
    $savedLIB       = $env:LIB
    $savedCMakeC    = $env:CMAKE_C_COMPILER
    $savedCMakeCX   = $env:CMAKE_CXX_COMPILER
    $savedCMakeG    = $env:CMAKE_GENERATOR
    $savedCMakeMk   = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn   = $env:CMAKE_LINKER
    $savedWinSDKVer = $env:WindowsSDKVersion
    $savedWinSDKDir = $env:WindowsSDKDir

    use-clang-win

    # Use standalone cmake explicitly — prevents pip-installed cmake (Python\Scripts) from
    # shadowing the profile's $cmakeRoot\bin\cmake.exe via PATH ordering.
    $cmakeExe = "$cmakeRoot\bin\cmake.exe"
    if (-not (Test-Path $cmakeExe)) {
        Write-Host "✗ Standalone cmake not found at $cmakeExe — run Update-WinCmake first" -ForegroundColor Red
        $env:PATH               = $savedPath
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCC)        { $env:CC                  = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
        if ($savedCXX)       { $env:CXX                 = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
        if ($savedCMakeC)    { $env:CMAKE_C_COMPILER    = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
        if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
        if ($savedCMakeLn)   { $env:CMAKE_LINKER        = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
        if ($savedWinSDKVer) { $env:WindowsSDKVersion   = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
        if ($savedWinSDKDir) { $env:WindowsSDKDir       = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }
        Set-Location D:\
        return
    }

    # Probe optional dependencies.
    # Readline and Editline are permanently OFF — pcre2test is disabled.
    # BZip2 and ZLIB are linked in when installed at their profile roots.
    $useBzip2 = $false
    $useZlib  = $false

    if ((Test-Path "$bzip2Root\include\bzlib.h") -and (Test-Path "$bzip2Root\lib")) {
        $useBzip2 = $true
        Write-Host "  BZip2 found at $bzip2Root — enabling" -ForegroundColor Cyan
    } else {
        Write-Host "  BZip2 not found at $bzip2Root — building without" -ForegroundColor DarkGray
    }
    if ((Test-Path "$zlibRoot\include\zlib.h") -and (Test-Path "$zlibRoot\lib")) {
        $useZlib = $true
        Write-Host "  ZLIB found at $zlibRoot — enabling" -ForegroundColor Cyan
    } else {
        Write-Host "  ZLIB not found at $zlibRoot — building without" -ForegroundColor DarkGray
    }

    # Build cmake argument list dynamically
    $cmakeArgs = @(
        "-B", "build",
        "-G", "Ninja",
        "-DCMAKE_BUILD_TYPE=Release",
        "-DCMAKE_INSTALL_PREFIX=D:\Programs\pcre2-clang-win",
        "-DCMAKE_C_COMPILER=$clangRoot\bin\clang-cl.exe",
        "-DCMAKE_CXX_COMPILER=$clangRoot\bin\clang-cl.exe",
        "-DCMAKE_LINKER=$clangRoot\bin\lld-link.exe",
        "-DBUILD_SHARED_LIBS=ON",
        "-DBUILD_STATIC_LIBS=ON",
        "-DPCRE2_BUILD_PCRE2_8=ON",
        "-DPCRE2_BUILD_PCRE2_16=OFF",
        "-DPCRE2_BUILD_PCRE2_32=OFF",
        "-DPCRE2_SUPPORT_JIT=ON",
        "-DPCRE2_SUPPORT_UNICODE=ON",
        "-DPCRE2_BUILD_TESTS=OFF",
        "-DPCRE2_BUILD_PCRE2GREP=OFF",
        "-DPCRE2_BUILD_PCRE2TEST=OFF",
        # Suppress searches for optional deps only used by disabled components
        "-DPCRE2_SUPPORT_LIBREADLINE=OFF",
        "-DPCRE2_SUPPORT_LIBEDIT=OFF"
    )

    if ($useBzip2) {
        $bzip2LibFile = Get-ChildItem "$bzip2Root\lib\*.lib" |
                        Where-Object { $_.Name -notmatch 'static|dll' } |
                        Select-Object -First 1
        if (-not $bzip2LibFile) {
            $bzip2LibFile = Get-ChildItem "$bzip2Root\lib\*.lib" | Select-Object -First 1
        }
        $cmakeArgs += "-DPCRE2_SUPPORT_LIBBZ2=ON"
        $cmakeArgs += "-DBZIP2_INCLUDE_DIR=$bzip2Root\include"
        if ($bzip2LibFile) { $cmakeArgs += "-DBZIP2_LIBRARIES=$($bzip2LibFile.FullName)" }
    } else {
        $cmakeArgs += "-DPCRE2_SUPPORT_LIBBZ2=OFF"
    }

    if ($useZlib) {
        # zlib cmake installs: z.lib (import), zs.lib (static), z.dll (newer naming)
        # or zlib.lib / zlibstatic.lib / zlib1.dll (older naming) — probe both
        # Resolve to a full path string — prefer import lib (z.lib/zlib.lib) for linking
        $zlibLibPath = @("$zlibRoot\lib\z.lib","$zlibRoot\lib\zlib.lib") |
                       Where-Object { Test-Path $_ } | Select-Object -First 1
        if (-not $zlibLibPath) {
            $zlibLibPath = (Get-ChildItem "$zlibRoot\lib\*.lib" | Select-Object -First 1).FullName
        }
        $cmakeArgs += "-DPCRE2_SUPPORT_LIBZ=ON"
        $cmakeArgs += "-DZLIB_INCLUDE_DIR=$zlibRoot\include"
        if ($zlibLibPath) { $cmakeArgs += "-DZLIB_LIBRARY=$zlibLibPath" }
    } else {
        $cmakeArgs += "-DPCRE2_SUPPORT_LIBZ=OFF"
    }

    # Configure
    Write-Host "==> Configuring PCRE2..." -ForegroundColor Cyan
    & $cmakeExe @cmakeArgs
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ CMake configure failed" -ForegroundColor Red
        $env:PATH               = $savedPath
        $env:INCLUDE            = $savedINCLUDE
        $env:LIB                = $savedLIB
        $env:CMAKE_GENERATOR    = $savedCMakeG
        $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
        if ($savedCC)        { $env:CC                  = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
        if ($savedCXX)       { $env:CXX                 = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
        if ($savedCMakeC)    { $env:CMAKE_C_COMPILER    = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
        if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
        if ($savedCMakeLn)   { $env:CMAKE_LINKER        = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
        if ($savedWinSDKVer) { $env:WindowsSDKVersion   = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
        if ($savedWinSDKDir) { $env:WindowsSDKDir       = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }
        Set-Location D:\
        return
    }

    # Build
    Write-Host "==> Building PCRE2..." -ForegroundColor Cyan
    & $cmakeExe --build build --config Release
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ CMake build failed" -ForegroundColor Red
    } else {
        Write-Host "==> Installing PCRE2..." -ForegroundColor Cyan
        & $cmakeExe --install build
    }

    # Restore env
    $env:PATH               = $savedPath
    $env:INCLUDE            = $savedINCLUDE
    $env:LIB                = $savedLIB
    $env:CMAKE_GENERATOR    = $savedCMakeG
    $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
    if ($savedCC)        { $env:CC                  = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
    if ($savedCXX)       { $env:CXX                 = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
    if ($savedCMakeC)    { $env:CMAKE_C_COMPILER    = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
    if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
    if ($savedCMakeLn)   { $env:CMAKE_LINKER        = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
    if ($savedWinSDKVer) { $env:WindowsSDKVersion   = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
    if ($savedWinSDKDir) { $env:WindowsSDKDir       = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }

    Set-Location D:\

    # Confirm outputs freshly written
    $cutoff    = (Get-Date).AddMinutes(-5)
    $staticLib = "D:\Programs\pcre2-clang-win\lib\pcre2-8-static.lib"
    $dll       = "D:\Programs\pcre2-clang-win\bin\pcre2-8.dll"
    $importLib = "D:\Programs\pcre2-clang-win\lib\pcre2-8.lib"

    if ((Test-Path $staticLib) -and ((Get-Item $staticLib).LastWriteTime -gt $cutoff)) {
        Write-Host "✓ Static lib: $staticLib" -ForegroundColor Green
    } else {
        Write-Host "✗ Static lib missing or stale" -ForegroundColor Red
    }
    if ((Test-Path $dll) -and ((Get-Item $dll).LastWriteTime -gt $cutoff)) {
        Write-Host "✓ DLL:        $dll" -ForegroundColor Green
    } else {
        Write-Host "✗ DLL missing or stale" -ForegroundColor Red
    }
    if ((Test-Path $importLib) -and ((Get-Item $importLib).LastWriteTime -gt $cutoff)) {
        Write-Host "✓ Import lib: $importLib" -ForegroundColor Green
    } else {
        Write-Host "✗ Import lib missing or stale" -ForegroundColor Red
    }
}
#====================================================
# Building pcre2 from github source
# ===================================================

function Update-Pcre2 {
    # All git work BEFORE toolchain switch so MinGit never runs with polluted PATH
    Set-Location D:\dev\pcre2.py
    git pull

    git config --global --add safe.directory D:/dev/pcre2.py/src/libpcre2
    Set-Location src\libpcre2
    git fetch origin
    git fetch --tags origin

    # Read version from installed pcre2-clang-win header — reliable, no ctypes needed
    $headerPath   = "D:\Programs\pcre2-clang-win\include\pcre2.h"
    $installedVer = $null
    if (Test-Path $headerPath) {
        $major = (Select-String '#define PCRE2_MAJOR\s+(\d+)' $headerPath).Matches[0].Groups[1].Value
        $minor = (Select-String '#define PCRE2_MINOR\s+(\d+)' $headerPath).Matches[0].Groups[1].Value
        if ($major -and $minor) { $installedVer = "$major.$minor" }
    }

    if ($installedVer) {
        Write-Host "  Installed pcre2-clang-win reports: $installedVer" -ForegroundColor Cyan
        $tag       = "pcre2-$installedVer"
        $tagExists = git tag -l $tag
        if ($tagExists) {
            git checkout $tag
            Write-Host "  ✓ Submodule pinned to $tag" -ForegroundColor Green
        } else {
            git checkout origin/main
            $configureAc = "D:\dev\pcre2.py\src\libpcre2\configure.ac"
            $subVer = $null
            if (Test-Path $configureAc) {
                $maj = (Select-String "m4_define\(pcre2_major,\s*\[(\d+)\]\)" $configureAc -ErrorAction SilentlyContinue)
                $min = (Select-String "m4_define\(pcre2_minor,\s*\[(\d+)\]\)" $configureAc -ErrorAction SilentlyContinue)
                if ($maj -and $min) {
                    $subVer = "$($maj.Matches[0].Groups[1].Value).$($min.Matches[0].Groups[1].Value)"
                }
            }
            if ($subVer -eq $installedVer) {
                Write-Host "  ✓ Submodule origin/main ($subVer) matches installed — no release tag yet" -ForegroundColor Green
            } else {
                Write-Host "  ⚠ Tag $tag not found — using origin/main ($subVer vs installed $installedVer)" -ForegroundColor Yellow
            }
        }
    } else {
        git checkout origin/main
        Write-Host "  ⚠ Could not read installed header version — using origin/main" -ForegroundColor Yellow
    }

    Set-Location D:\dev\pcre2.py

    # Snapshot env
    $savedPath      = $env:PATH
    $savedCC        = $env:CC
    $savedCXX       = $env:CXX
    $savedINCLUDE   = $env:INCLUDE
    $savedLIB       = $env:LIB
    $savedCMakeC    = $env:CMAKE_C_COMPILER
    $savedCMakeCX   = $env:CMAKE_CXX_COMPILER
    $savedCMakeG    = $env:CMAKE_GENERATOR
    $savedCMakeMk   = $env:CMAKE_MAKE_PROGRAM
    $savedCMakeLn   = $env:CMAKE_LINKER
    $savedWinSDKVer = $env:WindowsSDKVersion
    $savedWinSDKDir = $env:WindowsSDKDir

    use-clang-win
    pip cache purge 2>&1 | Out-Null
    pip install . --no-build-isolation --no-cache-dir --force-reinstall `
      --config-settings=setup-args="-Dpcre2_include_dir=D:\Programs\pcre2-clang-win\include" `
      --config-settings=setup-args="-Dpcre2_library=D:\Programs\pcre2-clang-win\lib\pcre2-8.lib"

    # Restore env
    $env:PATH               = $savedPath
    $env:INCLUDE            = $savedINCLUDE
    $env:LIB                = $savedLIB
    $env:CMAKE_GENERATOR    = $savedCMakeG
    $env:CMAKE_MAKE_PROGRAM = $savedCMakeMk
    if ($savedCC)        { $env:CC                  = $savedCC        } else { Remove-Item Env:\CC                  -ErrorAction SilentlyContinue }
    if ($savedCXX)       { $env:CXX                 = $savedCXX       } else { Remove-Item Env:\CXX                 -ErrorAction SilentlyContinue }
    if ($savedCMakeC)    { $env:CMAKE_C_COMPILER    = $savedCMakeC    } else { Remove-Item Env:\CMAKE_C_COMPILER    -ErrorAction SilentlyContinue }
    if ($savedCMakeCX)   { $env:CMAKE_CXX_COMPILER  = $savedCMakeCX   } else { Remove-Item Env:\CMAKE_CXX_COMPILER  -ErrorAction SilentlyContinue }
    if ($savedCMakeLn)   { $env:CMAKE_LINKER        = $savedCMakeLn   } else { Remove-Item Env:\CMAKE_LINKER        -ErrorAction SilentlyContinue }
    if ($savedWinSDKVer) { $env:WindowsSDKVersion   = $savedWinSDKVer } else { Remove-Item Env:\WindowsSDKVersion   -ErrorAction SilentlyContinue }
    if ($savedWinSDKDir) { $env:WindowsSDKDir       = $savedWinSDKDir } else { Remove-Item Env:\WindowsSDKDir       -ErrorAction SilentlyContinue }

    Set-Location D:\
    python -c "import pcre2; print('pcre2 Python:', pcre2.__version__, '| PCRE2 C:', pcre2.__libpcre2_version__)"
}

# =====================================================
# NASM / OpenSSL Bisect Regression Automation
# =====================================================

function Find-NasmOpenSSLRegression {
    [CmdletBinding()]
    param(
        [string]$StartCommit = "18c778c",
        [string]$EndCommit   = "b2734a9",
        [string]$OpenSSLDir  = "D:\Downloads\OpenSSL"
    )

    $nasmSrc = "D:\dev\nasm-src"
    if (-not (Test-Path $nasmSrc)) {
        throw "NASM source directory not found at $nasmSrc"
    }

    # ASM targets to probe: [perl generator script, output asm path, symbol to verify]
    $asmTargets = @(
        @{
            Pl     = "$OpenSSLDir\crypto\sm3\asm\sm3-x86_64.pl"
            Asm    = "$OpenSSLDir\crypto\sm3\sm3-x86_64.asm"
            Obj    = "$OpenSSLDir\crypto\sm3\sm3-x86_64.obj"
            Symbol = "ossl_hwsm3_block_data_order"
        },
        @{
            Pl     = "$OpenSSLDir\crypto\aes\asm\aesni-x86_64.pl"
            Asm    = "$OpenSSLDir\crypto\aes\aesni-x86_64.asm"
            Obj    = "$OpenSSLDir\crypto\aes\aesni-x86_64.obj"
            Symbol = "aesni_encrypt"
        }
    )

    # Pre-generate .asm files once (they don't change between NASM versions)
    Write-Host "=== Pre-generating ASM files ===" -ForegroundColor Cyan
    $savedPath = $env:PATH
    $env:PATH  = "$perlRoot\perl\bin;D:\Programs\nasm;$env:PATH"
    foreach ($t in $asmTargets) {
        if (-not (Test-Path $t.Asm)) {
            Write-Host "  Generating $($t.Asm)..." -ForegroundColor DarkCyan
            perl $t.Pl win64 $t.Asm
            if ($LASTEXITCODE -ne 0) { throw "Failed to generate $($t.Asm)" }
        } else {
            Write-Host "  Reusing existing $($t.Asm)" -ForegroundColor DarkGray
        }
    }
    $env:PATH = $savedPath

    # --- Bisect setup ---
    git -C "$nasmSrc" bisect reset 2>$null
    git -C "$nasmSrc" checkout "$StartCommit" --force
    git -C "$nasmSrc" reset --hard
    git -C "$nasmSrc" clean -fdx

    Write-Host "`n=== Initializing Git Bisect for NASM ===" -ForegroundColor Cyan
    Write-Host "  Good: $StartCommit" -ForegroundColor Green
    Write-Host "  Bad:  $EndCommit"   -ForegroundColor Red

    git -C "$nasmSrc" bisect start
    git -C "$nasmSrc" bisect bad  "$EndCommit"
    git -C "$nasmSrc" bisect good "$StartCommit"

    try {
        while ($true) {

            $currentCommit  = (git -C "$nasmSrc" rev-parse --short HEAD).Trim()
            $currentSubject = (git -C "$nasmSrc" log --no-walk --format="%s" HEAD).Trim()
            Write-Host "`n--------------------------------------------------" -ForegroundColor Yellow
            Write-Host "Testing NASM commit: $currentCommit  $currentSubject" -ForegroundColor Yellow
            Write-Host "--------------------------------------------------" -ForegroundColor Yellow

            # --- Patch 1: file.c windows.h (clang-cl compat) ---
            $fileC = "$nasmSrc\nasmlib\file.c"
            if (Test-Path $fileC) {
                $content = Get-Content $fileC -Raw
                if ($content -match '#include <stringapiset\.h>' -and
                    $content -notmatch '#include <windows\.h>') {
                    $content = $content -replace '#include <stringapiset\.h>',
                        "#include <windows.h>`r`n#include <stringapiset.h>"
                    [System.IO.File]::WriteAllText($fileC, $content)
                    Write-Host "  -> Patch 1 applied: file.c windows.h" -ForegroundColor Cyan
                } else {
                    Write-Host "  -> Patch 1 skipped" -ForegroundColor DarkGray
                }
            }

            # --- Patch version file ---
            $gitDesc = (git -C "$nasmSrc" describe --tags --long --dirty 2>$null)
            if ($gitDesc) {
                $verStr = $gitDesc -replace '^nasm-', ''
                [System.IO.File]::WriteAllText("$nasmSrc\version", "$verStr`n")
            }

            # --- Build NASM ---
            Write-Host "  Building NASM..." -ForegroundColor DarkCyan
            use-clang-win
            Push-Location $nasmSrc
            nmake-msvc /f Mkfiles\msvc.mak clean 2>$null
            nmake-msvc /f Mkfiles\msvc.mak `
                CC="$clangRoot\bin\clang-cl.exe" `
                AR="$clangRoot\bin\llvm-lib.exe" `
                OPTFLAGS="/O2" `
                LDFLAGS="/opt:ref /opt:icf"
            $nasmBuildExit = $LASTEXITCODE
            Pop-Location

            if ($nasmBuildExit -ne 0) {
                Write-Host "  ✗ NASM build failed — skipping" -ForegroundColor Red
                git -C "$nasmSrc" reset --hard
                git -C "$nasmSrc" clean -fdx
                git -C "$nasmSrc" bisect skip
                continue
            }

            Copy-Item "$nasmSrc\nasm.exe"    "D:\Programs\nasm\nasm.exe"    -Force
            Copy-Item "$nasmSrc\ndisasm.exe" "D:\Programs\nasm\ndisasm.exe" -Force
            Write-Host "  ✓ NASM built: $(& D:\Programs\nasm\nasm.exe --version)" -ForegroundColor Cyan

            # --- Fast test: assemble + symbol check ---
            Write-Host "  Assembling probe targets..." -ForegroundColor DarkCyan
            $assemblyOK = $true

            foreach ($t in $asmTargets) {
                # Remove stale obj
                if (Test-Path $t.Obj) { Remove-Item $t.Obj -Force }

                & "D:\Programs\nasm\nasm.exe" -f win64 $t.Asm -o $t.Obj 2>&1 |
                    ForEach-Object { Write-Host "    nasm: $_" -ForegroundColor DarkGray }

                if (-not (Test-Path $t.Obj)) {
                    Write-Host "  ✗ Assembly failed — no .obj produced for $($t.Asm)" -ForegroundColor Red
                    $assemblyOK = $false
                    break
                }

                $syms = & "$clangRoot\bin\llvm-nm.exe" $t.Obj 2>&1
                if ($syms -match [regex]::Escape($t.Symbol)) {
                    Write-Host "  ✓ Symbol found: $($t.Symbol)" -ForegroundColor Green
                } else {
                    Write-Host "  ✗ Symbol MISSING: $($t.Symbol)" -ForegroundColor Red
                    $assemblyOK = $false
                    break
                }
            }

            # --- Clean tree before bisect step ---
            git -C "$nasmSrc" reset --hard
            git -C "$nasmSrc" clean -fdx

            if ($assemblyOK) {
                Write-Host "  → GOOD: $currentCommit  $currentSubject" -ForegroundColor Green
                $bisectOut = git -C "$nasmSrc" bisect good 2>&1
            } else {
                Write-Host "  → BAD:  $currentCommit  $currentSubject" -ForegroundColor Red
                $bisectOut = git -C "$nasmSrc" bisect bad 2>&1
            }

            Write-Host "  bisect: $bisectOut" -ForegroundColor Gray

            if ($bisectOut -match 'is the first bad commit' -or
                $bisectOut -match 'first bad commit'        -or
                $bisectOut -match 'There are only') {
                Write-Host "`n=== BISECT COMPLETE ===" -ForegroundColor Magenta
                Write-Host $bisectOut -ForegroundColor Magenta
                break
            }
        }
    } finally {
        git -C "$nasmSrc" bisect reset
        Set-Location D:\
    }
}

function Find-NasmOpenSSLRegression-New {
    [CmdletBinding()]
    param(
        [string]$StartCommit = "4a56d66", # Stable 3.02 release commit
        [string]$EndCommit = "HEAD",       # Latest broken commit
        [string]$OpenSSLDir = "D:\Downloads\OpenSSL"
    )

    $nasmSrc = "D:\dev\nasm-src"
    if (-not (Test-Path $nasmSrc)) {
        throw "NASM source directory not found at $nasmSrc"
    }

    Write-Host "=== Initializing Git Bisect for NASM ===" -ForegroundColor Cyan
    git -C "$nasmSrc" reset --hard > $null 2>&1
    git -C "$nasmSrc" clean -fdx > $null 2>&1
    git -C "$nasmSrc" bisect start > $null 2>&1
    git -C "$nasmSrc" bisect bad "$EndCommit" > $null 2>&1
    git -C "$nasmSrc" bisect good "$StartCommit" > $null 2>&1

    # --- ONE-TIME OPENSSL CONFIGURATION ---
    Write-Host "==> Performing initial OpenSSL configuration..." -ForegroundColor Cyan
    $savedPath =$env:PATH
    $savedCC =$env:CC
    $savedCXX =$env:CXX
    $savedLD =$env:LD

    try {
        $env:PATH = "$perlRoot\perl\bin;D:\Programs\nasm;$env:PATH"
        use-clang-win > $null 2>&1
        $env:CC = "$clangRoot\bin\clang-cl.exe"
        $env:CXX = "$clangRoot\bin\clang-cl.exe"
        $env:LD = "$clangRoot\bin\lld-link.exe"

        Set-Location $OpenSSLDir
        nmake-msvc distclean > $null 2>&1
        if (Test-Path "$OpenSSLDir\Makefile") { Remove-Item "$OpenSSLDir\Makefile" -Force }

        perl Configure VC-WIN64A no-makedepend --prefix="D:\Programs\OpenSSL" --openssldir="D:\Programs\OpenSSL" > $null 2>&1
        if ($LASTEXITCODE -ne 0) { throw "OpenSSL initial Configure failed" }

        (Get-Content "$OpenSSLDir\Makefile") -replace '^AR="lib"', "AR=`"$clangRoot\bin\llvm-lib.exe`"" | Set-Content "$OpenSSLDir\Makefile"
    }
    finally {
        $env:PATH =$savedPath
        if ($savedCC) { $env:CC =$savedCC } else { Remove-Item Env:\CC -ErrorAction SilentlyContinue }
        if ($savedCXX) { $env:CXX =$savedCXX } else { Remove-Item Env:\CXX -ErrorAction SilentlyContinue }
        if ($savedLD) { $env:LD =$savedLD } else { Remove-Item Env:\LD -ErrorAction SilentlyContinue }
        Set-Location D:\
    }

    try {
        while ($true) {
            $currentCommit = (git -C "$nasmSrc" rev-parse --short HEAD).Trim()
            Write-Host "`n--------------------------------------------------" -ForegroundColor Yellow
            Write-Host "Testing NASM commit: $currentCommit" -ForegroundColor Yellow
            Write-Host "--------------------------------------------------" -ForegroundColor Yellow

            # 1. Clean and prepare NASM working tree
            git -C "$nasmSrc" reset --hard > $null 2>&1
            git -C "$nasmSrc" clean -fdx > $null 2>&1

            # 2. Apply Patch 1 (file.c windows.h fix)
            $fileC = "$nasmSrc\nasmlib\file.c"
            if (Test-Path $fileC) {
                $content = Get-Content $fileC -Raw
                if ($content -notmatch '#include <windows\.h>') {
                    $content = $content -replace '#include <stringapiset\.h>', "#include <windows.h>`r`n#include <stringapiset.h>"
                    [System.IO.File]::WriteAllText($fileC, $content)
                }
            }

            # 3. Patch version file for correct embedding via git describe
            $gitDesc = (git -C "$nasmSrc" describe --tags --long --dirty 2>$null)
            if ($gitDesc) {
                $verStr = $gitDesc -replace '^nasm-', ''
                [System.IO.File]::WriteAllText("$nasmSrc\version", "$verStr`n")
            }

            # 4. Build NASM
            Write-Host "Building NASM..." -ForegroundColor DarkCyan
            use-clang-win > $null 2>&1
            Push-Location $nasmSrc
            nmake-msvc /f Mkfiles\msvc.mak clean > $null 2>&1
            nmake-msvc /f Mkfiles\msvc.mak `
                CC="$clangRoot\bin\clang-cl.exe" `
                AR="$clangRoot\bin\llvm-lib.exe" `
                OPTFLAGS="/O2" `
                LDFLAGS="/opt:ref /opt:icf" > $null 2>&1

            if ($LASTEXITCODE -ne 0) {
                Pop-Location
                Write-Host "✗ NASM build failed at this commit. Skipping..." -ForegroundColor Red
                git -C "$nasmSrc" bisect skip > $null 2>&1
                continue
            }

            if (-not (Test-Path "D:\Programs\nasm")) { New-Item -ItemType Directory -Path "D:\Programs\nasm" | Out-Null }
            Copy-Item "$nasmSrc\nasm.exe" D:\Programs\nasm\nasm.exe -Force
            Copy-Item "$nasmSrc\ndisasm.exe" D:\Programs\nasm\ndisasm.exe -Force
            Pop-Location

            # 5. Build OpenSSL
            Write-Host "Building OpenSSL with NASM $currentCommit..." -ForegroundColor DarkCyan
            $savedPath =$env:PATH
            $savedCC =$env:CC
            $savedCXX =$env:CXX
            $savedLD =$env:LD

            try {
                $env:PATH = "$perlRoot\perl\bin;D:\Programs\nasm;$env:PATH"
                use-clang-win > $null 2>&1
                $env:CC = "$clangRoot\bin\clang-cl.exe"
                $env:CXX = "$clangRoot\bin\clang-cl.exe"
                $env:LD = "$clangRoot\bin\lld-link.exe"

                Set-Location $OpenSSLDir
                
                & "$jomRoot\jom.exe" clean > $null 2>&1

                $jobs = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors
                & "$jomRoot\jom.exe" /J $jobs >$null 2>&1

                if ($LASTEXITCODE -ne 0) {
                    throw "OpenSSL build failed"
                }

                Write-Host "✓ Build succeeded for NASM $currentCommit" -ForegroundColor Green
                git -C "$nasmSrc" bisect good > $null 2>&1
            }
            catch {
                Write-Host "✗ OpenSSL build/link failed with NASM $currentCommit" -ForegroundColor Red
                git -C "$nasmSrc" bisect bad > $null 2>&1
            }
            finally {
                $env:PATH =$savedPath
                if ($savedCC) { $env:CC =$savedCC } else { Remove-Item Env:\CC -ErrorAction SilentlyContinue }
                if ($savedCXX) { $env:CXX =$savedCXX } else { Remove-Item Env:\CXX -ErrorAction SilentlyContinue }
                if ($savedLD) { $env:LD =$savedLD } else { Remove-Item Env:\LD -ErrorAction SilentlyContinue }
                Set-Location D:\
            }
        }
    }
    finally {
        git -C "$nasmSrc" bisect reset > $null 2>&1
        Set-Location D:\
    }
}

# =====================================================
# Profile Load Message
# =====================================================
function Show-ProfileInfo {
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
    Write-Host "  ✓ Bison:      $bisonVer" -ForegroundColor Green
} else {
    Write-Host "  ⚠ Bison:      not found at $bisonRoot" -ForegroundColor Red
}
if (Test-Path "$jomRoot\jom.exe") {
    Write-Host "  ✓ jom:        found at $jomRoot" -ForegroundColor Green
} else {
    Write-Host "  ⚠ jom:        not found at $jomRoot" -ForegroundColor Red
}

# Ninja status: show which binary is the active one for Windows toolchains
#$_ninjaResolved = Update-WinNinja
if (Test-Path "$ninjaRoot\bin\ninja.exe") {
    $ninjaVer = & "$ninjaRoot\bin\ninja.exe" --version 2>&1
    Write-Host "  ✓ Ninja:      $ninjaVer (standalone at $ninjaRoot)" -ForegroundColor Green
    if (Test-Path "$cmakeRoot\bin\ninja.exe") {
        $ninjaCmakeVer = & "$cmakeRoot\bin\ninja.exe" --version 2>&1
        Write-Host "    cmake-bundled also available: $ninjaCmakeVer (ninja-cmake alias)" -ForegroundColor Gray
    }
} elseif (Test-Path "$cmakeRoot\bin\ninja.exe") {
    $ninjaVer = & "$cmakeRoot\bin\ninja.exe" --version 2>&1
    Write-Host "  ✓ Ninja:      $ninjaVer (cmake-bundled — install standalone to $ninjaRoot for upgrade)" -ForegroundColor Yellow
} else {
    Write-Host "  ⚠ Ninja:      not found (install to $ninjaRoot or $cmakeRoot\bin)" -ForegroundColor Red
}

# Meson status: show which binary is active
#$_mesonResolved = Update-WinMeson
if (Test-Path "$mesonRoot\meson.cmd") {
    $mesonVer = & "$mesonRoot\meson.cmd" --version 2>&1
    Write-Host "  ✓ Meson:      $mesonVer (standalone cmd at $mesonRoot)" -ForegroundColor Green
    if (Test-Path "$pythonRoot\Scripts\meson.exe") {
        $mesonPipVer = & "$pythonRoot\Scripts\meson.exe" --version 2>&1
        Write-Host "    pip meson also available: $mesonPipVer (meson-pip alias)" -ForegroundColor Gray
    }
} elseif (Test-Path "$mesonRoot\meson.pyz") {
    $mesonVer = & "$pythonRoot\python.exe" "$mesonRoot\meson.pyz" --version 2>&1
    Write-Host "  ✓ Meson:      $mesonVer (standalone pyz at $mesonRoot)" -ForegroundColor Green
    if (Test-Path "$pythonRoot\Scripts\meson.exe") {
        $mesonPipVer = & "$pythonRoot\Scripts\meson.exe" --version 2>&1
        Write-Host "    pip meson also available: $mesonPipVer (meson-pip alias)" -ForegroundColor Gray
    }
} elseif (Test-Path "$mesonRoot\meson.exe") {
    $mesonVer = & "$mesonRoot\meson.exe" --version 2>&1
    Write-Host "  ✓ Meson:      $mesonVer (standalone at $mesonRoot)" -ForegroundColor Green
    if (Test-Path "$pythonRoot\Scripts\meson.exe") {
        $mesonPipVer = & "$pythonRoot\Scripts\meson.exe" --version 2>&1
        Write-Host "    pip meson also available: $mesonPipVer (meson-pip alias)" -ForegroundColor Gray
    }
} elseif (Test-Path "$pythonRoot\Scripts\meson.exe") {
    $mesonVer = & "$pythonRoot\Scripts\meson.exe" --version 2>&1
    Write-Host "  ✓ Meson:      $mesonVer (pip — install standalone to $mesonRoot for upgrade)" -ForegroundColor Yellow
} else {
    Write-Host "  ⚠ Meson:      not found (pip install meson or install standalone to $mesonRoot)" -ForegroundColor Red
}

# Set MESON env var so meson-python always uses standalone meson explicitly
# This bypasses PATH lookup in subprocess calls (pip, meson-python builds)


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

if (Test-Path "$bzip2Root\lib\bzip2.lib") {
    $bzip2Ver = (Get-Content "$bzip2Root\include\bzlib.h" -ErrorAction SilentlyContinue |
                 Select-String 'BZ_VERSION') -replace '.*"(.*)".*', '$1'
    Write-Host "  ✓ BZip2:      $bzip2Ver at $bzip2Root" -ForegroundColor Green
} else {
    Write-Host "  ⚠ BZip2:      not found at $bzip2Root — run Update-WinBzip2" -ForegroundColor DarkGray
}
$_zlibLib = @("$zlibRoot\lib\zs.lib","$zlibRoot\lib\zlibstatic.lib","$zlibRoot\lib\z.lib","$zlibRoot\lib\zlib.lib") |
            Where-Object { Test-Path $_ } | Select-Object -First 1
if ($_zlibLib) {
    $zlibVer = (Get-Content "$zlibRoot\include\zlib.h" -ErrorAction SilentlyContinue |
                Select-String '#define ZLIB_VERSION') -replace '.*"(.*)".*', '$1'
    Write-Host "  ✓ ZLib:       $zlibVer at $zlibRoot" -ForegroundColor Green
} else {
    Write-Host "  ⚠ ZLib:       not found at $zlibRoot — run Update-WinZlib" -ForegroundColor DarkGray
}

Write-Host "`nToolchain Switching (sets PATH + environment):" -ForegroundColor Yellow
Write-Host "  use-msvc         → MSVC (D:\dev\msvc\...)" -ForegroundColor White
Write-Host "  use-gcc          → MSYS2 GCC (D:\Programs\msys64\ucrt64\...)" -ForegroundColor White
Write-Host "  use-clang-msys   → MSYS2 Clang (D:\Programs\msys64\ucrt64\...)" -ForegroundColor White
Write-Host "  use-clang-win    → Windows Clang (D:\Programs\clang\... + D:\Programs\cmake\...)" -ForegroundColor White
Write-Host "  use-none         → Reset (no toolchain active)" -ForegroundColor White

Write-Host "`nUpdate Commands:" -ForegroundColor Yellow
Write-Host "  Update-Cargo          → Update Rust/Cargo packages" -ForegroundColor White
Write-Host "  Patch-MysqlclientSrc  → Patch mysqlclient-src build.rs for Windows MSVC" -ForegroundColor White
Write-Host "  npmupdate             → Update all global npm packages to @latest" -ForegroundColor White

Write-Host "`nExplicit Aliases (always available):" -ForegroundColor Yellow
Write-Host "  Compilers:" -ForegroundColor Cyan
Write-Host "    cl-msvc, link-msvc, lib-msvc, nmake-msvc" -ForegroundColor White
Write-Host "    gcc-msys, g++-msys, ld-msys, ar-msys" -ForegroundColor White
Write-Host "    clang-msys, clang++-msys, lld-msys" -ForegroundColor White
Write-Host "    clang-win, clang++-win, clang-cl-win, lld-link-win" -ForegroundColor White
Write-Host "  Build Tools:" -ForegroundColor Cyan
Write-Host "    cmake-win, cmake-msys" -ForegroundColor White
Write-Host "    ninja-win (standalone), ninja-cmake (cmake-bundled), ninja-msys" -ForegroundColor White
Write-Host "    meson-win (preferred), meson-pip (pip fallback), meson-standalone" -ForegroundColor White
Write-Host "    make-msys" -ForegroundColor White
Write-Host "  Python:" -ForegroundColor Cyan
Write-Host "    python314, py314, pip314" -ForegroundColor White
Write-Host "    python-msys, pip-msys" -ForegroundColor White
Write-Host "  Perl:" -ForegroundColor Cyan
Write-Host "    perl-win, perl-pcre2 (PCRE2 10.47)" -ForegroundColor White
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
Write-Host "  use-rust-stable       → Switch to stable rustc (session only, nightly stays default)" -ForegroundColor White
Write-Host "  use-rust-nightly      → Restore nightly rustc (unsets RUSTUP_TOOLCHAIN)" -ForegroundColor White
Write-Host "  rust-toolchain        → Show active and installed Rust toolchains" -ForegroundColor White

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host ""
} # end Show-ProfileInfo

$_mesonExe = Update-WinMeson
if ($_mesonExe) {
    $script:_mesonGitExe = $_mesonExe
}
# Set $env:MESON so meson-python/ninja subprocess spawning gets a directly-execable .exe.
# Prefer the self-built meson.exe from Update-WinMeson; fall back to pip only if absent.
if (Test-Path "$mesonRoot\meson.exe") {
    $env:MESON = "$mesonRoot\meson.exe"
} elseif (Test-Path "$pythonRoot\Scripts\meson.exe") {
    $env:MESON = "$pythonRoot\Scripts\meson.exe"
}

# =====================================================
# Startup message (fast — no subprocess calls)
# =====================================================
Write-Host "PS Profile loaded. Run Show-ProfileInfo for tool versions." -ForegroundColor Cyan
