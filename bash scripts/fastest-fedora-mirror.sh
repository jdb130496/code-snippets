#!/bin/bash
# Fastest Fedora Rawhide Mirror Selector
# Tests all mirrors and pins the fastest one in fedora-rawhide.repo

REPO_FILE="/etc/yum.repos.d/fedora-rawhide.repo"
ARCH=$(uname -m)
COUNTRY="${1:-IN}"  # Default to India, pass country code as argument
TIMEOUT=5
BEST_TIME=999
BEST_URL=""

echo "=== Fedora Rawhide Mirror Speed Test ==="
echo "Country: $COUNTRY | Arch: $ARCH"
echo ""

# Fetch mirrorlist
MIRRORS=$(curl -s "https://mirrors.fedoraproject.org/mirrorlist?repo=rawhide&arch=${ARCH}&country=${COUNTRY}" | grep -v "^#" | grep -v "^$")

# If no country-specific mirrors found, fallback to global
if [ -z "$MIRRORS" ]; then
    echo "No mirrors found for country $COUNTRY, falling back to global list..."
    MIRRORS=$(curl -s "https://mirrors.fedoraproject.org/mirrorlist?repo=rawhide&arch=${ARCH}" | grep -v "^#" | grep -v "^$" | head -20)
fi

echo "Testing mirrors..."
echo ""

while IFS= read -r url; do
    [ -z "$url" ] && continue
    TIME=$(curl -o /dev/null -s -w "%{time_total}" --max-time $TIMEOUT "${url}repodata/repomd.xml" 2>/dev/null)
    
    # Check if curl succeeded
    if [ $? -eq 0 ] && [ "$(echo "$TIME > 0" | bc -l)" -eq 1 ]; then
        echo "  ${TIME}s -> $url"
        if [ "$(echo "$TIME < $BEST_TIME" | bc -l)" -eq 1 ]; then
            BEST_TIME=$TIME
            BEST_URL=$url
        fi
    else
        echo "  TIMEOUT/FAIL -> $url"
    fi
done <<< "$MIRRORS"

echo ""
echo "=== Winner: ${BEST_TIME}s ==="
echo "  $BEST_URL"
echo ""

if [ -z "$BEST_URL" ]; then
    echo "ERROR: No working mirrors found. Keeping existing config."
    exit 1
fi

# Backup current repo file
sudo cp "$REPO_FILE" "${REPO_FILE}.bak"
echo "Backed up $REPO_FILE to ${REPO_FILE}.bak"

# Update repo file - comment out metalink, set baseurl in [rawhide] section only
sudo python3 - "$REPO_FILE" "$BEST_URL" << 'PYEOF'
import sys
import re

repo_file = sys.argv[1]
best_url = sys.argv[2]

with open(repo_file, 'r') as f:
    content = f.read()

# Process only the [rawhide] section (not debuginfo or source)
def update_rawhide_section(content, best_url):
    lines = content.split('\n')
    in_rawhide = False
    result = []
    
    for line in lines:
        # Detect section headers
        if line.startswith('['):
            in_rawhide = line.strip() == '[rawhide]'
        
        if in_rawhide:
            # Comment out metalink
            if line.strip().startswith('metalink='):
                result.append('#' + line)
                continue
            # Remove old baseurl (commented or not)
            if line.strip().startswith('#baseurl=') or line.strip().startswith('baseurl='):
                result.append(f'baseurl={best_url}')
                continue
        
        result.append(line)
    
    return '\n'.join(result)

new_content = update_rawhide_section(content, best_url)

with open(repo_file, 'w') as f:
    f.write(new_content)

print(f"Updated {repo_file} with baseurl={best_url}")
PYEOF

echo ""
echo "=== Verifying change ==="
grep -A4 '^\[rawhide\]' "$REPO_FILE"

echo ""
echo "=== Cleaning metadata and testing ==="
sudo dnf clean metadata
echo "Done. Run 'sudo dnf upgrade --refresh' to test."
