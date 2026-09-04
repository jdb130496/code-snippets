for f in /e/1/*.[Mm][Pp]3; do
    echo -n "$f | "
    ffmpeg -i "$f" -af loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json -f null - 2>&1 \
    | grep -E '"input_i"|"input_tp"|"input_lra"|"input_thresh"' \
    | grep -oP '[-0-9.]+' \
    | tr '\n' ' ' \
    | awk '{printf "LUFS: %s | TruePeak: %s | LRA: %s | Thresh: %s\n", $1, $2, $3, $4}'
done | tee /e/1/diagnostic.txt
