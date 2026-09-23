#!/bin/bash

export PATH="/ucrt64/bin:$PATH"

INPUT_DIR="/d/dev/pdf-images"
CUT_DIR="/d/dev/pdf-images/cut"
OUTPUT="/d/dev/pdf-images/panchdev-atharvashirsh.pdf"

mkdir -p "$CUT_DIR"

# --- Step 1: Cut pages ---
echo "=== Cutting pages ==="
counter=1

for img in $(ls "$INPUT_DIR"/img1_Page_*.png | sort -V); do
    width=$(magick "$img" -format "%w" info:)
    height=$(magick "$img" -format "%h" info:)

    echo "Processing: $(basename $img) — ${width}x${height}"

    if [ "$width" -gt "$height" ]; then
        half=$((width / 2))
        magick "$img" -crop "${half}x${height}+0+0" +repage "$CUT_DIR/page_$(printf '%04d' $counter).png"
        counter=$((counter + 1))
        magick "$img" -crop "${half}x${height}+${half}+0" +repage "$CUT_DIR/page_$(printf '%04d' $counter).png"
        counter=$((counter + 1))
    else
        magick "$img" "$CUT_DIR/page_$(printf '%04d' $counter).png"
        counter=$((counter + 1))
    fi
done

echo "Done! $((counter - 1)) pages written to $CUT_DIR"

# --- Step 2: Stitch into PDF ---
echo ""
echo "=== Stitching PDF ==="
magick $(ls "$CUT_DIR"/page_*.png | sort -V) "$OUTPUT"

echo "Done! → $OUTPUT"
