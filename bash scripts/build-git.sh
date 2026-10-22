#!/bin/bash
set -euo pipefail

SRC="/d/dev/git-src"
STAGE="/d/dev/git-stage"
MINGIT="/d/Programs/MinGit"
LOG="/d/dev/build-git.log"

#exec 1>"$LOG" 2>&1

echo "========================================"
echo " Git Build — ucrt64 clang"
echo " $(date)"
echo "========================================"

export PATH="/ucrt64/bin:/usr/bin:$PATH"
export CC=/ucrt64/bin/clang
export CXX=/ucrt64/bin/clang++
unset MAKEFLAGS MFLAGS MAKELEVEL CARGO_MAKEFLAGS

echo "clang: $(clang --version | head -1)"
echo "make : $(make --version | head -1)"

# -------------------------------------------------------
# Update source
# -------------------------------------------------------
echo ""
echo "=== Updating source ==="
if [ -d "$SRC/.git" ]; then
    cd "$SRC"
    git checkout compat/posix.h 2>/dev/null || true
    git pull
else
    git clone --depth=1 https://github.com/git-for-windows/git.git "$SRC"
    cd "$SRC"
fi

cd "$SRC"

# Version
GIT_BUILD_VERSION=$(git log --pretty=%s | grep -oP "v[\d.]+\.windows\.\d+" | head -1 | sed 's/^v//' || true)
[ -z "$GIT_BUILD_VERSION" ] && GIT_BUILD_VERSION="(unknown)"
echo "Version : $GIT_BUILD_VERSION"

# -------------------------------------------------------
# Build — parallel
# -------------------------------------------------------
echo ""
echo "=== Building ==="
CARGO_MAKEFLAGS="" \
make \
    -j$(nproc) \
    --no-print-directory \
    CC=/ucrt64/bin/clang \
    prefix="$STAGE" \
    CFLAGS="-march=native -O2" \
    USE_LIBPCRE2=1 \
    NO_GETTEXT=1 \
    NO_PERL=1 \
    NO_TCLTK=1 \
    NO_GITWEB=1 \
    NO_FUZZING=1 \
    2>&1 | grep -v "jobserver unavailable\|Add '+' to parent"

# -------------------------------------------------------
# Install to staging — serial to avoid race conditions
# -------------------------------------------------------
echo ""
echo "=== Installing to staging ==="
unset MAKEFLAGS MFLAGS MAKELEVEL CARGO_MAKEFLAGS
rm -rf "$STAGE"
make \
    -j1 \
    --no-print-directory \
    MAKEFLAGS= \
    CARGO_MAKEFLAGS= \
    CC=/ucrt64/bin/clang \
    prefix="$STAGE" \
    CFLAGS="-march=native -O2" \
    USE_LIBPCRE2=1 \
    NO_GETTEXT=1 \
    NO_PERL=1 \
    NO_TCLTK=1 \
    NO_GITWEB=1 \
    NO_FUZZING=1 \
    install 2>&1 | grep -v "jobserver unavailable\|Add '+' to parent"

mkdir -p "$STAGE/cmd"
cp "$STAGE/bin/git.exe" "$STAGE/cmd/git.exe"

# -------------------------------------------------------
# Copy staging to MinGit
# -------------------------------------------------------
echo ""
echo "=== Copying to MinGit ==="
cp -r "$STAGE/." "$MINGIT/"

BIN_VER=$("$MINGIT/bin/git.exe" --version 2>/dev/null || echo "(could not read version)")

echo ""
echo "========================================"
echo " Build complete"
echo " $BIN_VER"
echo "========================================"
