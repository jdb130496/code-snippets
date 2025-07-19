#!/bin/bash

#
#
##*************************************   CONTINUOUS BATTERY MONITOR  *******************************
#
#
# This script continuously monitors battery and alerts at 25% and 85% thresholds
# Runs in background until stopped with Ctrl+C
# Linux version for Sway WM with Waybar integration
# NOW WITH SINGLE INSTANCE PROTECTION AND REPEATING ALERTS!
#
# FEATURES:
# - Real-time battery monitoring
# - Popup alerts at 25% (plug in) and 85% (unplug)
# - REPEATING ALERTS every 2 minutes for critical conditions
# - Notifications using libnotify (notify-send)
# - Logs all activities with timestamps
# - Detects hibernation/sleep resume
# - Works on any Linux laptop with battery
# - Sway WM compatible
# - PREVENTS MULTIPLE INSTANCES from running
#

#
#
##*************************************   SINGLE INSTANCE PROTECTION  **************************
#
SCRIPT_NAME="battery-limiter"
PIDFILE="/tmp/${SCRIPT_NAME}.pid"
LOCKFILE="/tmp/${SCRIPT_NAME}.lock"

# Function to check if another instance is running
check_single_instance() {
    # Use flock for robust locking
    exec 200>"$LOCKFILE"
    
    if ! flock -n 200; then
        write_log "Another instance is already running. Exiting." "ERROR"
        echo "Battery monitor is already running. Use 'pkill -f battery-limiter.sh' to stop it."
        exit 1
    fi
    
    # Check if PID file exists and process is running
    if [ -f "$PIDFILE" ]; then
        local existing_pid=$(cat "$PIDFILE" 2>/dev/null)
        if [ -n "$existing_pid" ] && kill -0 "$existing_pid" 2>/dev/null; then
            write_log "Battery monitor already running with PID $existing_pid" "ERROR"
            echo "Battery monitor is already running with PID $existing_pid"
            echo "Use 'kill $existing_pid' or 'pkill -f battery-limiter.sh' to stop it."
            exit 1
        else
            write_log "Removing stale PID file" "INFO"
            rm -f "$PIDFILE"
        fi
    fi
    
    # Write current PID
    echo $$ > "$PIDFILE"
    write_log "Started with PID $$" "INFO"
}

# Function to cleanup on exit
cleanup_instance() {
    write_log "Cleaning up instance $$" "INFO"
    rm -f "$PIDFILE"
    rm -f "$LOCKFILE"
    
    local total_runtime_seconds=$(($(date +%s) - SCRIPT_START_TIME))
    local total_runtime_hours=$(echo "scale=2; $total_runtime_seconds / 3600" | bc -l 2>/dev/null || echo "0")
    write_log "=== BATTERY MONITOR STOPPED ===" "INFO"
    write_log "Total runtime: $total_runtime_hours hours" "INFO"
    exit 0
}

# Kill any existing instances (optional - comment out if you don't want this)
kill_existing_instances() {
    local current_pid=$$
    local existing_pids=$(pgrep -f "battery-limiter.sh" | grep -v "$current_pid")
    
    if [ -n "$existing_pids" ]; then
        write_log "Found existing instances, terminating them: $existing_pids" "WARN"
        echo "$existing_pids" | xargs -r kill -TERM 2>/dev/null
        sleep 2
        # Force kill if still running
        echo "$existing_pids" | xargs -r kill -KILL 2>/dev/null
    fi
}

#
#
##*************************************   SETTINGS SECTION  **************************
#
BATTERY_FLOOR=25      # Alert when battery drops to 25%
BATTERY_CEILING=85    # Alert when battery reaches 85%
CHECK_INTERVAL=30     # Check battery every 30 seconds
REPEAT_ALERT_INTERVAL=120    # Repeat critical alerts every 2 minutes (120 seconds)
INITIAL_ALERT_COOLDOWN=300   # Wait 5 minutes before first alert for same condition

