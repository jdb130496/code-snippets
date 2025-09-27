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
    sudo dnf install -y gcc-c++ meson ninja-build pkgconfig gtk3-devel glib2-devel cairo-devel gdk-pixbuf2-devel bubblewrap git
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
ninja-build -C build
sudo ninja-build -C build install
sudo ldconfig
cd ..

echo "Building BABL..."
if [[ ! -d babl ]]; then
    git clone --depth 1 https://github.com/GNOME/babl.git
else
    cd babl && git pull && cd ..
fi
cd babl
rm -rf build
meson setup build --prefix=/usr/local
ninja-build -C build
sudo ninja-build -C build install
sudo ldconfig
cd ..

echo "Building GEGL..."
if [[ ! -d gegl ]]; then
    git clone --depth 1 https://github.com/GNOME/gegl.git
else
    cd gegl && git pull && cd ..
fi
cd gegl
rm -rf build
meson setup build --prefix=/usr/local -Dauto_features=disabled
ninja-build -C build
sudo ninja-build -C build install
sudo ldconfig
cd ..

echo "Building GIMP..."
if [[ ! -d gimp ]]; then
    git clone --depth 1 https://github.com/GNOME/gimp.git
fi

if [[ ! -d gimp-data ]]; then
    git clone --depth 1 https://github.com/GNOME/gimp-data.git
fi

cd gimp
rm -rf gimp-data build
git pull
cd ..

cd gimp-data
git pull
cd ..

cd gimp
ln -sf ../gimp-data .
meson setup build -Dauto_features=disabled --prefix=/usr/local
ninja-build -C build
sudo ninja-build -C build install

# Find and rename the GIMP binary to gimp-git (future-proof)
GIMP_BINARY=$(find /usr/local/bin -name "gimp-[0-9]*" -not -name "gimp-console*" -not -name "gimp-script*" -not -name "gimp-test*" -not -name "gimptool*" | head -1)
if [ -n "$GIMP_BINARY" ]; then
    sudo mv "$GIMP_BINARY" /usr/local/bin/gimp-git-bin
    echo "Renamed $(basename $GIMP_BINARY) to gimp-git-bin"
    
    # Create wrapper script to set correct library path
    sudo tee /usr/local/bin/gimp-git << 'EOF' > /dev/null
#!/bin/bash
export LD_LIBRARY_PATH="/usr/local/lib64:/usr/local/lib:$LD_LIBRARY_PATH"
export PKG_CONFIG_PATH="/usr/local/lib64/pkgconfig:/usr/local/lib/pkgconfig:$PKG_CONFIG_PATH"
exec /usr/local/bin/gimp-git-bin "$@"
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
