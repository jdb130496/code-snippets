#!/bin/bash
set -e

# ==============================================================================
# GIMP-GIT ISOLATED BUILD SCRIPT
# ==============================================================================
# This script builds GIMP-git in complete isolation using a custom prefix
# It does NOT remove or modify any system-installed packages
# All builds go to: /opt/gimp-git/
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
echo "GIMP-GIT ISOLATED BUILD"
echo "===================================================================="
echo "Install prefix: $INSTALL_PREFIX"
echo "Build directory: $BUILD_DIR"
echo "This will NOT modify any system packages"
echo "===================================================================="
echo ""

# Check for existing /usr/local installation
if [ -f "/usr/local/bin/gimp-git" ] || [ -f "/usr/local/bin/gimp-git-bin" ] || \
   [ -d "/usr/local/lib64/gimp" ] || [ -d "/usr/local/lib/gimp" ]; then
    echo "⚠️  WARNING: Found existing GIMP-git installation in /usr/local"
    echo ""
    echo "You have an old GIMP-git installation that should be cleaned up first."
    echo "This will avoid conflicts and save disk space."
    echo ""
    echo "Detected files:"
    [ -f "/usr/local/bin/gimp-git" ] && echo "  - /usr/local/bin/gimp-git"
    [ -f "/usr/local/bin/gimp-git-bin" ] && echo "  - /usr/local/bin/gimp-git-bin"
    [ -d "/usr/local/lib64/gimp" ] && echo "  - /usr/local/lib64/gimp/"
    [ -d "/usr/local/lib/gimp" ] && echo "  - /usr/local/lib/gimp/"
    [ -d "/usr/local/lib64/babl-0.1" ] && echo "  - /usr/local/lib64/babl-0.1/"
    [ -d "/usr/local/lib64/gegl-0.4" ] && echo "  - /usr/local/lib64/gegl-0.4/"
    echo ""
    echo "Cleanup commands (run manually if you want to remove old installation):"
    echo "  sudo rm -rf /usr/local/bin/gimp-git*"
    echo "  sudo rm -rf /usr/local/lib*/gimp* /usr/local/lib*/libgimp*"
    echo "  sudo rm -rf /usr/local/lib*/babl* /usr/local/lib*/libbabl*"
    echo "  sudo rm -rf /usr/local/lib*/gegl* /usr/local/lib*/libgegl*"
    echo "  sudo rm -rf /usr/local/lib*/gexiv2* /usr/local/lib*/libgexiv2*"
    echo "  sudo rm -rf /usr/local/lib*/pkgconfig/{babl,gegl,gexiv2}*"
    echo "  sudo rm -rf /usr/local/share/gimp*"
    echo "  sudo ldconfig"
    echo ""
    read -p "Continue with installation? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "Installation cancelled."
        exit 0
    fi
    echo ""
    echo "Continuing with installation (old files in /usr/local remain)..."
    echo ""
fi

if [[ "$CLEAN" == true ]]; then
    echo "Cleaning previous build..."
    rm -rf "$BUILD_DIR"
    sudo rm -rf "$INSTALL_PREFIX"
    rm -f ~/.local/share/applications/gimp-git.desktop
    update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
    echo "✓ Clean complete."
    exit 0
fi

# Check if we need sudo for creating the prefix directory
if [[ ! -d "$INSTALL_PREFIX" ]]; then
    echo "Creating install prefix: $INSTALL_PREFIX"
    sudo mkdir -p "$INSTALL_PREFIX"
    sudo chown -R $(whoami):$(whoami) "$INSTALL_PREFIX"
fi

