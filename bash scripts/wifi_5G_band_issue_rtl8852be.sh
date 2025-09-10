#!/bin/bash
#
# Force Enable 5GHz WiFi Band Detection Script
# Compatible with Fedora Rawhide and Arch Linux
# Specifically targets RTL8852BE and similar WiFi cards
#
# Usage: sudo ./force_5ghz_wifi.sh
#

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   echo -e "${RED}This script must be run as root (use sudo)${NC}"
   exit 1
fi

echo -e "${BLUE}=== 5GHz WiFi Force Enable Script ===${NC}"
echo "This script will attempt to force enable 5GHz WiFi detection"
echo ""

# Step 1: Identify WiFi interface
echo -e "${YELLOW}Step 1: Identifying WiFi interface...${NC}"
WIFI_INTERFACES=$(iw dev | grep Interface | awk '{print $2}')
if [ -z "$WIFI_INTERFACES" ]; then
    echo -e "${RED}No WiFi interfaces found!${NC}"
    exit 1
fi

WIFI_IF=$(echo "$WIFI_INTERFACES" | head -n1)
echo -e "${GREEN}Using WiFi interface: $WIFI_IF${NC}"

# Step 2: Check current WiFi card
echo -e "${YELLOW}Step 2: Checking WiFi hardware...${NC}"
WIFI_CARD=$(lspci | grep -i "network\|wireless" | head -n1)
echo "WiFi Card: $WIFI_CARD"

# Check if RTL8852BE (common problematic card)
RTL8852BE_PRESENT=$(lspci | grep -i "RTL8852BE" | wc -l)
if [ "$RTL8852BE_PRESENT" -gt 0 ]; then
    echo -e "${YELLOW}RTL8852BE detected - applying specific fixes${NC}"
    RTL_FIX=true
else
    RTL_FIX=false
fi

# Step 3: Check current regulatory domain
echo -e "${YELLOW}Step 3: Setting regulatory domain...${NC}"
CURRENT_REG=$(iw reg get | grep country | awk '{print $2}' | cut -d: -f1)
echo "Current regulatory domain: $CURRENT_REG"

# Set regulatory domain (try India first, then US, then World)
for REG in IN US 00; do
    echo "Trying regulatory domain: $REG"
    iw reg set $REG
    sleep 2
    break
done

# Step 4: Disable power management
echo -e "${YELLOW}Step 4: Disabling power management...${NC}"
iw dev $WIFI_IF set power_save off
echo "Power save disabled for $WIFI_IF"

# Step 5: RTL8852BE specific fixes
if [ "$RTL_FIX" = true ]; then
    echo -e "${YELLOW}Step 5: Applying RTL8852BE specific fixes...${NC}"
    
    # Create modprobe configuration for RTL8852BE
    cat > /etc/modprobe.d/rtw89-5ghz-fix.conf << EOF
# RTL8852BE 5GHz fixes
options rtw89_core disable_ps_mode=Y
options rtw89_pci disable_aspm_l1=Y disable_aspm_l1ss=Y disable_clkreq=Y
EOF
    
    # Reload RTL driver modules
    echo "Reloading RTL8852BE driver modules..."
    modprobe -r rtw89_8852be rtw89_8852b rtw89_pci rtw89_core 2>/dev/null || true
    sleep 2
    modprobe rtw89_8852be
    sleep 3
    
    echo -e "${GREEN}RTL8852BE fixes applied${NC}"
else
    echo -e "${YELLOW}Step 5: Applying generic WiFi fixes...${NC}"
    
    # Generic WiFi driver reload
    DRIVER_MODULE=$(basename $(readlink /sys/class/net/$WIFI_IF/device/driver) 2>/dev/null)
    if [ ! -z "$DRIVER_MODULE" ]; then
        echo "Reloading driver: $DRIVER_MODULE"
        modprobe -r $DRIVER_MODULE 2>/dev/null || true
        sleep 2
        modprobe $DRIVER_MODULE 2>/dev/null || true
        sleep 3
    fi
fi

