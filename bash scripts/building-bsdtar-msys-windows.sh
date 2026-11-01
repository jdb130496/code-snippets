#!/usr/bin/bash
set -e

LIBARCHIVE_SRC="/d/dev/libarchive-src"
LIBARCHIVE_PREFIX="/d/Programs/bsdtar"
BUILD_DIR="/d/dev/libarchive-build"
JOBS=$(nproc)

# ── Compiler and library setup ────────────────────────────────────
# Minimal PATH — prevents Perl/MinGW/system libs from sneaking in
export PATH=/ucrt64/bin:/usr/bin

export CC=/ucrt64/bin/clang.exe
export CXX=/ucrt64/bin/clang++.exe
export LD=/ucrt64/bin/ld.lld.exe
export AR=/ucrt64/bin/llvm-ar.exe
export RANLIB=/ucrt64/bin/llvm-ranlib.exe
export NM=/ucrt64/bin/llvm-nm.exe

# Force UCRT64 pkg-config — finds correct library versions
export PKG_CONFIG_PATH=/ucrt64/lib/pkgconfig
export PKG_CONFIG_LIBDIR=/ucrt64/lib/pkgconfig

echo "==> Build environment:"
echo "  Compiler : $($CC --version | head -1)"
echo "  Ninja    : $(ninja --version)"
echo "  Jobs     : $JOBS"

# ── Cleanup previous build and install ───────────────────────────
echo "==> Cleaning previous build and install..."
rm -rf "$BUILD_DIR"
rm -rf "$LIBARCHIVE_PREFIX"
mkdir -p "$BUILD_DIR"
mkdir -p "$LIBARCHIVE_PREFIX"

# ── 1. Clone or update libarchive ────────────────────────────────
if [ -d "$LIBARCHIVE_SRC/.git" ]; then
    echo "==> Updating libarchive source..."
    git -C "$LIBARCHIVE_SRC" pull
else
    echo "==> Cloning libarchive..."
    git clone https://github.com/libarchive/libarchive.git "$LIBARCHIVE_SRC"
fi

HEAD=$(git -C "$LIBARCHIVE_SRC" log --oneline -1)
echo "  HEAD: $HEAD"

# ── 2. Configure ─────────────────────────────────────────────────
echo "==> Configuring with CMake + Ninja + Clang..."
cmake -S "$LIBARCHIVE_SRC" -B "$BUILD_DIR" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$LIBARCHIVE_PREFIX" \
    -DCMAKE_C_COMPILER=$CC \
    -DCMAKE_CXX_COMPILER=$CXX \
    -DCMAKE_LINKER=$LD \
    -DCMAKE_AR=$AR \
    -DCMAKE_RANLIB=$RANLIB \
    -DCMAKE_NM=$NM \
    -DCMAKE_C_FLAGS="-O2 -pipe" \
    -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld" \
    -DCMAKE_SHARED_LINKER_FLAGS="-fuse-ld=lld" \
    -DENABLE_ZLIB=ON \
    -DENABLE_BZip2=ON \
    -DENABLE_LZMA=ON \
    -DENABLE_ZSTD=ON \
    -DENABLE_LZ4=ON \
    -DENABLE_LZO2=OFF \
    -DENABLE_OPENSSL=ON \
    -DENABLE_MBEDTLS=OFF \
    -DENABLE_LIBB2=OFF \
    -DENABLE_EXPAT=ON \
    -DENABLE_LIBXML2=OFF \
    -DENABLE_TAR=ON \
    -DENABLE_CPIO=ON \
    -DENABLE_CAT=ON \
    -DENABLE_UNZIP=ON \
    -DENABLE_TEST=OFF

# ── 3. Build ──────────────────────────────────────────────────────
echo "==> Building with Ninja ($JOBS parallel jobs)..."
ninja -C "$BUILD_DIR" -j "$JOBS"

# ── 4. Install ────────────────────────────────────────────────────
echo "==> Installing to $LIBARCHIVE_PREFIX..."
ninja -C "$BUILD_DIR" install

# ── 5. Copy UCRT64 DLLs next to exe — wins over Perl's c\bin at runtime ──
echo "==> Copying UCRT64 runtime DLLs..."
for dll in liblzma-5 libbz2-1 liblz4 libzstd libexpat-1; do
    src="/ucrt64/bin/${dll}.dll"
    if [ -f "$src" ]; then
        cp "$src" "$LIBARCHIVE_PREFIX/bin/"
        echo "  Copied: ${dll}.dll"
    fi
done

# ── 6. Verify ─────────────────────────────────────────────────────
BSDTAR="$LIBARCHIVE_PREFIX/bin/bsdtar.exe"
if [ -f "$BSDTAR" ]; then
    echo ""
    echo "✓ bsdtar built and installed successfully"
    echo "  Version  : $("$BSDTAR" --version | head -1)"
    echo "  Binary   : $BSDTAR"
    echo "  Source   : $HEAD"
    echo "  Formats  :"
    "$BSDTAR" --format help 2>&1 | sed 's/^/    /'
else
    echo "✗ bsdtar.exe not found at $BSDTAR"
    exit 1
fi
