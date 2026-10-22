# Bisect-NasmOpenSSL.ps1
# Usage: .\Bisect-NasmOpenSSL.ps1
# Reads commits from D:\dev\nasm-commits.txt (format: "<hash> <date> <msg>")

$logFile     = "D:\dev\bisect-log.txt"
$commitsFile = "D:\dev\nasm-commits.txt"

function Write-Log {
    param([string]$Message, [string]$Color = "White")
    $line = "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    Write-Host $line -ForegroundColor $Color
    Add-Content -Path $logFile -Value $line
}

function Invoke-Silent([scriptblock]$sb) {
    $oldOut = [Console]::Out
    $oldErr = [Console]::Error
    [Console]::SetOut([System.IO.TextWriter]::Null)
    [Console]::SetOut([System.IO.TextWriter]::Null)
    try { & $sb *>&1 | Out-Null } finally {
        [Console]::SetOut($oldOut)
        [Console]::SetError($oldErr)
    }
}

# ─── Clean both trees once at start ──────────────────────────────────────────
Invoke-Silent { git -C D:\dev\nasm-src clean -fdx }
Invoke-Silent { git -C D:\dev\nasm-src reset --hard }
Invoke-Silent { git -C "D:\Downloads\OpenSSL" clean -fdx }
Invoke-Silent { git -C "D:\Downloads\OpenSSL" reset --hard }
Write-Log "Both source trees cleaned" "Cyan"

# ─── Load commits from file ───────────────────────────────────────────────────
# File format — one commit per line:  <hash> <YYYY-MM-DD> <message>
# Generate with: git log nasm-3.02..HEAD --format="%h %ad %s" --date=short --reverse > D:\dev\nasm-commits.txt
$commits = Get-Content $commitsFile | Where-Object { $_ -match '\S' } | ForEach-Object {
    if ($_ -match '^(\S+)\s+(\S+)\s+(.+)$') {
        [PSCustomObject]@{ Hash = $Matches[1]; Date = $Matches[2]; Msg = $Matches[3] }
    }
}
Write-Log "Loaded $($commits.Count) commits from $commitsFile" "Cyan"

# ─── Build NASM at a specific commit ─────────────────────────────────────────
function Build-Nasm {
    param([string]$Hash, [string]$Date, [string]$Msg)

    $saved = @{
        PATH = $env:PATH; CC = $env:CC; CXX = $env:CXX
        INCLUDE = $env:INCLUDE; LIB = $env:LIB
        CMAKE_C_COMPILER = $env:CMAKE_C_COMPILER
        CMAKE_CXX_COMPILER = $env:CMAKE_CXX_COMPILER
        CMAKE_GENERATOR = $env:CMAKE_GENERATOR
        CMAKE_MAKE_PROGRAM = $env:CMAKE_MAKE_PROGRAM
        CMAKE_LINKER = $env:CMAKE_LINKER
    }

    try {
        Invoke-Silent {
            git -C D:\dev\nasm-src clean -fdx
            git -C D:\dev\nasm-src reset --hard
            git -C D:\dev\nasm-src checkout $Hash
            git -C D:\dev\nasm-src clean -fdx
        }

        $gitDesc = git -C D:\dev\nasm-src describe --tags --long --dirty 2>$null
        if ($gitDesc) {
            [System.IO.File]::WriteAllText("D:\dev\nasm-src\version", ($gitDesc -replace '^nasm-', '') + "`n")
        }
        # Patch 2 — outcoff.c: FN_MAPPED_INFILE null guard
        # Required from commit 851460a10 onwards, never merged upstream

        Invoke-Silent { use-clang-win }
        Set-Location D:\dev\nasm-src
        Invoke-Silent { nmake-msvc /f Mkfiles\msvc.mak clean }

        $out = & {
            $oldOut = [Console]::Out
            $oldErr = [Console]::Error
            [Console]::SetOut([System.IO.TextWriter]::Null)
            [Console]::SetError([System.IO.TextWriter]::Null)
            try {
                nmake-msvc /f Mkfiles\msvc.mak `
                    CC="$clangRoot\bin\clang-cl.exe" `
                    AR="$clangRoot\bin\llvm-lib.exe" `
                    OPTFLAGS="/O2" `
                    LDFLAGS="/opt:ref /opt:icf" *>&1
            } finally {
                [Console]::SetOut($oldOut)
                [Console]::SetError($oldErr)
            }
        }

        if ($LASTEXITCODE -ne 0) {
            Write-Log "NASM ✗ $Hash $Date — $Msg" "Red"
            $out | Select-Object -Last 5 | ForEach-Object { Write-Log "    $_" "DarkRed" }
            Write-Log "    https://github.com/netwide-assembler/nasm/commit/$Hash" "Red"
            return $false
        }

        Copy-Item D:\dev\nasm-src\nasm.exe    D:\Programs\nasm\nasm.exe    -Force
        Copy-Item D:\dev\nasm-src\ndisasm.exe D:\Programs\nasm\ndisasm.exe -Force
        Write-Log "NASM ✓ $Hash $Date — $Msg" "Green"
        return $true

    } catch {
        Write-Log "NASM ✗ $Hash $Date — exception: $_" "Red"
        return $false
    } finally {
        $env:PATH = $saved.PATH; $env:CC = $saved.CC; $env:CXX = $saved.CXX
        $env:INCLUDE = $saved.INCLUDE; $env:LIB = $saved.LIB
        $env:CMAKE_C_COMPILER = $saved.CMAKE_C_COMPILER
        $env:CMAKE_CXX_COMPILER = $saved.CMAKE_CXX_COMPILER
        $env:CMAKE_GENERATOR = $saved.CMAKE_GENERATOR
        $env:CMAKE_MAKE_PROGRAM = $saved.CMAKE_MAKE_PROGRAM
        if ($saved.CMAKE_LINKER) { $env:CMAKE_LINKER = $saved.CMAKE_LINKER }
        else { Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue }
        Set-Location D:\
    }
}

