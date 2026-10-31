#!/bin/bash
set -e

# ── Configuration ────────────────────────────────────────────
REPO_DIR="/home/admin/Downloads/RawTherapee"
GH_USER="jdb130496"
GH_TOKEN=$(grep -oP '(?<=:)ghp_[^@]+' /root/.git-credentials)  # Update this when token changes
GH_REPO="RawTherapee"
# ─────────────────────────────────────────────────────────────

echo "==> Ensuring correct GitHub credentials..."
git -C "$REPO_DIR" remote set-url origin \
  "https://${GH_USER}:${GH_TOKEN}@github.com/${GH_USER}/${GH_REPO}.git"
echo "https://${GH_USER}:${GH_TOKEN}@github.com" > /root/.git-credentials
echo "https://${GH_USER}:${GH_TOKEN}@github.com" > /home/admin/.git-credentials

echo "==> Fetching latest from upstream (Beep6581)..."
cd "$REPO_DIR"
git fetch upstream
git merge upstream/dev --no-edit

echo "==> Pushing to your GitHub fork (jdb130496)..."
git push origin dev

echo "==> Building..."
cd build
ninja -j$(nproc)

echo "==> Installing..."
sudo ninja install

echo "==> Done!"
cat /usr/local/share/doc/rawtherapee/AboutThisBuild.txt

