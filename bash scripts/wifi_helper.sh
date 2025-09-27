#!/bin/bash

# Router 5GHz Configuration Verifier
# Verifies if your router is actually broadcasting on 5GHz after configuration

TARGET_SSID="Girnari 5G"
ALT_SSID="Girnari 5G"

echo "=== Router 5GHz Configuration Verifier ==="
echo "This script verifies if your router is broadcasting on actual 5GHz frequencies"
echo "Date: $(date)"
echo

# Function to print section headers
print_header() {
    echo "=========================================="
    echo "$1"
    echo "=========================================="
}

# Check if 5GHz frequencies are being detected
check_5ghz_detection() {
    print_header "1. Checking for ANY 5GHz Networks"

    echo "Scanning for networks on 5GHz frequencies..."
    INTERFACE=$(iw dev | grep Interface | head -1 | awk '{print $2}')

    # Full scan
    sudo iw dev $INTERFACE scan > /tmp/router_scan.txt 2>&1

    # Look for any 5GHz frequencies
    echo "Networks detected on 5GHz frequencies:"
    echo "SSID                     Frequency    Channel   Signal"
    echo "--------------------------------------------------------"

    # Parse for 5GHz networks
    awk '
    BEGIN { ssid=""; freq=""; signal=""; bssid="" }
    /^BSS/ {
        if(ssid && freq ~ /^5[0-9]{3}/) {
            # Convert frequency to channel
            chan = ""
            f = int(freq)
            if(f == 5180) chan = "36"
            else if(f == 5200) chan = "40"
            else if(f == 5220) chan = "44"
            else if(f == 5240) chan = "48"
            else if(f == 5260) chan = "52"
            else if(f == 5280) chan = "56"
            else if(f == 5300) chan = "60"
            else if(f == 5320) chan = "64"
            else if(f == 5500) chan = "100"
            else if(f == 5520) chan = "104"
            else if(f == 5540) chan = "108"
            else if(f == 5560) chan = "112"
            else if(f == 5580) chan = "116"
            else if(f == 5600) chan = "120"
            else if(f == 5620) chan = "124"
            else if(f == 5640) chan = "128"
            else if(f == 5660) chan = "132"
            else if(f == 5680) chan = "136"
            else if(f == 5700) chan = "140"
            else if(f == 5720) chan = "144"
            else if(f == 5745) chan = "149"
            else if(f == 5765) chan = "153"
            else if(f == 5785) chan = "157"
            else if(f == 5805) chan = "161"
            else if(f == 5825) chan = "165"
            else chan = "?"

            printf "%-24s %-12s %-9s %s\n", ssid, freq " MHz", chan, signal
        }
        ssid=""; freq=""; signal=""
    }
    /SSID:/ { ssid = substr($0, index($0, ":") + 2) }
    /freq:/ { freq = $2 }
    /signal:/ { signal = $2 " " $3 }
    END {
        if(ssid && freq ~ /^5[0-9]{3}/) {
            chan = ""
            f = int(freq)
            if(f == 5180) chan = "36"
            else if(f == 5200) chan = "40"
            else if(f == 5220) chan = "44"
            else if(f == 5240) chan = "48"
            else if(f == 5260) chan = "52"
            else if(f == 5280) chan = "56"
            else if(f == 5300) chan = "60"
            else if(f == 5320) chan = "64"
            else if(f == 5500) chan = "100"
            else if(f == 5520) chan = "104"
            else if(f == 5540) chan = "108"
            else if(f == 5560) chan = "112"
            else if(f == 5580) chan = "116"
            else if(f == 5600) chan = "120"
            else if(f == 5620) chan = "124"
            else if(f == 5640) chan = "128"
            else if(f == 5660) chan = "132"
            else if(f == 5680) chan = "136"
            else if(f == 5700) chan = "140"
            else if(f == 5720) chan = "144"
            else if(f == 5745) chan = "149"
            else if(f == 5765) chan = "153"
            else if(f == 5785) chan = "157"
            else if(f == 5805) chan = "161"
            else if(f == 5825) chan = "165"
            else chan = "?"
            printf "%-24s %-12s %-9s %s\n", ssid, freq " MHz", chan, signal
        }
    }' /tmp/router_scan.txt

    # Count 5GHz networks
    five_ghz_count=$(grep -E "freq: 5[0-9]{3}" /tmp/router_scan.txt | wc -l)

    echo
    if [ "$five_ghz_count" -eq 0 ]; then
        echo "❌ NO 5GHz networks detected!"
        echo "This means either:"
        echo "   1. No routers in your area are broadcasting 5GHz"
        echo "   2. Your router's 5GHz is not enabled"
        echo "   3. Routers are using DFS channels your card can't detect"
    else
        echo "✅ Found $five_ghz_count 5GHz networks!"
    fi

    echo
}