# ─── Build + test OpenSSL ─────────────────────────────────────────────────────
# ─── Build OpenSSL (no test, no install_sw) ───────────────────────────────────
function Build-OpenSSL {
    param([string]$Hash, [string]$Date, [string]$Msg)

    $saved = @{
        PATH = $env:PATH; CC = $env:CC; CXX = $env:CXX
        INCLUDE = $env:INCLUDE; LIB = $env:LIB; CL = $env:CL
    }

    try {
        $env:PATH = "$perlRoot\perl\bin;$nasmRoot;$env:PATH"
        Invoke-Silent { use-clang-win }
        $env:CC  = "$clangRoot\bin\clang-cl.exe"
        $env:CXX = "$clangRoot\bin\clang-cl.exe"
        $env:LD  = "$clangRoot\bin\lld-link.exe"

        Set-Location "D:\Downloads\OpenSSL"
        Invoke-Silent {
            git -C "D:\Downloads\OpenSSL" clean -fdx
            git -C "D:\Downloads\OpenSSL" reset --hard
            nmake-msvc distclean
        }

        $cfgOut = & {
            $oldOut = [Console]::Out; $oldErr = [Console]::Error
            [Console]::SetOut([System.IO.TextWriter]::Null)
            [Console]::SetError([System.IO.TextWriter]::Null)
            try {
                perl Configure VC-WIN64A no-makedepend `
                    --prefix="D:\Programs\OpenSSL" `
                    --openssldir="D:\Programs\OpenSSL" *>&1
            } finally {
                [Console]::SetOut($oldOut); [Console]::SetError($oldErr)
            }
        }
        if ($LASTEXITCODE -ne 0) {
            Write-Log "OSSL ✗ NASM $Hash $Date — Configure failed" "Red"
            $cfgOut | Select-Object -Last 5 | ForEach-Object { Write-Log "    $_" "DarkRed" }
            Write-Log "    https://github.com/netwide-assembler/nasm/commit/$Hash" "Red"
            return $false
        }

        (Get-Content "D:\Downloads\OpenSSL\Makefile") `
            -replace '^AR="lib"', "AR=`"$clangRoot\bin\llvm-lib.exe`"" |
            Set-Content "D:\Downloads\OpenSSL\Makefile"

        $jobs = (Get-CimInstance Win32_ComputerSystem).NumberOfLogicalProcessors

        Write-Log "  → OpenSSL building... (this takes ~10 min)" "Gray"
        $buildOut = & "$jomRoot\jom.exe" /J $jobs *>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "OSSL ✗ NASM $Hash $Date — Build failed" "Red"
            $buildOut | Select-Object -Last 5 | ForEach-Object { Write-Log "    $_" "DarkRed" }
            Write-Log "    https://github.com/netwide-assembler/nasm/commit/$Hash" "Red"
            return $false
        }

        Write-Log "OSSL ✓ NASM $Hash $Date — $Msg" "Green"
        return $true

    } catch {
        Write-Log "OSSL ✗ NASM $Hash $Date — exception: $_" "Red"
        return $false
    } finally {
        $env:PATH = $saved.PATH; $env:CC = $saved.CC; $env:CXX = $saved.CXX
        $env:INCLUDE = $saved.INCLUDE; $env:LIB = $saved.LIB
        Remove-Item Env:\LD -ErrorAction SilentlyContinue
        if ($saved.CL) { $env:CL = $saved.CL }
        else { Remove-Item Env:\CL -ErrorAction SilentlyContinue }
        Set-Location D:\
    }
}
# ─── Main loop ────────────────────────────────────────────────────────────────
Write-Log "═══ Bisect start — $($commits.Count) commits ═══" "Cyan"

$i = 0
foreach ($c in $commits) {
    $i++
    Write-Log "[$i/$($commits.Count)] $($c.Hash) $($c.Date) — $($c.Msg)" "Yellow"

    if (-not (Build-Nasm -Hash $c.Hash -Date $c.Date -Msg $c.Msg)) { continue }
    if (-not (Build-OpenSSL -Hash $c.Hash -Date $c.Date -Msg $c.Msg)) { break }
}

Write-Log "═══ Bisect complete. Log: $logFile ═══" "Cyan"
