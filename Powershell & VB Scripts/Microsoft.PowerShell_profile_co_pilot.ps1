$MaximumHistoryCount=10000

# Base paths
$msvcRoot="D:\dev\msvc"
$clangRoot="D:\Programs\clang"
$cmakeRoot="D:\Programs\cmake"
$msys64Root="D:\Programs\msys64"
$nodejsRoot="D:\Programs\nodejs"

# Python 3.14 auto-detect
$pythonRoot=$null
$possiblePaths=@(
  "D:\Programs\Python314",
  "D:\Programs\Python\Python314",
  "C:\Program Files\Python314",
  "$env:LOCALAPPDATA\Programs\Python\Python314"
)
foreach($p in $possiblePaths){
  if(Test-Path "$p\python.exe"){
    $v=& "$p\python.exe" --version 2>&1
    if($v -match '3\.14'){$pythonRoot=$p;break}
  }
}
if(-not $pythonRoot){
  try{
    $pyPath=& py -3.14 -c "import sys; print(sys.executable)" 2>$null
    if($pyPath -and (Test-Path $pyPath)){$pythonRoot=Split-Path -Parent $pyPath}
  }catch{Write-Warning "Python 3.14 not found. Python paths will be skipped."}
}

$vcToolsVersion="14.50.35717"
$windowsSDKVersion="10.0.26100.0"
$hostArch="x64"
$targetArch="x64"

# MSVC env
$env:VSCMD_ARG_HOST_ARCH=$hostArch
$env:VSCMD_ARG_TGT_ARCH=$targetArch
$env:VCToolsVersion=$vcToolsVersion
$env:WindowsSDKVersion="$windowsSDKVersion\"
$env:VCToolsInstallDir="$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
$env:WindowsSdkBinPath="$msvcRoot\Windows Kits\10\bin\"
$env:WindowsSDKDir="$msvcRoot\Windows Kits\10"
$env:DISTUTILS_USE_SDK="1"
$env:MSSdk="1"

# INCLUDE
$includePaths=@(
  "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include",
  "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\ucrt",
  "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\shared",
  "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\um",
  "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\winrt",
  "$msvcRoot\Windows Kits\10\Include\$windowsSDKVersion\cppwinrt",
  "$clangRoot\include",
  "$msys64Root\ucrt64\include"
)
$env:INCLUDE=$includePaths -join ";"

# LIB
$libPaths=@(
  "$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\lib\$targetArch",
  "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\ucrt\$targetArch",
  "$msvcRoot\Windows Kits\10\Lib\$windowsSDKVersion\um\$targetArch",
  "$clangRoot\lib",
  "$msys64Root\ucrt64\lib"
)
$env:LIB=$libPaths -join ";"

# PATH priority
$nodejsPaths=@()
if(Test-Path "$nodejsRoot\node.exe"){$nodejsPaths=@("$nodejsRoot")}
$pythonPaths=@()
if($pythonRoot){$pythonPaths=@("$pythonRoot","$pythonRoot\Scripts")}
$cmakePaths=@()
if(Test-Path "$cmakeRoot\bin\cmake.exe"){$cmakePaths=@("$cmakeRoot\bin")}

$msvcBinPath="$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\bin\Host$hostArch\$targetArch"
$compilerPaths=@(
  "$clangRoot\bin",
  "$msvcBinPath",
  "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch",
  "$msvcRoot\Windows Kits\10\bin\$windowsSDKVersion\$targetArch\ucrt"
)
$msys2Paths=@(
  "$msys64Root\ucrt64\bin",
  "$msys64Root\usr\bin"
)

$pathsToClean=$nodejsPaths+$pythonPaths+$cmakePaths+$compilerPaths+$msys2Paths
$currentPathArray=$env:PATH -split ';'
$cleanedPath=$currentPathArray|Where-Object{
  $x=$_;-not($pathsToClean|Where-Object{$x -eq $_})
}
$env:PATH=$cleanedPath -join ';'

foreach($p in $nodejsPaths){if(Test-Path $p){$env:PATH="$p;$env:PATH"}}
foreach($p in $pythonPaths){if(Test-Path $p){$env:PATH="$p;$env:PATH"}}
foreach($p in $cmakePaths){if(Test-Path $p){$env:PATH="$p;$env:PATH"}}
foreach($p in $compilerPaths){if(Test-Path $p){$env:PATH="$env:PATH;$p"}}
foreach($p in $msys2Paths){if(Test-Path $p){$env:PATH="$env:PATH;$p"}}

