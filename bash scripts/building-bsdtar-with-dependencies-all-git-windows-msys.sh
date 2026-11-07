#!/usr/bin/bash
# Build bsdtar (libarchive) + all dependencies from source using MSYS2 UCRT64.
#
# Generator: "MSYS Makefiles" (not Ninja) — keeps the entire build in
# POSIX space. CMake writes POSIX paths into Makefiles; GNU make invokes
# the compiler directly without Windows-path-mangling.
#
# Prerequisites (all from MSYS2 UCRT64 — install with pacman if missing):
#   pacman -S --needed \
#     mingw-w64-ucrt-x86_64-clang \
#     mingw-w64-ucrt-x86_64-lld \
#     mingw-w64-ucrt-x86_64-llvm \
#     mingw-w64-ucrt-x86_64-cmake \
#     mingw-w64-ucrt-x86_64-nasm \
#     make perl git

set -euo pipefail

# ── Paths ─────────────────────────────────────────────────────────────────────
PREFIX="/d/Programs/bsdtar"
SRC="/d/dev"
BLD="/d/dev/build"

ZLIB_SRC="$SRC/zlib-src"
BZIP2_SRC="$SRC/bzip2-src"
LZ4_SRC="$SRC/lz4-src"
ZSTD_SRC="$SRC/zstd-src"
XZ_SRC="$SRC/xz-src"
EXPAT_SRC="$SRC/expat-src"
OSSL_SRC="$SRC/openssl-src"
LIBARCHIVE_SRC="$SRC/libarchive-src"

ZLIB_BLD="$BLD/zlib"
BZIP2_BLD="$BLD/bzip2"
LZ4_BLD="$BLD/lz4"
ZSTD_BLD="$BLD/zstd"
XZ_BLD="$BLD/xz"
EXPAT_BLD="$BLD/expat"
LIBARCHIVE_BLD="$BLD/libarchive"

# ── Sanitise PATH — MSYS2 POSIX tools only, no Windows-native dirs ────────────
# /usr/bin MUST come before /ucrt64/bin so MSYS2 perl shadows UCRT64 perl.
# OpenSSL's Configure requires POSIX perl (OS=cygwin); the UCRT64 one
# (OS=MSWin32) chokes on POSIX paths and aborts the build.
export PATH=/usr/local/bin:/usr/bin:/ucrt64/bin

# ── Compiler ──────────────────────────────────────────────────────────────────
export CC=clang
export CXX=clang++
export AR=llvm-ar
export RANLIB=llvm-ranlib
export NM=llvm-nm
export LD=ld.lld

export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig:/ucrt64/lib/pkgconfig"
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig:/ucrt64/lib/pkgconfig"

JOBS=$(nproc)

# ── Failure trap ──────────────────────────────────────────────────────────────
STEP="(init)"
LA_HEAD="unknown"
trap 'RC=$?
if [ $RC -ne 0 ]; then
    echo ""
    echo "✗ Failed at: $STEP (exit $RC)"
    echo "  Prefix (partial): $PREFIX"
    echo "  Build dirs kept for inspection under: $BLD"
fi' EXIT

# ── Sanity-check ──────────────────────────────────────────────────────────────
STEP="sanity check"
echo "==> Build environment"
echo "  PATH     : $PATH"
echo "  clang    : $(command -v clang) — $(clang --version | head -1)"
echo "  make     : $(command -v make) — $(make --version | head -1)"
echo "  cmake    : $(command -v cmake) — $(cmake --version | head -1)"
echo "  nasm     : $(command -v nasm) — $(nasm --version)"
echo "  perl     : $(command -v perl) — $(perl -e 'print "$^O\n"')"
echo "  git      : $(command -v git)"
echo "  Jobs     : $JOBS"
echo ""

PERL_OS=$(perl -e 'print $^O')
if [ "$PERL_OS" = "MSWin32" ]; then
    echo "✗ perl is UCRT64 native (MSWin32) — OpenSSL needs MSYS2 perl."
    echo "  Install: pacman -S perl"
    exit 1
