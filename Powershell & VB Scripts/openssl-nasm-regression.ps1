param(
    [switch]$Test
)

$nasmRepo = "D:\dev\nasm-src"
$openSslDir = "D:\Downloads\openssl"
$goodCommit = "9d94cac7aea790664096a95cb16e3c00c4ed9e3e" 

if ($Test) {
    # --- TEST ITERATION LOGIC ---
    Write-Host "`n--------------------------------------------------" -ForegroundColor Yellow
    Write-Host "Testing current commit: $(git -C $nasmRepo rev-parse --short HEAD)" -ForegroundColor Yellow
    Write-Host "Commit Message: $(git -C $nasmRepo log -1 --pretty=format:'%s')" -ForegroundColor Yellow
    Write-Host "--------------------------------------------------" -ForegroundColor Yellow

    # Thoroughly clean repositories
    git -C $nasmRepo reset --hard | Out-Null
    git -C $nasmRepo clean -fdx | Out-Null

    # Apply dynamic patch for nasm_remove() regression
    $fileC = "$nasmRepo\nasmlib\file.c"
    if (Test-Path $fileC) {
        $content = Get-Content $fileC -Raw
        $patched = $content -replace 'int nasm_remove\(const char \*pathname\)\s*\{[^}]*\}', 'int nasm_remove(const char *pathname) { return pathname ? remove(pathname) : 0; }'
        Set-Content $fileC -Value $patched -NoNewline
    }

    # Build NASM using a batch wrapper to properly initialize MSVC & Windows SDK environment
    Write-Host "==> Building NASM..." -ForegroundColor Cyan
    Set-Location $nasmRepo

    $buildScript = @"
@echo off
set "VSCMD_START_DIR=%CD%"
call "D:\dev\msvc\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 >nul 2>&1
)
nmake /f Mkfiles/msvc.mak clean >nul 2>&1
nmake /f Mkfiles/msvc.mak
exit /b %ERRORLEVEL%
"@

    $scriptPath = "$nasmRepo\build_nasm.bat"
    Set-Content -Path $scriptPath -Value $buildScript -Encoding ASCII
    & C:\Windows\System32\cmd.exe /c $scriptPath
    $nasmExitCode = $LASTEXITCODE
    Remove-Item $scriptPath -ErrorAction SilentlyContinue

    if ($nasmExitCode -ne 0) {
        Write-Host "-> NASM compilation failed. Skipping commit." -ForegroundColor Red
        exit 125 
    }

    # Build OpenSSL
    Write-Host "==> Building OpenSSL..." -ForegroundColor Cyan
    Set-Location $openSslDir
    git -C $openSslDir reset --hard | Out-Null
    git -C $openSslDir clean -fdx | Out-Null

    $sslScript = @"
@echo off
call "D:\dev\msvc\VC\Auxiliary\Build\vcvars64.bat" >nul 2>&1
if errorlevel 1 (
    call "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\Tools\VsDevCmd.bat" -arch=x64 >nul 2>&1
)
jom clean >nul 2>&1
jom
exit /b %ERRORLEVEL%
"@

    $sslScriptPath = "$openSslDir\build_ssl.bat"
    Set-Content -Path $sslScriptPath -Value $sslScript -Encoding ASCII
    & C:\Windows\System32\cmd.exe /c $sslScriptPath
    $sslExitCode = $LASTEXITCODE
    Remove-Item $sslScriptPath -ErrorAction SilentlyContinue

    if ($sslExitCode -eq 0) {
        Write-Host "-> Build SUCCESSFUL (OpenSSL linked cleanly)." -ForegroundColor Green
        exit 0 
    } else {
        Write-Host "-> Build FAILED (Linker errors encountered)." -ForegroundColor Red
        exit 1 
    }
} else {
    # --- INITIALIZATION BLOCK ---
    Write-Host "==> Initializing Git Bisect for Post-9d94cac7a Commits..." -ForegroundColor Cyan
    git -C $nasmRepo bisect reset
    git -C $nasmRepo bisect start
    git -C $nasmRepo bisect bad HEAD
    git -C $nasmRepo bisect good $goodCommit

    Write-Host "==> Starting Bisect Run..." -ForegroundColor Cyan
    git -C $nasmRepo bisect run pwsh -File "$PSCommandPath" -Test
}
