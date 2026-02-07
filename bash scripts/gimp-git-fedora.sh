#!/bin/bash
set -e

SKIP_DEPS=false
SKIP_TESTS=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --nodeps) SKIP_DEPS=true; shift ;;
        --nocheck) SKIP_TESTS=true; shift ;;
        --clean) CLEAN=true; shift ;;
        *) shift ;;
    esac
done

if [[ "$CLEAN" == true ]]; then
    rm -rf ~/gimp-build
    sudo rm -rf /usr/local/bin/gimp* /usr/local/lib*/gimp* /usr/local/lib*/libgimp* /usr/local/share/gimp* /usr/local/share/applications/gimp* 2>/dev/null || true
    sudo ldconfig
fi

if [[ "$SKIP_DEPS" == false ]]; then
    sudo dnf install -y gcc-c++ meson ninja-build pkgconfig gtk3-devel glib2-devel cairo-devel gdk-pixbuf2-devel bubblewrap git json-glib-devel glycin-devel glycin-loaders gobject-introspection-devel python3-gobject vala exiv2 exiv2-devel libgexiv2 libgexiv2-devel ghostscript mypaint-brushes mypaint-brushes-devel mypaint2-brushes mypaint2-brushes-devel python3-gobject-devel appstream appstream-devel openexr openexr-libs openexr-devel aalib-libs aalib-devel lua libexif libexif-devel jasper jasper-devel gi-docgen.noarch libmng libmng-devel libjxl libjxl-devel libheif libheif-devel libwebp libwebp-devel librsvg2 librsvg2-devel libarchive libarchive-devel iso-codes iso-codes-devel libtiff libtiff-devel lua-devel libwmf libwmf-devel libmypaint libmypaint-devel
    # Remove system babl/gegl packages that conflict with our custom build
    sudo dnf remove -y babl gegl 2>/dev/null || true
fi

rm -f ~/.local/bin/ninja 2>/dev/null || true

mkdir -p ~/gimp-build
cd ~/gimp-build

export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"

echo "Building LCMS2..."
if [[ ! -d Little-CMS ]]; then
    git clone --depth 1 https://github.com/mm2/Little-CMS.git
else
    cd Little-CMS && git pull && cd ..
fi
cd Little-CMS
rm -rf build
meson setup build --prefix=/usr/local
ninja-build -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
sudo ninja-build -C build install 2>&1 | grep -v "WARNING: Glycin running without sandbox" || true
sudo ldconfig
cd ..

echo "Building BABL..."
if [[ ! -d babl ]]; then
    # Clone from official GitLab repository
    git clone https://gitlab.gnome.org/GNOME/babl.git
    cd babl
    # Fetch and checkout latest release tag
    git fetch --tags
    LATEST_TAG=$(git tag | grep "^BABL_0_1" | sort -V | tail -1)
    echo "Checking out latest babl tag: $LATEST_TAG"
    git checkout $LATEST_TAG
    cd ..
else
    cd babl
    git fetch --tags
    LATEST_TAG=$(git tag | grep "^BABL_0_1" | sort -V | tail -1)
    echo "Checking out latest babl tag: $LATEST_TAG"
    git checkout $LATEST_TAG
    cd ..
fi
cd babl
rm -rf build
meson setup build --prefix=/usr/local -Denable-gir=true

# Verify introspection will be built
echo "Checking BABL build configuration..."
if meson configure build | grep -q "enable-gir.*true"; then
    echo "✓ BABL GObject introspection enabled"
else
    echo "✗ ERROR: BABL GObject introspection NOT enabled!"
    echo "This is required for Python plugins. Check if gobject-introspection-devel is installed."
    exit 1
fi

ninja-build -C build
sudo ninja-build -C build install
sudo ldconfig

# Verify babl version and typelib
BABL_VERSION=$(pkg-config --modversion babl-0.1)
echo "✓ Installed babl version: $BABL_VERSION"

# Simple version comparison without bc
MAJOR_MINOR=$(echo "$BABL_VERSION" | cut -d. -f1-2)
PATCH=$(echo "$BABL_VERSION" | cut -d. -f3)
if [[ "$MAJOR_MINOR" == "0.1" ]] && [[ "$PATCH" -lt 116 ]]; then
    echo "ERROR: babl version $BABL_VERSION is less than required 0.1.116"
    exit 1
fi