if [[ "$SKIP_DEPS" == false ]]; then
    echo "Installing build dependencies (no removals)..."
    
    # First, ensure system packages are installed (in case they were removed before)
    echo "Ensuring system image libraries are installed..."
    sudo dnf install -y libgexiv2 libgexiv2-devel exiv2-libs exiv2-devel \
        babl gegl04 gegl04-devel lcms2 lcms2-devel 2>/dev/null || {
        echo "ℹ️  Note: Some system packages already installed or unavailable"
    }
    
    # Install build dependencies
    sudo dnf install -y gcc-c++ meson ninja-build pkgconfig gtk3-devel glib2-devel \
        cairo-devel gdk-pixbuf2-devel bubblewrap git json-glib-devel \
        gobject-introspection-devel python3-gobject vala ghostscript \
        mypaint-brushes mypaint-brushes-devel python3-gobject-devel \
        appstream appstream-devel openexr openexr-libs openexr-devel \
        aalib-libs aalib-devel lua libexif libexif-devel jasper jasper-devel \
        gi-docgen.noarch libmng libmng-devel libjxl libjxl-devel \
        libheif libheif-devel libwebp libwebp-devel librsvg2 librsvg2-devel \
        libarchive libarchive-devel iso-codes iso-codes-devel libtiff libtiff-devel \
        lua-devel libwmf libwmf-devel libmypaint libmypaint-devel \
        libopenraw libopenraw-devel cmake gettext-devel expat-devel
    
    # Handle zlib variants (zlib-devel or zlib-ng-compat-devel)
    if ! dnf list installed zlib-devel &>/dev/null && ! dnf list installed zlib-ng-compat-devel &>/dev/null; then
        sudo dnf install -y zlib-devel 2>/dev/null || sudo dnf install -y zlib-ng-compat-devel 2>/dev/null || true
    fi
    
    # Try to install glycin if available (Fedora 39+)
    sudo dnf install -y glycin-devel glycin-loaders 2>/dev/null || echo "ℹ️  Note: glycin not available, GIMP will build without it"
    
    echo "✓ Dependencies installed"
    echo "✓ System packages (babl, gegl04, libgexiv2, exiv2-libs) verified/restored"
fi

mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

# Set up isolated environment for all builds
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib64/pkgconfig:$INSTALL_PREFIX/lib/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib64:$INSTALL_PREFIX/lib:$LD_LIBRARY_PATH"
export PATH="$INSTALL_PREFIX/bin:$PATH"
export GI_TYPELIB_PATH="$INSTALL_PREFIX/lib64/girepository-1.0:$INSTALL_PREFIX/lib/girepository-1.0:$GI_TYPELIB_PATH"
export XDG_DATA_DIRS="$INSTALL_PREFIX/share:${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

echo ""
echo "===================================================================="
echo "Building exiv2 0.27.x in isolation..."
echo "===================================================================="
if [[ ! -d exiv2 ]]; then
    git clone https://github.com/Exiv2/exiv2.git
    cd exiv2
    git fetch --tags
    LATEST_027=$(git tag | grep "^v0\.27\." | sort -V | tail -1)
    echo "Checking out exiv2 tag: $LATEST_027"
    git checkout "$LATEST_027"
    cd ..
else
    cd exiv2
    git fetch --tags
    LATEST_027=$(git tag | grep "^v0\.27\." | sort -V | tail -1)
    git checkout "$LATEST_027"
    cd ..
fi
cd exiv2
rm -rf build
mkdir build
cd build
cmake .. -DCMAKE_INSTALL_PREFIX="$INSTALL_PREFIX" -DCMAKE_BUILD_TYPE=Release -DEXIV2_ENABLE_NLS=ON
make -j$(nproc)
make install
cd ../..

EXIV2_VERSION=$(pkg-config --modversion exiv2)
echo "✓ Installed exiv2 version: $EXIV2_VERSION to $INSTALL_PREFIX"
echo ""

echo "===================================================================="
echo "Building gexiv2 0.14.x in isolation..."
echo "===================================================================="
if [[ ! -d gexiv2 ]]; then
    git clone https://gitlab.gnome.org/GNOME/gexiv2.git
    cd gexiv2
    git fetch --tags
    LATEST_014=$(git tag | grep "^gexiv2-0\.14\." | sort -V | tail -1)
    echo "Checking out gexiv2 tag: $LATEST_014"
    git checkout "$LATEST_014"
    cd ..
else
    cd gexiv2
    git fetch --tags
    LATEST_014=$(git tag | grep "^gexiv2-0\.14\." | sort -V | tail -1)
    git checkout "$LATEST_014"
    cd ..
