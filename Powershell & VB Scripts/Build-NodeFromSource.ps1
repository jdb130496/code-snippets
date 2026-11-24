[CmdletBinding()]
param(
    [string]$SourceRoot = 'D:\dev\node-src',
    [string]$InstallRoot = 'D:\Programs\nodejs',
    [ValidateRange(1, 16)]
    [int]$Jobs = 4,
    [switch]$SkipInstall
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$pathDefaults = [ordered]@{
    clangRoot  = 'D:\Programs\clang'
    cmakeRoot  = 'D:\Programs\cmake'
    ninjaRoot  = 'D:\Programs\ninja'
    pythonRoot = 'D:\Programs\Python'
    cargoRoot  = 'D:\Programs\cargo'
    rustRoot   = 'D:\Programs\rustup'
    opensslRoot = 'D:\Programs\OpenSSL'
    zlibRoot   = 'D:\Programs\zlib'
    zstdRoot   = 'D:\Programs\zstd'
    sqliteRoot = 'D:\Programs\sqlite'
    nasmRoot   = 'D:\Programs\nasm'
}
$profilePaths = @{}
foreach ($name in $pathDefaults.Keys) {
    $value = Get-Variable -Name $name -Scope 1 -ValueOnly -ErrorAction SilentlyContinue
    if ($value) {
        $profilePaths[$name] = [string]$value
    }
}
foreach ($name in $pathDefaults.Keys) {
    if (-not $profilePaths.ContainsKey($name)) {
        $profilePaths[$name] = $pathDefaults[$name]
    }
}

$clangRoot = $profilePaths['clangRoot']
$cmakeRoot = $profilePaths['cmakeRoot']
$ninjaRoot = $profilePaths['ninjaRoot']
$pythonRoot = $profilePaths['pythonRoot']
$cargoHome = $profilePaths['cargoRoot']
$rustupHome = $profilePaths['rustRoot']
$opensslRoot = $profilePaths['opensslRoot']
$zlibRoot = $profilePaths['zlibRoot']
$zstdRoot = $profilePaths['zstdRoot']
$sqliteRoot = $profilePaths['sqliteRoot']
$nasmRoot = $profilePaths['nasmRoot']

if (-not $PSBoundParameters.ContainsKey('InstallRoot')) {
    $profileInstallRoot = Get-Variable -Name 'nodejsRoot' -Scope 1 -ValueOnly -ErrorAction SilentlyContinue
    if ($profileInstallRoot) {
        $InstallRoot = [string]$profileInstallRoot
    }
}

$cmakeExe = Join-Path $cmakeRoot 'bin\cmake.exe'
$ninjaExe = Join-Path $ninjaRoot 'bin\ninja.exe'
$pythonExe = Join-Path $pythonRoot 'python.exe'
$nasmExe = Join-Path $nasmRoot 'nasm.exe'
$backupRoot = $null
$stageRoot = $null
$promoted = $false
$oldMoved = $false

$SourceRoot = [IO.Path]::GetFullPath($SourceRoot)
$InstallRoot = [IO.Path]::GetFullPath($InstallRoot)
$buildRoot = Join-Path $SourceRoot 'out\Release'
$sharedRoot = Join-Path $SourceRoot 'out\shared-deps'
$uvBuild = Join-Path $sharedRoot 'uv-build'
$caresBuild = Join-Path $sharedRoot 'cares-build'
$caresInstall = Join-Path $sharedRoot 'cares'
$clangCl = Join-Path $clangRoot 'bin\clang-cl.exe'
$lldLink = Join-Path $clangRoot 'bin\lld-link.exe'
$llvmReadObj = Join-Path $clangRoot 'bin\llvm-readobj.exe'
$nodeExe = Join-Path $buildRoot 'node.exe'
$configPath = Join-Path $SourceRoot 'config.gypi'

function Assert-Path {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Required path not found: $Path"
    }
}

