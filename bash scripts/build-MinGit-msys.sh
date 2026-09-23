#!/bin/bash
set -e

SRC="/d/dev/git-src"
PREFIX="/d/Programs/MinGit"
LOG="/d/dev/build-git.log"

echo "========================================"
echo " Git-for-Windows Build Script"
echo " $(date)"
echo "========================================"

echo ""
echo "=== Setting up ucrt64 toolchain ==="
export PATH="/ucrt64/bin:/usr/bin:$PATH"
echo "cargo : $(which cargo) -- $(cargo --version)"
echo "rustc : $(which rustc) -- $(rustc --version)"
echo "gcc   : $(which gcc) -- $(gcc --version | head -1)"
echo "make  : $(which make) -- $(make --version | head -1)"
echo "git   : $(which git) -- $(git --version)"

echo ""
echo "=== Cleaning install dir and Rust cache ==="
rm -rf "$PREFIX"
rm -rf "$SRC/target"

echo ""
echo "=== Updating source ==="
if [ -d "$SRC/.git" ]; then
    echo "Repo exists — pulling latest"
    cd "$SRC"
    git checkout compat/posix.h 2>/dev/null || true
    git pull
else
    echo "Fresh shallow clone"
    git clone --depth=1 https://github.com/git-for-windows/git.git "$SRC"
    cd "$SRC"
fi

echo ""
echo "=== Determining version string ==="
cd "$SRC"
# Search recent log for last merge tag commit (works on shallow clones)
GIT_BUILD_VERSION=$(git log --pretty=%s | grep -oP "v[\d.]+\.windows\.\d+" | head -1 | sed 's/^v//' || true)
if [ -z "$GIT_BUILD_VERSION" ]; then
    GIT_BUILD_VERSION="(unknown)"
fi
echo "Version : $GIT_BUILD_VERSION"

echo ""
echo "=== Building Rust component ==="
# Strip Windows-incompatible named pipe jobserver handles (-2,-2) from
# MAKEFLAGS before cargo inherits the environment — cargo can't open them
export MAKEFLAGS=$(echo "${MAKEFLAGS}" | \
  sed 's/--jobserver-auth=-2,-2[^ ]* \?//g' | \
  sed 's/--jobserver-auth=[0-9,]*//g' | \
  xargs)
cargo build --release --target x86_64-pc-windows-gnu

echo ""
echo "=== Staging libgitcore.a ==="
mkdir -p target/release
cp target/x86_64-pc-windows-gnu/release/libgitcore.a target/release/libgitcore.a

echo ""
echo "=== Building and installing git ==="
# NO_RUST omitted — passing it drops cmd_format_rev/cmd_name_rev builtins
# causing undefined-reference link errors.
# GIT_VERSION passed on command line so binary reports clean tag even after
# make regenerates GIT-VERSION-FILE with the long describe suffix.
# jobserver warning filtered from stderr — it is harmless on MSYS2/Windows
# (sub-make falls back to -j1 for the small templates step only).
unset MAKEFLAGS
make -j$(nproc) \
  prefix="$PREFIX" \
  NO_GETTEXT=1 \
  NO_TCLTK=1 \
  NO_GITWEB=1 \
  install 2> >(grep -v "jobserver unavailable" >&2)

echo ""
echo "=== Updating cmd/git.exe ==="
mkdir -p "$PREFIX/cmd"
cp "$PREFIX/bin/git.exe" "$PREFIX/cmd/git.exe"

BIN_VER=$("$PREFIX"/bin/git.exe --version)
CMD_VER=$("$PREFIX"/cmd/git.exe --version)

echo ""
echo "========================================"
echo " Build complete"
echo " bin : $BIN_VER"
echo " cmd : $CMD_VER"
echo "========================================"

# Write summary to log at the end
{
echo "========================================"
echo " Build complete: $(date)"
echo " bin : $BIN_VER"
echo " cmd : $CMD_VER"
echo "========================================"
} > "$LOG"

