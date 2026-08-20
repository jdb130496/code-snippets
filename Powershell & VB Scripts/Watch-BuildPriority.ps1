function Watch-BuildPriority {
    param(
        [string[]]$ProcessNames = @("nasm", "cl", "link", "cmd", "rustc", "nmake", "perl", "jom"),
        [int]$PollIntervalMs = 200
    )

    Write-Host "Watching for processes: $($ProcessNames -join ', ')... (Ctrl+C to stop)" -ForegroundColor Cyan
    $seen = @{}

    while ($true) {
        $procs = Get-Process -Name $ProcessNames -ErrorAction SilentlyContinue
        foreach ($p in $procs) {
            if (-not $seen.ContainsKey($p.Id)) {
                try {
                    $p.PriorityClass = "High"
                    Write-Host "  ✓ Set $($p.Name) PID $($p.Id) to High priority" -ForegroundColor Green
                } catch {
                    Write-Host "  ⚠ Could not set priority for $($p.Name) PID $($p.Id): $_" -ForegroundColor Yellow
                }
                $seen[$p.Id] = $true
            }
        }

        # Clean up finished PIDs
        $activeIds = $procs.Id
        foreach ($key in @($seen.Keys)) {
            if ($activeIds -notcontains $key) {
                $seen.Remove($key)
            }
        }

        Start-Sleep -Milliseconds $PollIntervalMs
    }
}
