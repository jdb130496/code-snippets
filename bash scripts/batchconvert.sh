#!/bin/bash

# Set the working directory
INPUT_DIR="/d/dump/Religious Books PDF And Audio"

# Loop through matching .opus files only
for file in "$INPUT_DIR"/SHRIMAD\ BHAGWAT\ MAHA\ PURAN\ COMPLETE\ IN\ SANSKRIT\ PART*".opus"; do
    # Extract filename without extension
    filename=$(basename "$file" .opus)

    # Convert to MP3 320kbps using ffmpeg, saving in the same directory
    ffmpeg -i "$file" -b:a 320k "$INPUT_DIR/${filename}.mp3"
done

echo "✅ Conversion complete. MP3 files saved in: $INPUT_DIR"

