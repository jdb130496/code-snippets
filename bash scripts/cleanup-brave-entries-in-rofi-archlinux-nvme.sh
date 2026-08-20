#!/usr/bin/env bash

# ==============================================================================
# Script Name: cleanup_brave_shortcuts.sh
# Description: Detects and removes duplicate/broken Brave Nightly shortcuts
#              from system-wide and user-local desktop directories, then
#              resets the Rofi history cache to fix launcher duplicates.
# Author: AI Assistant
# OS Target: Arch Linux / Generic SysAdmin
# ==============================================================================

set -euo pipefail

# --- Color Definitions for Clean Output ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Brave Nightly Rofi Shortcut Cleaner ===${NC}\n"

# --- Define Paths ---
SYS_DIR="/usr/share/applications"
LOCAL_DIR="$HOME/.local/share/applications"
ROFI_CACHE="$HOME/.cache/rofi-3.history"

# --- Function to list existing entries ---
check_entries() {
    local dir=$1
    local label=$2
    echo -e "${BLUE}[*] Checking ${label} directory...${NC}"
    if [ -d "$dir" ]; then
        # Find files matching brave or nightly case-insensitively
        local files
        files=$(find "$dir" -maxdepth 1 -iname "*brave*" -o -iname "*nightly*" 2>/dev/null | sed "s|$dir/||")
        if [ -z "$files" ]; then
            echo "    No matching entries found."
        else
            echo -e "${YELLOW}    Found entries:${NC}"
            echo "$files" | awk '{print "     - " $0}'
        fi
    else
        echo "    Directory does not exist."
    fi
    echo ""
}

# --- 1. Display current state ---
check_entries "$SYS_DIR" "System-wide (/usr)"
check_entries "$LOCAL_DIR" "User-local (~/.local)"

# --- 2. Prompt user choice for action ---
echo -e "${YELLOW}Choose an action to fix the duplicates:${NC}"
echo "1) Keep ONLY Native Arch/AUR version (Removes Flatpak entries)"
echo "2) Keep ONLY Flatpak version (Removes Native entries)"
echo "3) Clean up User-Local (~/.local) duplicates only"
echo "4) Hide Flatpak entry from menus safely (No-uninstall trick)"
echo "5) Exit without changes"
read -rp "Enter choice [1-5]: " choice

case $choice in
    1)
        echo -e "\n${YELLOW}[!] Target: Remove Flatpak entries...${NC}"
        # Remove Flatpak configuration shortcut if it exists locally
        if [ -f "$LOCAL_DIR/com.brave.Browser.nightly.desktop" ]; then
            rm -v "$LOCAL_DIR/com.brave.Browser.nightly.desktop"
        fi
        # Offer flatpak command execution if tool is present
        if command -v flatpak &> /dev/null; then
            echo -e "${BLUE}[*] Flatpak detected. Uninstalling package...${NC}"
            flatpak uninstall --delete-data com.brave.Browser.nightly || true
        else
            echo -e "${RED}[!] Flatpak binary not found, please clean system files manually if needed.${NC}"
        fi
        ;;
    2)
        echo -e "\n${YELLOW}[!] Target: Remove Native Arch version...${NC}"
        if [ -f "$LOCAL_DIR/brave-browser-nightly.desktop" ]; then
            rm -v "$LOCAL_DIR/brave-browser-nightly.desktop"
        fi
        echo -e "${BLUE}[*] Requesting root privileges to remove native package via pacman...${NC}"
        sudo pacman -R brave-browser-nightly || true
        ;;
    3)
        echo -e "\n${YELLOW}[!] Purging matching entries inside user local directory...${NC}"
        find "$LOCAL_DIR" -maxdepth 1 \( -name "*brave*" -o -name "*nightly*" \) -exec rm -v {} + || echo "No local files removed."
        ;;
    4)
        echo -e "\n${YELLOW}[!] Injecting NoDisplay flag to safely hide Flatpak entry...${NC}"
        mkdir -p "$LOCAL_DIR"
        if [ -f "$SYS_DIR/com.brave.Browser.nightly.desktop" ]; then
            cp "$SYS_DIR/com.brave.Browser.nightly.desktop" "$LOCAL_DIR/"
            echo "NoDisplay=true" >> "$LOCAL_DIR/com.brave.Browser.nightly.desktop"
            echo -e "${GREEN}[+] Successfully hid Flatpak version from Rofi interface.${NC}"
        else
            echo -e "${RED}[-] Source system flatpak file not found.${NC}"
        fi
        ;;
    *)
        echo -e "\n${BLUE}[*] Exiting script safely.${NC}"
        exit 0
        ;;
esac

# --- 3. Wipe Rofi Launcher Cache ---
echo -e "\n${BLUE}[*] Cleaning out Rofi history cache index...${NC}"
if [ -f "$ROFI_CACHE" ]; then
    rm -v "$ROFI_CACHE"
    echo -e "${GREEN}[+] Rofi cache wiped out successfully.${NC}"
else
    echo "    No rofi cache file found to delete."
fi

echo -e "\n${GREEN}=== Cleanup Process Complete! Open Rofi to check. ===${NC}"