fi
cd gexiv2
rm -rf build
meson setup build --prefix="$INSTALL_PREFIX"
ninja -C build
ninja -C build install
cd ..

GEXIV2_VERSION=$(pkg-config --modversion gexiv2)
echo "✓ Installed gexiv2 version: $GEXIV2_VERSION to $INSTALL_PREFIX"
if [[ ! "$GEXIV2_VERSION" =~ ^0\.14\. ]]; then
    echo "⚠️  WARNING: Expected gexiv2 0.14.x but got $GEXIV2_VERSION"
fi
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
echo "✓ LCMS2 installed to $INSTALL_PREFIX"
echo ""

echo "===================================================================="
echo "Building BABL in isolation..."
echo "===================================================================="
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
    git checkout $LATEST_TAG
    cd ..
fi
cd babl
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

BABL_VERSION=$(pkg-config --modversion babl-0.1)
echo "✓ Installed babl version: $BABL_VERSION to $INSTALL_PREFIX"

# Verify version requirement
MAJOR_MINOR=$(echo "$BABL_VERSION" | cut -d. -f1-2)
PATCH=$(echo "$BABL_VERSION" | cut -d. -f3)
if [[ "$MAJOR_MINOR" == "0.1" ]] && [[ "$PATCH" -lt 116 ]]; then
    echo "✗ ERROR: babl version $BABL_VERSION is less than required 0.1.116"
    exit 1
fi

if [ -f "$INSTALL_PREFIX/lib64/girepository-1.0/Babl-0.1.typelib" ] || [ -f "$INSTALL_PREFIX/lib/girepository-1.0/Babl-0.1.typelib" ]; then
    echo "✓ Babl-0.1.typelib installed successfully"
else
    echo "✗ ERROR: Babl-0.1.typelib NOT found!"
    exit 1
fi

# Check VAPI (optional but nice to have)
if [ -f "$INSTALL_PREFIX/share/vala/vapi/babl-0.1.vapi" ]; then
    echo "✓ Babl-0.1.vapi installed successfully"
    export VALA_VAPIDIR="$INSTALL_PREFIX/share/vala/vapi"
else
    echo "ℹ️  Babl-0.1.vapi not found (Vala bindings not built - usually not critical)"
fi
echo ""

