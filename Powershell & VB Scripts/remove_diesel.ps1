# 1. Remove installed diesel binary
Remove-Item "D:\Programs\cargo\bin\diesel.exe" -Force -ErrorAction SilentlyContinue
Write-Host "✓ diesel.exe removed"

# 2. Remove diesel + related crates from registry src cache
$registryPath = "D:\Programs\cargo\registry\src\index.crates.io-1949cf8c6b5b557f"
$toRemove = @(
    "diesel_cli-2.3.10",
    "diesel_derives-2.3.9",
    "diesel_migrations-2.3.2",
    "diesel_table_macro_syntax-0.3.0",
    "diesel-2.3.10",
    "libsqlite3-sys-0.31.0",
    "libsqlite3-sys-0.37.0",
    "mysqlclient-src-0.2.1+9.5.0",
    "mysqlclient-sys-0.5.2",
    "openssl-src-300.6.1+3.6.3",
    "openssl-sys-0.9.117",
    "pq-src-0.3.11+libpq-18.3",
    "pq-sys-0.7.5",
    "rusqlite-0.33.0"
)
foreach ($dir in $toRemove) {
    $full = Join-Path $registryPath $dir
    if (Test-Path $full) {
        Remove-Item $full -Recurse -Force
        Write-Host "✓ Removed registry src: $dir"
    }
}

# 3. Remove matching entries from registry CACHE (the .crate files)
$cacheBase = "D:\Programs\cargo\registry\cache\index.crates.io-1949cf8c6b5b557f"
$patterns = @("diesel*", "libsqlite3*", "mysqlclient*", "openssl-src*", "openssl-sys*", "pq-src*", "pq-sys*", "rusqlite*")
foreach ($pat in $patterns) {
    Get-ChildItem $cacheBase -Filter $pat -ErrorAction SilentlyContinue | ForEach-Object {
        Remove-Item $_.FullName -Force
        Write-Host "✓ Removed cache .crate: $($_.Name)"
    }
}

# 4. Remove D:\dev\mysqlclient-src-0.2.1+9.5.0 (leftover from failed bundled build)
if (Test-Path "D:\dev\mysqlclient-src-0.2.1+9.5.0") {
    Remove-Item "D:\dev\mysqlclient-src-0.2.1+9.5.0" -Recurse -Force
    Write-Host "✓ Removed D:\dev\mysqlclient-src-0.2.1+9.5.0"
}

# 5. Remove D:\dev\diesel_patch and all its build artifacts
if (Test-Path "D:\dev\diesel_patch") {
    Remove-Item "D:\dev\diesel_patch" -Recurse -Force
    Write-Host "✓ Removed D:\dev\diesel_patch"
}

# 6. Remove cargo package cache lock files
Remove-Item "D:\Programs\cargo\.package-cache" -Force -ErrorAction SilentlyContinue
Remove-Item "D:\Programs\cargo\.package-cache-mutate" -Force -ErrorAction SilentlyContinue
Write-Host "✓ Removed cargo lock files"

Write-Host "`n=== All done. Remaining registry size: ==="
$size = (Get-ChildItem "D:\Programs\cargo\registry" -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum / 1MB
Write-Host "D:\Programs\cargo\registry — $([math]::Round($size, 1)) MB"
