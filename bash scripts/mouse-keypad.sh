#!/bin/sh

swaymsg -t subscribe -m '[ "input" ]' | while read line
do
    change="$(echo "$line" | jq -r 'select(.input.type=="pointer").change')"
    case $change in
        added)
            swaymsg input type:touchpad events toggle disabled \
                && echo "Mouse/pointer was added, disabled touchpad"
            ;;
        removed)
            swaymsg input type:touchpad events toggle enabled \
                && echo "Mouse/pointer was removed, enabled touchpad"
            ;;
    esac
done
