#!/bin/bash

# Battery Monitor Management Script
# This script helps you start, stop, and check the status of your battery monitor

SCRIPT_NAME="battery-limiter"
SCRIPT_PATH="$HOME/battery-limiter.sh"
PIDFILE="/tmp/${SCRIPT_NAME}.pid"
LOCKFILE="/tmp/${SCRIPT_NAME}.lock"
LOGFILE="$HOME/.battery-monitor.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

show_help() {
    echo "Battery Monitor Management Script"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start     - Start the battery monitor"
    echo "  stop      - Stop the battery monitor"
    echo "  restart   - Restart the battery monitor"
    echo "  status    - Show current status"
    echo "  log       - Show recent log entries"
    echo "  tail      - Follow log in real-time"
    echo "  clean     - Clean up old files and processes"
    echo "  debug     - Run battery monitor in foreground for debugging"
    echo "  test      - Test battery monitor startup"
    echo "  help      - Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start"
    echo "  $0 status"
    echo "  $0 debug"
}

check_script_exists() {
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo -e "${RED}Error: Battery monitor script not found at $SCRIPT_PATH${NC}"
        echo "Please make sure the script exists and is executable."
        exit 1
    fi
}

get_running_pids() {
    pgrep -f "battery-limiter.sh" 2>/dev/null | tr '\n' ' '
}

is_running() {
    local pids=$(get_running_pids)
    [ -n "$pids" ]
}

start_monitor() {
    check_script_exists
    
    if is_running; then
        echo -e "${YELLOW}Battery monitor is already running.${NC}"
        show_status
        return 1
    fi
    
    echo -e "${BLUE}Starting battery monitor...${NC}"
    
    # Make sure script is executable
    chmod +x "$SCRIPT_PATH"
    
    # Create a temporary log file to capture startup errors
    local temp_log="/tmp/battery-monitor-startup.log"
    
    # Start the script in background and capture output
    echo "Starting battery monitor at $(date)" > "$temp_log"
    echo "Script path: $SCRIPT_PATH" >> "$temp_log"
    echo "Current directory: $(pwd)" >> "$temp_log"
    echo "Script exists: $([ -f "$SCRIPT_PATH" ] && echo "YES" || echo "NO")" >> "$temp_log"
    echo "Script executable: $([ -x "$SCRIPT_PATH" ] && echo "YES" || echo "NO")" >> "$temp_log"
    echo "----------------------------------------" >> "$temp_log"
    
    # Try to start the script and capture both stdout and stderr
    nohup "$SCRIPT_PATH" >> "$temp_log" 2>&1 &
    local start_pid=$!
    
    echo "Started with PID: $start_pid" >> "$temp_log"
    
    # Give it a moment to start
    sleep 3
    
    if is_running; then
        echo -e "${GREEN}Battery monitor started successfully!${NC}"
        show_status
        rm -f "$temp_log"  # Clean up temp log on success
    else
        echo -e "${RED}Failed to start battery monitor.${NC}"
        echo -e "${RED}Startup log:${NC}"
        cat "$temp_log"
        echo ""
        echo -e "${RED}Main log file:${NC}"
        if [ -f "$LOGFILE" ]; then
            tail -n 10 "$LOGFILE"
        else
            echo "No main log file found at $LOGFILE"
        fi
        return 1
    fi
}

stop_monitor() {
    if ! is_running; then
        echo -e "${YELLOW}Battery monitor is not running.${NC}"
        return 1
    fi
    
    echo -e "${BLUE}Stopping battery monitor...${NC}"
    
    # Get PIDs before killing
    local pids=$(get_running_pids)
    
    # Try graceful shutdown first
    pkill -TERM -f "battery-limiter.sh" 2>/dev/null
    
    # Wait a moment
    sleep 2
    
    # Force kill if still running
    if is_running; then
        echo -e "${YELLOW}Forcing shutdown...${NC}"
        pkill -KILL -f "battery-limiter.sh" 2>/dev/null
        sleep 1
    fi
    
    # Clean up files
    rm -f "$PIDFILE" "$LOCKFILE" 2>/dev/null
    
    if is_running; then
        echo -e "${RED}Failed to stop battery monitor.${NC}"
        return 1
    else
        echo -e "${GREEN}Battery monitor stopped successfully.${NC}"
        echo "Previous PIDs: $pids"
    fi
}

restart_monitor() {
    echo -e "${BLUE}Restarting battery monitor...${NC}"
    stop_monitor
    sleep 1
    start_monitor
}