# Detect Windows Ninja
$windowsNinja=$null
$ninjaPossiblePaths=@("$cmakeRoot\bin\ninja.exe","$clangRoot\bin\ninja.exe")
foreach($n in $ninjaPossiblePaths){if(Test-Path $n){$windowsNinja=$n;break}}

# CMake generator for Cargo
$env:CMAKE_GENERATOR="Ninja"
if($windowsNinja){
  $env:CMAKE_MAKE_PROGRAM=$windowsNinja
}else{
  Write-Warning "Windows Ninja not found! Cargo builds will use NMake instead."
  Write-Warning "For better performance, download ninja.exe and place it in $cmakeRoot\bin\ninja.exe"
  $env:CMAKE_GENERATOR="NMake Makefiles"
  $env:CMAKE_MAKE_PROGRAM="$msvcBinPath\nmake.exe"
}

# Cargo / Rust env
$env:CC="$msvcBinPath\cl.exe"
$env:CXX="$msvcBinPath\cl.exe"
$env:AR="$msvcBinPath\lib.exe"
$env:LINK="$msvcBinPath\link.exe"
$env:NMAKE="$msvcBinPath\nmake.exe"
$env:VCINSTALLDIR="$msvcRoot\VC\"
$env:VCToolsInstallDir="$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
$env:WindowsSdkDir="$msvcRoot\Windows Kits\10\"
$env:CMAKE_C_COMPILER="$msvcBinPath\cl.exe"
$env:CMAKE_CXX_COMPILER="$msvcBinPath\cl.exe"
$env:VSINSTALLDIR="$msvcRoot\"
$env:VCTOOLSINSTALLDIR="$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\"
$env:RUSTFLAGS="-C linker=$msvcBinPath\link.exe"
$env:CARGO_TARGET_X86_64_PC_WINDOWS_MSVC_LINKER="$msvcBinPath\link.exe"
$env:CC_x86_64_pc_windows_msvc="$msvcBinPath\cl.exe"
$env:CXX_x86_64_pc_windows_msvc="$msvcBinPath\cl.exe"
$env:AR_x86_64_pc_windows_msvc="$msvcBinPath\lib.exe"
$env:CFLAGS_x86_64_pc_windows_msvc="/I$msvcRoot\VC\Tools\MSVC\$vcToolsVersion\include"

# MSYS2 tools
$ucrt64Tools=@{
  make="$msys64Root\ucrt64\bin\make.exe"
  "mingw32-make"="$msys64Root\ucrt64\bin\mingw32-make.exe"
}
foreach($k in $ucrt64Tools.Keys){
  $e=$ucrt64Tools[$k]
  if(Test-Path $e){Set-Alias -Name $k -Value $e -Force -Option AllScope}
}

# Python aliases
if($pythonRoot){
  $python314Exe="$pythonRoot\python.exe"
  $pip314Exe="$pythonRoot\Scripts\pip.exe"
  if(Test-Path $python314Exe){
    Set-Alias python314 $python314Exe -Force -Option AllScope
    Set-Alias py314 $python314Exe -Force -Option AllScope
  }
  if(Test-Path $pip314Exe){Set-Alias pip314 $pip314Exe -Force -Option AllScope}
}
$pythonMsysExe="$msys64Root\ucrt64\bin\python.exe"
if(Test-Path $pythonMsysExe){
  Set-Alias python-msys $pythonMsysExe -Force -Option AllScope
  Set-Alias pip-msys "$msys64Root\ucrt64\bin\pip.exe" -Force -Option AllScope
}

# Compiler aliases
$clangExe="$clangRoot\bin\clang.exe"
$clangPPExe="$clangRoot\bin\clang++.exe"
$clangMsysExe="$msys64Root\ucrt64\bin\clang.exe"
$clangPPMsysExe="$msys64Root\ucrt64\bin\clang++.exe"
if(Test-Path $clangExe){
  Set-Alias clang-win $clangExe -Force -Option AllScope
  Set-Alias "clang++-win" $clangPPExe -Force -Option AllScope
}
if(Test-Path $clangMsysExe){
  Set-Alias clang-msys $clangMsysExe -Force -Option AllScope
  Set-Alias "clang++-msys" $clangPPMsysExe -Force -Option AllScope
}

# CMake aliases
$cmakeWinExe="$cmakeRoot\bin\cmake.exe"
$cmakeMsysExe="$msys64Root\ucrt64\bin\cmake.exe"
if(Test-Path $cmakeWinExe){Set-Alias cmake-win $cmakeWinExe -Force -Option AllScope}
if(Test-Path $cmakeMsysExe){Set-Alias cmake-msys $cmakeMsysExe -Force -Option AllScope}