# Verify typelib was installed
if [ -f "/usr/local/lib64/girepository-1.0/Babl-0.1.typelib" ] || [ -f "/usr/local/lib/girepository-1.0/Babl-0.1.typelib" ]; then
    echo "✓ Babl-0.1.typelib installed successfully"
else
    echo "✗ ERROR: Babl-0.1.typelib NOT found!"
    echo "Introspection build may have failed."
    exit 1
fi
cd ..

echo "Building GEGL..."
if [[ ! -d gegl ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gegl.git
else
    cd gegl
    # Clean up any untracked files that might conflict
    git clean -fd
    git pull
    cd ..
fi
cd gegl
rm -rf build
meson setup build --prefix=/usr/local -Dintrospection=true

# Verify introspection will be built
echo "Checking GEGL build configuration..."
if meson configure build | grep -q "introspection.*true"; then
    echo "✓ GEGL GObject introspection enabled"
else
    echo "✗ ERROR: GEGL GObject introspection NOT enabled!"
    echo "This is required for Python plugins. Check dependencies."
    exit 1
fi

ninja-build -C build
sudo ninja-build -C build install
sudo ldconfig

# Verify typelib was installed
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

echo "Building GIMP..."
if [[ ! -d gimp ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gimp.git
fi

cd gimp

# Handle the gimp-data symlink issue
echo "Cleaning up submodule state..."
rm -rf .git/modules/gimp-data
rm -rf gimp-data
git submodule deinit -f gimp-data 2>/dev/null || true

rm -rf build
git pull

# Initialize submodules with shallow clone for speed
echo "Initializing gimp-data submodule (shallow clone)..."
git submodule sync
GIT_TRACE=1 GIT_CURL_VERBOSE=1 GIT_PROGRESS_DELAY=0 git submodule update --init --depth 1 --progress gimp-data
echo "✓ gimp-data submodule initialized"

# Verify glycin is available
echo "Checking for glycin support..."
if pkg-config --exists glycin-2; then
    GLYCIN_VERSION=$(pkg-config --modversion glycin-2)
    echo "Found glycin-2 version: $GLYCIN_VERSION"
    echo "GIMP will auto-detect glycin during build"
else
    echo "Warning: glycin-2 not found. GIMP will build without glycin support."
fi

# Double-check babl is found in the right location
echo ""
echo "Verifying typelib files are accessible..."
ls -lh /usr/local/lib*/girepository-1.0/ 2>/dev/null || echo "No typelib directory found!"
echo ""

# Set PKG_CONFIG_PATH to prioritize /usr/local
export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib64/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"

meson setup build -Dauto_features=disabled --prefix=/usr/local

echo ""
echo "Checking build configuration..."
meson configure build | grep -i glycin || echo "  (glycin status not shown in meson options)"
echo ""

# Build with all environment variables set
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"
export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:/usr/lib64/pkgconfig:$PKG_CONFIG_PATH"

ninja-build -C build 2>&1 | grep -v "WARNING: Glycin running without sandbox" | cat
sudo ninja-build -C build install

# Find and rename the GIMP binary to gimp-git (future-proof)
GIMP_BINARY=$(find /usr/local/bin -name "gimp-[0-9]*" -not -name "gimp-console*" -not -name "gimp-script*" -not -name "gimp-test*" -not -name "gimptool*" | head -1)
if [ -n "$GIMP_BINARY" ]; then
    sudo mv "$GIMP_BINARY" /usr/local/bin/gimp-git-bin
    echo "Renamed $(basename $GIMP_BINARY) to gimp-git-bin"
    
    # Create wrapper script to set correct library path and glycin environment
    # Note: Suppresses glycin sandbox warnings due to kernel 6.17+ seccomp incompatibility
    sudo tee /usr/local/bin/gimp-git << 'EOF' > /dev/null
#!/bin/bash
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"
export GLYCIN_LOADERS_PATH="/usr/libexec/glycin-loaders/2+"
export PATH="/usr/bin:$PATH"
exec /usr/local/bin/gimp-git-bin "$@" 2>&1 | grep -v "WARNING: Glycin running without sandbox"
EOF
    sudo chmod +x /usr/local/bin/gimp-git
    echo "Created gimp-git wrapper with correct library paths"
else
    echo "Warning: No GIMP binary found to rename"
fi

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

echo "GIMP-git installed successfully!"
echo "Run: /usr/local/bin/gimp-git"
echo "Desktop: GIMP (Git) in applications menu"
