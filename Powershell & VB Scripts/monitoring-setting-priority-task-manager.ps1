while ($true) {
    $procs = Get-Process -Name "ffmpeg" -ErrorAction SilentlyContinue
    if ($procs) {
        foreach ($p in $procs) {
            try {
                $p.PriorityClass = [System.Diagnostics.ProcessPriorityClass]::High
                Write-Host "Set High priority on ffmpeg PID: $($p.Id)" -ForegroundColor Green
            } catch {
                # Process may have died between detection and setting
            }
        }
    } else {
        Write-Host "Waiting for ffmpeg..." -ForegroundColor Yellow
    }
    Start-Sleep -Milliseconds 500
}
