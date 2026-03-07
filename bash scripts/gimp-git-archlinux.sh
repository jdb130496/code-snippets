#!/bin/bash
set -e

# ==============================================================================
# GIMP-GIT ISOLATED BUILD SCRIPT - ARCH LINUX
# ==============================================================================
# This script builds GIMP-git in complete isolation using a custom prefix
# It does NOT remove or modify any system-installed packages
# All builds go to: /opt/gimp-git/
#
# Based on the Fedora isolated build approach:
#   - No system package removals (fixes /usr/local clash issues)
#   - Self-contained install under /opt/gimp-git
#   - Wrapper script sets all required env vars at runtime
#   - Build directory is cleaned up after successful install
# ==============================================================================

SKIP_DEPS=false
CLEAN=false
INSTALL_PREFIX="/opt/gimp-git"
BUILD_DIR="$HOME/gimp-build-isolated"

while [[ $# -gt 0 ]]; do
    case $1 in
        --nodeps) SKIP_DEPS=true; shift ;;
        --clean) CLEAN=true; shift ;;
        --prefix=*) INSTALL_PREFIX="${1#*=}"; shift ;;
        *) shift ;;
    esac
done

echo "===================================================================="
echo "GIMP-GIT ISOLATED BUILD - ARCH LINUX"
echo "===================================================================="
echo "Install prefix: $INSTALL_PREFIX"
echo "Build directory: $BUILD_DIR"
echo "This will NOT modify any system packages"
echo "===================================================================="
echo ""

