# ================== CONFIG ==================
$Source = "D:\OneDrive - 0yt2k"
$Target = "D:\Onedrive Backup"
$LogFile = "D:\dev\sync-log.txt"
$DryRun = $false   # set to $true to preview only, no copy/delete
# ==============================================

function Is-GitRelated($path) {
    return $path -match '(^|\\)\.git(\\|$)'
}

function Get-Snapshot($root) {
    Get-ChildItem -Recurse -File $root -ErrorAction SilentlyContinue | ForEach-Object {
        [PSCustomObject]@{
            RelPath  = $_.FullName.Substring($root.Length).TrimStart('\')
            Length   = $_.Length
            Modified = $_.LastWriteTimeUtc
        }
    }
}

Write-Host "Scanning source: $Source"
$a = Get-Snapshot $Source
Write-Host "Scanning target: $Target"
$b = Get-Snapshot $Target

$aMap = @{}; $a | ForEach-Object { $aMap[$_.RelPath] = $_ }
$bMap = @{}; $b | ForEach-Object { $bMap[$_.RelPath] = $_ }

$allPaths = ($aMap.Keys + $bMap.Keys) | Select-Object -Unique

$copied  = @()
$deleted = @()
$skipped = @()
$errors  = @()

foreach ($path in $allPaths) {

    if (Is-GitRelated $path) {
        $skipped += $path
        continue
    }

    $inA = $aMap.ContainsKey($path)
    $inB = $bMap.ContainsKey($path)

    $srcPath = Join-Path $Source $path
    $dstPath = Join-Path $Target $path

    if ($inA -and -not $inB) {
        # Added or Changed -> copy to target
        if ($DryRun) {
            Write-Host "[DRY-RUN] Would COPY (new): $path"
        } else {
            try {
                $dstDir = Split-Path $dstPath -Parent
                if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
                Copy-Item -LiteralPath $srcPath -Destination $dstPath -Force
                $copied += $path
            } catch {
                $errors += "COPY FAILED: $path -- $($_.Exception.Message)"
            }
        }
    }
    elseif (-not $inA -and $inB) {
        # Missing in source -> delete from target (backup)
        if ($DryRun) {
            Write-Host "[DRY-RUN] Would DELETE: $path"
        } else {
            try {
                Remove-Item -LiteralPath $dstPath -Force
                $deleted += $path
            } catch {
                $errors += "DELETE FAILED: $path -- $($_.Exception.Message)"
            }
        }
    }
    elseif ($aMap[$path].Length -ne $bMap[$path].Length -or $aMap[$path].Modified -ne $bMap[$path].Modified) {
        # Changed -> copy to target
        if ($DryRun) {
            Write-Host "[DRY-RUN] Would COPY (changed): $path"
        } else {
            try {
                $dstDir = Split-Path $dstPath -Parent
                if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
                Copy-Item -LiteralPath $srcPath -Destination $dstPath -Force
                $copied += $path
            } catch {
                $errors += "COPY FAILED: $path -- $($_.Exception.Message)"
            }
        }
    }
    # else: identical, do nothing
}

# ================== SUMMARY ==================
$summary = @()
$summary += "===== SYNC SUMMARY ====="
$summary += "Mode: $(if ($DryRun) { 'DRY RUN (no changes made)' } else { 'LIVE' })"
$summary += "Copied/Updated: $($copied.Count)"
$summary += "Deleted:        $($deleted.Count)"
$summary += "Skipped (.git): $($skipped.Count)"
$summary += "Errors:         $($errors.Count)"
$summary += ""
$summary += "--- Copied/Updated files ---"
$summary += $copied
$summary += ""
$summary += "--- Deleted files ---"
$summary += $deleted
$summary += ""
$summary += "--- Skipped .git-related paths ---"
$summary += $skipped
$summary += ""
$summary += "--- Errors ---"
$summary += $errors

$summary | Out-File -FilePath $LogFile -Encoding UTF8

Write-Host ""
Write-Host "===== DONE ====="
Write-Host "Copied/Updated: $($copied.Count)"
Write-Host "Deleted:        $($deleted.Count)"
Write-Host "Skipped (.git): $($skipped.Count)"
Write-Host "Errors:         $($errors.Count)"
Write-Host "Full log written to: $LogFile"