# Alert preferences
PLAY_SOUND=true       # Play system sound with alerts
SHOW_VERBOSE_LOG=true # Show detailed logging info (set to true for debugging)
USE_NOTIFICATIONS=true # Use desktop notifications

# Hibernation detection settings
HIBERNATION_DETECTION_THRESHOLD=120  # If gap > 2 minutes, consider it hibernation/sleep

#
#
##*************************************   GLOBAL VARIABLES  **************************
#
LAST_FLOOR_ALERT=0
LAST_CEILING_ALERT=0
LAST_FLOOR_CONDITION_START=0      # When did we first detect floor condition
LAST_CEILING_CONDITION_START=0    # When did we first detect ceiling condition
FLOOR_CONDITION_ACTIVE=false      # Is floor condition currently active
CEILING_CONDITION_ACTIVE=false    # Is ceiling condition currently active
IS_RUNNING=true
LAST_CHECK_TIME=$(date +%s)
SCRIPT_START_TIME=$(date +%s)
PREVIOUS_PERCENTAGE=0
PREVIOUS_CHARGING_STATUS=""

# Battery path - auto-detect or default
BATTERY_PATH="/sys/class/power_supply/BAT0"
if [ ! -d "$BATTERY_PATH" ]; then
    BATTERY_PATH="/sys/class/power_supply/BAT1"
fi

# Colors for logging
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

#
#
##*************************************   FUNCTIONS  **************************
#

write_log() {
    local message="$1"
    local level="${2:-INFO}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local log_message="$timestamp [$level] - $message"
    
    # Color coding for different log levels
    case "$level" in
        "ERROR")
            echo -e "${RED}$log_message${NC}" >&2
            ;;
        "WARN")
            echo -e "${YELLOW}$log_message${NC}"
            ;;
        "ALERT")
            echo -e "${MAGENTA}$log_message${NC}"
            ;;
        "REPEAT")
            echo -e "${CYAN}$log_message${NC}"
            ;;
        "INFO")
            echo -e "${GREEN}$log_message${NC}"
            ;;
        "HIBERNATE")
            echo -e "${CYAN}$log_message${NC}"
            ;;
        *)
            echo "$log_message"
            ;;
    esac
    echo "$timestamp [$level] - $message" >> "$HOME/.battery-monitor.log"
}

play_alert_sound() {
    if [ "$PLAY_SOUND" = true ]; then
        # Try different sound players
        if command -v paplay >/dev/null 2>&1; then
            paplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null &
        elif command -v aplay >/dev/null 2>&1; then
            aplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null &
        elif command -v speaker-test >/dev/null 2>&1; then
            timeout 0.5 speaker-test -t sine -f 800 -l 1 2>/dev/null &
        else
            # Fallback: system bell
            echo -e "\a"
        fi
    fi
}

show_notification() {
    local message="$1"
    local title="$2"
    local urgency="${3:-normal}"
    local icon="${4:-dialog-information}"
    
    if [ "$USE_NOTIFICATIONS" = true ]; then
        # Play sound first
        play_alert_sound
        
        # Choose notification method based on urgency
        if [ "$urgency" = "critical" ]; then
            # For critical alerts, try modal dialog boxes first
            show_modal_dialog "$message" "$title" "$icon"
        else
            # For normal alerts, use desktop notifications
            if command -v notify-send >/dev/null 2>&1; then
                notify-send -u "$urgency" -i "$icon" -t 10000 "$title" "$message"
            else
                write_log "notify-send not found. Install libnotify-bin for notifications." "WARN"
                # Fallback to console
                echo -e "\n*** $title ***"
                echo -e "$message"
                echo "******************"
            fi
        fi
    fi
    
    write_log "Alert shown: $title" "ALERT"
}

