$files = Get-ChildItem "E:\1\" -Include "*.mp3","*.MP3" -Recurse

$files | ForEach-Object -Parallel {
    $file = $_.FullName
    $stats = & ffmpeg -i $file -af "loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json" -f null - 2>&1
    $il  = ($stats | Select-String '"input_i"'     | Select-Object -First 1) -replace '[^0-9.\-]',''
    $itp = ($stats | Select-String '"input_tp"'    | Select-Object -First 1) -replace '[^0-9.\-]',''
    $lra = ($stats | Select-String '"input_lra"'   | Select-Object -First 1) -replace '[^0-9.\-]',''
    $thr = ($stats | Select-String '"input_thresh"'| Select-Object -First 1) -replace '[^0-9.\-]',''
    "$file | LUFS: $il | TruePeak: $itp | LRA: $lra | Thresh: $thr"
} -ThrottleLimit 4 | Tee-Object -FilePath "E:\1\diagnostic.txt"
