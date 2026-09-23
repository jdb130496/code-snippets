#!/bin/bash
# Safe iwd migration script with automatic rollback
# Usage: sudo bash this_script.sh

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Safe iwd Migration Script ===${NC}\n"

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Please run as root (sudo)${NC}"
    exit 1
fi

# Function to rollback to wpa_supplicant
rollback() {
    echo -e "\n${YELLOW}Rolling back to wpa_supplicant...${NC}"
    
    # Remove iwd backend configuration
    rm -f /etc/NetworkManager/conf.d/wifi-backend.conf
    
    # Stop and disable iwd
    systemctl stop iwd 2>/dev/null || true
    systemctl disable iwd 2>/dev/null || true
    
    # Unmask and start wpa_supplicant
    systemctl unmask wpa_supplicant 2>/dev/null || true
    systemctl start wpa_supplicant 2>/dev/null || true
    
    # Restart NetworkManager
    systemctl restart NetworkManager
    
    echo -e "${GREEN}Rollback complete. wpa_supplicant is active again.${NC}"
    echo -e "${YELLOW}Please verify your WiFi connection.${NC}"
}

# Set trap to rollback on script failure
trap 'echo -e "\n${RED}Script failed! Rolling back...${NC}"; rollback; exit 1' ERR

echo "Step 1: Installing iwd..."
dnf install -y iwd

echo -e "\n${GREEN}Step 2: Configuring NetworkManager to use iwd...${NC}"
mkdir -p /etc/NetworkManager/conf.d/
cat > /etc/NetworkManager/conf.d/wifi-backend.conf << EOF
[device]
wifi.backend=iwd
EOF

echo -e "\n${GREEN}Step 3: Stopping wpa_supplicant...${NC}"
systemctl stop wpa_supplicant
systemctl mask wpa_supplicant

echo -e "\n${GREEN}Step 4: Starting iwd...${NC}"
systemctl enable --now iwd
sleep 2

echo -e "\n${GREEN}Step 5: Restarting NetworkManager...${NC}"
systemctl restart NetworkManager
sleep 3

echo -e "\n${GREEN}Step 6: Testing iwd...${NC}"

# Check if iwd service is running
if ! systemctl is-active --quiet iwd; then
    echo -e "${RED}iwd service failed to start!${NC}"
    rollback
    exit 1
fi

# Check for errors in iwd logs
if journalctl -u iwd --since "1 minute ago" | grep -i "segmentation fault\|core dumped"; then
    echo -e "${RED}iwd has crashed (segmentation fault detected)!${NC}"
    rollback
    exit 1
fi

# Try to list devices with iwctl
echo "Testing iwctl device list..."
timeout 5 iwctl device list > /tmp/iwd_test.txt 2>&1 || {
    echo -e "${RED}iwctl command failed or timed out!${NC}"
    cat /tmp/iwd_test.txt
    rollback
    exit 1
}

# Check if wlan0 is detected
if ! grep -q "wlan0" /tmp/iwd_test.txt; then
    echo -e "${RED}wlan0 not detected by iwd!${NC}"
    cat /tmp/iwd_test.txt
    rollback
    exit 1
fi

echo -e "\n${GREEN}=== iwd Successfully Activated! ===${NC}\n"
echo "Your WiFi card is now managed by iwd."
echo ""
echo "Next steps:"
echo "1. Test connecting to your 5GHz network via NetworkManager GUI"
echo "2. Verify connection stability"
echo "3. Test after a reboot"
echo ""
echo "Available commands:"
echo "  - List networks:  sudo iwctl station wlan0 scan && sudo iwctl station wlan0 get-networks"
echo "  - Check status:   sudo systemctl status iwd"
echo "  - View logs:      sudo journalctl -u iwd -f"
echo ""
echo -e "${YELLOW}If you experience any issues, run this to rollback:${NC}"
echo -e "${GREEN}sudo bash $0 rollback${NC}"
echo ""

# Remove trap since we succeeded
trap - ERR

exit 0