# Check specifically for your router
check_your_router() {
    print_header "2. Checking Your Router Configuration"

    echo "Looking for your specific network names..."
    echo

    # Check for both possible SSID names
    for ssid in "$TARGET_SSID" "Girnari" "girnari"; do
        echo "Searching for: $ssid"
        if grep -q "$ssid" /tmp/router_scan.txt; then
            echo "✅ Found '$ssid':"

            # Get details for this SSID
            awk -v target="$ssid" '
            BEGIN { found=0; ssid=""; freq=""; signal=""; sec="" }
            /^BSS/ {
                if(found && ssid) {
                    printf "   SSID: %s\n", ssid
                    printf "   Frequency: %s MHz\n", freq
                    if(freq ~ /^24[0-9]{2}/) printf "   Band: 2.4GHz ❌\n"
                    else if(freq ~ /^5[0-9]{3}/) printf "   Band: 5GHz ✅\n"
                    else printf "   Band: Unknown\n"
                    printf "   Signal: %s\n", signal
                    printf "   Security: %s\n", sec
                    found=0
                }
                ssid=""; freq=""; signal=""; sec=""
            }
            /SSID:/ {
                candidate = substr($0, index($0, ":") + 2)
                if(candidate == target) found=1
                ssid = candidate
            }
            /freq:/ { freq = $2 }
            /signal:/ { signal = $2 " " $3 }
            /Privacy|WPA|WEP/ { if(sec) sec = sec " " $0; else sec = $0 }
            END {
                if(found && ssid) {
                    printf "   SSID: %s\n", ssid
                    printf "   Frequency: %s MHz\n", freq
                    if(freq ~ /^24[0-9]{2}/) printf "   Band: 2.4GHz ❌\n"
                    else if(freq ~ /^5[0-9]{3}/) printf "   Band: 5GHz ✅\n"
                    else printf "   Band: Unknown\n"
                    printf "   Signal: %s\n", signal
                    printf "   Security: %s\n", sec
                }
            }' /tmp/router_scan.txt
            echo
        else
            echo "❌ '$ssid' not found"
        fi
    done
}

# Test connection to 5GHz network if found
test_5ghz_connection() {
    print_header "3. Testing 5GHz Connection"

    # Check if any 5GHz version of your network exists
    five_ghz_network=""

    for ssid in "$TARGET_SSID" "Girnari 5G"; do
        if grep -A 10 "$ssid" /tmp/router_scan.txt | grep -q "freq: 5"; then
            five_ghz_network="$ssid"
            break
        fi
    done

    if [ ! -z "$five_ghz_network" ]; then
        echo "✅ Found 5GHz network: $five_ghz_network"
        echo
        echo "Attempting to connect..."
        echo "You will be prompted for the password."
        echo

        nmcli device wifi connect "$five_ghz_network" --ask

        if [ $? -eq 0 ]; then
            echo "🎉 SUCCESS! Connected to 5GHz network!"
            echo
            echo "Verifying connection details:"
            nmcli connection show "$five_ghz_network" | grep -E "(802-11-wireless|frequency|channel)"
            echo
            echo "Speed test recommendation:"
            echo "Run: speedtest-cli"
            echo "Expected: Much faster speeds than 2.4GHz"
        else
            echo "❌ Connection failed"
            echo "Check password and try again"
        fi
    else
        echo "❌ No 5GHz network found for your router"
        echo
        echo "🔧 ROUTER CONFIGURATION NEEDED:"
        echo "1. Access your router admin panel"
        echo "2. Enable 5GHz radio"
        echo "3. Set 5GHz channel to: 36, 40, 44, or 48"
        echo "4. Use different SSID name for 5GHz (e.g., 'Girnari_5G')"
        echo "5. Save and reboot router"
        echo "6. Run this script again"
    fi

    echo
}

# Provide router configuration guidance
router_config_guidance() {
    print_header "4. Router Configuration Guidance"

    echo "Based on the scan results, here's what you need to do:"
    echo

    five_ghz_count=$(grep -E "freq: 5[0-9]{3}" /tmp/router_scan.txt | wc -l)

    if [ "$five_ghz_count" -eq 0 ]; then
        echo "🚨 URGENT: No 5GHz networks detected in your area!"
        echo
        echo "Your router configuration steps:"
        echo "1. 🌐 Open browser and go to your router admin page:"
        echo "   - Try: http://192.168.1.1"
        echo "   - Or: http://192.168.0.1"
        echo "   - Or: http://10.0.0.1"
        echo
        echo "2. 🔐 Login with admin credentials"
        echo "   - Username: admin, Password: admin"
        echo "   - Or check router label for defaults"
        echo
        echo "3. ⚙️ Navigate to: Wireless/WiFi Settings"
        echo
        echo "4. 📡 5GHz Band Configuration:"
        echo "   ✅ Enable 5GHz Radio: ON"
        echo "   ✅ SSID: Girnari 5G (same name, but ensure it's on 5GHz)"
        echo "   ✅ Channel: 36 (start here)"
        echo "   ✅ Channel Width: 20 MHz"
        echo "   ✅ Mode: 802.11ac (WiFi 5) or 802.11ax (WiFi 6)"
        echo "   ✅ Region: India"
        echo "   ✅ Security: WPA2 or WPA3"
        echo
        echo "5. 💾 Save settings and reboot router"
        echo
        echo "6. 🔄 Run this script again in 2-3 minutes"

    else
        echo "✅ Other 5GHz networks detected - your hardware works!"
        echo
        echo "Your router just needs proper configuration."
        echo "Follow the same steps above to enable 5GHz on your router."
    fi

    echo
    echo "📋 Recommended Channel Priority:"
    echo "   1st choice: Channel 36 (5180 MHz)"
    echo "   2nd choice: Channel 40 (5200 MHz)"
    echo "   3rd choice: Channel 44 (5220 MHz)"
    echo "   4th choice: Channel 48 (5240 MHz)"
    echo
    echo "❌ Avoid: Channels 52-144 (DFS - problematic)"
}

# Main execution
main() {
    echo "Starting 5GHz verification..."
    echo

    check_5ghz_detection
    echo "Press Enter to continue..."
    read

    check_your_router
    echo "Press Enter to continue..."
    read

    test_5ghz_connection
    echo "Press Enter to continue..."
    read

    router_config_guidance

    echo "=== Verification Complete ==="
    echo
    echo "📄 Scan results saved to: /tmp/router_scan.txt"
    echo "🔍 You can examine detailed results with: less /tmp/router_scan.txt"
}

# Run main function
main
