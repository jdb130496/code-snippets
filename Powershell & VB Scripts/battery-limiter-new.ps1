#
#
##*************************************   CONTINUOUS BATTERY MONITOR  *******************************
#
#
# This script continuously monitors battery and alerts at 25% and 85% thresholds
# Runs in background until stopped with Ctrl+C
# NOW WITH WORKING TOPMOST ALERTS!
#
# FEATURES:
# - Real-time battery monitoring
# - Popup alerts at 25% (plug in) and 85% (unplug)
# - ALERTS APPEAR ON TOP OF ALL WINDOWS (FIXED!)
# - Prevents spam alerts with cooldown periods
# - Logs all activities with timestamps
# - Detects hibernation/sleep resume
# - Works on any Windows laptop
#

#
#
##*************************************   SETTINGS SECTION  **************************
#
$batteryFloor = 25      # Alert when battery drops to 25%
$batteryCeiling = 85    # Alert when battery reaches 85%
$checkInterval = 30     # Check battery every 30 seconds
$alertCooldown = 300    # Wait 5 minutes before showing same alert again

# Alert preferences
$playSound = $true      # Play system sound with alerts
$showVerboseLog = $false # Show detailed logging info (set to false to reduce power)
$useToastNotifications = $false  # Disabled - using reliable topmost popups instead

# Hibernation detection settings
$hibernationDetectionThreshold = 120  # If gap > 2 minutes, consider it hibernation/sleep

#
#
##*************************************   GLOBAL VARIABLES  **************************
#
$lastFloorAlert = [DateTime]::MinValue
$lastCeilingAlert = [DateTime]::MinValue
$isRunning = $true
$lastCheckTime = Get-Date
$scriptStartTime = Get-Date

# Status codes for better understanding
$availabilityTranslator = @{
    1 = "Other"; 2 = "Unknown"; 3 = "Running/Full Power"; 4 = "Warning"
    5 = "In Test"; 6 = "Not Applicable"; 7 = "Power Off"; 8 = "Off Line"
}

$statusTranslator = @{
    1 = "Other"; 2 = "Unknown"; 3 = "Fully Charged"; 4 = "Low"; 5 = "Critical"
    6 = "Charging"; 7 = "Charging High"; 8 = "Charging Low"; 9 = "Charging Critical"
    10 = "Undefined"; 11 = "Partially Charged"
}

#
#
##*************************************   FUNCTIONS  **************************
#

# Add required assemblies
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "$timestamp [$Level] - $Message"
    
    # Color coding for different log levels
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN"  { Write-Host $logMessage -ForegroundColor Yellow }
        "ALERT" { Write-Host $logMessage -ForegroundColor Magenta }
        "INFO"  { Write-Host $logMessage -ForegroundColor Green }
        "HIBERNATE" { Write-Host $logMessage -ForegroundColor Cyan }
        default { Write-Host $logMessage }
    }
}

function Show-TopMostAlert {
    param(
        [string]$Message,
        [string]$Title,
        [int]$Icon = 48,
        [int]$Timeout = 0
    )
    
    try {
        # Play sound
        if ($playSound) {
            [System.Media.SystemSounds]::Exclamation.Play()
        }
        
        # Create invisible topmost form as parent
        $form = New-Object System.Windows.Forms.Form
        $form.TopMost = $true
        $form.WindowState = 'Minimized'
        $form.ShowInTaskbar = $false
        $form.Visible = $false
        
        # Convert icon number to MessageBoxIcon enum
        $iconType = switch($Icon) {
            16 { 'Stop' }
            48 { 'Exclamation' }
            64 { 'Information' }
            default { 'Exclamation' }
        }
        
        # Show message box with topmost parent
        $result = [System.Windows.Forms.MessageBox]::Show($form, $Message, $Title, 'OK', $iconType)
        
        # Clean up
        $form.Dispose()
        
        Write-Log "Alert shown (TopMost): $Title" "ALERT"
        
    }
    catch {
        Write-Log "Alert failed: $($_.Exception.Message)" "ERROR"
        
        # Fallback - multiple beeps and console message
        1..3 | ForEach-Object { 
            [Console]::Beep(800, 200)
            Start-Sleep -Milliseconds 100
        }
        
        Write-Host "`n*** BATTERY ALERT ***" -ForegroundColor Red -BackgroundColor Yellow
        Write-Host "$Title" -ForegroundColor Yellow
        Write-Host "$Message" -ForegroundColor White
        Write-Host "********************" -ForegroundColor Red -BackgroundColor Yellow
    }
}

