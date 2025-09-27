#!/bin/bash

# WiFi 5G Frequency Diagnostic Script
# This script checks for 5GHz band support and tries to connect to a 5G network

TARGET_SSID="Girnari 5G"
INTERFACE=""

echo "=== WiFi 5G Frequency Diagnostic Script ==="
echo "Target SSID: $TARGET_SSID"
echo "Date: $(date)"
echo

# Function to print section headers
print_header() {
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Function to pause for user input
pause() {
    read -p "Press Enter to continue..."
    echo
}

# Auto-detect wireless interface
detect_interface() {
    INTERFACE=$(iw dev | grep Interface | head -1 | awk '{print $2}')
    if [ -z "$INTERFACE" ]; then
        echo "ERROR: No wireless interface found!"
        exit 1
    fi
    echo "Detected wireless interface: $INTERFACE"
    echo
}

# Check hardware capabilities
check_hardware() {
    print_header "1. Hardware Detection"

    echo "PCI WiFi devices:"
    lspci | grep -i -E "(wireless|wifi|network)" | grep -i realtek
    echo

    echo "WiFi interfaces:"
    ip link show | grep -E "wl|wifi"
    echo

    echo "Driver modules loaded:"
    lsmod | grep -E "rtw89|rtl"
    echo

    pause
}

# Check supported bands and frequencies
check_frequencies() {
    print_header "2. Supported Bands and Frequencies"

    echo "All supported bands:"
    iw phy | grep -A 30 "Band"
    echo

    echo "Available channels and frequencies:"
    iw list | grep -A 100 "Frequencies:" | head -50
    echo

    pause
}

# Check regulatory domain
check_regulatory() {
    print_header "3. Regulatory Domain"

    echo "Current regulatory domain:"
    iw reg get
    echo

    echo "Setting regulatory domain to India (IN)..."
    sudo iw reg set IN
    sleep 2

    echo "Updated regulatory domain:"
    iw reg get
    echo

    pause
}

# Check rfkill status
check_rfkill() {
    print_header "4. RF Kill Status"

    echo "RF Kill status:"
    rfkill list all
    echo

    echo "Unblocking all RF devices..."
    sudo rfkill unblock all
    echo "Updated RF Kill status:"
    rfkill list all
    echo

    pause
}

# Driver information and messages
check_driver() {
    print_header "5. Driver Information"

    echo "Driver module info:"
    modinfo rtw89_8852be | grep -E "(description|version|filename)"
    echo

    echo "Recent driver messages from dmesg:"
    dmesg | grep -i rtw89 | tail -15
    echo

    pause
}

# Scan for networks
scan_networks() {
    print_header "6. Network Scanning"

    echo "Bringing interface up..."
    sudo ip link set $INTERFACE up
    sleep 2

    echo "Scanning for all networks (this may take 10-15 seconds)..."
    sudo iw dev $INTERFACE scan > /tmp/wifi_scan.txt 2>&1

    if [ $? -eq 0 ]; then
        echo "All detected networks:"
        grep -E "(SSID|freq|signal)" /tmp/wifi_scan.txt | head -30
        echo

        echo "Looking specifically for '$TARGET_SSID'..."
        if grep -q "$TARGET_SSID" /tmp/wifi_scan.txt; then
            echo "✓ Found '$TARGET_SSID'!"
            echo "Network details:"
            grep -A 10 -B 5 "$TARGET_SSID" /tmp/wifi_scan.txt
        else
            echo "✗ '$TARGET_SSID' not found in scan results"
        fi
    else
        echo "Scan failed. Trying with nmcli..."
        nmcli device wifi rescan
        sleep 5
        nmcli device wifi list
    fi

    echo
    pause
}

# Try NetworkManager scan
nm_scan() {
    print_header "7. NetworkManager Scan"

    echo "NetworkManager WiFi status:"
    nmcli radio wifi
    echo

    echo "Enabling WiFi radio..."
    nmcli radio wifi on
    sleep 2

    echo "Rescanning with NetworkManager..."
    nmcli device wifi rescan
    sleep 5

    echo "Available networks via NetworkManager:"
    nmcli device wifi list
    echo

    echo "Looking for '$TARGET_SSID' specifically..."
    nmcli device wifi list | grep -i "girnari"
    echo

    pause
}

# Attempt connection
attempt_connection() {
    print_header "8. Connection Attempt"

    if nmcli device wifi list | grep -q "$TARGET_SSID"; then
        echo "✓ '$TARGET_SSID' is visible!"
        echo
        echo "Attempting to connect..."
        echo "You will be prompted for the password."
        echo

        nmcli device wifi connect "$TARGET_SSID" --ask

        if [ $? -eq 0 ]; then
            echo "✓ Connection successful!"
            echo
            echo "Connection details:"
            nmcli connection show "$TARGET_SSID"
            echo
            echo "IP configuration:"
            ip addr show $INTERFACE
        else
            echo "✗ Connection failed"
        fi
    else
        echo "✗ '$TARGET_SSID' is not visible, cannot attempt connection"
    fi

    echo
    pause
}

# Check final status
check_status() {
    print_header "9. Final Status Check"

    echo "Current connections:"
    nmcli connection show --active
    echo

    echo "Interface status:"
    ip addr show $INTERFACE
    echo

    echo "WiFi signal strength:"
    nmcli device wifi list | head -5
    echo

    if ping -c 3 8.8.8.8 &>/dev/null; then
        echo "✓ Internet connectivity test: PASSED"
    else
        echo "✗ Internet connectivity test: FAILED"
    fi

    echo
}

# Troubleshooting suggestions
troubleshooting() {
    print_header "10. Troubleshooting Suggestions"

    echo "If 5GHz is still not working, try these additional steps:"
    echo
    echo "1. Reload driver with different parameters:"
    echo "   sudo modprobe -r rtw89_8852be"
    echo "   sudo modprobe rtw89_8852be disable_clkreq=1"
    echo
    echo "2. Check if your router is broadcasting 5GHz on a supported channel:"
    echo "   - Try channels 36, 40, 44, 48 (lower 5GHz band)"
    echo "   - Avoid DFS channels (52-144) which might not be supported"
    echo
    echo "3. Update firmware if available:"
    echo "   sudo dnf update"
    echo
    echo "4. Check router settings:"
    echo "   - Ensure 5GHz is enabled"
    echo "   - Try changing channel width (20/40/80MHz)"
    echo "   - Check if hidden SSID is causing issues"
    echo
    echo "5. Try connecting to a different 5GHz network for testing"
    echo
}

# Main execution
main() {
    # Check if running as root for some commands
    if [ "$EUID" -ne 0 ]; then
        echo "Note: This script will use sudo for some commands that require root privileges."
        echo
    fi

    detect_interface
    check_hardware
    check_frequencies
    check_regulatory
    check_rfkill
    check_driver
    scan_networks
    nm_scan
    attempt_connection
    check_status
    troubleshooting

    echo "=== Diagnostic Complete ==="
    echo "Log files created:"
    echo "- /tmp/wifi_scan.txt (raw scan results)"
    echo
    echo "If issues persist, share the output of this script for further assistance."
}

# Run main function
main