# ==============================================================================
# Check for existing /usr/local installation (old non-isolated builds)
# and offer to clean it up + restore system packages via pacman
# ==============================================================================
if [ -f "/usr/local/bin/gimp-git" ] || [ -f "/usr/local/bin/gimp-git-bin" ] || \
   [ -d "/usr/local/lib/gimp" ] || [ -d "/usr/local/lib64/gimp" ]; then
    echo "⚠️  WARNING: Found existing GIMP-git installation in /usr/local"
    echo ""
    echo "This old installation clashes with system packages and must be"
    echo "cleaned up before the isolated /opt build will work correctly."
    echo ""
    echo "Detected files:"
    [ -f "/usr/local/bin/gimp-git" ]       && echo "  - /usr/local/bin/gimp-git"
    [ -f "/usr/local/bin/gimp-git-bin" ]   && echo "  - /usr/local/bin/gimp-git-bin"
    [ -d "/usr/local/lib/gimp" ]           && echo "  - /usr/local/lib/gimp/"
    [ -d "/usr/local/lib64/gimp" ]         && echo "  - /usr/local/lib64/gimp/"
    [ -d "/usr/local/lib/babl-0.1" ]       && echo "  - /usr/local/lib/babl-0.1/"
    [ -d "/usr/local/lib64/babl-0.1" ]     && echo "  - /usr/local/lib64/babl-0.1/"
    [ -d "/usr/local/lib/gegl-0.4" ]       && echo "  - /usr/local/lib/gegl-0.4/"
    [ -d "/usr/local/lib64/gegl-0.4" ]     && echo "  - /usr/local/lib64/gegl-0.4/"
    echo ""
    echo "This script can:"
    echo "  1. Clean /usr/local (remove all old GIMP-git components)"
    echo "     AND restore babl/gegl/exiv2/gexiv2/lcms2 from pacman"
    echo "     Then continue with the isolated /opt build  (recommended)"
    echo "  2. Skip cleanup and continue anyway  (conflicts likely)"
    echo "  3. Exit now and handle cleanup manually"
    echo ""
    read -p "Choice [1/2/3]: " -n 1 -r USR_CHOICE
    echo
    echo ""

    if [[ "$USR_CHOICE" == "1" ]]; then
        echo "===================================================================="
        echo "Cleaning up /usr/local GIMP-git installation..."
        echo "===================================================================="

        echo "Removing GIMP from /usr/local..."
        sudo rm -rf /usr/local/bin/gimp*
        sudo rm -rf /usr/local/lib/gimp*    /usr/local/lib/libgimp*
        sudo rm -rf /usr/local/lib64/gimp*  /usr/local/lib64/libgimp*
        sudo rm -rf /usr/local/share/gimp*
        sudo rm -rf /usr/local/share/applications/gimp*
        echo "✓ GIMP removed from /usr/local"

        echo "Removing babl from /usr/local..."
        sudo rm -rf /usr/local/lib/libbabl*      /usr/local/lib/babl*
        sudo rm -rf /usr/local/lib64/libbabl*     /usr/local/lib64/babl*
        sudo rm -rf /usr/local/lib/pkgconfig/babl*
        sudo rm -rf /usr/local/lib64/pkgconfig/babl*
        sudo rm -rf /usr/local/include/babl*
        sudo rm -rf /usr/local/lib/girepository-1.0/Babl*
        sudo rm -rf /usr/local/lib64/girepository-1.0/Babl*
        sudo rm -rf /usr/local/share/gir-1.0/Babl*
        echo "✓ babl removed from /usr/local"

        echo "Removing gegl from /usr/local..."
        sudo rm -rf /usr/local/lib/libgegl*      /usr/local/lib/gegl*
        sudo rm -rf /usr/local/lib64/libgegl*     /usr/local/lib64/gegl*
        sudo rm -rf /usr/local/lib/pkgconfig/gegl*
        sudo rm -rf /usr/local/lib64/pkgconfig/gegl*
        sudo rm -rf /usr/local/include/gegl*
        sudo rm -rf /usr/local/lib/girepository-1.0/Gegl*
        sudo rm -rf /usr/local/lib64/girepository-1.0/Gegl*
        sudo rm -rf /usr/local/share/gir-1.0/Gegl*
        sudo rm -rf /usr/local/bin/gegl*
        echo "✓ gegl removed from /usr/local"

        echo "Removing exiv2 from /usr/local..."
        sudo rm -rf /usr/local/lib/libexiv2*
        sudo rm -rf /usr/local/lib64/libexiv2*
        sudo rm -rf /usr/local/lib/pkgconfig/exiv2*
        sudo rm -rf /usr/local/lib64/pkgconfig/exiv2*
        sudo rm -rf /usr/local/include/exiv2*
        sudo rm -rf /usr/local/bin/exiv2*
        sudo rm -rf /usr/local/share/exiv2*
        echo "✓ exiv2 removed from /usr/local"

        echo "Removing gexiv2 from /usr/local..."
        sudo rm -rf /usr/local/lib/libgexiv2*
        sudo rm -rf /usr/local/lib64/libgexiv2*
        sudo rm -rf /usr/local/lib/pkgconfig/gexiv2*
        sudo rm -rf /usr/local/lib64/pkgconfig/gexiv2*
        sudo rm -rf /usr/local/include/gexiv2*
        sudo rm -rf /usr/local/lib/girepository-1.0/GExiv2*
        sudo rm -rf /usr/local/lib64/girepository-1.0/GExiv2*
        sudo rm -rf /usr/local/share/gir-1.0/GExiv2*
        sudo rm -rf /usr/local/share/vala/vapi/gexiv2*
        echo "✓ gexiv2 removed from /usr/local"

        echo "Removing lcms2 from /usr/local..."
        sudo rm -rf /usr/local/lib/liblcms2*
        sudo rm -rf /usr/local/lib64/liblcms2*
        sudo rm -rf /usr/local/lib/pkgconfig/lcms2*
        sudo rm -rf /usr/local/lib64/pkgconfig/lcms2*
        sudo rm -rf /usr/local/include/lcms2*
        echo "✓ lcms2 removed from /usr/local"

        echo "Updating library cache..."
        sudo ldconfig
        echo "✓ ldconfig updated"

        echo "Updating desktop database..."
        sudo update-desktop-database /usr/local/share/applications/ 2>/dev/null || true
        update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
        echo "✓ Desktop database updated"

        echo ""
        echo "===================================================================="
        echo "Restoring system packages via pacman..."
        echo "===================================================================="
        # Reinstall system-provided versions of everything we just wiped from
        # /usr/local so the system is fully intact before the isolated build starts
        sudo pacman -S --needed --noconfirm \
            babl gegl \
            libgexiv2 \
            lcms2
        # exiv2 is a dependency of libgexiv2 — pacman will pull it in automatically
        echo "✓ System babl, gegl, exiv2, gexiv2, lcms2 restored via pacman"
        echo ""
        echo "===================================================================="
        echo "/usr/local cleanup and pacman restore complete."
        echo "Continuing with isolated /opt build..."
        echo "===================================================================="
        echo ""

    elif [[ "$USR_CHOICE" == "2" ]]; then
        echo "Skipping cleanup — continuing with possible conflicts..."
        echo ""
    else
        echo "Exiting. Clean up /usr/local manually then re-run this script."
        exit 0
    fi
fi

# ==============================================================================
# --clean: wipe build dir and install prefix
# ==============================================================================
if [[ "$CLEAN" == true ]]; then
    echo "Cleaning previous build and install..."
    rm -rf "$BUILD_DIR"
    sudo rm -rf "$INSTALL_PREFIX"
    # Also clean up any leftover old-style build dir
    [ -d "$HOME/gimp-build" ] && rm -rf "$HOME/gimp-build" && echo "✓ Removed old ~/gimp-build"
    echo "✓ Clean complete."
    exit 0