show_status() {
    echo -e "${BLUE}=== Battery Monitor Status ===${NC}"
    
    if is_running; then
        local pids=$(get_running_pids)
        echo -e "${GREEN}Status: RUNNING${NC}"
        echo -e "PIDs: $pids"
        
        if [ -f "$PIDFILE" ]; then
            local pid_file_content=$(cat "$PIDFILE" 2>/dev/null)
            echo -e "PID file: $pid_file_content"
        fi
        
        # Show process details
        echo -e "\nProcess details:"
        ps aux | grep "battery-limiter.sh" | grep -v grep
        
    else
        echo -e "${RED}Status: NOT RUNNING${NC}"
    fi
    
    # File status
    echo -e "\nFile status:"
    echo -e "Script: ${SCRIPT_PATH} $([ -f "$SCRIPT_PATH" ] && echo -e "${GREEN}EXISTS${NC}" || echo -e "${RED}MISSING${NC}")"
    echo -e "PID file: ${PIDFILE} $([ -f "$PIDFILE" ] && echo -e "${GREEN}EXISTS${NC}" || echo -e "${YELLOW}MISSING${NC}")"
    echo -e "Lock file: ${LOCKFILE} $([ -f "$LOCKFILE" ] && echo -e "${GREEN}EXISTS${NC}" || echo -e "${YELLOW}MISSING${NC}")"
    echo -e "Log file: ${LOGFILE} $([ -f "$LOGFILE" ] && echo -e "${GREEN}EXISTS${NC}" || echo -e "${YELLOW}MISSING${NC}")"
    
    # Show recent battery status if available
    if [ -f "$LOGFILE" ]; then
        echo -e "\nRecent activity:"
        tail -n 3 "$LOGFILE" 2>/dev/null | head -n 3
    fi
}

show_log() {
    if [ ! -f "$LOGFILE" ]; then
        echo -e "${YELLOW}No log file found at $LOGFILE${NC}"
        return 1
    fi
    
    echo -e "${BLUE}=== Recent Battery Monitor Log ===${NC}"
    tail -n 20 "$LOGFILE"
}

tail_log() {
    if [ ! -f "$LOGFILE" ]; then
        echo -e "${YELLOW}No log file found at $LOGFILE${NC}"
        echo "Starting monitor first might create the log file."
        return 1
    fi
    
    echo -e "${BLUE}Following battery monitor log (Ctrl+C to stop)...${NC}"
    tail -f "$LOGFILE"
}

debug_monitor() {
    check_script_exists
    
    if is_running; then
        echo -e "${YELLOW}Battery monitor is already running. Stopping it first...${NC}"
        stop_monitor
        sleep 1
    fi
    
    echo -e "${BLUE}Running battery monitor in debug mode (foreground)...${NC}"
    echo -e "${YELLOW}This will show all output directly. Press Ctrl+C to stop.${NC}"
    echo ""
    
    # Make sure script is executable
    chmod +x "$SCRIPT_PATH"
    
    # Run in foreground to see all output
    exec "$SCRIPT_PATH"
}

test_monitor() {
    check_script_exists
    
    echo -e "${BLUE}Testing battery monitor startup...${NC}"
    
    # Check prerequisites
    echo "Checking prerequisites..."
    echo "- Script path: $SCRIPT_PATH $([ -f "$SCRIPT_PATH" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
    echo "- Script executable: $([ -x "$SCRIPT_PATH" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
    echo "- Battery path: /sys/class/power_supply/BAT0 $([ -d "/sys/class/power_supply/BAT0" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
    echo "- Battery path: /sys/class/power_supply/BAT1 $([ -d "/sys/class/power_supply/BAT1" ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
    echo "- notify-send available: $(command -v notify-send >/dev/null && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}")"
    
    # Test battery reading
    echo ""
    echo "Testing battery reading..."
    for bat in /sys/class/power_supply/BAT*; do
        if [ -d "$bat" ]; then
            echo "Found battery: $bat"
            if [ -f "$bat/capacity" ]; then
                local cap=$(cat "$bat/capacity" 2>/dev/null)
                echo "  Capacity: $cap%"
            fi
            if [ -f "$bat/status" ]; then
                local status=$(cat "$bat/status" 2>/dev/null)
                echo "  Status: $status"
            fi
        fi
    done
    
    # Test basic script execution
    echo ""
    echo "Testing script execution (5 seconds)..."
    timeout 5 "$SCRIPT_PATH" 2>&1 | head -20
    echo ""
    echo -e "${GREEN}Test completed.${NC}"
}

clean_up() {
    echo -e "${BLUE}Cleaning up battery monitor files...${NC}"
    
    # Stop if running
    if is_running; then
        echo "Stopping running instances..."
        stop_monitor
    fi
    
    # Remove files
    rm -f "$PIDFILE" "$LOCKFILE" 2>/dev/null
    
    echo -e "${GREEN}Cleanup completed.${NC}"
}

# Main script logic
case "${1:-help}" in
    "start")
        start_monitor
        ;;
    "stop")
        stop_monitor
        ;;
    "restart")
        restart_monitor
        ;;
    "status")
        show_status
        ;;
    "log")
        show_log
        ;;
    "tail")
        tail_log
        ;;
    "clean")
        clean_up
        ;;
    "debug")
        debug_monitor
        ;;
    "test")
        test_monitor
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        show_help
        exit 1
        ;;
esac
