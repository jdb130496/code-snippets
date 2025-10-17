$packages = pip freeze | ForEach-Object { ($_ -split '==')[0] }

foreach ($pkg in $packages) {
    Write-Host "Uninstalling $pkg..." -ForegroundColor Yellow
    pip uninstall -y $pkg
}

$failed = @()

foreach ($pkg in $packages) {
    Write-Host "Installing $pkg..." -ForegroundColor Cyan
    pip install --no-deps $pkg 2>$null
    if ($LASTEXITCODE -ne 0) {
        $failed += $pkg
        Write-Host "Failed: $pkg" -ForegroundColor Red
    }
}

Write-Host "`nRetrying failed packages with --pre..." -ForegroundColor Yellow
foreach ($pkg in $failed) {
    Write-Host "Retrying $pkg..." -ForegroundColor Cyan
    pip install --pre $pkg
}

Write-Host "`nDone!" -ForegroundColor Green
