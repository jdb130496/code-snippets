analyze() {
    f="$1"
    result=$(ffmpeg -i "$f" -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 \
        | grep -E '"input_i"|"input_tp"|"input_lra"|"input_thresh"' \
        | grep -oP '[-0-9.]+' | tr '\n' ' ')
    echo "$f | $result"
}
export -f analyze

ls /e/1/*.[Mm][Pp]3 | xargs -P 4 -I {} bash -c 'analyze "$@"' _ {} | tee /e/1/diagnostic.txt
