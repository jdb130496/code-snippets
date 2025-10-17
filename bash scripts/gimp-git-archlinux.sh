#!/bin/bash
set -e

SKIP_DEPS=false
SKIP_TESTS=false
CLEAN=false
REBUILD_BABL=false
REBUILD_GEGL=false
REBUILD_GIMP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --nodeps) SKIP_DEPS=true; shift ;;
        --nocheck) SKIP_TESTS=true; shift ;;
        --clean) CLEAN=true; shift ;;
        --rebuild-babl) REBUILD_BABL=true; shift ;;
        --rebuild-gegl) REBUILD_GEGL=true; shift ;;
        --rebuild-gimp) REBUILD_GIMP=true; shift ;;
        --rebuild-all) REBUILD_BABL=true; REBUILD_GEGL=true; REBUILD_GIMP=true; shift ;;
        *) shift ;;
    esac
done

if [[ "$CLEAN" == true ]]; then
    rm -rf ~/gimp-build
    sudo rm -rf /usr/local/bin/gimp* /usr/local/lib*/gimp* /usr/local/lib*/libgimp* /usr/local/share/gimp* /usr/local/share/applications/gimp* 2>/dev/null || true
    sudo ldconfig
    echo "Clean complete. Exiting."
    exit 0
fi

if [[ "$SKIP_DEPS" == false ]]; then
    echo "Installing dependencies..."
    sudo pacman -S --needed base-devel git meson ninja pkgconfig gtk3 glib2 cairo gdk-pixbuf2 \
        bubblewrap json-glib gobject-introspection python-gobject vala lcms2 \
        mypaint-brushes1 poppler-glib poppler-data libwmf openexr libjxl \
        libheif libwebp librsvg libarchive appstream-glib iso-codes python-cairo \
        aalib libexif jasper libgexiv2 ghostscript libmng libtiff lua gi-docgen
    
    # Try to remove system babl/gegl/libmypaint packages that conflict with our custom build
    # We'll skip libmypaint for now since it depends on system babl/gegl
    echo "Note: Keeping system babl/gegl due to libmypaint dependency."
    echo "Our custom babl/gegl in /usr/local will take precedence via PKG_CONFIG_PATH."
fi

mkdir -p ~/gimp-build
cd ~/gimp-build

export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:/usr/lib/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"

# Function to check if a component needs building
needs_build() {
    local component=$1
    local version_check=$2
    
    if ! command -v pkg-config &> /dev/null; then
        return 0  # Need to build if pkg-config missing
    fi
    
    if ! pkg-config --exists "$version_check" 2>/dev/null; then
        return 0  # Need to build if package not found
    fi
    
    return 1  # Already built
}

