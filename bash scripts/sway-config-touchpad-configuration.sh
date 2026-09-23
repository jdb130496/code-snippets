CONFIG="$HOME/.config/sway/config"

NEW_ID=$(swaymsg -t get_inputs --pretty | grep -A2 'Type: Touchpad' | grep 'Identifier:' | head -1 | sed 's/.*Identifier: //')

CURRENT_LINE=$(grep -n '^[[:space:]]*input ".*Touchpad"' "$CONFIG" | head -1)
LINE_NUM=$(echo "$CURRENT_LINE" | cut -d: -f1)
CURRENT_ID=$(echo "$CURRENT_LINE" | grep -oP '(?<=input ")[^"]+')

if [[ "$CURRENT_ID" == "$NEW_ID" ]]; then
    echo "Already correct. Nothing to do."
    exit 0
fi

INDENT=$(sed -n "${LINE_NUM}p" "$CONFIG" | grep -oP '^[[:space:]]*')

TMPFILE=$(mktemp)
awk -v line="$LINE_NUM" \
    -v indent="$INDENT" \
    -v new_id="$NEW_ID" '
NR == line {
    print indent "input \"" new_id "\" {"
    next
}
{ print }
' "$CONFIG" > "$TMPFILE"

cp "$CONFIG" "${CONFIG}.bak"
mv "$TMPFILE" "$CONFIG"

echo "Replaced: $CURRENT_ID"
echo "With:     $NEW_ID"
echo "Backup:   ${CONFIG}.bak"

swaymsg reload
echo "Done."
