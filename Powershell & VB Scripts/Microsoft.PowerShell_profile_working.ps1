# MSVC Setup - Correct path
$MSVCRoot = "D:\dev\msvc"

$env:VSCMD_ARG_HOST_ARCH = "x64"
$env:VSCMD_ARG_TGT_ARCH = "x64"
$env:VCToolsVersion = "14.50.35717"
$env:WindowsSDKVersion = "10.0.26100.0\"

$env:VCToolsInstallDir = "$MSVCRoot\VC\Tools\MSVC\14.50.35717\"
$env:WindowsSdkBinPath = "$MSVCRoot\Windows Kits\10\bin\"

$env:PATH = "$MSVCRoot\VC\Tools\MSVC\14.50.35717\bin\Hostx64\x64;$MSVCRoot\Windows Kits\10\bin\10.0.26100.0\x64;$MSVCRoot\Windows Kits\10\bin\10.0.26100.0\x64\ucrt;$env:PATH"

$env:INCLUDE = "$MSVCRoot\VC\Tools\MSVC\14.50.35717\include;$MSVCRoot\Windows Kits\10\Include\10.0.26100.0\ucrt;$MSVCRoot\Windows Kits\10\Include\10.0.26100.0\shared;$MSVCRoot\Windows Kits\10\Include\10.0.26100.0\um;$MSVCRoot\Windows Kits\10\Include\10.0.26100.0\winrt;$MSVCRoot\Windows Kits\10\Include\10.0.26100.0\cppwinrt"

$env:LIB = "$MSVCRoot\VC\Tools\MSVC\14.50.35717\lib\x64;$MSVCRoot\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64;$MSVCRoot\Windows Kits\10\Lib\10.0.26100.0\um\x64"

Write-Host "MSVC environment configured for x64 from $MSVCRoot" -ForegroundColor Green

# Verify
if (Get-Command link.exe -ErrorAction SilentlyContinue) {
    Write-Host "✓ link.exe found at: $((Get-Command link.exe).Source)" -ForegroundColor Green
} else {
    Write-Host "✗ link.exe NOT found in PATH!" -ForegroundColor Red
}

