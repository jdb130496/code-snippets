# Build Environment Test Suite

This test suite verifies that your PowerShell profile correctly configures both Windows MSVC and MSYS2 build environments.

## Files Included

- `test_build.cpp` - C++ test program that displays compiler and platform information
- `CMakeLists.txt` - CMake configuration for the test program
- `test_windows_clang.ps1` - Test script for Windows Clang-cl + MSVC toolchain
- `test_msys2_clang.ps1` - Test script for MSYS2 Clang + MinGW toolchain
- `test_all.ps1` - Master script that runs all tests
- `README.txt` - This file

## Quick Start

1. **Extract all files to the same directory**

2. **Open PowerShell in that directory**

3. **Run the master test script:**
   ```powershell
   .\test_all.ps1
   ```

This will test both build environments and show you a summary.

## Individual Tests

You can also run individual tests:

### Test Windows Clang-cl (MSVC toolchain)
```powershell
.\test_windows_clang.ps1
```

This tests:
- Windows CMake 4.2.3
- Windows Ninja
- Windows Clang-cl (MSVC-compatible frontend)
- MSVC linker and runtime

### Test MSYS2 Clang (MinGW toolchain)
```powershell
.\test_msys2_clang.ps1
```

This tests:
- MSYS2 CMake
- MSYS2 Ninja
- MSYS2 Clang
- MinGW/UCRT runtime

## Expected Output

If everything is configured correctly, you should see:

1. **CMake configuration output** showing:
   - CMake version
   - Generator (Ninja)
   - Compiler information
   - Build system details

2. **Build output** from Ninja

3. **Test program output** showing:
   - Compiler information (Clang-cl for Windows, Clang for MSYS2)
   - Platform information
   - Runtime library (MSVC CRT or MinGW UCRT)
   - C++ standard version

4. **Success message** for each test

## What's Being Tested

### Windows Test (test_windows_clang.ps1)
- Calls `use-clang-win` to set up Windows environment
- Uses `cmake` (which should be cmake-win)
- Should detect Clang-cl as compiler
- Should link against MSVC runtime
- Should use Windows paths

### MSYS2 Test (test_msys2_clang.ps1)
- Calls `use-clang-msys` to set up MSYS2 environment
- Uses `cmake-msys` explicitly
- Should detect Clang (not Clang-cl) as compiler
- Should link against MinGW/UCRT runtime
- Should use Unix-style paths

## Troubleshooting

### "Windows Ninja not found"
- Download ninja.exe from https://github.com/ninja-build/ninja/releases
- Place it in `D:\Programs\cmake\bin\ninja.exe`
- Reload your PowerShell profile: `. $PROFILE`

### "cmake-msys: command not found"
- Make sure MSYS2 is installed at `D:\Programs\msys64`
- Install CMake in MSYS2: `pacman -S mingw-w64-ucrt-x86_64-cmake`

### Build fails with "compiler not found"
- For Windows test: Check that Clang is installed at `D:\Programs\clang`
- For MSYS2 test: Install Clang in MSYS2: `pacman -S mingw-w64-ucrt-x86_64-clang`

### Linker errors
- Make sure MSVC is properly installed at `D:\dev\msvc`
- Verify the version number matches your profile (14.50.35717)

## Clean Up

To remove build artifacts:
```powershell
Remove-Item -Recurse -Force build-windows-clang, build-msys2-clang
```

## What This Proves

If both tests pass, it proves:
1. Your PowerShell profile correctly separates Windows and MSYS2 environments
2. `cmake-win` uses Windows Ninja and doesn't mix with MSYS2 tools
3. `cmake-msys` uses MSYS2 Ninja and doesn't mix with Windows tools
4. Cargo builds will use the correct Windows MSVC toolchain
5. You can switch between environments using `use-*` commands