function Invoke-Native {
    param(
        [string]$FilePath,
        [string[]]$Arguments,
        [string]$WorkingDirectory
    )

    Write-Host "`n> $FilePath $($Arguments -join ' ')" -ForegroundColor Cyan
    Push-Location $WorkingDirectory
    try {
        & $FilePath @Arguments
        $exitCode = $LASTEXITCODE
    }
    finally {
        Pop-Location
    }
    if ($exitCode -ne 0) {
        throw "Command failed with exit code ${exitCode}: $FilePath"
    }
}

function Write-TextIfChanged {
    param([string]$Path, [string]$Text)
    $current = [IO.File]::ReadAllText($Path)
    if ($current -cne $Text) {
        [IO.File]::WriteAllText($Path, $Text, [Text.UTF8Encoding]::new($false))
    }
}

function Set-NinjaVariable {
    param([string]$Path, [string]$Name, [string]$Value)
    $text = [IO.File]::ReadAllText($Path)
    $pattern = '(?m)^' + [regex]::Escape($Name) + '\s*=.*$'
    $matches = [regex]::Matches($text, $pattern)
    if ($matches.Count -ne 1) {
        throw "Expected one '$Name' assignment in $Path; found $($matches.Count)."
    }
    $updated = [regex]::Replace(
        $text,
        $pattern,
        [System.Text.RegularExpressions.MatchEvaluator]{
            param($match)
            "$Name = $Value"
        },
        1
    )
    Write-TextIfChanged $Path $updated
}

function Replace-NinjaText {
    param([string]$Path, [string]$Old, [string]$New)
    $text = [IO.File]::ReadAllText($Path)
    $count = 0
    $start = 0
    while (($index = $text.IndexOf($Old, $start, [StringComparison]::Ordinal)) -ge 0) {
        $count++
        $start = $index + $Old.Length
    }
    if ($count -eq 0) {
        if ($text.Contains($New)) {
            return
        }
        throw "Expected generated text was not found in ${Path}:`n$Old"
    }
    $updated = $text.Replace($Old, $New)
    Write-TextIfChanged $Path $updated
}

function Set-EnvironmentBlockValue {
    param([string]$Path, [string]$Name, [string]$Value)
    $text = [Text.Encoding]::ASCII.GetString([IO.File]::ReadAllBytes($Path))
    if ($text.Length -lt 2 -or $text[$text.Length - 1] -ne [char]0 -or
        $text[$text.Length - 2] -ne [char]0) {
        throw "The generated Windows environment block is missing its double-NUL terminator: $Path"
    }

    $entries = [Collections.Generic.List[string]]::new()
    foreach ($entry in $text.Substring(0, $text.Length - 2).Split([char]0)) {
        if ($entry -notmatch ('(?i)^' + [regex]::Escape($Name) + '=')) {
            $entries.Add($entry)
        }
    }
    $entries.Add("$Name=$Value")
    $updated = ($entries -join [char]0) + [char]0 + [char]0
    [IO.File]::WriteAllBytes($Path, [Text.Encoding]::ASCII.GetBytes($updated))
}