# ====================
# BUILD BABL
# ====================
if [[ "$REBUILD_BABL" == true ]] || needs_build "babl" "babl-0.1"; then
    echo "========================================"
    echo "Building BABL..."
    echo "========================================"
    
    if [[ ! -d babl ]]; then
        git clone https://gitlab.gnome.org/GNOME/babl.git
        cd babl
        git fetch --tags
        LATEST_TAG=$(git tag | grep "^BABL_0_1" | sort -V | tail -1)
        echo "Checking out latest babl tag: $LATEST_TAG"
        git checkout $LATEST_TAG
        cd ..
    else
        cd babl
        git fetch --tags
        LATEST_TAG=$(git tag | grep "^BABL_0_1" | sort -V | tail -1)
        CURRENT_TAG=$(git describe --tags 2>/dev/null || echo "none")
        if [[ "$CURRENT_TAG" != "$LATEST_TAG" ]] || [[ "$REBUILD_BABL" == true ]]; then
            echo "Updating to latest babl tag: $LATEST_TAG"
            git checkout $LATEST_TAG
        else
            echo "Already on latest babl tag: $LATEST_TAG"
        fi
        cd ..
    fi

    cd babl
    rm -rf build
    meson setup build --prefix=/usr/local -Denable-gir=true

    echo "Checking BABL build configuration..."
    if meson configure build | grep -q "enable-gir.*true"; then
        echo "✓ BABL GObject introspection enabled"
    else
        echo "✗ ERROR: BABL GObject introspection NOT enabled!"
        echo "This is required for Python plugins. Check if gobject-introspection is installed."
        exit 1
    fi

    ninja -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
    sudo ninja -C build install 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
    sudo ldconfig

    # Verify babl version and typelib
    BABL_VERSION=$(pkg-config --modversion babl-0.1)
    echo "✓ Installed babl version: $BABL_VERSION"

    MAJOR_MINOR=$(echo "$BABL_VERSION" | cut -d. -f1-2)
    PATCH=$(echo "$BABL_VERSION" | cut -d. -f3)
    if [[ "$MAJOR_MINOR" == "0.1" ]] && [[ "$PATCH" -lt 116 ]]; then
        echo "ERROR: babl version $BABL_VERSION is less than required 0.1.116"
        exit 1
    fi

    if [ -f "/usr/local/lib64/girepository-1.0/Babl-0.1.typelib" ] || [ -f "/usr/local/lib/girepository-1.0/Babl-0.1.typelib" ]; then
        echo "✓ Babl-0.1.typelib installed successfully"
    else
        echo "✗ ERROR: Babl-0.1.typelib NOT found!"
        echo "Introspection build may have failed."
        exit 1
    fi
    cd ..
else
    echo "========================================"
    echo "BABL already built - skipping"
    echo "========================================"
    BABL_VERSION=$(pkg-config --modversion babl-0.1)
    echo "Current version: $BABL_VERSION"
    echo "Use --rebuild-babl to force rebuild"
    echo ""
fi

# ====================
# BUILD GEGL
# ====================
if [[ "$REBUILD_GEGL" == true ]] || [[ "$REBUILD_BABL" == true ]] || needs_build "gegl" "gegl-0.4"; then
    echo "========================================"
    echo "Building GEGL..."
    echo "========================================"
    
    if [[ ! -d gegl ]]; then
        git clone --depth 1 https://gitlab.gnome.org/GNOME/gegl.git
    else
        cd gegl && git pull && cd ..
    fi

    cd gegl
    rm -rf build
    meson setup build --prefix=/usr/local -Dintrospection=true

    echo "Checking GEGL build configuration..."
    if meson configure build | grep -q "introspection.*true"; then
        echo "✓ GEGL GObject introspection enabled"
    else
        echo "✗ ERROR: GEGL GObject introspection NOT enabled!"
        echo "This is required for Python plugins. Check dependencies."
        exit 1
    fi

    ninja -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
    sudo ninja -C build install 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
    sudo ldconfig

    if [ -f "/usr/local/lib64/girepository-1.0/Gegl-0.4.typelib" ] || [ -f "/usr/local/lib/girepository-1.0/Gegl-0.4.typelib" ]; then
        echo "✓ Gegl-0.4.typelib installed successfully"
    else
        echo "✗ ERROR: Gegl-0.4.typelib NOT found!"
        echo "Introspection build may have failed."
        exit 1
    fi

    # Create ldconfig configuration for /usr/local libraries
    echo "/usr/local/lib64" | sudo tee /etc/ld.so.conf.d/usr-local.conf > /dev/null
    echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf.d/usr-local.conf > /dev/null
    sudo ldconfig
    cd ..
else
    echo "========================================"
    echo "GEGL already built - skipping"
    echo "========================================"
    GEGL_VERSION=$(pkg-config --modversion gegl-0.4)
    echo "Current version: $GEGL_VERSION"
    echo "Use --rebuild-gegl to force rebuild"
    echo ""
fi

# ====================
# BUILD GIMP
# ====================
echo "========================================"
echo "Building GIMP..."
echo "========================================"

