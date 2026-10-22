#!/usr/bin/env bash
# Build NASM (from GitHub) + OpenSSL (from GitHub) using Clang, isolated under /opt.
# Parallel build with make -j$(nproc) — the Linux-native equivalent of jom on Windows.

# Check required Perl modules
for mod in IPC::Cmd Time::Piece; do
    perl -e "use ${mod}" 2>/dev/null || {
        echo "ERROR: Perl module ${mod} not found."
        echo "       Run: sudo dnf install -y perl-IPC-Cmd perl-Time-Piece"
        exit 1
    }
done

set -euo pipefail

# ────────────────────────────────────────────────────────────────
# Config — adjust versions/paths here
# ────────────────────────────────────────────────────────────────
JOBS=$(nproc)
NASM_SRC=/opt/nasm-src
NASM_PREFIX=/opt/nasm
OPENSSL_SRC=/opt/openssl-src
OPENSSL_PREFIX=/opt/openssl

export CC=clang
export CXX=clang++
export AR=llvm-ar
export RANLIB=llvm-ranlib

# ────────────────────────────────────────────────────────────────
# Prerequisite checks
# ────────────────────────────────────────────────────────────────
need() { command -v "$1" >/dev/null 2>&1 || { echo "ERROR: '$1' not found. Install it first."; exit 1; }; }
need clang
need git
need perl
need autoconf
need automake

echo ">>> Jobs: ${JOBS}, CC: ${CC}"

# ────────────────────────────────────────────────────────────────
# 1. NASM
# ────────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════"
echo " Building NASM → ${NASM_PREFIX}"
echo "════════════════════════════════════"

if [[ -d "${NASM_SRC}/.git" ]]; then
    echo ">>> NASM source exists; pulling latest..."
    git -C "${NASM_SRC}" pull --ff-only
else
    echo ">>> Cloning NASM..."
    git clone https://github.com/netwide-assembler/nasm.git "${NASM_SRC}"
fi

cd "${NASM_SRC}"
echo ">>> Running autogen.sh..."
./autogen.sh

echo ">>> Configuring NASM..."
CC=clang ./configure \
    --prefix="${NASM_PREFIX}" \
    --disable-debug

echo ">>> Building NASM (${JOBS} parallel jobs)..."
make -j"${JOBS}"

# 'make install' fails on git checkouts — man pages are not generated without
# asciidoc/xmlto. Binaries are already built; copy them directly.
echo ">>> Installing NASM binaries (skipping docs — git checkout has no pre-built man pages)..."
mkdir -p "${NASM_PREFIX}/bin"
install -Dm755 "${NASM_SRC}/nasm"    "${NASM_PREFIX}/bin/nasm"
install -Dm755 "${NASM_SRC}/ndisasm" "${NASM_PREFIX}/bin/ndisasm"

echo ">>> NASM: $("${NASM_PREFIX}/bin/nasm" --version)"

# ────────────────────────────────────────────────────────────────
# Prepend custom NASM so OpenSSL's Configure uses it
# ────────────────────────────────────────────────────────────────
export PATH="${NASM_PREFIX}/bin:${PATH}"
echo ">>> which nasm: $(which nasm)"

# ────────────────────────────────────────────────────────────────
# 2. OpenSSL
# ────────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════"
echo " Building OpenSSL → ${OPENSSL_PREFIX}"
echo "════════════════════════════════════"

if [[ -d "${OPENSSL_SRC}/.git" ]]; then
    echo ">>> OpenSSL source exists; pulling latest..."
    git -C "${OPENSSL_SRC}" pull --ff-only
else
    echo ">>> Cloning OpenSSL (default/HEAD branch)..."
    git clone --depth 1 https://github.com/openssl/openssl.git "${OPENSSL_SRC}"
fi

cd "${OPENSSL_SRC}"
echo ">>> OpenSSL tree: $(git log -1 --oneline)"

echo ">>> Cleaning any previous build..."
make clean || true

echo ">>> Configuring OpenSSL..."
perl Configure linux-x86_64 \
    CC=clang \
    CXX=clang++ \
    AR=llvm-ar \
    RANLIB=llvm-ranlib \
    NASM="${NASM_PREFIX}/bin/nasm" \
    --prefix="${OPENSSL_PREFIX}" \
    --openssldir="${OPENSSL_PREFIX}/ssl" \
    shared

echo ">>> Building OpenSSL (${JOBS} parallel jobs)..."
make -j"${JOBS}"

echo ">>> Running full OpenSSL test suite (${JOBS} parallel jobs)..."
make test -j"${JOBS}" || { echo "ERROR: OpenSSL tests failed — aborting install."; exit 1; }

echo ">>> Installing OpenSSL..."
make install_sw install_ssldirs

echo ">>> OpenSSL: $(LD_LIBRARY_PATH="${OPENSSL_PREFIX}/lib64" "${OPENSSL_PREFIX}/bin/openssl" version)"

# ────────────────────────────────────────────────────────────────
# Summary
# ────────────────────────────────────────────────────────────────
echo
echo "════════════════════════════════════"
echo " All done!"
echo "════════════════════════════════════"
echo "  NASM    : ${NASM_PREFIX}"
echo "  OpenSSL : ${OPENSSL_PREFIX}"
echo
echo "To activate in your shell (do NOT add to /etc/profile — keep it opt-in):"
echo "  export PATH=${NASM_PREFIX}/bin:${OPENSSL_PREFIX}/bin:\$PATH"
echo "  export PKG_CONFIG_PATH=${OPENSSL_PREFIX}/lib64/pkgconfig:\$PKG_CONFIG_PATH"
echo "  export LD_LIBRARY_PATH=${OPENSSL_PREFIX}/lib64:\$LD_LIBRARY_PATH"
echo
echo "To compile against this OpenSSL:"
echo "  clang myapp.c \$(${OPENSSL_PREFIX}/bin/openssl-config --cflags --libs)"
