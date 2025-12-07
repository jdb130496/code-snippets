# Run this as Administrator
# This script fixes permissions and monitors for new files

$configPath = "D:\Config.Msi"

Write-Host "Stopping Windows Installer service..." -ForegroundColor Yellow
Stop-Service -Name msiserver -Force -ErrorAction SilentlyCue

Write-Host "`nTaking ownership of $configPath..." -ForegroundColor Cyan
takeown /F $configPath /R /A /D Y 2>&1 | Out-Null

Write-Host "Resetting and applying permissions..." -ForegroundColor Cyan
icacls $configPath /reset /T /C /Q 2>&1 | Out-Null
icacls $configPath /grant:r "Everyone:(OI)(CI)F" /T /C /Q 2>&1 | Out-Null
icacls $configPath /grant:r "SYSTEM:(OI)(CI)F" /T /C /Q 2>&1 | Out-Null
icacls $configPath /grant:r "Administrators:(OI)(CI)F" /T /C /Q 2>&1 | Out-Null

Write-Host "Starting Windows Installer service..." -ForegroundColor Yellow
Start-Service -Name msiserver

Write-Host "`n✓ Permissions fixed!" -ForegroundColor Green
Write-Host "`nStarting file system watcher for new files..." -ForegroundColor Cyan

# Create file system watcher
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $configPath
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true

# Action when new file is created
$action = {
    $path = $Event.SourceEventArgs.FullPath
    Start-Sleep -Milliseconds 100
    
    try {
        icacls $path /grant "Everyone:F" /C /Q 2>&1 | Out-Null
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Fixed: $path" -ForegroundColor Green
    } catch {
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] Failed: $path" -ForegroundColor Red
    }
}

# Register events
Register-ObjectEvent -InputObject $watcher -EventName Created -Action $action | Out-Null

Write-Host "✓ Monitoring active! New files will auto-fix permissions." -ForegroundColor Green
Write-Host "Press Ctrl+C to stop monitoring after Python repair completes.`n" -ForegroundColor Yellow

# Keep script running
try {
    while ($true) {
        Start-Sleep -Seconds 1
    }
} finally {
    $watcher.Dispose()
    Get-EventSubscriber | Unregister-Event
    Write-Host "`nMonitoring stopped." -ForegroundColor Yellow
}