# Step 6: Reset NetworkManager
echo -e "${YELLOW}Step 6: Resetting NetworkManager...${NC}"
systemctl restart NetworkManager
sleep 3

# Step 7: Force comprehensive WiFi scan
echo -e "${YELLOW}Step 7: Performing comprehensive WiFi scan...${NC}"

# Force rescan
nmcli device wifi rescan
sleep 5

# Try different scanning methods
echo "Method 1: NetworkManager scan"
nmcli device wifi list | head -20

echo ""
echo "Method 2: Direct iw scan for 5GHz networks"
timeout 30 iw dev $WIFI_IF scan | grep -E "(freq: 5[0-9]{3}|SSID)" | grep -B1 -A1 "freq: 5" | head -20

# Step 8: Test specific 5GHz channels
echo -e "${YELLOW}Step 8: Testing specific 5GHz channels...${NC}"

# Common 5GHz channels to test
CHANNELS_5GHZ="5180 5200 5220 5240 5260 5280 5300 5320 5500 5520 5540 5560 5580 5600 5620 5640 5660 5680 5700 5720 5745 5765 5785 5805 5825"

echo "Scanning specific 5GHz frequencies..."
timeout 45 iw dev $WIFI_IF scan freq $CHANNELS_5GHZ | grep -E "(SSID|freq: 5)" | head -20

# Step 9: Summary and recommendations
echo ""
echo -e "${BLUE}=== Summary and Recommendations ===${NC}"

# Check for 5GHz networks
FOUND_5GHZ=$(nmcli device wifi list | grep -E "270 Mbit/s|5G" | wc -l)

if [ "$FOUND_5GHZ" -gt 0 ]; then
    echo -e "${GREEN}✓ 5GHz networks detected successfully!${NC}"
    echo -e "${GREEN}Found $FOUND_5GHZ 5GHz network(s)${NC}"
else
    echo -e "${YELLOW}⚠ No 5GHz networks detected${NC}"
    echo ""
    echo -e "${BLUE}Additional troubleshooting steps:${NC}"
    echo "1. Check if your router's 5GHz band is enabled"
    echo "2. Try setting your router to channel 36, 44, or 149"
    echo "3. Ensure router's 5GHz channel width is 80MHz (not 160MHz)"
    echo "4. Move closer to router (5GHz has shorter range than 2.4GHz)"
    echo "5. Check if other devices can see the 5GHz network"
    
    if [ "$RTL_FIX" = true ]; then
        echo ""
        echo -e "${YELLOW}RTL8852BE specific notes:${NC}"
        echo "- This card has known issues with channels above 64"
        echo "- Try setting router to channels 36-48 (lower 5GHz band)"
        echo "- Some hardware revisions (rfe_type 41) have persistent issues"
        echo "- Consider updating router firmware or trying different channels"
    fi
fi

echo ""
echo -e "${BLUE}Configuration files created:${NC}"
if [ "$RTL_FIX" = true ]; then
    echo "- /etc/modprobe.d/rtw89-5ghz-fix.conf"
fi

echo ""
echo -e "${GREEN}Script completed. Reboot recommended for full effect.${NC}"

# Step 10: Optional - Create permanent service
read -p "Create permanent service to apply fixes on boot? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cat > /etc/systemd/system/wifi-5ghz-fix.service << 'EOF'
[Unit]
Description=WiFi 5GHz Detection Fix
After=network.target

[Service]
Type=oneshot
ExecStart=/bin/bash -c 'sleep 10 && iw dev $(iw dev | grep Interface | awk "{print \$2}" | head -n1) set power_save off && nmcli device wifi rescan'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable wifi-5ghz-fix.service
    echo -e "${GREEN}Permanent service created and enabled${NC}"
fi

echo ""
echo -e "${BLUE}To manually test 5GHz connection to a specific network:${NC}"
echo "nmcli device wifi connect \"YourNetworkName_5G\" --ask"
echo ""
echo -e "${BLUE}To scan for 5GHz networks manually:${NC}"
echo "nmcli device wifi list | grep -E \"270 Mbit/s|5G\""
