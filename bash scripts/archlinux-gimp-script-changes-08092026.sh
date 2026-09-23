#!/bin/bash
set -e

FILE=~/OneDrive/'bash scripts'/gimp-git-archlinux-19082026.sh

echo "Patching: $FILE"

# ==============================================================================
# 1. All gitlab.gnome.org → github.com (covers gexiv2, babl, gegl, gimp)
# ==============================================================================
sed -i 's|https://gitlab.gnome.org/GNOME/|https://github.com/GNOME/|g' "$FILE"

# ==============================================================================
# 2. gexiv2 — add --depth 1, remove redundant checkout+pull
# ==============================================================================
sed -i 's|git clone https://github.com/GNOME/gexiv2.git|git clone --depth 1 https://github.com/GNOME/gexiv2.git|' "$FILE"
sed -i '/^git checkout master$/d' "$FILE"

# ==============================================================================
# 3. exiv2 — replace static tag block with dynamic v0.28.x detection
# ==============================================================================
python3 - "$FILE" << 'PYEOF'
import sys, re

f = sys.argv[1]
with open(f) as fh:
    content = fh.read()

old = re.compile(
    r'if \[\[ ! -d exiv2 \]\]; then\n'
    r'    git clone https://github\.com/Exiv2/exiv2\.git\n'
    r'fi\n'
    r'cd exiv2\n'
    r'git fetch --tags\n'
    r'\n'
    r'# Use latest release tag \(not main[^\n]*\n'
    r'EXIV2_TAG=\$\(git tag[^\n]*\)\n'
    r'echo "Using exiv2 tag: \$EXIV2_TAG"\n'
    r'git checkout "\$EXIV2_TAG"\n'
    r'git clean -fd\n'
    r'\n'
    r'rm -rf build && mkdir build && cd build'
)

new = (
    '# Dynamically find latest stable exiv2 tag (v0.28.x) compatible with gexiv2\n'
    'EXIV2_TAG=$(git ls-remote --tags https://github.com/Exiv2/exiv2.git \\\n'
    '    | grep -oP \'refs/tags/v0\\.28\\.[0-9]+\' \\\n'
    '    | sed \'s|refs/tags/||g\' \\\n'
    '    | sort -V | tail -1)\n'
    'echo "Using exiv2 tag: $EXIV2_TAG (latest stable v0.28.x)"\n'
    '\n'
    'if [[ ! -d exiv2 ]]; then\n'
    '    git clone --depth 1 --branch "$EXIV2_TAG" https://github.com/Exiv2/exiv2.git\n'
    'else\n'
    '    cd exiv2\n'
    '    git fetch --tags\n'
    '    git checkout "$EXIV2_TAG"\n'
    '    cd ..\n'
    'fi\n'
    'cd exiv2\n'
    'rm -rf build && mkdir build && cd build'
)

result, count = old.subn(new, content)
if count == 0:
    print("WARNING: exiv2 block not matched — check manually")
else:
    print(f"✓ exiv2 block replaced ({count} match)")

with open(f, 'w') as fh:
    fh.write(result)
PYEOF

# ==============================================================================
# 4. gimp-data submodule — add sed rewrite of .gitmodules before sync
# ==============================================================================
python3 - "$FILE" << 'PYEOF'
import sys

f = sys.argv[1]
with open(f) as fh:
    content = fh.read()

old = 'echo "Initializing gimp-data submodule..."'

new = (
    'echo "Initializing gimp-data submodule..."\n'
    'echo "Fixing submodule URL to use GitHub mirror..."\n'
    'sed -i \'s|https://gitlab.gnome.org/GNOME/gimp-data|https://github.com/GNOME/gimp-data|g\' .gitmodules\n'
    'git config submodule.gimp-data.url https://github.com/GNOME/gimp-data.git'
)

result = content.replace(old, new, 1)
if result == content:
    print("WARNING: gimp-data submodule block not matched — check manually")
else:
    print("✓ gimp-data submodule block replaced")

with open(f, 'w') as fh:
    fh.write(result)
PYEOF

echo ""
echo "✓ All patches applied."
echo ""
echo "Verify — should show zero gitlab hits:"
grep -n 'gitlab' "$FILE" && echo "⚠ gitlab URLs remain!" || echo "✓ No gitlab URLs remaining"
grep -n 'ls-remote\|Fixing submodule' "$FILE"
