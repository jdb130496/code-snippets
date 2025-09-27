#!/bin/bash

# RTL8852BE 5GHz Band Fix Script
# Fixes the 5GHz band detection issue with rtw89_8852be driver

TARGET_SSID="Girnari 5G"

echo "=== RTL8852BE 5GHz Band Fix Script ==="
echo "This script attempts to fix 5GHz band detection for RTL8852BE cards"
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

# Check current status
check_current_status() {
    print_header "Current Status Check"

    echo "Current regulatory domain:"
    iw reg get
    echo

    echo "Current loaded rtw89 modules:"
    lsmod | grep rtw89
    echo

    echo "Current 5GHz frequency support:"
    iw phy | grep -A 5 "Band 2"
    echo

    pause
}

# Method 1: Regulatory Domain and Driver Reload
method1_regulatory_fix() {
    print_header "Method 1: Regulatory Domain and Driver Reload"

    echo "Setting regulatory domain to India..."
    sudo iw reg set IN
    sleep 2

    echo "Unloading rtw89 modules..."
    sudo modprobe -r rtw89_8852be
    sudo modprobe -r rtw89_pci
    sudo modprobe -r rtw89_8852b
    sudo modprobe -r rtw89_core
    sleep 3

    echo "Reloading rtw89 modules..."
    sudo modprobe rtw89_core
    sleep 1
    sudo modprobe rtw89_8852b
    sleep 1
    sudo modprobe rtw89_pci
    sleep 1
    sudo modprobe rtw89_8852be
    sleep 2

    echo "Updated regulatory domain:"
    iw reg get
    echo

    echo "Checking for 5GHz support after reload:"
    iw phy | grep -A 10 "Band 2"
    echo

    echo "Testing scan for 5GHz networks..."
    interface=$(iw dev | grep Interface | head -1 | awk '{print $2}')
    if [ ! -z "$interface" ]; then
        sudo iw dev $interface scan | grep -E "(freq: 5|SSID.*5[Gg])" | head -10
    fi
    echo

    pause
}

# Method 2: Module Parameters Fix
method2_module_parameters() {
    print_header "Method 2: Module Parameters Configuration"

    echo "Creating rtw89 module configuration..."

    # Create modprobe configuration
    sudo tee /etc/modprobe.d/rtw89.conf > /dev/null << 'EOF'
# RTW89 Configuration for 5GHz band support
options rtw89_core debug_mask=0x00000001
options rtw89_pci disable_clkreq=1 disable_aspm_l1=1
options rtw89_8852be disable_ps_mode=1
# Force regulatory domain
options cfg80211 ieee80211_regdom=IN
EOF

    echo "Configuration created at /etc/modprobe.d/rtw89.conf"
    cat /etc/modprobe.d/rtw89.conf
    echo

    echo "Unloading and reloading modules with new parameters..."
    sudo modprobe -r rtw89_8852be rtw89_pci rtw89_8852b rtw89_core cfg80211
    sleep 3

    echo "Reloading cfg80211 and rtw89 modules..."
    sudo modprobe cfg80211
    sleep 1
    sudo modprobe rtw89_core
    sleep 1
    sudo modprobe rtw89_8852b
    sleep 1
    sudo modprobe rtw89_pci
    sleep 1
    sudo modprobe rtw89_8852be
    sleep 2

    echo "Checking loaded modules:"
    lsmod | grep -E "rtw89|cfg80211"
    echo

    pause
}

# Method 3: Firmware and Hardware Reset
method3_firmware_reset() {
    print_header "Method 3: Firmware and Hardware Reset"

    echo "Checking firmware loading messages..."
    dmesg | grep -i "rtw89.*firmware" | tail -5
    echo

    echo "Performing complete wireless subsystem reset..."

    # Disable all RF
    sudo rfkill block all
    sleep 2
    sudo rfkill unblock all
    sleep 2

    # Reset network interface
    interface=$(iw dev | grep Interface | head -1 | awk '{print $2}')
    if [ ! -z "$interface" ]; then
        echo "Resetting interface $interface..."
        sudo ip link set $interface down
        sleep 2
        sudo ip link set $interface up
        sleep 2
    fi

    echo "Checking regulatory domain after reset..."
    iw reg get
    echo

    pause
}