show_modal_dialog() {
    local message="$1"
    local title="$2"
    local icon="${3:-dialog-information}"
    
    # Try different modal dialog options (most intrusive first)
    
    # Option 1: zenity (most Windows-like)
    if command -v zenity >/dev/null 2>&1; then
        zenity --info --title="$title" --text="$message" --width=400 2>/dev/null &
        return
    fi
    
    # Option 2: kdialog (for KDE users)
    if command -v kdialog >/dev/null 2>&1; then
        kdialog --msgbox "$message" --title "$title" 2>/dev/null &
        return
    fi
    
    # Option 3: swaynag (Sway-specific, blocking)
    if command -v swaynag >/dev/null 2>&1; then
        echo "$message" | swaynag -t warning -m "$title" -B "OK" "true" &
        return
    fi
    
    # Option 4: yad (Yet Another Dialog)
    if command -v yad >/dev/null 2>&1; then
        yad --info --title="$title" --text="$message" --width=400 --center 2>/dev/null &
        return
    fi
    
    # Fallback: desktop notification
    if command -v notify-send >/dev/null 2>&1; then
        notify-send -u "critical" -i "$icon" -t 0 "$title" "$message"
    else
        # Last resort: console + beep
        echo -e "\n*** CRITICAL ALERT: $title ***"
        echo -e "$message"
        echo "********************************"
        echo -e "\a\a\a"  # Triple beep
    fi
}

test_hibernation_resume() {
    local last_check=$1
    local current_check=$2
    local time_difference=$((current_check - last_check))
    
    # Debug: Log time gaps for troubleshooting
    if [ $time_difference -gt $((CHECK_INTERVAL + 10)) ]; then
        write_log "Time gap detected: ${time_difference} seconds (threshold: $HIBERNATION_DETECTION_THRESHOLD seconds)" "INFO"
    fi
    
    if [ $time_difference -gt $HIBERNATION_DETECTION_THRESHOLD ]; then
        local hibernation_duration=$(echo "scale=1; $time_difference / 60" | bc -l 2>/dev/null || echo "$((time_difference / 60))")
        write_log "HIBERNATION/SLEEP DETECTED! System was suspended for $hibernation_duration minutes" "HIBERNATE"
        write_log "Last check: $(date -d @$last_check '+%Y-%m-%d %H:%M:%S')" "HIBERNATE"
        write_log "Current check: $(date -d @$current_check '+%Y-%m-%d %H:%M:%S')" "HIBERNATE"
        write_log "Script continued running after hibernation resume!" "HIBERNATE"
        
        # Optional: Show popup notification
        local message="🔄 HIBERNATION DETECTED!\n\nSystem was suspended for $hibernation_duration minutes.\n\nBattery monitor script continued running successfully!"
        show_notification "$message" "Script Resumed from Hibernation" "normal" "dialog-information"
        
        return 0
    fi
    
    return 1
}

get_system_uptime() {
    if [ -f /proc/uptime ]; then
        local uptime_seconds=$(cut -d. -f1 /proc/uptime)
        local uptime_hours=$(echo "scale=1; $uptime_seconds / 3600" | bc -l 2>/dev/null || echo "$((uptime_seconds / 3600))")
        echo "$uptime_hours"
    else
        echo "unknown"
    fi
}

get_battery_info() {
    if [ ! -d "$BATTERY_PATH" ]; then
        write_log "No battery found at $BATTERY_PATH - running on desktop?" "ERROR"
        return 1
    fi
    
    local capacity_file="$BATTERY_PATH/capacity"
    local status_file="$BATTERY_PATH/status"
    
    if [ ! -f "$capacity_file" ] || [ ! -f "$status_file" ]; then
        write_log "Battery files not found in $BATTERY_PATH" "ERROR"
        return 1
    fi
    
    local percentage=$(cat "$capacity_file" 2>/dev/null || echo "0")
    local status=$(cat "$status_file" 2>/dev/null || echo "Unknown")
    
    # Validate percentage is a number
    if ! [[ "$percentage" =~ ^[0-9]+$ ]]; then
        write_log "Invalid battery percentage: $percentage" "ERROR"
        return 1
    fi
    
    # Determine if charging - be more strict about charging detection
    local is_charging=false
    case "$status" in
        "Charging")
            is_charging=true
            ;;
        "Full")
            is_charging=true
            ;;
        "Discharging"|"Not charging"|"Unknown")
            is_charging=false
            ;;
        *)
            is_charging=false
            ;;
    esac
    
    # Export variables for use in calling function
    BATTERY_PERCENTAGE=$percentage
    BATTERY_IS_CHARGING=$is_charging
    BATTERY_STATUS=$status
    
    return 0
}

