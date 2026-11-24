#!/bin/bash
set -e

echo "=== Setting up ProtonVPN ==="

# 1. Create and activate venv
python3 -m venv ~/.venv
source ~/.venv/bin/activate

# 2. Clone repos if not already present
cd ~/Downloads

for repo in python-proton-core python-proton-vpn-api-core proton-vpn-gtk-app; do
    if [ ! -d "$repo" ]; then
        GIT_TERMINAL_PROMPT=0 git clone https://github.com/ProtonVPN/$repo
    else
        echo "$repo already exists, pulling latest..."
        cd $repo && git pull && cd ..
    fi
done

# 3. Install python packages
pip install -e ~/Downloads/python-proton-core
pip install -e ~/Downloads/python-proton-vpn-api-core
pip install -e ~/Downloads/proton-vpn-gtk-app

# 4. Enable Proton repo and download RPM
sudo dnf config-manager addrepo --from-repofile=https://repo.protonvpn.com/fedora/protonvpn-stable.repo 2>/dev/null || true
cd ~/Downloads
mkdir -p proton-extract
cd proton-extract
sudo dnf download --enablerepo=protonvpn-fedora-stable python3-proton-vpn-api-core
rpm2cpio python3-proton-vpn-api-core*.x86_64.rpm | cpio -idmv

# 5. Copy platform.abi3.so
rm -f ~/Downloads/python-proton-vpn-api-core/proton/vpn/platform.abi3.so
cp ~/Downloads/proton-extract/usr/lib64/python3.15/site-packages/proton/vpn/platform.abi3.so \
   ~/Downloads/python-proton-vpn-api-core/proton/vpn/platform.abi3.so

# 6. Create wrapper script
cat > ~/.local/bin/pvpn-start << 'WRAPPER'
#!/bin/bash
source /home/admin/.venv/bin/activate
protonvpn-app
WRAPPER
chmod +x ~/.local/bin/pvpn-start

# 7. Create correct .desktop entry
sudo tee /usr/share/applications/protonvpn.desktop > /dev/null << 'DESKTOP'
[Desktop Entry]
Name=ProtonVPN
Exec=/bin/bash -c "export XDG_RUNTIME_DIR=/run/user/$(id -u); source /home/admin/.venv/bin/activate && protonvpn-app"
Icon=protonvpn
Type=Application
Categories=Network;VPN;
Terminal=false
StartupNotify=true
DESKTOP

# 8. Remove old desktop entry if exists
rm -f ~/.local/share/applications/protonvpn.desktop
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true

echo "=== ProtonVPN setup complete! Run: protonvpn-app ==="
