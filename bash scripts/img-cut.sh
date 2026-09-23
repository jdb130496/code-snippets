#!/bin/bash

export PATH="/ucrt64/bin:$PATH"

INPUT_DIR="/d/dev/pdf-images"
OUTPUT_DIR="/d/dev/pdf-images/cut"
mkdir -p "$OUTPUT_DIR"

counter=1

for img in $(ls "$INPUT_DIR"/img1_Page_*.png | sort -V); do
    width=$(magick "$img" -format "%w" info:)
    height=$(magick "$img" -format "%h" info:)

    echo "Processing: $(basename $img) — ${width}x${height}"

    if [ "$width" -gt "$height" ]; then
        half=$((width / 2))
        magick "$img" -crop "${half}x${height}+0+0" +repage "$OUTPUT_DIR/page_$(printf '%04d' $counter).png"
        counter=$((counter + 1))
        magick "$img" -crop "${half}x${height}+${half}+0" +repage "$OUTPUT_DIR/page_$(printf '%04d' $counter).png"
        counter=$((counter + 1))
    else
        magick "$img" "$OUTPUT_DIR/page_$(printf '%04d' $counter).png"
        counter=$((counter + 1))
    fi

done

echo "Done! $((counter-1)) pages written to $OUTPUT_ID"
