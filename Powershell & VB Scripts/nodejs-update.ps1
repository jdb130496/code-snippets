$indexUrl   = "https://nodejs.org/download/nightly/index.json"
$installDir = "D:\Programs\nodejs"
$zipPath    = "$env:TEMP\node-nightly.zip"
$tempExtract = "$env:TEMP\node_extract"

Write-Host "Fetching nightly index..." -ForegroundColor Cyan
$index  = Invoke-RestMethod $indexUrl
$latest = $index | Sort-Object date -Descending | Select-Object -First 1

Write-Host "Latest nightly: $($latest.version) ($($latest.date))" -ForegroundColor Green

# ── Check if already installed ──────────────────────────────────────────
$currentVer = if (Test-Path "$installDir\node.exe") {
    & "$installDir\node.exe" --version 2>$null
} else { "" }

if ($currentVer -eq $latest.version) {
    Write-Host "✓ Already on latest nightly ($currentVer) — nothing to do." -ForegroundColor Green
    exit 0
}
Write-Host "  Installed: $currentVer → Updating to: $($latest.version)" -ForegroundColor Yellow

# ── Download ────────────────────────────────────────────────────────────
$fileName = "node-$($latest.version)-win-x64.zip"
$fileUrl  = "https://nodejs.org/download/nightly/$($latest.version)/$fileName"

Write-Host "Downloading $fileName ..." -ForegroundColor Cyan
& aria2c $fileUrl --out="node-nightly.zip" --dir="$env:TEMP" `
    --max-connection-per-server=16 --split=16 --min-split-size=5M `
    --continue=true --console-log-level=notice
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ aria2c download failed" -ForegroundColor Red
    exit 1
}

# ── Verify download ─────────────────────────────────────────────────────
$zipSize = (Get-Item $zipPath).Length
Write-Host "  Downloaded: $([math]::Round($zipSize/1MB, 1)) MB" -ForegroundColor DarkGray
if ($zipSize -lt 10MB) {
    Write-Host "✗ Download looks too small — aborting" -ForegroundColor Red
    exit 1
}

# ── Extract ─────────────────────────────────────────────────────────────
Write-Host "Extracting..." -ForegroundColor Cyan
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue
Expand-Archive $zipPath -DestinationPath $tempExtract -Force

$innerDir = Get-ChildItem $tempExtract -Directory | Select-Object -First 1
if (-not $innerDir) {
    Write-Host "✗ Extraction failed — no folder found in zip" -ForegroundColor Red
    exit 1
}

# ── Install ─────────────────────────────────────────────────────────────
Write-Host "Installing to $installDir ..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force $installDir | Out-Null
Copy-Item "$($innerDir.FullName)\*" $installDir -Recurse -Force

# ── Cleanup ─────────────────────────────────────────────────────────────
Write-Host "Cleaning up..." -ForegroundColor DarkGray
Remove-Item $zipPath     -Force -ErrorAction SilentlyContinue
Remove-Item $tempExtract -Recurse -Force -ErrorAction SilentlyContinue

# ── Verify ──────────────────────────────────────────────────────────────
$newVer = & "$installDir\node.exe" --version 2>&1
$npmVer = & "$installDir\node.exe" "$installDir\node_modules\npm\bin\npm-cli.js" --version 2>&1
Write-Host "✓ Node.js $newVer installed" -ForegroundColor Green
Write-Host "✓ npm $npmVer bundled" -ForegroundColor Green