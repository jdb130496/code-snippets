for ($i=0; $i -lt 10000; $i++) {
    Start-Process -FilePath msedge -ArgumentList '--new-window www.google.com'
    Start-Sleep -Seconds 5
    Stop-Process -Name msedge
}
