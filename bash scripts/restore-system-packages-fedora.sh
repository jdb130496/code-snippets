#!/bin/bash
# ==============================================================================
# RESTORE SYSTEM PACKAGES SCRIPT
# ==============================================================================
# This script reinstalls system packages that may have been removed by the
# original gimp-git-fedora.sh script (which ran: dnf remove babl gegl exiv2...)
# 
# Run this AFTER cleanup if you want your system packages back
# ==============================================================================

set -e

echo "===================================================================="
echo "RESTORE SYSTEM PACKAGES"
echo "===================================================================="
echo ""
echo "This script will reinstall system packages that may have been"
echo "removed by the original GIMP-git build script:"
echo ""
echo "  - babl (and babl-devel if available)"
echo "  - gegl04 (and gegl04-devel if available)"
echo "  - exiv2 (and exiv2-devel)"
echo "  - libgexiv2 (and libgexiv2-devel)"
echo ""
echo "These are the official Fedora packages from repositories."
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Restore cancelled."
    exit 0
fi

echo ""
echo "===================================================================="
echo "Checking and installing system packages..."
echo "===================================================================="
echo ""

# Function to try installing a package
install_if_available() {
    local package=$1
    echo "Checking $package..."
    if dnf list available "$package" &>/dev/null || dnf list installed "$package" &>/dev/null; then
        if dnf list installed "$package" &>/dev/null; then
            echo "  Already installed: $package"
        else
            echo "  Installing: $package"
            sudo dnf install -y "$package"
        fi
        echo "✓ $package handled"
    else
        echo "⊘ $package not available in repositories (may have different name in your Fedora version)"
    fi
    echo ""
}

# Install babl
echo "--- BABL ---"
install_if_available "babl"
# babl-devel usually doesn't exist as separate package in Fedora
echo ""

# Install gegl
echo "--- GEGL ---"
# In newer Fedora, it's gegl04
install_if_available "gegl04"
install_if_available "gegl04-devel"
# Try old name for older Fedora versions
install_if_available "gegl"
echo ""

# Install exiv2
echo "--- EXIV2 ---"
install_if_available "exiv2"
install_if_available "exiv2-devel"
install_if_available "exiv2-libs"
echo ""

# Install gexiv2
echo "--- GEXIV2 ---"
install_if_available "libgexiv2"
install_if_available "libgexiv2-devel"
echo ""

echo "===================================================================="
echo "Updating library cache..."
echo "===================================================================="
sudo ldconfig
echo "✓ Library cache updated"
echo ""

echo "===================================================================="
echo "Verifying installations..."
echo "===================================================================="
echo ""

# Check what got installed
echo "Installed packages:"
dnf list installed | grep -E "^(babl|gegl|exiv2|gexiv2)" || echo "  (using dnf list to check...)"
echo ""

# Check for libraries
echo "Library files found:"
ldconfig -p | grep -E "(babl|gegl|exiv2|gexiv2)" | head -10 || echo "  No matching libraries in cache"
echo ""

echo "===================================================================="
echo "SYSTEM PACKAGES RESTORED!"
echo "===================================================================="
echo ""
echo "Your system now has the official Fedora packages for:"
echo "  - babl/gegl (for GIMP)"
echo "  - exiv2/gexiv2 (for metadata handling)"
echo ""
echo "These are from Fedora repositories and will be updated normally"
echo "with 'dnf update'."
echo ""
echo "Note: If you want to use system GIMP (not GIMP-git), install it with:"
echo "  sudo dnf install gimp"
echo "===================================================================="