# Ninja aliases
$ninjaMsysExe="$msys64Root\ucrt64\bin\ninja.exe"
if(Test-Path $ninjaMsysExe){Set-Alias ninja-msys $ninjaMsysExe -Force -Option AllScope}
if($windowsNinja -and (Test-Path $windowsNinja)){Set-Alias ninja-win $windowsNinja -Force -Option AllScope}

# Build env switchers
function Use-WindowsMSVC{
  Write-Host "Switching to Windows MSVC build environment..." -ForegroundColor Cyan
  $env:CMAKE_GENERATOR="Ninja"
  if($windowsNinja){
    $env:CMAKE_MAKE_PROGRAM=$windowsNinja
  }else{
    $env:CMAKE_GENERATOR="NMake Makefiles"
    $env:CMAKE_MAKE_PROGRAM="$msvcBinPath\nmake.exe"
  }
  $env:CC="$msvcBinPath\cl.exe"
  $env:CXX="$msvcBinPath\cl.exe"
  $env:LINKER="$msvcBinPath\link.exe"
  Remove-Item Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
}
function Use-MSYS2GCC{
  Write-Host "Switching to MSYS2/GCC build environment..." -ForegroundColor Cyan
  $env:CMAKE_GENERATOR="Ninja"
  $env:CMAKE_MAKE_PROGRAM="$msys64Root\ucrt64\bin\ninja.exe"
  $env:CC="$msys64Root\ucrt64\bin\gcc.exe"
  $env:CXX="$msys64Root\ucrt64\bin\g++.exe"
  Remove-Item Env:\LINKER,Env:\LINK,Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
}
function Use-MSYS2Clang{
  Write-Host "Switching to MSYS2/Clang build environment..." -ForegroundColor Cyan
  $env:CMAKE_GENERATOR="Ninja"
  $env:CMAKE_MAKE_PROGRAM="$msys64Root\ucrt64\bin\ninja.exe"
  $env:CC="$msys64Root\ucrt64\bin\clang.exe"
  $env:CXX="$msys64Root\ucrt64\bin\clang++.exe"
  Remove-Item Env:\LINKER,Env:\LINK,Env:\CMAKE_LINKER -ErrorAction SilentlyContinue
}
function Use-WindowsClangMSVC{
  Write-Host "Switching to Windows Clang-cl (MSVC backend) build environment..." -ForegroundColor Cyan
  $env:CMAKE_GENERATOR="Ninja"
  if($windowsNinja){
    $env:CMAKE_MAKE_PROGRAM=$windowsNinja
  }else{
    $env:CMAKE_GENERATOR="NMake Makefiles"
    $env:CMAKE_MAKE_PROGRAM="$msvcBinPath\nmake.exe"
  }
  $env:CC="$clangRoot\bin\clang-cl.exe"
  $env:CXX="$clangRoot\bin\clang-cl.exe"
  $env:CMAKE_LINKER="$clangRoot\bin\lld-link.exe"
  Remove-Item Env:\LINKER,Env:\LINK -ErrorAction SilentlyContinue
}
Set-Alias use-msvc Use-WindowsMSVC
Set-Alias use-gcc Use-MSYS2GCC
Set-Alias use-clang-msys Use-MSYS2Clang
Set-Alias use-clang-win Use-WindowsClangMSVC

# Rust/Cargo helper
function Update-Cargo{
  $custom=@(
    @{name='ripgrep';flags='-C target-cpu=native';features='--all-features'},
    @{name='xh';flags='--cfg reqwest_unstable';features='--all-features'}
  )
  Write-Host "Checking cargo-binstall..." -ForegroundColor Cyan
  cargo install cargo-binstall
  Write-Host "`nUpdating custom-compiled packages..." -ForegroundColor Cyan
  foreach($p in $custom){
    Write-Host "  Updating $($p.name)..." -ForegroundColor Yellow
    $env:RUSTFLAGS=$p.flags
    if($p.features){cargo install $p.name @($p.features.Split(' '))}else{cargo install $p.name}
    Remove-Item Env:\RUSTFLAGS -ErrorAction SilentlyContinue
  }
  Write-Host "`nUpdating remaining cargo packages..." -ForegroundColor Cyan
  cargo install-update -a
  Write-Host "`nAll updates complete!" -ForegroundColor Green
}

