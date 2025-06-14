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

echo "Step 1: Scanning for OPUS files..."
echo "Available OPUS files with 'SHRIMAD BHAGWAT' in name:"
echo "----------------------------------------"

# List all matching files first to see what we have
ls -1 *SHRIMAD*BHAGWAT*PURAN*SANSKRIT*.opus 2>/dev/null | head -10
echo "..."
echo

# Create temporary file list
> "$TEMP_LIST"

echo "Step 2: Processing files with flexible matching..."

# Use wildcards and find to locate files more flexibly
declare -A found_files

# Try to find files for parts 1-30 using pattern matching
for i in {1..30}; do
    # Try different patterns for each part number
    patterns=(
        "*SHRIMAD*BHAGWAT*PURAN*SANSKRIT*PART*$i[^0-9]*श्रीमद*.opus"
        "*SHRIMAD*BHAGWAT*PURAN*SANSKRIT*PART*0$i[^0-9]*श्रीमद*.opus"
    )
    
    found=false
    for pattern in "${patterns[@]}"; do
        # Use find with pattern matching
        while IFS= read -r -d '' file; do
            if [[ -f "$file" ]]; then
                echo "Found PART $i: $(basename "$file")"
                temp_name="bhagwat_part_$(printf "%02d" $i).opus"
                temp_path="$TEMP_DIR/$temp_name"
                
                cp "$file" "$temp_path" || {
                    echo "Error: Failed to copy PART $i"
                    continue
                }
                
                # Convert MSYS2 path to Windows path for FFmpeg
                win_temp_path=$(cygpath -w "$temp_path" 2>/dev/null || echo "$temp_path")
                # Escape backslashes and wrap in quotes for the file list
                echo "file '${win_temp_path//\\/\/}'" >> "$TEMP_LIST"
                found_files[$i]="$file"
                found=true
                break
            fi
        done < <(find . -maxdepth 1 -name "$pattern" -print0 2>/dev/null)
        
        if $found; then
            break
        fi
    done
    
    if ! $found; then
        echo "Warning: PART $i not found with any pattern"
    fi
done

# Special handling for Part 30 LAST
echo "Looking for Part 30 LAST..."
last_patterns=(
    "*SHRIMAD*BHAGWAT*PURAN*SANSKRIT*PART*30*LAST*श्रीमद*.opus"
    "*SHRIMAD*BHAGWAT*PURAN*SANSKRIT*30*LAST*श्रीमद*.opus"
)

found_last=false
for pattern in "${last_patterns[@]}"; do
    while IFS= read -r -d '' file; do
        if [[ -f "$file" ]]; then
            echo "Found PART 30 LAST: $(basename "$file")"
            temp_name="bhagwat_part_30_last.opus"
            temp_path="$TEMP_DIR/$temp_name"
            
            cp "$file" "$temp_path" || {
                echo "Error: Failed to copy PART 30 LAST"
                continue
            }
            
            # Remove the regular part 30 entry if it exists
            if [[ -n "${found_files[30]}" ]]; then
                # Remove the regular part 30 from the list
                temp_list_content=$(grep -v "bhagwat_part_30.opus" "$TEMP_LIST")
                echo "$temp_list_content" > "$TEMP_LIST"
            fi
            
            # Convert MSYS2 path to Windows path for FFmpeg
            win_temp_path=$(cygpath -w "$temp_path" 2>/dev/null || echo "$temp_path")
            echo "file '${win_temp_path//\\/\/}'" >> "$TEMP_LIST"
            found_last=true
            break
        fi
    done < <(find . -maxdepth 1 -name "$pattern" -print0 2>/dev/null)
    
    if $found_last; then
        break
    fi
done

if ! $found_last; then
    echo "Warning: PART 30 LAST not found with any pattern"
fi

# Check if any files were found
if [[ ! -s "$TEMP_LIST" ]]; then
    echo "Error: No OPUS files found!"
    echo "Please check if files exist in: $SOURCE_DIR"
    echo
    echo "Let's see what OPUS files are actually present:"
    echo "All .opus files in directory:"
    ls -la *.opus 2>/dev/null || echo "No .opus files found"
    echo
    echo "Files containing 'SHRIMAD':"
    ls -la *SHRIMAD* 2>/dev/null || echo "No files with 'SHRIMAD' found"
    
    rm -rf "$TEMP_DIR"
    rm -f "$TEMP_LIST"
    exit 1
fi

echo
echo "Step 3: Files prepared for concatenation:"
cat "$TEMP_LIST"
echo

# Count total files
total_files=$(wc -l < "$TEMP_LIST")
echo "Total files found: $total_files"
echo

# Ask for confirmation
read -p "Proceed with concatenation? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    rm -rf "$TEMP_DIR"
    rm -f "$TEMP_LIST"
    exit 0
fi

echo "Step 4: Starting concatenation..."
echo "This may take several minutes..."

# Convert file list path to Windows format for FFmpeg
win_temp_list=$(cygpath -w "$TEMP_LIST" 2>/dev/null || echo "$TEMP_LIST")
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
    rm -rf "$TEMP_DIR"
    rm -f "$TEMP_LIST"
    exit 1
fi

# Cleanup temporary files
echo
echo "Step 5: Cleaning up temporary files..."
rm -rf "$TEMP_DIR"
rm -f "$TEMP_LIST"

echo
echo "=== Process Complete ==="
echo "You can now use the combined file: $OUTPUT_FILE"
echo
echo "Original files with Sanskrit names are preserved."
echo "Temporary ASCII copies have been removed."