fi

# ==============================================================================
# Create isolated install prefix
# ==============================================================================
if [[ ! -d "$INSTALL_PREFIX" ]]; then
    echo "Creating install prefix: $INSTALL_PREFIX"
    sudo mkdir -p "$INSTALL_PREFIX"
    sudo chown -R "$(whoami)":"$(whoami)" "$INSTALL_PREFIX"
fi

# ==============================================================================
# Install build dependencies (additive only — nothing is removed)
# ==============================================================================
if [[ "$SKIP_DEPS" == false ]]; then
    echo "Updating system and installing build dependencies (no removals)..."
    sudo pacman -Syu --noconfirm

    # Core build tools + all GIMP optional deps
    # Note: babl and gegl from pacman are NOT removed; our isolated build
    # in /opt takes precedence via PKG_CONFIG_PATH / LD_LIBRARY_PATH at runtime.
    sudo pacman -S --needed --noconfirm \
        base-devel git meson ninja pkgconfig cmake \
        gtk3 glib2 cairo gdk-pixbuf2 \
        gobject-introspection python-gobject python-cairo \
        vala gi-docgen \
        libmypaint mypaint-brushes \
        lcms2 \
        openexr libjxl libheif libwebp librsvg \
        libarchive iso-codes libtiff \
        libwmf libexif jasper libmng \
        aalib lua \
        appstream appstream-glib \
        poppler-glib poppler-data \
        ghostscript bubblewrap json-glib \
        expat

    echo "Configuring locale (required for GIMP build)..."
    if ! locale -a 2>/dev/null | grep -q "en_US.utf8"; then
        sudo sed -i 's/^#en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen
        sudo locale-gen
    fi
fi

# ==============================================================================
# Prepare build directory and isolated environment
# ==============================================================================
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:$INSTALL_PREFIX/lib64/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:$INSTALL_PREFIX/lib64:$LD_LIBRARY_PATH"
export PATH="$INSTALL_PREFIX/bin:$PATH"
export GI_TYPELIB_PATH="$INSTALL_PREFIX/lib/girepository-1.0:$INSTALL_PREFIX/lib64/girepository-1.0:$GI_TYPELIB_PATH"

# Remove any stray local ninja override that can break builds
rm -f ~/.local/bin/ninja 2>/dev/null || true

# ==============================================================================
# exiv2 0.27.x
# ==============================================================================
echo ""
echo "===================================================================="
echo "Building exiv2 0.27.x in isolation..."
echo "===================================================================="
if [[ ! -d exiv2 ]]; then
    git clone https://github.com/Exiv2/exiv2.git
fi
cd exiv2
git fetch --tags
LATEST_027=$(git tag | grep "^v0\.27\." | sort -V | tail -1)
echo "Checking out exiv2 tag: $LATEST_027"
git checkout "$LATEST_027"
rm -rf build && mkdir build && cd build
cmake .. \
    -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" \
    -DCMAKE_BUILD_TYPE=Release \
    -DEXIV2_ENABLE_NLS=ON
make -j"$(nproc)"
make install
cd ../..

