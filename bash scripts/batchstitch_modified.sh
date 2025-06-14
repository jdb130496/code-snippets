#!/bin/bash

# Script to rename and stitch multiple OPUS files into one
# For MSYS2 environment - handles Unicode filenames with Windows path compatibility

# Set the directory path (Windows path converted to MSYS2 format)
SOURCE_DIR="/d/dump/Religious Books PDF And Audio"
OUTPUT_FILE="/d/dump/Religious Books PDF And Audio/SHRIMAD_BHAGWAT_MAHA_PURAN_COMPLETE_SANSKRIT_FULL.opus"
TEMP_LIST="/d/dump/Religious Books PDF And Audio/opus_files_list.txt"
TEMP_DIR="/d/dump/Religious Books PDF And Audio/bhagwat_temp"

echo "=== OPUS File Stitching Script with Flexible Matching ==="
echo "Source Directory: $SOURCE_DIR"
echo "Output File: $OUTPUT_FILE"
echo

# Change to source directory
cd "$SOURCE_DIR" || {
    echo "Error: Cannot access directory '$SOURCE_DIR'"
    exit 1
}

# Create temporary directory for renamed files
mkdir -p "$TEMP_DIR"

echo "Step 1: Cleaning and Renaming files to ASCII-compatible names..."
echo "------------------------------------------------------------"

# Create a temporary directory to hold the ASCII-compatible renamed files
CLEAN_DIR="$TEMP_DIR/cleaned_files"
mkdir -p "$CLEAN_DIR"

# Find all original OPUS files and rename them into CLEAN_DIR
# This step ensures that all subsequent operations deal with ASCII-only filenames.
find . -maxdepth 1 -name "*SHRIMAD*BHAGWAT*PURAN*SANSKRIT*.opus" -print0 | while IFS= read -r -d '' original_file; do
    # Extract filename without path
    filename=$(basename "$original_file")

    # Clean the filename to remove Devanagari characters and normalize spaces
    # Replace Hindi characters (and common problematic chars) with nothing,
    # then replace multiple spaces with single spaces, and finally trim.
    # We use a pattern that matches the specific "श्रीमद भगवत महा पुराण संस्कृत में" part.
    cleaned_filename=$(echo "$filename" | \
                       sed 's/[[:space:]]*श्रीमद भगवत महा पुराण संस्कृत में\.opus//' | \
                       sed 's/[[:space:]]*श्रीमद भगवत महा पुराण संस्कृत मे\.opus//' | \
                       sed 's/[[:space:]]*श्रीमद भगवत महा पुराण संस्क्रित में\.opus//' | \
                       sed 's/[[:space:]]*श्रीमद भगवत महा पुराण संस्क्रित मे\.opus//' | \
                       sed 's/[[:space:]]*श्रीमद भगवत महा पुराण संस्कृतम्\.opus//' | \
                       sed 's/[[:space:]]*श्रीमद भगवत महा पुराण संस्कृतम\.opus//' | \
                       sed 's/[[:space:]]*[^\x00-\x7F]*\.opus/\.opus/' | \
                       sed 's/[[:space:]][[:space:]]*/ /g' | \
                       sed 's/PART[[:space:]]\([0-9]*\)[[:space:]]*LAST/PART_\1_LAST/' | \
                       sed 's/PART[[:space:]]\([0-9]*\)/PART_\1/' | \
                       sed 's/ /_/g' | \
                       tr -d '\n\r' | \
                       sed 's/__/_/g' | \
                       sed 's/_-_/-/g' | \
                       sed 's/_-_/_/g' | \
                       sed 's/\._/\./' | \
                       sed 's/_\.opus/\.opus/')

    # Add .opus extension back if somehow lost, and ensure no leading/trailing underscores
    cleaned_filename=$(echo "$cleaned_filename" | sed 's/\.opus$//' | sed 's/^_//;s/_$//')".opus"

    # Ensure the part number is separated by an underscore for easier parsing later
    cleaned_filename=$(echo "$cleaned_filename" | sed 's/PART\([0-9]\)/PART_\1/g' | sed 's/PART_\([0-9]\{1,2\}\)_LAST/PART_\1_LAST/g')

    # Construct the full path for the cleaned file
    cleaned_file_path="$CLEAN_DIR/$cleaned_filename"

    echo "Renaming: $(basename "$original_file") -> $(basename "$cleaned_file_path")"
    cp "$original_file" "$cleaned_file_path" || {
        echo "Error: Failed to copy '$original_file' to '$cleaned_file_path'"
        continue
    }
done

echo "------------------------------------------------------------"
echo "Finished cleaning and renaming files."
echo

# Now, change to the CLEAN_DIR to work with the cleaned filenames
cd "$CLEAN_DIR" || {
    echo "Error: Cannot access cleaned files directory '$CLEAN_DIR'"
    exit 1
}

# Create temporary file list for ffmpeg
> "$TEMP_LIST"

declare -A found_files # Associative array to store paths of found files

echo "Step 2: Scanning for cleaned OPUS files and preparing for concatenation..."
echo "----------------------------------------------------------------------"