# NEW: Enhanced alert logic with repeating alerts
should_show_alert() {
    local alert_type="$1"
    local current_time=$(date +%s)
    local should_alert=false
    local alert_reason=""
    
    case "$alert_type" in
        "floor_critical")
            if [ "$FLOOR_CONDITION_ACTIVE" = false ]; then
                # First time detecting floor condition
                FLOOR_CONDITION_ACTIVE=true
                LAST_FLOOR_CONDITION_START=$current_time
                LAST_FLOOR_ALERT=$current_time
                should_alert=true
                alert_reason="First floor alert"
            else
                # Floor condition is ongoing - check if we should repeat
                local time_since_last_alert=$((current_time - LAST_FLOOR_ALERT))
                if [ $time_since_last_alert -ge $REPEAT_ALERT_INTERVAL ]; then
                    LAST_FLOOR_ALERT=$current_time
                    should_alert=true
                    alert_reason="Repeated floor alert (${time_since_last_alert}s since last)"
                fi
            fi
            ;;
        "ceiling_critical")
            if [ "$CEILING_CONDITION_ACTIVE" = false ]; then
                # First time detecting ceiling condition
                CEILING_CONDITION_ACTIVE=true
                LAST_CEILING_CONDITION_START=$current_time
                LAST_CEILING_ALERT=$current_time
                should_alert=true
                alert_reason="First ceiling alert"
            else
                # Ceiling condition is ongoing - check if we should repeat
                local time_since_last_alert=$((current_time - LAST_CEILING_ALERT))
                if [ $time_since_last_alert -ge $REPEAT_ALERT_INTERVAL ]; then
                    LAST_CEILING_ALERT=$current_time
                    should_alert=true
                    alert_reason="Repeated ceiling alert (${time_since_last_alert}s since last)"
                fi
            fi
            ;;
        "floor_info"|"ceiling_info")
            # For info messages, use original cooldown logic
            local last_alert_time
            if [ "$alert_type" = "floor_info" ]; then
                last_alert_time=$LAST_FLOOR_ALERT
            else
                last_alert_time=$LAST_CEILING_ALERT
            fi
            
            local time_since_last_alert=$((current_time - last_alert_time))
            if [ $time_since_last_alert -gt $INITIAL_ALERT_COOLDOWN ]; then
                should_alert=true
                alert_reason="Info alert (${time_since_last_alert}s since last)"
            fi
            ;;
    esac
    
    if [ "$should_alert" = true ]; then
        write_log "Alert decision: $alert_reason" "INFO"
        return 0
    else
        return 1
    fi
}

# NEW: Function to clear condition flags when battery moves to safe range
clear_condition_flags() {
    local percentage=$1
    local is_charging=$2
    local current_time=$(date +%s)
    
    # Clear floor condition if battery is above floor OR now charging
    if [ "$FLOOR_CONDITION_ACTIVE" = true ]; then
        if [ "$percentage" -gt $BATTERY_FLOOR ] || [ "$is_charging" = true ]; then
            local condition_duration=$((current_time - LAST_FLOOR_CONDITION_START))
            write_log "Floor condition cleared after ${condition_duration} seconds" "INFO"
            FLOOR_CONDITION_ACTIVE=false
            LAST_FLOOR_CONDITION_START=0
        fi
    fi
    
    # Clear ceiling condition if battery is below ceiling OR now discharging
    if [ "$CEILING_CONDITION_ACTIVE" = true ]; then
        if [ "$percentage" -lt $BATTERY_CEILING ] || [ "$is_charging" = false ]; then
            local condition_duration=$((current_time - LAST_CEILING_CONDITION_START))
            write_log "Ceiling condition cleared after ${condition_duration} seconds" "INFO"
            CEILING_CONDITION_ACTIVE=false
            LAST_CEILING_CONDITION_START=0
        fi
    fi
}