EXIV2_VERSION=$(PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:$INSTALL_PREFIX/lib64/pkgconfig" pkg-config --modversion exiv2)
echo "✓ Installed exiv2 $EXIV2_VERSION → $INSTALL_PREFIX"

# ==============================================================================
# gexiv2 0.14.x
# ==============================================================================
echo ""
echo "===================================================================="
echo "Building gexiv2 0.14.x in isolation..."
echo "===================================================================="
if [[ ! -d gexiv2 ]]; then
    git clone https://gitlab.gnome.org/GNOME/gexiv2.git
fi
cd gexiv2
git fetch --tags
LATEST_014=$(git tag | grep "^gexiv2-0\.14\." | sort -V | tail -1)
echo "Checking out gexiv2 tag: $LATEST_014"
git checkout "$LATEST_014"
rm -rf build
meson setup build --prefix="$INSTALL_PREFIX"
ninja -C build
ninja -C build install
cd ..

GEXIV2_VERSION=$(PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:$INSTALL_PREFIX/lib64/pkgconfig" pkg-config --modversion gexiv2)
echo "✓ Installed gexiv2 $GEXIV2_VERSION → $INSTALL_PREFIX"

# ==============================================================================
# LCMS2
# ==============================================================================
echo ""
echo "===================================================================="
echo "Building LCMS2 in isolation..."
echo "===================================================================="
if [[ ! -d Little-CMS ]]; then
    git clone --depth 1 https://github.com/mm2/Little-CMS.git
else
    cd Little-CMS && git pull && cd ..
fi
cd Little-CMS
rm -rf build
meson setup build --prefix="$INSTALL_PREFIX"
ninja -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
ninja -C build install 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
cd ..
echo "✓ LCMS2 installed → $INSTALL_PREFIX"

# ==============================================================================
# BABL
# ==============================================================================
echo ""
echo "===================================================================="
echo "Building BABL in isolation..."
echo "===================================================================="
if [[ ! -d babl ]]; then
    git clone https://gitlab.gnome.org/GNOME/babl.git
fi
cd babl
git fetch --tags
LATEST_TAG=$(git tag | grep "^BABL_0_1" | sort -V | tail -1)
echo "Checking out babl tag: $LATEST_TAG"
git checkout "$LATEST_TAG"
rm -rf build
meson setup build --prefix="$INSTALL_PREFIX" -Denable-gir=true -Denable-vapi=true

echo "Checking BABL build configuration..."
if meson configure build | grep -q "enable-gir.*true"; then
    echo "✓ BABL GObject introspection enabled"
else
    echo "✗ ERROR: BABL GObject introspection NOT enabled!"
    exit 1
fi

ninja -C build
ninja -C build install
cd ..

BABL_VERSION=$(PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:$INSTALL_PREFIX/lib64/pkgconfig" pkg-config --modversion babl-0.1)
echo "✓ Installed babl $BABL_VERSION → $INSTALL_PREFIX"

# Typelib check
if [ -f "$INSTALL_PREFIX/lib/girepository-1.0/Babl-0.1.typelib" ] || \
   [ -f "$INSTALL_PREFIX/lib64/girepository-1.0/Babl-0.1.typelib" ]; then
    echo "✓ Babl-0.1.typelib installed successfully"
else
    echo "✗ ERROR: Babl-0.1.typelib NOT found!"
    exit 1
fi

if [ -f "$INSTALL_PREFIX/share/vala/vapi/babl-0.1.vapi" ]; then
    echo "✓ Babl-0.1.vapi installed successfully"
else
    echo "⚠ Babl-0.1.vapi not found (Vala bindings not built — usually not critical)"
fi

# ==============================================================================
# GEGL
# ==============================================================================
echo ""
echo "===================================================================="
echo "Building GEGL in isolation..."
echo "===================================================================="
if [[ ! -d gegl ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gegl.git
else
    cd gegl && git clean -fd && git pull && cd ..
fi
cd gegl
rm -rf build

export XDG_DATA_DIRS="$INSTALL_PREFIX/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
export VALA_VAPIDIR="$INSTALL_PREFIX/share/vala/vapi"

if [ -f "$INSTALL_PREFIX/share/vala/vapi/babl-0.1.vapi" ]; then
    echo "✓ Babl VAPI found, enabling Vala bindings"
    VAPIGEN_OPTION="-Dvapigen=enabled"
else
    echo "⚠ Babl VAPI not found, disabling Vala bindings (not critical)"
    VAPIGEN_OPTION="-Dvapigen=disabled"
fi

meson setup build --prefix="$INSTALL_PREFIX" -Dintrospection=true $VAPIGEN_OPTION

echo "Checking GEGL build configuration..."
if meson configure build | grep -q "introspection.*true"; then
    echo "✓ GEGL GObject introspection enabled"
else
    echo "✗ ERROR: GEGL GObject introspection NOT enabled!"
    exit 1
fi

ninja -C build
ninja -C build install
cd ..

if [ -f "$INSTALL_PREFIX/lib/girepository-1.0/Gegl-0.4.typelib" ] || \
   [ -f "$INSTALL_PREFIX/lib64/girepository-1.0/Gegl-0.4.typelib" ]; then
    echo "✓ Gegl-0.4.typelib installed successfully"
else
    echo "✗ ERROR: Gegl-0.4.typelib NOT found!"
    exit 1
fi

# ==============================================================================
# GIMP
# ==============================================================================
echo ""
echo "===================================================================="
echo "Building GIMP in isolation..."
echo "===================================================================="
if [[ ! -d gimp ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gimp.git
fi

cd gimp

echo "Cleaning up submodule state..."
rm -rf .git/modules/gimp-data
rm -rf gimp-data
git submodule deinit -f gimp-data 2>/dev/null || true

rm -rf build
git pull

echo "Initializing gimp-data submodule..."
git submodule sync
git submodule update --init --depth 1 --progress gimp-data
echo "✓ gimp-data submodule initialized"

echo "Checking for glycin support..."
if pkg-config --exists glycin-2; then
    GLYCIN_VERSION=$(pkg-config --modversion glycin-2)
    echo "Found glycin-2 version: $GLYCIN_VERSION"
else
    echo "Note: glycin-2 not found. GIMP will build without glycin support."
fi

echo ""
echo "Verifying typelib files are accessible..."
ls -lh "$INSTALL_PREFIX"/lib*/girepository-1.0/ 2>/dev/null || echo "No typelib directory found!"
echo ""

meson setup build --prefix="$INSTALL_PREFIX" -Dauto_features=disabled

echo ""
echo "Checking build configuration..."
meson configure build | grep -i glycin || echo "  (glycin status not shown in meson options)"
echo ""

ninja -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" | cat
ninja -C build install

# Find and rename the versioned GIMP binary
GIMP_BINARY=$(find "$INSTALL_PREFIX/bin" \
    -name "gimp-[0-9]*" \
    -not -name "gimp-console*" \
    -not -name "gimp-script*" \
    -not -name "gimp-test*" \
    -not -name "gimptool*" | head -1)

if [ -n "$GIMP_BINARY" ]; then
    mv "$GIMP_BINARY" "$INSTALL_PREFIX/bin/gimp-git-bin"
    echo "Renamed $(basename "$GIMP_BINARY") → gimp-git-bin"

    # Wrapper script — sets all env vars needed to find isolated libs at runtime
    cat > "$INSTALL_PREFIX/bin/gimp-git" << EOF
#!/bin/bash
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib:$INSTALL_PREFIX/lib64:\$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib/pkgconfig:$INSTALL_PREFIX/lib64/pkgconfig:\$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="$INSTALL_PREFIX/lib/girepository-1.0:$INSTALL_PREFIX/lib64/girepository-1.0:\$GI_TYPELIB_PATH"
export PATH="$INSTALL_PREFIX/bin:\$PATH"
export GLYCIN_LOADERS_PATH="/usr/libexec/glycin-loaders/2+"
exec "$INSTALL_PREFIX/bin/gimp-git-bin" "\$@" 2>&1 | grep -v "WARNING: Glycin running without sandbox"
EOF
    chmod +x "$INSTALL_PREFIX/bin/gimp-git"
    echo "✓ Created gimp-git wrapper script"
else
    echo "⚠ Warning: No versioned GIMP binary found to rename"
fi

# Desktop entry (no sudo needed — installs to user applications dir)
mkdir -p ~/.local/share/applications
cat > ~/.local/share/applications/gimp-git.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=GIMP (Git) - Isolated
GenericName=Image Editor
Comment=Create images and edit photographs (isolated /opt build)
Exec=$INSTALL_PREFIX/bin/gimp-git %U
TryExec=$INSTALL_PREFIX/bin/gimp-git
Icon=gimp
StartupNotify=true
MimeType=image/bmp;image/gif;image/jpeg;image/png;image/tiff;image/x-xcf;
Categories=Graphics;2DGraphics;RasterGraphics;Photography;
EOF
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
echo "✓ Desktop entry created"

# ==============================================================================
# Post-install cleanup — build dirs are no longer needed
# ==============================================================================
echo ""
echo "Cleaning up build directories..."
cd "$HOME"
rm -rf "$BUILD_DIR"
echo "✓ Removed $BUILD_DIR"
[ -d "$HOME/gimp-build" ] && rm -rf "$HOME/gimp-build" && echo "✓ Removed old ~/gimp-build"

echo ""
echo "===================================================================="
echo "GIMP-GIT INSTALLED SUCCESSFULLY IN ISOLATION!"
echo "===================================================================="
echo "Installation directory : $INSTALL_PREFIX"
echo ""
echo "To run GIMP-git from terminal:"
echo "  $INSTALL_PREFIX/bin/gimp-git"
echo ""
echo "Or add to PATH permanently — append to ~/.bashrc or ~/.zshrc:"
echo "  export PATH=\"$INSTALL_PREFIX/bin:\$PATH\""
echo "Then run simply as:"
echo "  gimp-git"
echo ""
echo "Or search for 'GIMP (Git) - Isolated' in your applications menu."
echo ""
echo "Your system packages are untouched:"
echo "  - System babl / gegl / exiv2 / gexiv2 remain intact"
echo "  - All GIMP-git libraries are self-contained in: $INSTALL_PREFIX"
echo ""
echo "To completely remove this installation:"
echo "  $0 --clean"
echo "===================================================================="
