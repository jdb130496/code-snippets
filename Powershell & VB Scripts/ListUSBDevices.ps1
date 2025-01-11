# Get all USB devices
$usbDevices = Get-WmiObject -Query "Select * From Win32_USBControllerDevice" | ForEach-Object {
    $device = $_.Dependent -replace '"', ''
    $deviceID = $device.Split('=')[1]
    Get-WmiObject -Query "Select * From Win32_PnPEntity Where DeviceID = '$deviceID'"
}

# Display information about each USB device
foreach ($device in $usbDevices) {
    Write-Output "Description: $($device.Description)"
    Write-Output "DeviceID: $($device.DeviceID)"
    Write-Output "-----------------------------------"
}