# Clone repositories at the build root level
if [[ ! -d gimp ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gimp.git
fi

if [[ ! -d gimp-data ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gimp-data.git
fi

# Update gimp-data first (it's at build root)
cd gimp-data
git pull
cd ..

# Now handle gimp directory
cd gimp

# Remove existing symlink or directory called gimp-data inside gimp/
if [ -L gimp-data ]; then
    rm -f gimp-data
elif [ -d gimp-data ]; then
    rm -rf gimp-data
fi

if [[ "$REBUILD_GIMP" == true ]] || [[ ! -d build ]]; then
    rm -rf build
    git pull
    ln -sf ../gimp-data .
else
    echo "Build directory exists. Checking for updates..."
    BEFORE=$(git rev-parse HEAD)
    git pull
    AFTER=$(git rev-parse HEAD)
    
    if [[ "$BEFORE" != "$AFTER" ]]; then
        echo "GIMP source updated, rebuilding..."
        rm -rf build
    else
        echo "No updates, using existing build..."
    fi
    
    ln -sf ../gimp-data .
fi

echo ""
echo "Verifying typelib files are accessible..."
ls -lh /usr/local/lib*/girepository-1.0/ 2>/dev/null || echo "No typelib directory found!"
echo ""

export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:/usr/lib/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"

# Check if we need to run meson setup
if [[ ! -d build ]] || [[ ! -f build/build.ninja ]]; then
    echo "Running meson setup..."
    rm -rf build  # Clean up incomplete build directory
    meson setup build --prefix=/usr/local
else
    echo "Build already configured, skipping meson setup..."
fi

echo ""
echo "Checking build configuration..."
meson configure build | grep -E "(babl|gegl|gexiv2|python)" || true
echo ""

export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"

ninja -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" | cat
sudo ninja -C build install 2>&1 | grep -v "WARNING: Glycin running without sandbox" | cat

# Find and rename the GIMP binary to gimp-git
GIMP_BINARY=$(find /usr/local/bin -name "gimp-[0-9]*" -not -name "gimp-console*" -not -name "gimp-script*" -not -name "gimp-test*" -not -name "gimptool*" | head -1)
if [ -n "$GIMP_BINARY" ]; then
    sudo mv "$GIMP_BINARY" /usr/local/bin/gimp-git-bin
    echo "Renamed $(basename $GIMP_BINARY) to gimp-git-bin"
    
    # Create wrapper script to set correct library path
    sudo tee /usr/local/bin/gimp-git << 'EOF' > /dev/null
#!/bin/bash
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"
export PATH="/usr/bin:$PATH"
exec /usr/local/bin/gimp-git-bin "$@" 2>&1 | grep -v "WARNING: Glycin running without sandbox"
EOF
    sudo chmod +x /usr/local/bin/gimp-git
    echo "Created gimp-git wrapper with correct library paths"
else
    echo "Warning: No GIMP binary found to rename"
fi

# Create applications directory if it doesn't exist
sudo mkdir -p /usr/local/share/applications

sudo tee /usr/local/share/applications/gimp-git.desktop << EOF > /dev/null
[Desktop Entry]
Version=1.0
Type=Application
Name=GIMP (Git)
GenericName=Image Editor
Comment=Create images and edit photographs
Exec=/usr/local/bin/gimp-git %U
TryExec=/usr/local/bin/gimp-git
Icon=gimp
StartupNotify=true
MimeType=image/bmp;image/gif;image/jpeg;image/png;image/tiff;image/x-xcf;
Categories=Graphics;2DGraphics;RasterGraphics;Photography;
EOF

sudo update-desktop-database /usr/local/share/applications/ 2>/dev/null || true
sudo gtk-update-icon-cache -t /usr/local/share/icons/hicolor/ 2>/dev/null || true

echo ""
echo "========================================"
echo "GIMP-git installed successfully!"
echo "========================================"
echo "Run from terminal: /usr/local/bin/gimp-git"
echo "Or find 'GIMP (Git)' in your applications menu"
echo ""
echo "Usage:"
echo "  $0                    # Build only what's needed"
echo "  $0 --rebuild-gimp     # Force rebuild GIMP only"
echo "  $0 --rebuild-all      # Force rebuild everything"
echo "  $0 --clean            # Remove everything"