#
#
##*************************************   MAIN SCRIPT EXECUTION  **************************
#

# Handle Ctrl+C and termination signals gracefully
trap cleanup_instance SIGINT SIGTERM

# FIRST: Check for single instance before doing anything else
check_single_instance

# OPTIONAL: Kill existing instances (comment out if you don't want this)
# kill_existing_instances

write_log "=== CONTINUOUS BATTERY MONITOR STARTED ===" "INFO"
write_log "PID: $$ | Single instance protection: ENABLED" "INFO"
write_log "Monitoring battery: Floor=${BATTERY_FLOOR}%, Ceiling=${BATTERY_CEILING}%" "INFO"
write_log "Check interval: $CHECK_INTERVAL seconds" "INFO"
write_log "Repeat alert interval: $REPEAT_ALERT_INTERVAL seconds ($(($REPEAT_ALERT_INTERVAL / 60)) minutes)" "INFO"
write_log "Initial alert cooldown: $INITIAL_ALERT_COOLDOWN seconds" "INFO"
write_log "Hibernation detection threshold: $HIBERNATION_DETECTION_THRESHOLD seconds" "INFO"
write_log "Using notifications: $USE_NOTIFICATIONS" "INFO"
write_log "Battery path: $BATTERY_PATH" "INFO"
write_log "Lock file: $LOCKFILE | PID file: $PIDFILE" "INFO"
write_log "Press Ctrl+C to stop monitoring" "INFO"

# Get system uptime for reference
system_uptime=$(get_system_uptime)
write_log "System uptime: $system_uptime hours" "INFO"

write_log "=======================================" "INFO"

# Test the alert system
write_log "Testing alert system..." "INFO"
show_notification "🔋 Battery monitor is now running!\n\nAlerts will repeat every $(($REPEAT_ALERT_INTERVAL / 60)) minutes for critical conditions.\n\nThis is a test to confirm the system is working.\n\nPID: $$" "BATTERY MONITOR STARTED" "normal" "dialog-information"

