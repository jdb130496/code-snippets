# Step 1 - Backup originals to D:\dump\usb-backup
mkdir -p /d/dump/usb-backup
for f in /e/1/*_norm.mp3; do
    original="${f/_norm.mp3/.mp3}"
    cp "$original" "/d/dump/usb-backup/$(basename "$original")"
    echo "Backed up: $(basename "$original")"
done
echo "--- Backup complete ---"

# Step 2 - Replace originals with _norm versions
for f in /e/1/*_norm.mp3; do
    original="${f/_norm.mp3/.mp3}"
    mv "$f" "$original"
    echo "Replaced: $(basename "$original")"
done
echo "--- All done ---"
