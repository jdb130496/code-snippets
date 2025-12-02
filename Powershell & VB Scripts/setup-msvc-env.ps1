# MSVC Environment Variables
$env:VSCMD_ARG_HOST_ARCH="x64"
$env:VSCMD_ARG_TGT_ARCH="x64"
$env:VCToolsVersion="14.50.35717"
$env:WindowsSDKVersion="10.0.26100.0\"
$env:VCToolsInstallDir="D:\dev\msvc\VC\Tools\MSVC\14.50.35717\"
$env:WindowsSdkBinPath="D:\dev\msvc\Windows Kits\10\bin\"
$env:WindowsSDKDir="D:\dev\msvc\Windows Kits\10"
$env:DISTUTILS_USE_SDK="1"
$env:MSSdk="1"

# Add Clang paths to INCLUDE (Clang's headers should come after MSVC/Windows SDK)
$env:INCLUDE="D:\dev\msvc\VC\Tools\MSVC\14.50.35717\include;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\ucrt;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\shared;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\um;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\winrt;D:\dev\msvc\Windows Kits\10\Include\10.0.26100.0\cppwinrt;D:\Programs\clang\include"

# Add Clang paths to LIB
$env:LIB="D:\dev\msvc\VC\Tools\MSVC\14.50.35717\lib\x64;D:\dev\msvc\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64;D:\dev\msvc\Windows Kits\10\Lib\10.0.26100.0\um\x64;D:\Programs\clang\lib"

# Add both MSVC and Clang bin directories to PATH (Clang first if you want it as default)
$env:PATH="D:\Programs\clang\bin;D:\dev\msvc\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64;D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64;D:\dev\msvc\Windows Kits\10\bin\10.0.26100.0\x64\ucrt;$env:PATH"

Write-Host "MSVC and Clang environment configured" -ForegroundColor Green