function Patch-GeneratedBuildFiles {
    param([string]$Root)

    $ninjaFiles = @(Get-ChildItem -LiteralPath $Root -Filter '*.ninja' -File -Recurse)
    foreach ($file in $ninjaFiles) {
        $text = [IO.File]::ReadAllText($file.FullName)
        $updated = $text.Replace('$(Platform)', 'x64')
        $updated = $updated.Replace(
            '/Yutools/msvs/pch/node_pch.h',
            '/Yu../../tools/msvs/pch/node_pch.h'
        )
        $updated = $updated.Replace(
            '/FItools/msvs/pch/node_pch.h',
            '/FI../../tools/msvs/pch/node_pch.h'
        )
        $updated = $updated.Replace(
            '/Yctools/msvs/pch/node_pch.h',
            '/Yc../../tools/msvs/pch/node_pch.h'
        )
        $updated = [regex]::Replace(
            $updated,
            '(?i)\buserenv\.lib(?!\s+Synchronization\.lib)',
            'userenv.lib Synchronization.lib crypt32.lib'
        )
        $updated = [regex]::Replace(
            $updated,
            '(?i)\buserenv\.lib\s+Synchronization\.lib(?!\s+crypt32\.lib)',
            'userenv.lib Synchronization.lib crypt32.lib'
        )
        $updated = $updated.Replace(
            '/WHOLEARCHIVE:lib/node_base.lib',
            '/WHOLEARCHIVE:obj/node_base.lib'
        )
        $updated = $updated.Replace(
            '/WHOLEARCHIVE:lib/v8_base_without_compiler.lib',
            '/WHOLEARCHIVE:obj/tools/v8_gypfiles/v8_base_without_compiler.lib'
        )
        Write-TextIfChanged $file.FullName $updated
    }

    $rootNinja = Join-Path $Root 'build.ninja'
    Set-NinjaVariable $rootNinja 'cl_x64' $clangCl
    Set-NinjaVariable $rootNinja 'cc' $clangCl
    Set-NinjaVariable $rootNinja 'cxx' $clangCl
    Set-NinjaVariable $rootNinja 'ld' $lldLink
    Set-NinjaVariable $rootNinja 'ar' (Join-Path $clangRoot 'bin\llvm-lib.exe')

    $text = [IO.File]::ReadAllText($rootNinja)
    $text = [regex]::Replace(
        $text,
        '(?m)^(\s*command = ninja -t msvc -e \$arch -- \$cxx /nologo)(?! /std:c\+\+20)',
        '$1 /std:c++20'
    )
    $text = [regex]::Replace(
        $text,
        '(?m)^rule asm_clang\r?\n(?:[ \t].*(?:\r?\n|$))+',
        ''
    )
    $marker = '  description = ASM $out'
    if ([regex]::Matches($text, '(?m)^  description = ASM \$out\r?$').Count -ne 1) {
        throw "Could not locate exactly one generated ASM rule in $rootNinja"
    }
    $asmRule = @"
rule asm_clang
  command = "$pythonExe" gyp-win-tool asm-wrapper `$arch "$clangCl" `$defines `$includes `$asmflags /nologo /c /Fo`$out `$in
  description = ASM `$out
"@
    $text = $text.Replace($marker, "$marker`r`n$asmRule".TrimEnd())
    Write-TextIfChanged $rootNinja $text

    $baseNinja = Join-Path $Root 'obj\node_base.ninja'
    $baseText = [IO.File]::ReadAllText($baseNinja)
    $js2cPattern = '(?s)(rspfile_content = out\\Release\\node_js2c\.exe .*?)(?=\r?\n\r?\nbuild gen\\node_javascript\.cc)'
    $js2cMatch = [regex]::Match($baseText, $js2cPattern)
    if (-not $js2cMatch.Success) {
        throw "Could not find the generated JS2C response-file rule in $baseNinja"
    }
    $js2cBlock = [regex]::Replace(
        $js2cMatch.Groups[1].Value,
        '"deps\\([^"]+)"',
        [System.Text.RegularExpressions.MatchEvaluator]{
            param($match)
            '"deps/' + $match.Groups[1].Value.Replace('\', '/') + '"'
        }
    )
    $baseText = $baseText.Substring(0, $js2cMatch.Index) + $js2cBlock +
        $baseText.Substring($js2cMatch.Index + $js2cMatch.Length)
    $protocolPath = ($SourceRoot -replace '\\', '/') + '/deps/v8/include/js_protocol.pdl'
    $baseText = $baseText.Replace(
        '"deps\v8\include\js_protocol.pdl"',
        '"' + $protocolPath + '"'
    )
    Write-TextIfChanged $baseNinja $baseText

    $inspectorNinja = Join-Path $Root 'obj\tools\v8_gypfiles\v8_inspector_headers.ninja'
    $inspectorText = [IO.File]::ReadAllText($inspectorNinja)
    $configValuePattern = '"--config_value"\s+"[^"]*js_protocol\.pdl"'
    $configMatches = [regex]::Matches($inspectorText, $configValuePattern)
    if ($configMatches.Count -ne 1) {
        throw "Expected one inspector --config_value protocol argument in $inspectorNinja; found $($configMatches.Count)."
    }
    $inspectorText = [regex]::Replace(
        $inspectorText,
        $configValuePattern,
        '"--config_value" "protocol.path=' + $protocolPath + '"'
    )
    Write-TextIfChanged $inspectorNinja $inspectorText

    $snapshotNinja = Join-Path $Root 'obj\tools\v8_gypfiles\v8_snapshot.ninja'
    Replace-NinjaText $snapshotNinja `
        "    asm obj\tools\v8_gypfiles\v8_snapshot.gen\embedded.S || $" `
        "    asm_clang obj\tools\v8_gypfiles\v8_snapshot.gen\embedded.S || $"

    $environmentFile = Join-Path $Root 'environment.x64'
    Set-EnvironmentBlockValue $environmentFile 'CARGO_HOME' $cargoHome
    Set-EnvironmentBlockValue $environmentFile 'RUSTUP_HOME' $rustupHome
    Set-EnvironmentBlockValue $environmentFile 'RUSTUP_TOOLCHAIN' 'nightly-x86_64-pc-windows-msvc'
    Set-EnvironmentBlockValue $environmentFile 'CC' ($clangCl.Replace([char]92, [char]47))
    Set-EnvironmentBlockValue $environmentFile 'CXX' ($clangCl.Replace([char]92, [char]47))
}

function Copy-Directory {
    param(
        [string]$Source,
        [string]$Destination,
        [string[]]$ExcludeDirectories = @()
    )
    if (-not (Test-Path -LiteralPath $Source)) {
        return
    }
    New-Item -ItemType Directory -Force -Path $Destination | Out-Null
    $arguments = @(
        $Source, $Destination, '/E', '/COPY:DAT', '/DCOPY:DAT', '/XJ',
        '/R:1', '/W:1', '/NFL', '/NDL', '/NJH', '/NJS', '/NC', '/NS'
    )
    if ($ExcludeDirectories.Count -gt 0) {
        $arguments += '/XD'
        $arguments += $ExcludeDirectories
    }
    & robocopy @arguments
    if ($LASTEXITCODE -ge 8) {
        throw "robocopy failed with exit code $LASTEXITCODE copying $Source"
    }
}

function Test-NodeExecutable {
    param([string]$NodePath, [string]$WorkingDirectory)
    Invoke-Native $NodePath @('--version') $WorkingDirectory
    $smokeTest = 'const c=require("node:crypto"),z=require("node:zlib"),s=require("node:sqlite");const b=Buffer.from("node-build-ok");if(z.gunzipSync(z.gzipSync(b)).toString()!==b.toString())throw Error("zlib");const d=new s.DatabaseSync(":memory:");d.exec("CREATE TABLE t(v);INSERT INTO t VALUES(42)");if(d.prepare("SELECT v FROM t").get().v!==42)throw Error("sqlite");c.createHash("sha256").update(b).digest("hex");console.log(JSON.stringify({openssl:process.versions.openssl,zlib:process.versions.zlib,sqlite:process.versions.sqlite,crypto:true}));'
    Invoke-Native $NodePath @('-e', $smokeTest) $WorkingDirectory
}

Assert-Path $SourceRoot
Assert-Path (Join-Path $SourceRoot '.git')
Assert-Path (Join-Path $SourceRoot 'configure.py')

$gitCommand = Get-Command git -CommandType Application -ErrorAction Stop |
    Select-Object -First 1
$trackedChanges = & $gitCommand.Source -C $SourceRoot status --porcelain --untracked-files=no
if ($LASTEXITCODE -ne 0) {
    throw "Could not check Git status for $SourceRoot."
}
if ($trackedChanges) {
    throw "Refusing to pull because $SourceRoot has tracked local changes. Commit or stash them, then rerun."
}
Invoke-Native $gitCommand.Source @(
    '-C', $SourceRoot, 'pull', '--ff-only', 'origin', 'main'
) $SourceRoot

Assert-Path $InstallRoot
Assert-Path $clangCl
Assert-Path $lldLink
Assert-Path $llvmReadObj
Assert-Path $cmakeExe
Assert-Path $ninjaExe
Assert-Path $pythonExe
Assert-Path $cargoHome
Assert-Path $rustupHome
Assert-Path $opensslRoot
Assert-Path $zlibRoot
Assert-Path $zstdRoot
Assert-Path $sqliteRoot
Assert-Path $nasmExe

$sqliteHeader = Get-ChildItem -LiteralPath $sqliteRoot -Filter 'sqlite3.h' -File -Recurse |
    Select-Object -First 1
if (-not $sqliteHeader) {
    throw "Could not find sqlite3.h below $sqliteRoot"
}

$requiredFiles = @(
    (Join-Path $opensslRoot 'lib\libssl.lib'),
    (Join-Path $opensslRoot 'lib\libcrypto.lib'),
    (Join-Path $opensslRoot 'bin\libssl-4-x64.dll'),
    (Join-Path $opensslRoot 'bin\libcrypto-4-x64.dll'),
    (Join-Path $zlibRoot 'include\zlib.h'),
    (Join-Path $zlibRoot 'lib\z.lib'),
    (Join-Path $zlibRoot 'bin\z.dll'),
    (Join-Path $zstdRoot 'include\zstd.h'),
    (Join-Path $zstdRoot 'lib\zstd.lib'),
    (Join-Path $zstdRoot 'bin\zstd.dll'),
    (Join-Path $sqliteRoot 'sqlite3.lib'),
    (Join-Path $sqliteRoot 'sqlite3.dll')
)
foreach ($path in $requiredFiles) { Assert-Path $path }

$toolchain = Get-Command use-clang-win -ErrorAction SilentlyContinue
if (-not $toolchain) {
    throw 'Run this script from your PowerShell profile terminal, where use-clang-win is defined.'
}
use-clang-win

$env:CARGO_HOME = $cargoHome
$env:RUSTUP_HOME = $rustupHome
$env:RUSTUP_TOOLCHAIN = 'nightly-x86_64-pc-windows-msvc'
$env:PATH = @(
    (Join-Path $clangRoot 'bin'),
(Join-Path $ninjaRoot 'bin'),
(Split-Path -Parent $nasmExe),
    (Join-Path $cargoHome 'bin'),
    (Join-Path $rustupHome 'bin'),
    (Join-Path $opensslRoot 'bin'),
    (Join-Path $zlibRoot 'bin'),
    (Join-Path $zstdRoot 'bin'),
    $sqliteRoot,
    $env:PATH
) -join ';'
$env:CMAKE_GENERATOR = 'Ninja'
$env:CMAKE_MAKE_PROGRAM = $ninjaExe
$env:CMAKE_C_COMPILER = $clangCl
$env:CMAKE_CXX_COMPILER = $clangCl
$env:CMAKE_LINKER = $lldLink
$env:CC = $clangCl
$env:CXX = $clangCl
$env:DISTUTILS_USE_SDK = '1'
$env:MSSdk = '1'

Invoke-Native $cargoHome\bin\cargo.exe @('+nightly', '--version') $SourceRoot
Invoke-Native $nasmExe @('-version') $SourceRoot

Write-Host "`nBuilding shared libuv and c-ares..." -ForegroundColor Green
Invoke-Native $cmakeExe @(
    '-S', (Join-Path $SourceRoot 'deps\uv'),
    '-B', $uvBuild,
    '-G', 'Ninja',
    "-DCMAKE_C_COMPILER=$clangCl",
    '-DCMAKE_BUILD_TYPE=Release',
    '-DLIBUV_BUILD_SHARED=ON',
    '-DLIBUV_BUILD_TESTS=OFF'
) $SourceRoot
Invoke-Native $cmakeExe @('--build', $uvBuild, '--target', 'uv', '--parallel', "$Jobs") $SourceRoot

Invoke-Native $cmakeExe @(
    '-S', (Join-Path $SourceRoot 'deps\cares'),
    '-B', $caresBuild,
    '-G', 'Ninja',
    "-DCMAKE_C_COMPILER=$clangCl",
    '-DCMAKE_BUILD_TYPE=Release',
    "-DCMAKE_INSTALL_PREFIX=$caresInstall",
    '-DCARES_BUILD_TESTS=OFF',
    '-DCARES_BUILD_TOOLS=OFF',
    '-DCARES_INSTALL=ON',
    '-DCARES_SHARED=ON',
    '-DCARES_STATIC=OFF'
) $SourceRoot
Invoke-Native $cmakeExe @('--build', $caresBuild, '--target', 'install', '--parallel', "$Jobs") $SourceRoot

$uvDll = Join-Path $uvBuild 'uv.dll'
$uvImportLib = Join-Path $uvBuild 'uv.lib'
$caresDll = Join-Path $caresInstall 'bin\cares.dll'
$caresImportLib = Join-Path $caresInstall 'lib\cares.lib'
foreach ($path in @($uvDll, $uvImportLib, $caresDll, $caresImportLib)) { Assert-Path $path }

$configureArgs = @(
    'configure.py',
    '--ninja',
    '--dest-cpu=x64',
    '--clang-cl=23.1.6',
    '--download=all',
    '--shared-openssl',
    "--shared-openssl-includes=$opensslRoot\include",
    "--shared-openssl-libpath=$opensslRoot\lib",
    '--shared-openssl-libname=libssl,libcrypto',
    '--shared-zlib',
    "--shared-zlib-includes=$zlibRoot\include",
    "--shared-zlib-libpath=$zlibRoot\lib",
    '--shared-zlib-libname=z',
    '--shared-zstd',
    "--shared-zstd-includes=$zstdRoot\include",
    "--shared-zstd-libpath=$zstdRoot\lib",
    '--shared-zstd-libname=zstd',
    '--shared-sqlite',
    "--shared-sqlite-includes=$($sqliteHeader.DirectoryName)",
    "--shared-sqlite-libpath=$sqliteRoot",
    '--shared-sqlite-libname=sqlite3',
    '--shared-libuv',
    "--shared-libuv-includes=$SourceRoot\deps\uv\include",
    "--shared-libuv-libpath=$uvBuild",
    '--shared-libuv-libname=uv',
    '--shared-cares',
    "--shared-cares-includes=$caresInstall\include",
    "--shared-cares-libpath=$caresInstall\lib",
    '--shared-cares-libname=cares'
)
$clangClForConfigure = $clangCl.Replace([char]92, [char]47) + ' --driver-mode=g++'
$env:CC = $clangClForConfigure
$env:CXX = $clangClForConfigure
Invoke-Native $pythonExe $configureArgs $SourceRoot

Assert-Path $configPath
$configText = [IO.File]::ReadAllText($configPath)
foreach ($flag in @(
    'node_shared_openssl',
    'node_shared_zlib',
    'node_shared_zstd',
    'node_shared_sqlite',
    'node_shared_libuv',
    'node_shared_cares',
    'node_install_npm'
)) {
    if ($configText -notmatch ('(?m)^\s*"' + [regex]::Escape($flag) + '"\s*:\s*"true"')) {
        throw "Node configuration did not enable $flag."
    }
}
if ($configText -match '"openssl_no_asm"\s*:\s*"true"' -or
    $configText -notmatch '"nasm_version"\s*:\s*"[^"]+"') {
    throw 'Node configuration does not indicate an assembly-enabled OpenSSL build.'
}
$opensslVersion = [regex]::Match($configText, '"openssl_version"\s*:\s*(\d+)')
if (-not $opensslVersion.Success -or $opensslVersion.Groups[1].Value -eq '0') {
    throw 'Node configure could not read the OpenSSL headers. Verify the clang-cl GNU-mode probe and OpenSSL include directory.'
}
$env:CC = $clangCl
$env:CXX = $clangCl

Write-Host "`nPatching generated Ninja rules and Windows environment..." -ForegroundColor Green
Patch-GeneratedBuildFiles $buildRoot

Write-Host "`nBuilding Node with $Jobs Ninja workers. Existing objects are retained." -ForegroundColor Green
Invoke-Native $ninjaExe @('-C', $buildRoot, '-j', "$Jobs", 'node') $SourceRoot
Assert-Path $nodeExe

if ($SkipInstall) {
    Write-Host "`nBuild completed. Installation was skipped." -ForegroundColor Green
    return
}

$runtimeFiles = @(
    @{ Source = $opensslRoot + '\bin\libssl-4-x64.dll'; Name = 'libssl-4-x64.dll' },
    @{ Source = $opensslRoot + '\bin\libcrypto-4-x64.dll'; Name = 'libcrypto-4-x64.dll' },
    @{ Source = $zlibRoot + '\bin\z.dll'; Name = 'z.dll' },
    @{ Source = $zstdRoot + '\bin\zstd.dll'; Name = 'zstd.dll' },
    @{ Source = $sqliteRoot + '\sqlite3.dll'; Name = 'sqlite3.dll' },
    @{ Source = $uvDll; Name = 'uv.dll' },
    @{ Source = $caresDll; Name = 'cares.dll' }
)

$stageName = 'nodejs-stage-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
$stageRoot = Join-Path (Split-Path -Parent $InstallRoot) $stageName
New-Item -ItemType Directory -Path $stageRoot | Out-Null
Copy-Item -LiteralPath $nodeExe -Destination (Join-Path $stageRoot 'node.exe')
foreach ($manifest in @('node.exe.manifest', 'node.exe.assert.manifest')) {
    $manifestPath = Join-Path $buildRoot $manifest
    if (Test-Path -LiteralPath $manifestPath) {
        Copy-Item -LiteralPath $manifestPath -Destination (Join-Path $stageRoot $manifest)
    }
}
foreach ($runtime in $runtimeFiles) {
    Assert-Path $runtime.Source
    Copy-Item -LiteralPath $runtime.Source -Destination (Join-Path $stageRoot $runtime.Name)
}
foreach ($document in @('LICENSE', 'README.md', 'CHANGELOG.md')) {
    $documentPath = Join-Path $SourceRoot $document
    if (Test-Path -LiteralPath $documentPath) {
        Copy-Item -LiteralPath $documentPath -Destination (Join-Path $stageRoot $document)
    }
}
foreach ($extra in @('nodevars.bat', 'install_tools.bat')) {
    $extraPath = Join-Path $InstallRoot $extra
    if (Test-Path -LiteralPath $extraPath) {
        Copy-Item -LiteralPath $extraPath -Destination (Join-Path $stageRoot $extra)
    }
}

$stageNodeModules = Join-Path $stageRoot 'node_modules'
$npmSource = Join-Path $SourceRoot 'deps\npm'
$npmStage = Join-Path $stageNodeModules 'npm'
Assert-Path $npmSource
New-Item -ItemType Directory -Force -Path $stageNodeModules | Out-Null
if (Test-Path -LiteralPath (Join-Path $InstallRoot 'node_modules')) {
    Copy-Directory (Join-Path $InstallRoot 'node_modules') $stageNodeModules @(
        (Join-Path $InstallRoot 'node_modules\npm')
    )
}
Copy-Directory $npmSource $npmStage
foreach ($shim in @('npm', 'npm.cmd', 'npm.ps1', 'npx', 'npx.cmd', 'npx.ps1')) {
    Copy-Item -LiteralPath (Join-Path $npmSource "bin\$shim") -Destination (Join-Path $stageRoot $shim)
}

$savedPath = $env:PATH
try {
    $env:PATH = "$stageRoot;C:\Windows\System32;C:\Windows"
    Test-NodeExecutable (Join-Path $stageRoot 'node.exe') $stageRoot
    Invoke-Native (Join-Path $stageRoot 'npm.cmd') @('--version') $stageRoot
    Invoke-Native (Join-Path $stageRoot 'npx.cmd') @('--version') $stageRoot
    if (Test-Path -LiteralPath (Join-Path $stageNodeModules 'pdf-lib')) {
        $pdfTest = 'if(!require("pdf-lib").PDFDocument)process.exit(1);console.log("pdf-lib OK");'
        Invoke-Native (Join-Path $stageRoot 'node.exe') @('-e', $pdfTest) $stageRoot
    }
}
finally {
    $env:PATH = $savedPath
}

$imports = (& $llvmReadObj '--coff-imports' $nodeExe) -join "`n"
foreach ($runtime in $runtimeFiles) {
    if ($imports -notmatch ('(?im)^\s*Name:\s*' + [regex]::Escape($runtime.Name) + '\s*$')) {
        throw "node.exe does not import the expected shared library $($runtime.Name)."
    }
}

$runningInstalledNode = Get-CimInstance Win32_Process -Filter "Name='node.exe'" |
    Where-Object {
        $_.ExecutablePath -and
        $_.ExecutablePath.StartsWith($InstallRoot + '\', [StringComparison]::OrdinalIgnoreCase)
    }
if ($runningInstalledNode) {
    throw "A node.exe process is running from $InstallRoot. Stop it and rerun before replacing the installation."
}

$backupName = 'nodejs-backup-' + (Get-Date -Format 'yyyyMMdd-HHmmss')
$backupRoot = Join-Path (Split-Path -Parent $InstallRoot) $backupName
if (Test-Path -LiteralPath $backupRoot) {
    $backupRoot += '-' + [guid]::NewGuid().ToString('N').Substring(0, 8)
}

try {
    Move-Item -LiteralPath $InstallRoot -Destination $backupRoot
    $oldMoved = $true
    Move-Item -LiteralPath $stageRoot -Destination $InstallRoot
    $promoted = $true

    $savedPath = $env:PATH
    try {
        $env:PATH = "$InstallRoot;C:\Windows\System32;C:\Windows"
        Test-NodeExecutable (Join-Path $InstallRoot 'node.exe') $InstallRoot
        Invoke-Native (Join-Path $InstallRoot 'npm.cmd') @('--version') $InstallRoot
        Invoke-Native (Join-Path $InstallRoot 'npx.cmd') @('--version') $InstallRoot
    }
    finally {
        $env:PATH = $savedPath
    }

    Write-Host "`nInstalled Node and shared DLLs at $InstallRoot" -ForegroundColor Green
    Write-Host "Previous installation preserved at $backupRoot" -ForegroundColor Green
}
catch {
    if ($promoted -and (Test-Path -LiteralPath $InstallRoot)) {
        Move-Item -LiteralPath $InstallRoot -Destination $stageRoot
        $promoted = $false
    }
    if ($oldMoved -and (Test-Path -LiteralPath $backupRoot)) {
        Move-Item -LiteralPath $backupRoot -Destination $InstallRoot
        $oldMoved = $false
    }
    throw
}
finally {
    if ($stageRoot -and (Test-Path -LiteralPath $stageRoot)) {
        Remove-Item -LiteralPath $stageRoot -Recurse -Force
    }
}
