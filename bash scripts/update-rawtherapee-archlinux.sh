#!/bin/bash
set -e

echo "==> Fetching latest from upstream (Beep6581)..."
cd /home/admin/Downloads/RawTherapee
git fetch upstream
git merge upstream/dev

echo "==> Pushing to your GitHub fork (jdb130496)..."
git push origin dev

echo "==> Building..."
cd build
ninja -j$(nproc)

echo "==> Installing..."
sudo ninja install

echo "==> Done! $(rawtherapee --version 2>&1 | head -1)"