# Compiler setup shorthands
function Setup-MSVC{Write-Host "MSVC environment already configured!" -ForegroundColor Green}
function Setup-GCC{Write-Host "GCC environment already configured!" -ForegroundColor Green}
function Setup-Clang{Write-Host "Clang environment already configured!" -ForegroundColor Green}
function Setup-AllCompilers{Write-Host "All compiler environments already configured!" -ForegroundColor Green}
function Update-GlobalNpm{
  npm list -g --depth=0 --parseable|
    Select-Object -Skip 1|
    ForEach-Object{npm install -g "$(Split-Path $_ -Leaf)@latest"}
}
Set-Alias setupmsvc Setup-MSVC
Set-Alias setupgcc Setup-GCC
Set-Alias setupclang Setup-Clang
Set-Alias setupcc Setup-AllCompilers
Set-Alias npmupdate Update-GlobalNpm

# Compact summary (auto-run)
function Show-DevSummary{
  Write-Host ""
  Write-Host "TOOLS / ALIASES:"
  foreach($t in @(
    'cmake','cmake-win','cmake-msys',
    'ninja','ninja-win','ninja-msys',
    'python','python314','python-msys',
    'pip','pip314','pip-msys',
    'clang','clang-win','clang-msys',
    'gcc','make','mingw32-make'
  )){
    $c=Get-Command $t -ErrorAction SilentlyContinue
    if($c){
      $target = if($c.CommandType -eq 'Alias'){
        $c.Definition
      }elseif($c.PSObject.Properties.Match('Source').Count -and $c.Source){
        $c.Source
      }elseif($c.PSObject.Properties.Match('Path').Count -and $c.Path){
        $c.Path
      }else{$null}
      if($target){Write-Host ("  {0,-12} -> {1}" -f $t,$target)}
    }
  }

  Write-Host "`nVERSIONS:"
  if(Get-Command python -ErrorAction SilentlyContinue){
    Write-Host "  python      -> $(python --version 2>&1)"
  }
  if(Get-Command pip -ErrorAction SilentlyContinue){
    Write-Host "  pip         -> $(pip --version 2>&1)"
  }
  if(Get-Command cmake -ErrorAction SilentlyContinue){
    $cv=cmake --version 2>&1
    Write-Host "  cmake       -> $($cv -split '\n')[0]"
  }
  if(Get-Command ninja -ErrorAction SilentlyContinue){
    Write-Host "  ninja       -> $(ninja --version 2>&1)"
  }

  # ---- SMART LINKER LOGIC ----
  $effectiveLinker = $null

  if ($env:CMAKE_LINKER) {
    # set only in clang-cl mode
    $effectiveLinker = $env:CMAKE_LINKER
  }
  elseif ($env:LINKER) {
    # rarely used in your profile
    $effectiveLinker = $env:LINKER
  }
  elseif ($env:LINK) {
    # the real MSVC linker
    $effectiveLinker = $env:LINK
  }
  else {
    # MSYS2 GCC/Clang mode: use the compiler to print its linker path
    try {
      if ($env:CC) {
        $ld = & $env:CC -print-prog-name=ld 2>$null
        if ($ld) { $effectiveLinker = $ld }
      }
    } catch {}
    if (-not $effectiveLinker) { $effectiveLinker = "(auto-detected by GCC/Clang)" }
  }

  Write-Host "`nDEFAULT BUILD ENV:"
  Write-Host "  CMAKE_GENERATOR     = $env:CMAKE_GENERATOR"
  Write-Host "  CMAKE_MAKE_PROGRAM  = $env:CMAKE_MAKE_PROGRAM"
  Write-Host "  CC                  = $env:CC"
  Write-Host "  CXX                 = $env:CXX"
  Write-Host "  LINK                = $env:LINK"
  Write-Host "  LINKER              = $env:LINKER"
  Write-Host "  CMAKE_LINKER        = $env:CMAKE_LINKER"
  Write-Host "  EFFECTIVE_LINKER    = $effectiveLinker"

  Write-Host "`nENV SWITCH:"
  Write-Host "  use-msvc       : MSVC + cmake-win + ninja-win + cl.exe + link.exe"
  Write-Host "  use-clang-win  : clang-cl + lld-link + ninja-win"
  Write-Host "  use-gcc        : MSYS2 GCC + cmake-msys + ninja-msys"
  Write-Host "  use-clang-msys : MSYS2 clang + cmake-msys + ninja-msys"
}
Show-DevSummary