fi

NASM_PATH=$(command -v nasm)
if [[ "$NASM_PATH" != /ucrt64/* && "$NASM_PATH" != /usr/* ]]; then
    echo "✗ nasm at '$NASM_PATH' is not an MSYS2 package."
    echo "  Install: pacman -S mingw-w64-ucrt-x86_64-nasm"
    exit 1
fi

# ── Common CMake flags ────────────────────────────────────────────────────────
CDEP=(
    -G "MSYS Makefiles"
    -DCMAKE_BUILD_TYPE=Release
    -DCMAKE_INSTALL_PREFIX="$PREFIX"
    -DCMAKE_PREFIX_PATH="$PREFIX"
    -DCMAKE_C_COMPILER=clang
    -DCMAKE_CXX_COMPILER=clang++
    -DCMAKE_AR=/ucrt64/bin/llvm-ar
    -DCMAKE_RANLIB=/ucrt64/bin/llvm-ranlib
    -DCMAKE_NM=/ucrt64/bin/llvm-nm
    -DCMAKE_C_FLAGS="-O2 -pipe"
    -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld"
    -DCMAKE_SHARED_LINKER_FLAGS="-fuse-ld=lld"
    -DBUILD_TESTING=OFF
)

# ── Helper: clone or update a git repo ───────────────────────────────────────
# Always tracks the latest HEAD of the default branch (git HEAD / master / main).
# Uses `git reset --hard origin/<branch>` instead of `git pull`.
# `git pull` exits 128 when local and remote histories have diverged
# (e.g. upstream force-push/rebase). Since we never edit these trees,
# a hard reset to the remote tip is always correct and never interactive.
clone_or_update() {
    local dir="$1" url="$2"
    if [ -d "$dir/.git" ]; then
        echo "  Updating $(basename "$dir")..."
        git -C "$dir" fetch --tags --quiet --depth=1 origin
        local branch
        branch=$(git -C "$dir" symbolic-ref --short HEAD 2>/dev/null || true)
        if [ -n "$branch" ]; then
            git -C "$dir" reset --hard "origin/$branch"
        else
            local default_branch
            default_branch=$(git -C "$dir" remote show origin | awk '/HEAD branch/{print $NF}')
            echo "  Detached HEAD — switching to: $default_branch"
            git -C "$dir" checkout --quiet "$default_branch"
            git -C "$dir" reset --hard "origin/$default_branch"
        fi
    else
        echo "  Cloning $(basename "$dir")..."
        git clone --quiet --depth=1 "$url" "$dir"
    fi
    git -C "$dir" log --oneline -1
}

# ── Clean slate ───────────────────────────────────────────────────────────────
STEP="cleanup"
echo "==> Cleaning previous install and build dirs..."
rm -rf "$PREFIX" "$BLD"
mkdir -p "$PREFIX/bin" "$BLD"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 1 — zlib (latest git HEAD)
# BUILD_SHARED_LIBS=ON required — zlib CMake defaults to static only
# ════════════════════════════════════════════════════════════════════════════════
STEP="[1/7] zlib"
echo "==> $STEP"
clone_or_update "$ZLIB_SRC" "https://github.com/madler/zlib.git"
cmake -S "$ZLIB_SRC" -B "$ZLIB_BLD" "${CDEP[@]}" \
    -DBUILD_SHARED_LIBS=ON \
    -DZLIB_BUILD_EXAMPLES=OFF
make -C "$ZLIB_BLD" -j"$JOBS"
make -C "$ZLIB_BLD" install
echo "  ✓ zlib"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 2 — bzip2 (latest git HEAD)
# No custom naming flags — MinGW produces libbz2.dll natively and the
# import lib (libbz2.dll.a) references that same name. Both agree.
# However libarchive's find_package(BZip2) picks up UCRT64's system bzip2
# which embeds "bz2-1.dll" as the runtime name. We add a bz2-1.dll alias
# after install so bsdtar finds the DLL under either name at runtime.
# ════════════════════════════════════════════════════════════════════════════════
STEP="[2/7] bzip2"
echo "==> $STEP"
clone_or_update "$BZIP2_SRC" "https://github.com/libarchive/bzip2.git"

python3 - "$BZIP2_SRC/CMakeLists.txt" << 'PYEOF'
import sys, pathlib
f = pathlib.Path(sys.argv[1])
t = f.read_text(encoding='utf-8')
old = 'set_target_properties(bz2 PROPERTIES'
new = 'set_target_properties(bz2 PROPERTIES\n    OUTPUT_NAME bz2-1\n    PREFIX ""'
if old in t and new not in t:
    t = t.replace(old, new, 1)
    f.write_text(t, encoding='utf-8')
    print('  bzip2 patch: applied')
else:
    print('  bzip2 patch: already applied or target not found')
PYEOF
grep -q 'OUTPUT_NAME bz2-1' "$BZIP2_SRC/CMakeLists.txt" \
    || { echo "✗ bzip2 OUTPUT_NAME patch failed"; exit 1; }
echo "  ✓ bzip2 patch verified"
cmake -S "$BZIP2_SRC" -B "$BZIP2_BLD" "${CDEP[@]}" \
    -DBUILD_SHARED_LIBS=ON \
    -DENABLE_STATIC_LIB=ON \
    -DENABLE_SHARED_LIB=ON \
    -DENABLE_TESTS=OFF \
    -DENABLE_DOCS=OFF
make -C "$BZIP2_BLD" -j"$JOBS"
make -C "$BZIP2_BLD" install
# Fork installs the DLL to lib/ instead of bin/ on Windows — relocate it
find "$PREFIX/lib" -maxdepth 2 -name "*.dll" 2>/dev/null | while read -r f; do
    echo "  Relocating $(basename "$f") → bin/"
    mv "$f" "$PREFIX/bin/"
done
echo "  DLL name  : $(ls "$PREFIX/bin/"*bz2*.dll 2>/dev/null | xargs -I{} basename {})"
echo "  Import lib: $(ls "$PREFIX/lib/"*bz2*.dll.a 2>/dev/null | xargs -I{} basename {})"
echo "  ✓ bzip2"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 3 — lz4 (latest git HEAD)
# ════════════════════════════════════════════════════════════════════════════════
STEP="[3/7] lz4"
echo "==> $STEP"
clone_or_update "$LZ4_SRC" "https://github.com/lz4/lz4.git"
cmake -S "$LZ4_SRC/build/cmake" -B "$LZ4_BLD" "${CDEP[@]}" \
    -DBUILD_SHARED_LIBS=ON \
    -DLZ4_BUILD_CLI=OFF \
    -DLZ4_BUILD_LEGACY_LZ4C=OFF
make -C "$LZ4_BLD" -j"$JOBS"
make -C "$LZ4_BLD" install
echo "  ✓ lz4"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 4 — zstd (latest git HEAD)
# The dev branch declares "project(zstd LANGUAGES C)" but
# AddZstdCompilationFlags.cmake unconditionally calls CHECK_CXX_COMPILER_FLAG,
# which CMake refuses unless CXX is an enabled project language.
# Patch: add CXX to the project() languages line before configuring.
# ════════════════════════════════════════════════════════════════════════════════
STEP="[4/7] zstd"
echo "==> $STEP"
clone_or_update "$ZSTD_SRC" "https://github.com/facebook/zstd.git"
python3 - "$ZSTD_SRC/build/cmake/CMakeLists.txt" << 'PYEOF'
import sys, pathlib, re

f = pathlib.Path(sys.argv[1])
t = f.read_text(encoding='utf-8')

# Multiline project() block — replace "LANGUAGES C" line (with optional comment)
# Matches:  "    LANGUAGES C   # some comment"
# Leaves the comment intact, appends CXX
patched, n = re.subn(
    r'([ \t]*LANGUAGES[ \t]+C)([ \t]*(?:#[^\n]*)?)',
    r'\1 CXX\2',
    t, count=1
)
if n and patched != t:
    f.write_text(patched, encoding='utf-8')
    print('  zstd patch: appended CXX to LANGUAGES C line')
else:
    print('  zstd patch: already patched or pattern not found')
PYEOF

grep -qE 'LANGUAGES\s+C\s+CXX' "$ZSTD_SRC/build/cmake/CMakeLists.txt" \
    || { echo "✗ zstd CXX language patch failed"; exit 1; }
echo "  ✓ zstd patch verified"

cmake -S "$ZSTD_SRC/build/cmake" -B "$ZSTD_BLD" "${CDEP[@]}" \
    -DZSTD_BUILD_SHARED=ON \
    -DZSTD_BUILD_STATIC=ON \
    -DZSTD_BUILD_PROGRAMS=OFF \
    -DZSTD_BUILD_TESTS=OFF \
    -DZSTD_BUILD_CONTRIB=OFF
make -C "$ZSTD_BLD" -j"$JOBS"
make -C "$ZSTD_BLD" install
echo "  ✓ zstd"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 5 — xz / liblzma (latest git HEAD)
# ════════════════════════════════════════════════════════════════════════════════
STEP="[5/7] xz/liblzma"
echo "==> $STEP"
clone_or_update "$XZ_SRC" "https://github.com/tukaani-project/xz.git"
cmake -S "$XZ_SRC" -B "$XZ_BLD" "${CDEP[@]}" \
    -DBUILD_SHARED_LIBS=ON \
    -DXZ_BUILD_DOCS=OFF \
    -DENABLE_NLS=OFF \
    -DXZ_BUILD_XZ=OFF \
    -DXZ_BUILD_XZDEC=OFF \
    -DXZ_BUILD_LZMADEC=OFF \
    -DXZ_BUILD_LZMAINFO=OFF \
    -DXZ_BUILD_XZ_LINKS=OFF \
    -DXZ_BUILD_LZMA_LINKS=OFF
make -C "$XZ_BLD" -j"$JOBS"
make -C "$XZ_BLD" install
echo "  ✓ xz/liblzma"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 6 — expat (latest git HEAD)
# ════════════════════════════════════════════════════════════════════════════════
STEP="[6/7] expat"
echo "==> $STEP"
clone_or_update "$EXPAT_SRC" "https://github.com/libexpat/libexpat.git"
cmake -S "$EXPAT_SRC/expat" -B "$EXPAT_BLD" "${CDEP[@]}" \
    -DBUILD_SHARED_LIBS=ON \
    -DEXPAT_BUILD_EXAMPLES=OFF \
    -DEXPAT_BUILD_TESTS=OFF \
    -DEXPAT_BUILD_TOOLS=OFF \
    -DEXPAT_BUILD_DOCS=OFF
make -C "$EXPAT_BLD" -j"$JOBS"
make -C "$EXPAT_BLD" install
echo "  ✓ expat"

# ════════════════════════════════════════════════════════════════════════════════
# DEP 7 — OpenSSL (latest git HEAD — master branch)
# Uses its own perl Configure + GNU make (not CMake).
# Tracks master (currently OpenSSL 4.x dev) instead of a pinned stable tag.
# ════════════════════════════════════════════════════════════════════════════════
STEP="[7/7] OpenSSL"
echo "==> $STEP"
clone_or_update "$OSSL_SRC" "https://github.com/openssl/openssl.git"

pushd "$OSSL_SRC" > /dev/null
make distclean 2>/dev/null || true
perl ./Configure mingw64 \
    shared \
    no-apps \
    no-tests \
    no-makedepend \
    --prefix="$PREFIX" \
    --openssldir="$PREFIX/ssl" \
    --with-zlib-include="$PREFIX/include" \
    --with-zlib-lib="$PREFIX/lib" \
    "CC=clang" \
    "CFLAGS=-O2 -pipe" \
    "LDFLAGS=-fuse-ld=lld"
make -j"$JOBS"
make install_sw
popd > /dev/null
echo "  ✓ OpenSSL"

# ════════════════════════════════════════════════════════════════════════════════
# libarchive + bsdtar (latest git HEAD)
# ════════════════════════════════════════════════════════════════════════════════
STEP="libarchive clone"
echo "==> Cloning/updating libarchive..."
clone_or_update "$LIBARCHIVE_SRC" "https://github.com/libarchive/libarchive.git"
LA_HEAD=$(git -C "$LIBARCHIVE_SRC" log --oneline -1)

python3 - "$LIBARCHIVE_SRC/CMakeLists.txt" << 'PYEOF'
import sys, pathlib
f = pathlib.Path(sys.argv[1])
t = f.read_text(encoding='utf-8')
old = 'SET(POSIX_REGEX_LIB "AUTO" CACHE STRING'
new = 'SET(POSIX_REGEX_LIB "NONE" CACHE STRING'
insert_block = '\nIF(POSIX_REGEX_LIB STREQUAL "NONE")\n  SET(FOUND_POSIX_REGEX_LIB 1)\nENDIF()'
if old in t:
    t = t.replace(old, new, 1)
    print('  regex patch step 1: AUTO -> NONE')
else:
    print('  regex patch step 1: already patched or not found')
if 'STREQUAL "NONE"' not in t:
    t = t.replace(new, new + insert_block, 1)
    print('  regex patch step 2: STREQUAL block inserted')
else:
    print('  regex patch step 2: STREQUAL block already present')
f.write_text(t, encoding='utf-8')
PYEOF
grep -q 'POSIX_REGEX_LIB "NONE"' "$LIBARCHIVE_SRC/CMakeLists.txt" \
    || { echo "✗ regex patch step 1 failed"; exit 1; }
grep -q 'STREQUAL "NONE"' "$LIBARCHIVE_SRC/CMakeLists.txt" \
    || { echo "✗ regex patch step 2 failed"; exit 1; }
echo "  ✓ regex patch verified"

STEP="libarchive configure"
echo "==> Configuring libarchive..."

BZ2_IMP=$(ls "$PREFIX/lib/"*bz2*.dll.a 2>/dev/null | head -1)
echo "  Pinning bzip2 import lib: $BZ2_IMP"

EXPAT_IMP=$(ls "$PREFIX/lib/"*expat*.dll.a 2>/dev/null | head -1)
echo "  Pinning expat import lib: $EXPAT_IMP"

cmake -S "$LIBARCHIVE_SRC" -B "$LIBARCHIVE_BLD" \
    -G "MSYS Makefiles" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_PREFIX_PATH="$PREFIX" \
    -DCMAKE_C_COMPILER=clang \
    -DCMAKE_CXX_COMPILER=clang++ \
    -DCMAKE_AR=/ucrt64/bin/llvm-ar \
    -DCMAKE_RANLIB=/ucrt64/bin/llvm-ranlib \
    -DCMAKE_NM=/ucrt64/bin/llvm-nm \
    -DCMAKE_C_FLAGS="-O2 -pipe" \
    -DCMAKE_EXE_LINKER_FLAGS="-fuse-ld=lld" \
    -DCMAKE_SHARED_LINKER_FLAGS="-fuse-ld=lld" \
    -DENABLE_ZLIB=ON \
    -DENABLE_BZip2=ON \
    -DBZIP2_INCLUDE_DIR="$PREFIX/include" \
    -DBZIP2_LIBRARY_RELEASE="$BZ2_IMP" \
    -DBZIP2_LIBRARY_DEBUG="$BZ2_IMP" \
    -DENABLE_LZMA=ON \
    -DENABLE_ZSTD=ON \
    -DENABLE_LZ4=ON \
    -DENABLE_LZO2=OFF \
    -DENABLE_OPENSSL=ON \
    -DOPENSSL_USE_STATIC_LIBS=FALSE \
    -DOPENSSL_ROOT_DIR="$PREFIX" \
    -DENABLE_MBEDTLS=OFF \
    -DENABLE_LIBB2=OFF \
    -DENABLE_EXPAT=ON \
    -DEXPAT_INCLUDE_DIR="$PREFIX/include" \
    -DEXPAT_LIBRARY="$EXPAT_IMP" \
    -DENABLE_LIBXML2=OFF \
    -DENABLE_TAR=ON \
    -DENABLE_CPIO=ON \
    -DENABLE_CAT=ON \
    -DENABLE_UNZIP=ON \
    -DENABLE_STATIC=OFF \
    -DENABLE_TEST=OFF \
    -DENABLE_ICONV=OFF \
    -DPOSIX_REGEX_LIB=NONE \
    -DHAVE_REGEX_H=0 \
    -DENABLE_NLS=OFF

STEP="libarchive build"
echo "==> Building libarchive ($JOBS jobs)..."
make -C "$LIBARCHIVE_BLD" -j"$JOBS"

STEP="libarchive install"
echo "==> Installing to $PREFIX..."
make -C "$LIBARCHIVE_BLD" install

# ── Verify ────────────────────────────────────────────────────────────────────
STEP="verify"
BSDTAR="$PREFIX/bin/bsdtar.exe"

if [ ! -f "$BSDTAR" ]; then
    echo "✗ bsdtar.exe not found at $BSDTAR"
    exit 1
fi

export PATH="$PREFIX/bin:$PATH"

echo ""
echo "  DLLs in $PREFIX/bin/:"
ls -1 "$PREFIX/bin/"*.dll 2>/dev/null | sed 's|.*/|    |' \
    || echo "    (none)"

# Check for missing DLLs before attempting to run bsdtar.
# Filter Windows system DLLs (api-ms-win-*, ext-ms-win-*, KERNEL32, ntdll)
# which always exist on Win10/11 but are invisible to MSYS2 ldd.
echo ""
echo "  ldd check (filtering Windows system DLLs):"
MISSING=$(ldd "$BSDTAR" \
    | grep -i 'not found' \
    | grep -iv 'api-ms-win' \
    | grep -iv 'ext-ms-win' \
    | grep -iv 'KERNEL32\|ntdll\|KERNELBASE' || true)

if [ -n "$MISSING" ]; then
    echo "$MISSING"
    echo ""
    echo "  ✗ missing DLLs above — bsdtar will not start"
    exit 1
fi
echo "  ✓ all runtime DLLs resolved"

echo ""
VERSION=$("$BSDTAR" --version 2>&1 | head -1) || true
echo "✓ bsdtar built successfully"
echo "  Version : $VERSION"
echo "  Binary  : $BSDTAR"
echo "  Source  : $LA_HEAD"

# .dll.a files are import libs (linker stubs) — correct and expected.
# Flag only plain .a static archives.
echo ""
echo "  Static lib check (.dll.a import libs are fine — flagging .a only):"
STATICS=$(find "$PREFIX/lib" -name "*.a" ! -name "*.dll.a" 2>/dev/null)
if [ -n "$STATICS" ]; then
    echo "$STATICS" | sed 's|.*/|    |'
    echo "  (static libs present — expected if built with ENABLE_STATIC_LIB=ON)"
else
    echo "  ✓ no static libs"
fi

# ── Clean build dirs (source trees kept for fast re-runs) ────────────────────
STEP="cleanup"
echo ""
echo "==> Removing build dirs..."
rm -rf "$BLD"
pushd "$OSSL_SRC" > /dev/null
make distclean 2>/dev/null || true
popd > /dev/null
echo "  ✓ Done. Source trees kept under $SRC; install at $PREFIX"
