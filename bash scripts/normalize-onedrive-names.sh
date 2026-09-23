#!/bin/bash
# Normalize filenames in OneDrive folder:
# 1. Collapse multiple spaces to single space
# 2. Remove trailing space before file extension
# Uses -depth to process deepest paths first (safe for folder renames)

TARGET="${1:-$HOME/OneDrive}"
DRY_RUN="${2:-dry}"  # Pass 'apply' as second argument to actually rename

echo "=== OneDrive Filename Normalizer ==="
echo "Target: $TARGET"
echo "Mode: $DRY_RUN"
echo ""

RENAMED=0
FAILED=0
SKIPPED=0

# -depth ensures children are processed before parents
# so folder renames don't break queued child paths
while IFS= read -r f; do
    dir=$(dirname "$f")
    base=$(basename "$f")

    # Step 1: collapse multiple spaces to single
    newname=$(echo "$base" | tr -s ' ')

    # Step 2: remove trailing space before extension (e.g. "file .docx" -> "file.docx")
    newname=$(echo "$newname" | sed 's/ \(\.[a-zA-Z0-9]*\)$/\1/')

    if [ "$base" = "$newname" ]; then
        ((SKIPPED++))
        continue
    fi

    if [ "$DRY_RUN" = "apply" ]; then
        if mv "$f" "$dir/$newname" 2>/dev/null; then
            echo "RENAMED: '$base'"
            echo "     ->  '$newname'"
            echo ""
            ((RENAMED++))
        else
            echo "FAILED:  '$base'"
            ((FAILED++))
        fi
    else
        echo "WOULD RENAME: '$base'"
        echo "          ->  '$newname'"
        echo ""
        ((RENAMED++))
    fi

done < <(find "$TARGET" -depth \( -name "*  *" -o -name "* .*" \))

echo "=== Summary ==="
if [ "$DRY_RUN" = "apply" ]; then
    echo "Renamed:  $RENAMED"
    echo "Failed:   $FAILED"
    echo "Skipped:  $SKIPPED"
else
    echo "Would rename: $RENAMED"
    echo "Skipped:      $SKIPPED"
    echo ""
    echo "Run with 'apply' to execute: $0 '$TARGET' apply"
fi