function Test-HibernationResume {
    param(
        [DateTime]$LastCheck,
        [DateTime]$CurrentCheck
    )
    
    $timeDifference = ($CurrentCheck - $LastCheck).TotalSeconds
    
    # Debug: Log time gaps for troubleshooting
    if ($timeDifference -gt ($checkInterval + 10)) {  # More than expected interval + 10 seconds
        $gapDuration = [math]::Round($timeDifference, 1)
        Write-Log "Time gap detected: $gapDuration seconds (threshold: $hibernationDetectionThreshold seconds)" "INFO"
    }
    
    if ($timeDifference -gt $hibernationDetectionThreshold) {
        $hibernationDuration = [math]::Round($timeDifference / 60, 1)
        Write-Log "HIBERNATION/SLEEP DETECTED! System was suspended for $hibernationDuration minutes" "HIBERNATE"
        Write-Log "Last check: $($LastCheck.ToString('yyyy-MM-dd HH:mm:ss'))" "HIBERNATE"
        Write-Log "Current check: $($CurrentCheck.ToString('yyyy-MM-dd HH:mm:ss'))" "HIBERNATE"
        Write-Log "Script continued running after hibernation resume!" "HIBERNATE"
        
        # Optional: Show popup notification
        try {
            $message = "🔄 HIBERNATION DETECTED!`n`nSystem was suspended for $hibernationDuration minutes.`n`nBattery monitor script continued running successfully!"
            Show-TopMostAlert -Message $message -Title "Script Resumed from Hibernation" -Icon 64 -Timeout 5
        }
        catch {
            Write-Log "Could not show hibernation popup: $($_.Exception.Message)" "WARN"
        }
        
        return $true
    }
    
    return $false
}

function Get-SystemUptime {
    try {
        $uptime = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
        $uptimeSpan = (Get-Date) - $uptime
        return $uptimeSpan
    }
    catch {
        return $null
    }
}

function Get-BatteryInfo {
    try {
        $battery = Get-WmiObject Win32_Battery | Select-Object -First 1
        
        if (-not $battery) {
            Write-Log "No battery found - running on desktop?" "ERROR"
            return $null
        }
        
        $batteryInfo = @{
            Percentage = [int]$battery.EstimatedChargeRemaining
            IsCharging = $false
            Status = $battery.BatteryStatus
            Availability = $battery.Availability
            StatusText = $statusTranslator[[int]$battery.BatteryStatus]
            AvailabilityText = $availabilityTranslator[[int]$battery.Availability]
        }
        
        # Determine if charging (different laptops report differently)
        if ($battery.BatteryStatus -eq 2 -or $battery.BatteryStatus -eq 6 -or $battery.BatteryStatus -eq 7) {
            $batteryInfo.IsCharging = $true
        }
        
        return $batteryInfo
    }
    catch {
        Write-Log "Error getting battery info: $($_.Exception.Message)" "ERROR"
        return $null
    }
}

function Should-ShowAlert {
    param(
        [string]$AlertType,
        [DateTime]$LastAlert
    )
    
    $timeSinceLastAlert = (Get-Date) - $LastAlert
    return $timeSinceLastAlert.TotalSeconds -gt $alertCooldown
}

#
#
##*************************************   MAIN MONITORING LOOP  **************************
#
Write-Log "=== CONTINUOUS BATTERY MONITOR STARTED ===" "INFO"
Write-Log "Monitoring battery: Floor=$batteryFloor%, Ceiling=$batteryCeiling%" "INFO"
Write-Log "Check interval: $checkInterval seconds, Alert cooldown: $alertCooldown seconds" "INFO"
Write-Log "Hibernation detection threshold: $hibernationDetectionThreshold seconds" "INFO"
Write-Log "Using TopMost alerts (Toast notifications disabled)" "INFO"
Write-Log "Press Ctrl+C to stop monitoring" "INFO"

# Get system uptime for reference
$systemUptime = Get-SystemUptime
if ($systemUptime) {
    Write-Log "System uptime: $([math]::Round($systemUptime.TotalHours, 1)) hours" "INFO"
}

Write-Log "=======================================" "INFO"

