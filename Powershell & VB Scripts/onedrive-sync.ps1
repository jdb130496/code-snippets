# ================== CONFIG ==================
$Source = "D:\OneDrive - 0yt2k"
$Target = "D:\Onedrive Backup"
$LogFile = "D:\dev\sync-log.txt"
$DryRun = $false   # set to $true to preview only, no copy/delete
# ==============================================

function Is-GitRelated($path) {
    return $path -match '(^|\\)\.git(\\|$)'
}

$ProtectedPaths = @(
    "README.md"   # root-level README kept even if deleted from source
)

function Is-ProtectedFile($path) {
    return $ProtectedPaths -icontains $path
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

$copied        = @()
$deleted       = @()
$skipped       = @()
$protected     = @()
$orphanFolders = @()
$errors        = @()

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
        # New in source -> copy to target
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
        # Missing in source -> delete from target (unless protected)
        if (Is-ProtectedFile $path) {
            $protected += $path
            continue
        }
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
        # Size or timestamp differs -> copy to target
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
    elseif ((Get-FileHash (Join-Path $Source $path) -Algorithm MD5).Hash -ne
            (Get-FileHash (Join-Path $Target $path) -Algorithm MD5).Hash) {
        # Size+timestamp identical but content differs (OneDrive timestamp rounding)
        if ($DryRun) {
            Write-Host "[DRY-RUN] Would COPY (hash mismatch): $path"
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

# ================== CLEANUP ORPHAN FOLDERS ==================
Write-Host "Cleaning up orphan folders in target..."
Get-ChildItem -Recurse -Directory $Target -ErrorAction SilentlyContinue |
    Sort-Object { $_.FullName.Length } -Descending |
    ForEach-Object {
        $rel = $_.FullName.Substring($Target.Length).TrimStart('\')

        if (Is-GitRelated $rel) { return }

        $srcFolder = Join-Path $Source $rel
        if (-not (Test-Path $srcFolder)) {
            if ($DryRun) {
                Write-Host "[DRY-RUN] Would DELETE folder: $rel"
            } else {
                try {
                    Remove-Item -LiteralPath $_.FullName -Recurse -Force
                    $orphanFolders += $rel
                } catch {
                    $errors += "FOLDER DELETE FAILED: $rel -- $($_.Exception.Message)"
                }
            }
        }
    }

# ================== SUMMARY ==================
$summary = @()
$summary += "===== SYNC SUMMARY ====="
$summary += "Mode: $(if ($DryRun) { 'DRY RUN (no changes made)' } else { 'LIVE' })"
$summary += "Copied/Updated:   $($copied.Count)"
$summary += "Deleted:          $($deleted.Count)"
$summary += "Skipped (.git):   $($skipped.Count)"
$summary += "Protected (kept): $($protected.Count)"
$summary += "Orphan folders:   $($orphanFolders.Count)"
$summary += "Errors:           $($errors.Count)"
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
$summary += "--- Protected files (missing in source, NOT deleted) ---"
$summary += $protected
$summary += ""
$summary += "--- Deleted orphan folders ---"
$summary += $orphanFolders
$summary += ""
$summary += "--- Errors ---"
$summary += $errors

$summary | Out-File -FilePath $LogFile -Encoding UTF8

Write-Host ""
Write-Host "===== DONE ====="
Write-Host "Copied/Updated:   $($copied.Count)"
Write-Host "Deleted:          $($deleted.Count)"
Write-Host "Skipped (.git):   $($skipped.Count)"
Write-Host "Protected (kept): $($protected.Count)"
Write-Host "Orphan folders:   $($orphanFolders.Count)"
Write-Host "Errors:           $($errors.Count)"
Write-Host "Full log written to: $LogFile"
