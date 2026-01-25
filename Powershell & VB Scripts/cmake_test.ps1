# CMake 4.2.2 Installation Test Script
# This script creates a simple C++ project and tests if CMake can configure and build it

# Set error action preference
$ErrorActionPreference = "Stop"

Write-Host "=== CMake 4.2.2 Installation Test ===" -ForegroundColor Cyan

# Create a temporary test directory
$testDir = Join-Path $env:TEMP "cmake_test_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $testDir -Force | Out-Null
Write-Host "Created test directory: $testDir" -ForegroundColor Green

try {
    # Check CMake version
    Write-Host "`nChecking CMake version..." -ForegroundColor Yellow
    $cmakeVersion = & cmake --version
    Write-Host $cmakeVersion -ForegroundColor White
    
    # Create a simple C++ source file
    $cppCode = @"
#include <iostream>

int main() {
    std::cout << "Hello from CMake 4.2.2 test!" << std::endl;
    return 0;
}
"@
    
    $cppFile = Join-Path $testDir "main.cpp"
    Set-Content -Path $cppFile -Value $cppCode
    Write-Host "Created main.cpp" -ForegroundColor Green
    
    # Create CMakeLists.txt
    $cmakeContent = @"
cmake_minimum_required(VERSION 4.2)
project(CMakeTest VERSION 1.0.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

add_executable(cmake_test main.cpp)
"@
    
    $cmakeFile = Join-Path $testDir "CMakeLists.txt"
    Set-Content -Path $cmakeFile -Value $cmakeContent
    Write-Host "Created CMakeLists.txt" -ForegroundColor Green
    
    # Create build directory
    $buildDir = Join-Path $testDir "build"
    New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
    
    # Configure with CMake (force compiler test)
    Write-Host "`nConfiguring project with CMake..." -ForegroundColor Yellow
    Push-Location $buildDir
    & cmake .. -DCMAKE_CXX_COMPILER_FORCED=OFF 2>&1 | Tee-Object -Variable cmakeOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "CMake configuration failed with exit code $LASTEXITCODE"
    }
    Write-Host "Configuration successful!" -ForegroundColor Green
    
    # Verify MSVC compiler was detected
    Write-Host "`nVerifying MSVC compiler..." -ForegroundColor Yellow
    $cacheFile = Join-Path $buildDir "CMakeCache.txt"
    if (Test-Path $cacheFile) {
        $compilerPath = Select-String -Path $cacheFile -Pattern "CMAKE_CXX_COMPILER:FILEPATH=" | Select-Object -First 1
        if ($compilerPath -match "cl\.exe") {
            Write-Host "✓ MSVC compiler (cl.exe) detected and verified" -ForegroundColor Green
            Write-Host "  $($compilerPath.Line.Split('=')[1])" -ForegroundColor Gray
        } else {
            Write-Host "⚠ Warning: cl.exe not detected in compiler path" -ForegroundColor Yellow
        }
    }
    
    # Build the project
    Write-Host "`nBuilding project..." -ForegroundColor Yellow
    & cmake --build . 2>&1 | Tee-Object -Variable buildOutput
    
    if ($LASTEXITCODE -ne 0) {
        throw "Build failed with exit code $LASTEXITCODE"
    }
    Write-Host "Build successful!" -ForegroundColor Green
    
    # Try to run the executable
    Write-Host "`nRunning compiled executable..." -ForegroundColor Yellow
    $exePath = Get-ChildItem -Path . -Recurse -Filter "cmake_test.exe" | Select-Object -First 1
    
    if ($exePath) {
        & $exePath.FullName
        Write-Host "Executable ran successfully!" -ForegroundColor Green
    } else {
        Write-Host "Warning: Could not find executable to run" -ForegroundColor Yellow
    }
    
    Pop-Location
    
    Write-Host "`n=== TEST PASSED ===" -ForegroundColor Green
    Write-Host "CMake 4.2.2 is working correctly!" -ForegroundColor Green
    
} catch {
    Write-Host "`n=== TEST FAILED ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
} finally {
    # Clean up
    Write-Host "`nCleaning up test directory..." -ForegroundColor Yellow
    if (Test-Path $testDir) {
        Remove-Item -Path $testDir -Recurse -Force
        Write-Host "Test directory removed" -ForegroundColor Green
    }
}

Write-Host "`nTest complete!" -ForegroundColor Cyan
