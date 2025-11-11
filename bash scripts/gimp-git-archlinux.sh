#!/bin/bash
set -e

SKIP_DEPS=false
CLEAN=false
REBUILD_BABL=false
REBUILD_GEGL=false
REBUILD_GIMP=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --nodeps) SKIP_DEPS=true; shift ;;
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
    echo "Clean complete."
    exit 0
fi

if [[ "$SKIP_DEPS" == false ]]; then
    sudo pacman -S --needed base-devel git meson ninja pkgconfig gtk3 glib2 cairo gdk-pixbuf2 \
        bubblewrap json-glib gobject-introspection python-gobject vala lcms2 \
        mypaint-brushes1 poppler-glib poppler-data libwmf openexr libjxl \
        libheif libwebp librsvg libarchive appstream-glib iso-codes python-cairo \
        aalib libexif jasper libgexiv2 ghostscript libmng libtiff lua gi-docgen
fi

mkdir -p ~/gimp-build
cd ~/gimp-build

export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:/usr/lib/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"

needs_build() {
    local component=$1
    local version_check=$2
    if ! command -v pkg-config &> /dev/null; then
        return 0
    fi
    if ! pkg-config --exists "$version_check" 2>/dev/null; then
        return 0
    fi
    return 1
}

if [[ "$REBUILD_BABL" == true ]] || needs_build "babl" "babl-0.1"; then
    echo "Building BABL..."
    if [[ ! -d babl ]]; then
        git clone https://gitlab.gnome.org/GNOME/babl.git
    fi
    cd babl
    git fetch --tags
    LATEST_TAG=$(git tag | grep "^BABL_0_1" | sort -V | tail -1)
    git checkout $LATEST_TAG
    rm -rf build
    meson setup build --prefix=/usr/local -Denable-gir=true
    ninja -C build
    sudo ninja -C build install
    sudo ldconfig
    cd ..
fi

if [[ "$REBUILD_GEGL" == true ]] || [[ "$REBUILD_BABL" == true ]] || needs_build "gegl" "gegl-0.4"; then
    echo "Building GEGL..."
    if [[ ! -d gegl ]]; then
        git clone --depth 1 https://gitlab.gnome.org/GNOME/gegl.git
    fi
    cd gegl
    git pull
    rm -rf build
    meson setup build --prefix=/usr/local -Dintrospection=true
    ninja -C build
    sudo ninja -C build install
    echo "/usr/local/lib64" | sudo tee /etc/ld.so.conf.d/usr-local.conf > /dev/null
    echo "/usr/local/lib" | sudo tee -a /etc/ld.so.conf.d/usr-local.conf > /dev/null
    sudo ldconfig
    cd ..
fi

echo "Building GIMP..."

if [[ ! -d gimp ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gimp.git
fi

if [[ ! -d gimp-data ]]; then
    git clone --depth 1 https://gitlab.gnome.org/GNOME/gimp-data.git
fi

cd gimp-data
git pull
cd ../gimp

git config submodule.gimp-data.update none 2>/dev/null || true
rm -rf gimp-data

git pull
ln -sf ../gimp-data gimp-data

if [[ "$REBUILD_GIMP" == true ]] || [[ ! -f build/build.ninja ]]; then
    rm -rf build
fi

if [[ ! -f build/build.ninja ]]; then
    meson setup build --prefix=/usr/local
fi

ninja -C build
sudo ninja -C build install

GIMP_BINARY=$(find /usr/local/bin -name "gimp-[0-9]*" -not -name "gimp-console*" -not -name "gimp-script*" -not -name "gimp-test*" -not -name "gimptool*" | head -1)
if [ -n "$GIMP_BINARY" ]; then
    sudo mv "$GIMP_BINARY" /usr/local/bin/gimp-git-bin
    sudo tee /usr/local/bin/gimp-git << 'EOF' > /dev/null
#!/bin/bash
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/usr/lib64/pkgconfig:/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
export GI_TYPELIB_PATH="/usr/local/lib64/girepository-1.0:/usr/local/lib/girepository-1.0:$GI_TYPELIB_PATH"
exec /usr/local/bin/gimp-git-bin "$@"
EOF
    sudo chmod +x /usr/local/bin/gimp-git
fi

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

echo "GIMP-git installed successfully!"
echo "Run: /usr/local/bin/gimp-git"
