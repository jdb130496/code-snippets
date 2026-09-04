# command to run in powershell: & .\montitoring-multiple-processes.ps1
while ($true) {
    $processNames = @("ffmpeg", "bash", "python", "cmake", "ninja", "make")
    
    Get-Process -Name $processNames -ErrorAction SilentlyContinue | ForEach-Object {
        try {
            $_.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::High
            Write-Host "$(Get-Date -Format 'HH:mm:ss') | PID $($_.Id) | $($_.Name) set to High" -ForegroundColor Green
        } catch {}
    }
    Start-Sleep -Milliseconds 500
}
