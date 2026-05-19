function Test-MSYS2Layout {
    Write-Host "Checking your MSYS2 UCRT64 layout..." -ForegroundColor Cyan
    
    $ucrt64Root = "D:\Programs\msys64\ucrt64"
    
    # Check key directories
    $pathsToCheck = @(
        "$ucrt64Root\bin",
        "$ucrt64Root\include", 
        "$ucrt64Root\lib",
        "$ucrt64Root\share"
    )
    
    foreach ($path in $pathsToCheck) {
        if (Test-Path $path) {
            Write-Host "✓ Found: $path" -ForegroundColor Green
        } else {
            Write-Host "✗ Missing: $path" -ForegroundColor Red
        }
    }
    
    # Check critical executables
    $execsToCheck = @(
        "$ucrt64Root\bin\gcc.exe",
        "$ucrt64Root\bin\g++.exe",
        "$ucrt64Root\bin\clang.exe",
        "$ucrt64Root\bin\make.exe",
        "$ucrt64Root\bin\cmake.exe"
    )
    
    Write-Host "`nChecking executables:" -ForegroundColor Cyan
    foreach ($exec in $execsToCheck) {
        if (Test-Path $exec) {
            Write-Host "✓ $exec" -ForegroundColor Green
        } else {
            Write-Host "✗ $exec (not found)" -ForegroundColor Red
        }
    }
}
