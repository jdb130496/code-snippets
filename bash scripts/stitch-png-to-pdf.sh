#!/bin/bash

export PATH="/ucrt64/bin:$PATH"

INPUT_DIR="/d/dev/pdf-images/cut"
OUTPUT="/d/dev/pdf-images/panchdev-atharvashirsh.pdf"

magick $(ls "$INPUT_DIR"/page_*.png | sort -V) "$OUTPUT"

echo "Done! → $OUTPUT"
