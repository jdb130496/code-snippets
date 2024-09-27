@echo off
:: Set up environment variables for VC++ toolchain

:: Path to the MSVC toolchain
set VC_PATH=D:\Programs\vsbt\VC\Tools\MSVC\14.41.34120

:: Set INCLUDE environment variable
set INCLUDE=%VC_PATH%\include;D:\Programs\BuildTools\Windows Kits\10\Include\10.0.26100.0\ucrt

:: Set LIB environment variable
set LIB=%VC_PATH%\lib\x64;D:\Programs\BuildTools\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64

:: Set PATH environment variable for the MSVC compiler and tools
set PATH=%VC_PATH%\bin\Hostx64\x64;%PATH%

:: Set Windows Kits tools and libraries if needed
set PATH=D:\Programs\BuildTools\Windows Kits\10\bin\10.0.26100.0\x64;%PATH%

:: Display the values to check they are correctly set
echo INCLUDE=%INCLUDE%
echo LIB=%LIB%
echo PATH=%PATH%

:: Optional: Keep the prompt open for testing
pause