echo "===================================================================="
echo "Building GEGL in isolation..."
echo "===================================================================="
if [[ ! -d gegl ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gegl.git
else
    cd gegl
    git clean -fd
    git pull
    cd ..
fi
cd gegl
rm -rf build

# Determine vapigen option based on Babl VAPI availability
if [ -f "$INSTALL_PREFIX/share/vala/vapi/babl-0.1.vapi" ]; then
    echo "✓ Babl VAPI found, enabling Vala bindings"
    VAPIGEN_OPTION="-Dvapigen=enabled"
else
    echo "ℹ️  Babl VAPI not found, disabling Vala bindings (not critical)"
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

if [ -f "$INSTALL_PREFIX/lib64/girepository-1.0/Gegl-0.4.typelib" ] || [ -f "$INSTALL_PREFIX/lib/girepository-1.0/Gegl-0.4.typelib" ]; then
    echo "✓ Gegl-0.4.typelib installed successfully"
else
    echo "✗ ERROR: Gegl-0.4.typelib NOT found!"
    exit 1
fi
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
    echo "✓ Found glycin-2 version: $GLYCIN_VERSION"
else
    echo "ℹ️  glycin-2 not found. GIMP will build without glycin support."
fi

echo ""
echo "Verifying typelib files..."
ls -lh "$INSTALL_PREFIX"/lib*/girepository-1.0/ 2>/dev/null || echo "No typelib directory found!"
echo ""

meson setup build --prefix="$INSTALL_PREFIX" -Dauto_features=disabled

echo ""
echo "Checking build configuration..."
meson configure build | grep -i glycin || echo "  (glycin status not shown in meson options)"
echo ""

ninja -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" | cat
ninja -C build install

# Find and rename the GIMP binary
GIMP_BINARY=$(find "$INSTALL_PREFIX/bin" -name "gimp-[0-9]*" -not -name "gimp-console*" -not -name "gimp-script*" -not -name "gimp-test*" -not -name "gimptool*" | head -1)
if [ -n "$GIMP_BINARY" ]; then
    mv "$GIMP_BINARY" "$INSTALL_PREFIX/bin/gimp-git-bin"
    echo "✓ Renamed $(basename $GIMP_BINARY) to gimp-git-bin"
    
    # Create wrapper script with isolated environment
    cat > "$INSTALL_PREFIX/bin/gimp-git" << EOF
#!/bin/bash
# GIMP-git wrapper with isolated environment
# Ensures custom libraries don't interfere with system applications

export LD_LIBRARY_PATH="$INSTALL_PREFIX/lib64:$INSTALL_PREFIX/lib:\${LD_LIBRARY_PATH}"
export PKG_CONFIG_PATH="$INSTALL_PREFIX/lib64/pkgconfig:$INSTALL_PREFIX/lib/pkgconfig:\${PKG_CONFIG_PATH}"
export GI_TYPELIB_PATH="$INSTALL_PREFIX/lib64/girepository-1.0:$INSTALL_PREFIX/lib/girepository-1.0:\${GI_TYPELIB_PATH}"
export PATH="$INSTALL_PREFIX/bin:\${PATH}"
export XDG_DATA_DIRS="$INSTALL_PREFIX/share:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"

# Glycin loader path (if available on system)
if [ -d "/usr/libexec/glycin-loaders/2+" ]; then
    export GLYCIN_LOADERS_PATH="/usr/libexec/glycin-loaders/2+"
fi

# Suppress glycin sandbox warnings (kernel 6.17+ seccomp incompatibility)
exec "$INSTALL_PREFIX/bin/gimp-git-bin" "\$@" 2>&1 | grep -v "WARNING: Glycin running without sandbox"
EOF
    chmod +x "$INSTALL_PREFIX/bin/gimp-git"
    echo "✓ Created gimp-git wrapper script"
else
    echo "⚠️  Warning: No GIMP binary found to rename"
fi

# Create desktop entry
mkdir -p "$INSTALL_PREFIX/share/applications"
cat > "$INSTALL_PREFIX/share/applications/gimp-git.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=GIMP (Git) - Isolated
GenericName=Image Editor
Comment=Create images and edit photographs (isolated build in $INSTALL_PREFIX)
Exec=$INSTALL_PREFIX/bin/gimp-git %U
TryExec=$INSTALL_PREFIX/bin/gimp-git
Icon=gimp
StartupNotify=true
MimeType=image/bmp;image/gif;image/jpeg;image/png;image/tiff;image/x-xcf;
Categories=Graphics;2DGraphics;RasterGraphics;Photography;
EOF

# Copy to user applications directory (no sudo needed)
mkdir -p ~/.local/share/applications
cp "$INSTALL_PREFIX/share/applications/gimp-git.desktop" ~/.local/share/applications/
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo ""
echo "===================================================================="
echo "✓ GIMP-GIT INSTALLED SUCCESSFULLY IN ISOLATION!"
echo "===================================================================="
echo ""
echo "📁 Installation directory: $INSTALL_PREFIX"
echo ""
echo "🚀 To run GIMP-git:"
echo "   $INSTALL_PREFIX/bin/gimp-git"
echo ""
echo "   Or search for 'GIMP (Git) - Isolated' in your applications menu"
echo ""
echo "✅ Your system packages are untouched:"
echo "   • System babl/gegl/exiv2/gexiv2 remain intact"
echo "   • System GIMP (if installed) continues to work normally"
echo "   • All GIMP-git libraries are isolated in: $INSTALL_PREFIX"
echo ""
echo "💡 Optional: Add to PATH for easy access (current session only):"
echo "   export PATH=\"$INSTALL_PREFIX/bin:\$PATH\""
echo ""
echo "   Or add permanently to ~/.bashrc:"
echo "   echo 'export PATH=\"$INSTALL_PREFIX/bin:\$PATH\"' >> ~/.bashrc"
echo ""
echo "🧹 To remove this installation:"
echo "   $0 --clean"
echo "===================================================================="
