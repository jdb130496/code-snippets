#!/bin/bash
# ==============================================================================
# GIMP-GIT CLEANUP SCRIPT
# ==============================================================================
# This script completely removes the old GIMP-git installation from /usr/local
# Run this before using the isolated build script if you previously installed
# GIMP-git to /usr/local
# ==============================================================================

set -e

echo "===================================================================="
echo "GIMP-GIT CLEANUP - Removing /usr/local installation"
echo "===================================================================="
echo ""
echo "This will remove:"
echo "  - All GIMP binaries and libraries from /usr/local"
echo "  - babl, gegl, exiv2, gexiv2, lcms2 from /usr/local"
echo "  - Build directory: ~/gimp-build"
echo ""
read -p "Continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

echo ""
echo "Removing GIMP from /usr/local..."
sudo rm -rf /usr/local/bin/gimp* 
sudo rm -rf /usr/local/lib*/gimp* 
sudo rm -rf /usr/local/lib*/libgimp* 
sudo rm -rf /usr/local/share/gimp* 
sudo rm -rf /usr/local/share/applications/gimp*
echo "✓ GIMP removed"

echo ""
echo "Removing babl from /usr/local..."
sudo rm -rf /usr/local/lib*/libbabl*
sudo rm -rf /usr/local/lib*/babl*
sudo rm -rf /usr/local/lib*/pkgconfig/babl*
sudo rm -rf /usr/local/include/babl*
sudo rm -rf /usr/local/lib*/girepository-1.0/Babl*
sudo rm -rf /usr/local/share/gir-1.0/Babl*
echo "✓ babl removed"

echo ""
echo "Removing gegl from /usr/local..."
sudo rm -rf /usr/local/lib*/libgegl*
sudo rm -rf /usr/local/lib*/gegl*
sudo rm -rf /usr/local/lib*/pkgconfig/gegl*
sudo rm -rf /usr/local/include/gegl*
sudo rm -rf /usr/local/lib*/girepository-1.0/Gegl*
sudo rm -rf /usr/local/share/gir-1.0/Gegl*
sudo rm -rf /usr/local/bin/gegl*
echo "✓ gegl removed"

echo ""
echo "Removing exiv2 from /usr/local..."
sudo rm -rf /usr/local/lib*/libexiv2*
sudo rm -rf /usr/local/lib*/pkgconfig/exiv2*
sudo rm -rf /usr/local/include/exiv2*
sudo rm -rf /usr/local/bin/exiv2*
sudo rm -rf /usr/local/share/exiv2*
sudo rm -rf /usr/local/share/man/man1/exiv2*
echo "✓ exiv2 removed"

echo ""
echo "Removing gexiv2 from /usr/local..."
sudo rm -rf /usr/local/lib*/libgexiv2*
sudo rm -rf /usr/local/lib*/pkgconfig/gexiv2*
sudo rm -rf /usr/local/include/gexiv2*
sudo rm -rf /usr/local/lib*/girepository-1.0/GExiv2*
sudo rm -rf /usr/local/share/gir-1.0/GExiv2*
sudo rm -rf /usr/local/share/vala/vapi/gexiv2*
echo "✓ gexiv2 removed"

echo ""
echo "Removing lcms2 from /usr/local..."
sudo rm -rf /usr/local/lib*/liblcms2*
sudo rm -rf /usr/local/lib*/pkgconfig/lcms2*
sudo rm -rf /usr/local/include/lcms2*
echo "✓ lcms2 removed"

echo ""
echo "Removing build directory..."
rm -rf ~/gimp-build
rm -rf ~/gimp-build-isolated 2>/dev/null || true
echo "✓ Build directories removed"

echo ""
echo "Updating library cache..."
sudo ldconfig
echo "✓ Library cache updated"

echo ""
echo "Removing desktop database entries..."
sudo update-desktop-database /usr/local/share/applications/ 2>/dev/null || true
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
echo "✓ Desktop database updated"

echo ""
echo "===================================================================="
echo "CLEANUP COMPLETE!"
echo "===================================================================="
echo ""
echo "All GIMP-git components removed from /usr/local"
echo "You can now run the isolated build script safely."
echo ""
echo "Note: Your system packages (from dnf) are unaffected."
echo "===================================================================="