# Test the alert system
Write-Log "Testing alert system..." "INFO"
Show-TopMostAlert -Message "🔋 Battery monitor is now running!`n`nAlerts will appear on top of all windows.`n`nThis is a test to confirm the system is working." -Title "BATTERY MONITOR STARTED" -Icon 64

# Handle Ctrl+C gracefully
try {
    while ($isRunning) {
        $currentTime = Get-Date
        
        # Check for hibernation/sleep resume
        if ($lastCheckTime -ne $scriptStartTime) {  # Skip first iteration
            $hibernationDetected = Test-HibernationResume -LastCheck $lastCheckTime -CurrentCheck $currentTime
            
            if ($hibernationDetected) {
                # Reset alert timers after hibernation to prevent immediate spam
                # But allow alerts if battery levels are critical
                $timeSinceStart = ($currentTime - $scriptStartTime).TotalMinutes
                if ($timeSinceStart -gt 10) {  # Only reset if script has been running for a while
                    Write-Log "Resetting alert cooldowns after hibernation" "INFO"
                    # Don't completely reset - just reduce the cooldown effect
                    $lastFloorAlert = $currentTime.AddSeconds(-($alertCooldown / 2))
                    $lastCeilingAlert = $currentTime.AddSeconds(-($alertCooldown / 2))
                }
            }
        }
        
        $batteryInfo = Get-BatteryInfo
        
        if ($batteryInfo) {
            $percentage = $batteryInfo.Percentage
            $isCharging = $batteryInfo.IsCharging
            $chargingStatus = if ($isCharging) { "CHARGING" } else { "ON BATTERY" }
            
            if ($showVerboseLog) {
                Write-Log "Battery: $percentage% | $chargingStatus | Status: $($batteryInfo.StatusText)" "INFO"
            }
            
            # Check for ceiling breach (85%)
            if ($percentage -ge $batteryCeiling) {
                if ($isCharging) {
                    # Critical: Charging above 85%
                    if (Should-ShowAlert "ceiling" $lastCeilingAlert) {
                        Show-TopMostAlert -Message "🔋 BATTERY AT $percentage%!`n`n⚠️ UNPLUG CHARGER NOW ⚠️`n`nContinuous charging above 85% can reduce battery lifespan.`n`nRecommended: Use laptop on battery until it drops to 25%." -Title "BATTERY CEILING REACHED" -Icon 48
                        $lastCeilingAlert = $currentTime
                    }
                } else {
                    # Info: Above 85% but not charging
                    if (Should-ShowAlert "ceiling_info" $lastCeilingAlert) {
                        Show-TopMostAlert -Message "ℹ️ Battery at $percentage% (above recommended 85% limit)`n`nConsider using laptop on battery to reduce level for optimal battery health." -Title "BATTERY LEVEL INFO" -Icon 64
                        $lastCeilingAlert = $currentTime
                    }
                }
            }
            
            # Check for floor breach (25%)
            if ($percentage -le $batteryFloor) {
                if (-not $isCharging) {
                    # Critical: Below 25% and not charging
                    if (Should-ShowAlert "floor" $lastFloorAlert) {
                        Show-TopMostAlert -Message "🔋 BATTERY AT $percentage%!`n`n🔌 PLUG IN CHARGER NOW 🔌`n`nBattery is at minimum recommended level.`n`nRemember to unplug when it reaches 85%." -Title "LOW BATTERY WARNING" -Icon 48
                        $lastFloorAlert = $currentTime
                    }
                } else {
                    # Info: Below 25% but charging
                    if (Should-ShowAlert "floor_info" $lastFloorAlert) {
                        Write-Log "Battery at $percentage% and charging - Good!" "INFO"
                        $lastFloorAlert = $currentTime
                    }
                }
            }
        }
        
        # Update last check time for hibernation detection
        $lastCheckTime = $currentTime
        
        # Wait before next check
        Start-Sleep -Seconds $checkInterval
    }
}
catch {
    if ($_.Exception.Message -like "*interrupted*" -or $_.Exception.Message -like "*Ctrl+C*") {
        Write-Log "Monitor stopped by user (Ctrl+C)" "INFO"
    } else {
        Write-Log "Unexpected error: $($_.Exception.Message)" "ERROR"
    }
}
finally {
    $totalRuntime = ((Get-Date) - $scriptStartTime).TotalHours
    Write-Log "=== BATTERY MONITOR STOPPED ===" "INFO"
    Write-Log "Total runtime: $([math]::Round($totalRuntime, 2)) hours" "INFO"
}