# Method 4: Kernel Module Blacklist and Rebuild
method4_initramfs_rebuild() {
    print_header "Method 4: Initramfs Rebuild (if needed)"

    echo "Current initramfs info:"
    ls -la /boot/initramfs-$(uname -r).img
    echo

    echo "Rebuilding initramfs to include new module configurations..."
    sudo dracut -f /boot/initramfs-$(uname -r).img $(uname -r)

    echo "Initramfs rebuilt. A reboot may be required for full effect."
    echo

    pause
}

# Test 5GHz detection
test_5ghz_detection() {
    print_header "Testing 5GHz Detection"

    interface=$(iw dev | grep Interface | head -1 | awk '{print $2}')

    if [ -z "$interface" ]; then
        echo "ERROR: No wireless interface found!"
        return 1
    fi

    echo "Using interface: $interface"
    echo

    echo "Checking supported bands:"
    iw phy | grep -A 15 "Frequencies:"
    echo

    echo "Performing comprehensive scan..."
    sudo iw dev $interface scan > /tmp/5g_scan.txt 2>&1

    if [ $? -eq 0 ]; then
        echo "5GHz networks detected:"
        grep -B2 -A2 "freq: 5" /tmp/5g_scan.txt | head -20
        echo

        echo "Looking for '$TARGET_SSID':"
        if grep -q "$TARGET_SSID" /tmp/5g_scan.txt; then
            echo "✓ Found '$TARGET_SSID'!"
            grep -B5 -A5 "$TARGET_SSID" /tmp/5g_scan.txt
        else
            echo "✗ '$TARGET_SSID' not found"
        fi
    else
        echo "Scan failed, trying with NetworkManager..."
        nmcli device wifi rescan
        sleep 5
        nmcli device wifi list | grep -E "(5GHz|5G)"
    fi

    echo
    pause
}

# Connection attempt
attempt_5g_connection() {
    print_header "Attempting 5GHz Connection"

    echo "Scanning for '$TARGET_SSID'..."
    nmcli device wifi rescan
    sleep 5

    if nmcli device wifi list | grep -q "$TARGET_SSID"; then
        echo "✓ '$TARGET_SSID' detected!"
        echo

        nmcli device wifi list | grep -i girnari
        echo

        echo "Attempting connection..."
        nmcli device wifi connect "$TARGET_SSID" --ask

        if [ $? -eq 0 ]; then
            echo "✓ Successfully connected to 5GHz network!"
            echo
            echo "Connection details:"
            nmcli connection show "$TARGET_SSID" | grep -E "(802-11-wireless|frequency)"
        else
            echo "✗ Connection failed"
        fi
    else
        echo "✗ '$TARGET_SSID' still not visible"
        echo
        echo "Available networks:"
        nmcli device wifi list | head -10
    fi

    echo
}

# Reboot suggestion
suggest_reboot() {
    print_header "Completion and Next Steps"

    echo "Fix attempts completed. Current status:"
    echo

    echo "Loaded modules:"
    lsmod | grep rtw89
    echo

    echo "Regulatory domain:"
    iw reg get
    echo

    echo "Configuration files created:"
    ls -la /etc/modprobe.d/rtw89.conf 2>/dev/null && echo "✓ /etc/modprobe.d/rtw89.conf exists"
    echo

    echo "IMPORTANT: For complete effectiveness, you should:"
    echo "1. Reboot your system to ensure all changes take effect"
    echo "2. After reboot, run the diagnostic script again to verify 5GHz detection"
    echo "3. If still not working, try using the lwfinger driver instead of kernel rtw89"
    echo

    echo "Reboot now? (y/N):"
    read -n 1 response
    echo

    if [ "$response" = "y" ] || [ "$response" = "Y" ]; then
        echo "Rebooting in 5 seconds... (Ctrl+C to cancel)"
        sleep 5
        sudo reboot
    else
        echo "Manual reboot recommended when convenient."
    fi
}

# Main execution
main() {
    if [ "$EUID" -ne 0 ]; then
        echo "Note: This script requires sudo privileges for module operations."
        echo
    fi

    check_current_status
    method1_regulatory_fix
    method2_module_parameters
    method3_firmware_reset
    test_5ghz_detection

    # Only try connection if 5GHz detection succeeded
    if grep -q "freq: 5" /tmp/5g_scan.txt 2>/dev/null; then
        attempt_5g_connection
    fi

    method4_initramfs_rebuild
    suggest_reboot

    echo "=== Fix Script Complete ==="
}

# Run main function
main