# Try to find files for parts 1-30 using pattern matching on cleaned names
for i in {1..30}; do
    declare -a patterns # Declare as array for safety

    if [ "$i" -eq 30 ]; then
        # Specific pattern for PART 30 with "LAST" in cleaned names
        patterns=(
            "*SHRIMAD_BHAGWAT_MAHA_PURAN_COMPLETE_IN_SANSKRIT_PART_${i}_LAST.opus"
            "*SHRIMAD_BHAGWAT_MAHA_PURAN_COMPLETE_IN_SANSKRIT_PART_${i}_LAST_.opus" # In case of extra underscore
        )
    else
        # General pattern for other parts (1-29) in cleaned names
        patterns=(
            "*SHRIMAD_BHAGWAT_MAHA_PURAN_COMPLETE_IN_SANSKRIT_PART_${i}.opus"
            "*SHRIMAD_BHAGWAT_MAHA_PURAN_COMPLETE_IN_SANSKRIT_PART_${i}_.opus" # In case of extra underscore
        )
    fi

    found=false
    for pattern in "${patterns[@]}"; do
        # Use find with pattern matching. -print0 and read -d '' are crucial for filenames with spaces/special chars.
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                echo "Found PART $i: $(basename "$file")"
                # Ensure the temporary file name is always 0-padded for correct sorting
                temp_name="bhagwat_part_$(printf "%02d" $i).opus"
                temp_path="$TEMP_DIR/$temp_name" # Still copy to the original TEMP_DIR

                # Move the cleaned file to the final temporary directory for processing
                mv "$file" "$temp_path" || { # Use mv instead of cp since we copied to CLEAN_DIR first
                    echo "Error: Failed to move PART $i cleaned file to '$temp_path'"
                    continue
                }

                # Convert MSYS2 path to Windows path for FFmpeg
                win_temp_path=$(cygpath -w "$temp_path" 2>/dev/null || echo "$temp_path")
                # Escape backslashes and wrap in quotes for the file list
                echo "file '${win_temp_path//\\/\/}'" >> "$TEMP_LIST"
                found_files[$i]="$file"
                found=true
                break # Found the file for this part, move to next i
            fi
        done < <(find . -maxdepth 1 -name "$pattern" -print0 2>/dev/null)

        if $found; then
            break # Found the file for this part with one of the patterns, move to next i
        fi
    done

    if ! $found; then
        echo "Warning: PART $i not found with any pattern in '$CLEAN_DIR'"
    fi
done

if [ ${#found_files[@]} -eq 0 ]; then
    echo "❌ ERROR: No OPUS files found matching the patterns in the cleaned directory. Exiting."
    rm -rf "$TEMP_DIR"
    rm -f "$TEMP_LIST"
    exit 1
fi

echo
echo "Step 3: Temporary files copied and list created."
echo "Temporary directory for final concatenation: $TEMP_DIR"
echo "Temporary file list: $TEMP_LIST"
echo "Files to be concatenated (first 5 lines):"
head -n 5 "$TEMP_LIST"
echo "..."
echo

echo "Step 4: Concatenating files using FFmpeg..."

# Convert MSYS2 paths in TEMP_LIST to Windows paths for FFmpeg
win_temp_list="${TEMP_LIST}.win"
# This sed command converts /d/ to d:\ and all / to \
# It assumes TEMP_LIST contains MSYS2 paths relative to the root like /d/dump...
sed 's|^\/\([a-zA-Z]\)\/|\1:\\|; s|/|\\|g' "$TEMP_LIST" > "$win_temp_list"

# Convert the final output path to Windows format
win_output_file=$(cygpath -w "$OUTPUT_FILE" 2>/dev/null || echo "$OUTPUT_FILE")

# Use ffmpeg to concatenate
if ffmpeg -f concat -safe 0 -i "$win_temp_list" -c copy "$win_output_file"; then
    echo
    echo "✅ SUCCESS! Files concatenated successfully."
    echo "Output file: $OUTPUT_FILE"

    # Show file size
    if [[ -f "$OUTPUT_FILE" ]]; then
        file_size=$(du -h "$OUTPUT_FILE" | cut -f1)
        echo "File size: $file_size"

        # Get duration using ffprobe if available
        if command -v ffprobe >/dev/null 2>&1; then
            duration=$(ffprobe -v quiet -show_entries format=duration -of csv="p=0" "$win_output_file" 2>/dev/null)
            if [[ -n "$duration" ]]; then
                # Convert seconds to hours:minutes:seconds
                hours=$((${duration%.*} / 3600))
                minutes=$(((${duration%.*} % 3600) / 60))
                seconds=$((${duration%.*} % 60))
                echo "Duration: ${hours}h ${minutes}m ${seconds}s"
            fi
        fi
    fi
else
    echo
    echo "❌ ERROR: Concatenation failed!"
    echo "Check FFmpeg output above for specific error details."
    # Do not exit immediately, try to clean up
fi

# Clean up temporary files and directory
echo
echo "Step 5: Cleaning up temporary files..."
rm -rf "$TEMP_DIR" # This will remove both $TEMP_DIR and $CLEAN_DIR inside it
rm -f "$TEMP_LIST"
rm -f "$win_temp_list" # Remove the Windows-formatted list as well
echo "Temporary files cleaned up."

# Check if concatenation succeeded before exiting with success/failure code
if [[ -f "$OUTPUT_FILE" && $? -eq 0 ]]; then
    exit 0 # Success
else
    exit 1 # Failure
fi