# Main monitoring loop
while [ "$IS_RUNNING" = true ]; do
    current_time=$(date +%s)
    
    # Check for hibernation/sleep resume
    if [ $LAST_CHECK_TIME -ne $SCRIPT_START_TIME ]; then  # Skip first iteration
        if test_hibernation_resume $LAST_CHECK_TIME $current_time; then
            # Reset alert timers after hibernation to prevent immediate spam
            # But allow alerts if battery levels are critical
            time_since_start=$(((current_time - SCRIPT_START_TIME) / 60))
            if [ $time_since_start -gt 10 ]; then  # Only reset if script has been running for a while
                write_log "Resetting alert cooldowns after hibernation" "INFO"
                # Don't completely reset - just reduce the cooldown effect
                LAST_FLOOR_ALERT=$((current_time - REPEAT_ALERT_INTERVAL / 2))
                LAST_CEILING_ALERT=$((current_time - REPEAT_ALERT_INTERVAL / 2))
            fi
        fi
    fi
    
    if get_battery_info; then
        percentage=$BATTERY_PERCENTAGE
        is_charging=$BATTERY_IS_CHARGING
        status=$BATTERY_STATUS
        charging_status=""
        
        if [ "$is_charging" = true ]; then
            charging_status="CHARGING"
        else
            charging_status="ON BATTERY"
        fi
        
        # Clear condition flags if battery is no longer in critical range
        clear_condition_flags $percentage $is_charging
        
        # Log status changes and regular updates
        if [ "$SHOW_VERBOSE_LOG" = true ] || [ "$percentage" != "$PREVIOUS_PERCENTAGE" ] || [ "$charging_status" != "$PREVIOUS_CHARGING_STATUS" ]; then
            local condition_info=""
            if [ "$FLOOR_CONDITION_ACTIVE" = true ]; then
                condition_info="$condition_info [FLOOR_ACTIVE]"
            fi
            if [ "$CEILING_CONDITION_ACTIVE" = true ]; then
                condition_info="$condition_info [CEILING_ACTIVE]"
            fi
            write_log "Battery: ${percentage}% | $charging_status | Status: $status$condition_info" "INFO"
            PREVIOUS_PERCENTAGE=$percentage
            PREVIOUS_CHARGING_STATUS=$charging_status
        fi
        
        # Check for ceiling breach (85%)
        if [ -n "$percentage" ] && [ "$percentage" -ge $BATTERY_CEILING ]; then
            if [ "$is_charging" = true ]; then
                # Critical: Charging above 85%
                if should_show_alert "ceiling_critical"; then
                    local condition_duration=0
                    if [ "$CEILING_CONDITION_ACTIVE" = true ] && [ $LAST_CEILING_CONDITION_START -gt 0 ]; then
                        condition_duration=$(((current_time - LAST_CEILING_CONDITION_START) / 60))
                    fi
                    
                    local repeat_info=""
                    if [ $condition_duration -gt 0 ]; then
                        repeat_info="\n\n⏰ Condition has been active for $condition_duration minutes"
                    fi
                    
                    write_log "CEILING BREACH: ${percentage}% while charging - showing alert" "ALERT"
                    show_notification "🔋 BATTERY AT ${percentage}%!\n\n⚠️ UNPLUG CHARGER NOW ⚠️\n\nContinuous charging above 85% can reduce battery lifespan.\n\nRecommended: Use laptop on battery until it drops to ${BATTERY_FLOOR}%.$repeat_info" "BATTERY CEILING REACHED" "critical" "dialog-warning"
                fi
            else
                # Info: Above 85% but not charging
                if should_show_alert "ceiling_info"; then
                    write_log "CEILING INFO: ${percentage}% while on battery" "INFO"
                    show_notification "ℹ️ Battery at ${percentage}% (above recommended 85% limit)\n\nConsider using laptop on battery to reduce level for optimal battery health." "BATTERY LEVEL INFO" "normal" "dialog-information"
                    LAST_CEILING_ALERT=$current_time
                fi
            fi
        fi
        
        # Check for floor breach (25%)
        if [ -n "$percentage" ] && [ "$percentage" -le $BATTERY_FLOOR ]; then
            if [ "$is_charging" = false ]; then
                # Critical: Below floor and NOT charging
                if should_show_alert "floor_critical"; then
                    local condition_duration=0
                    if [ "$FLOOR_CONDITION_ACTIVE" = true ] && [ $LAST_FLOOR_CONDITION_START -gt 0 ]; then
                        condition_duration=$(((current_time - LAST_FLOOR_CONDITION_START) / 60))
                    fi
                    
                    local repeat_info=""
                    if [ $condition_duration -gt 0 ]; then
                        repeat_info="\n\n⏰ Condition has been active for $condition_duration minutes"
                    fi
                    
                    write_log "FLOOR BREACH: ${percentage}% while on battery - showing alert" "ALERT"
                    show_notification "🔋 BATTERY AT ${percentage}%!\n\n🔌 PLUG IN CHARGER NOW 🔌\n\nBattery is at minimum recommended level.\n\nRemember to unplug when it reaches ${BATTERY_CEILING}%.$repeat_info" "LOW BATTERY WARNING" "critical" "dialog-warning"
                fi
            else
                # Info: Below floor but charging (good!)
                if should_show_alert "floor_info"; then
                    write_log "FLOOR INFO: ${percentage}% while charging - Good!" "INFO"
                    LAST_FLOOR_ALERT=$current_time
                fi
            fi
        fi
    else
        write_log "Failed to get battery information" "ERROR"
    fi
    
    # Update last check time for hibernation detection
    LAST_CHECK_TIME=$current_time
    
    # Wait before next check
    sleep $CHECK_INTERVAL
done
