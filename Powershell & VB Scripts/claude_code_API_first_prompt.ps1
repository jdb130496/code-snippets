# first_prompt.ps1 — Starts a NEW session
# Usage: set variables below and run. Starts fresh context, new log file.

# ── Edit these lines only ──────────────────
$IMAGE      = "C:\Users\YourName\Pictures\screenshot.png"  # leave "" if no image
$PDF        = "C:\Users\YourName\Documents\report.pdf"     # leave "" if no PDF
$QUESTION   = "Analyse both files"
$API_KEY    = "YOUR_API_KEY"
$CLAUDE_DIR = "D:\ClaudeCode"
# ──────────────────────────────────────────

$INPUT_PRICE  = 3.00  / 1000000
$OUTPUT_PRICE = 15.00 / 1000000
$BALANCE_FILE = "$CLAUDE_DIR\session_balance.txt"
$SESSION_FILE = "$CLAUDE_DIR\current_session.txt"

# Create new session folder
$SESSION_ID  = Get-Date -Format "yyyy-MM-dd_HH-mm"
Set-Content $SESSION_FILE $SESSION_ID
$SESSION_DIR  = "$CLAUDE_DIR\$SESSION_ID"
New-Item -ItemType Directory -Force -Path $SESSION_DIR | Out-Null
$HISTORY_JSON = "$SESSION_DIR\history.json"
$CHAT_LOG     = "$SESSION_DIR\chat_log.md"

Set-Content -Path $HISTORY_JSON -Value "[]" -Encoding UTF8
Set-Content -Path $CHAT_LOG -Value "# Claude Session — $SESSION_ID`n> Started: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n" -Encoding UTF8
Write-Host "── NEW SESSION STARTED: $SESSION_ID ──────────"

$RUNNING_TOTAL = if (Test-Path $BALANCE_FILE) { [decimal](Get-Content $BALANCE_FILE) } else { 0 }

# Build payload, send, return response — all in Python for reliable JSON handling
$PY_RESPONSE = python3 - @"
import json, urllib.request, base64, os, sys

question  = """$QUESTION"""
api_key   = "$API_KEY"
image     = r"$IMAGE".strip()
pdf       = r"$PDF".strip()

user_content = []

if image:
    ext  = os.path.splitext(image)[1].lower().lstrip('.')
    mime = 'image/jpeg' if ext == 'jpg' else f'image/{ext}'
    with open(image, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    user_content.append({
        "type": "image",
        "source": {"type": "base64", "media_type": mime, "data": b64},
        "cache_control": {"type": "ephemeral", "ttl": "1h"}
    })

if pdf:
    with open(pdf, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    user_content.append({
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
        "cache_control": {"type": "ephemeral", "ttl": "1h"}
    })

user_content.append({
    "type": "text",
    "text": question,
    "cache_control": {"type": "ephemeral", "ttl": "1h"}
})

payload = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "low"},
    "messages": [{"role": "user", "content": user_content}]
}

req = urllib.request.Request(
    "https://api.anthropic.com/v1/messages",
    data=json.dumps(payload).encode(),
    headers={
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    },
    method="POST"
)
with urllib.request.urlopen(req) as resp:
    print(resp.read().decode())
"@

$RESPONSE_OBJ        = $PY_RESPONSE | ConvertFrom-Json
$RESPONSE_TEXT       = ($RESPONSE_OBJ.content | Where-Object { $_.type -eq "text" } | Select-Object -First 1).text
$INPUT_TOKENS        = $RESPONSE_OBJ.usage.input_tokens
$OUTPUT_TOKENS       = $RESPONSE_OBJ.usage.output_tokens
$CACHE_READ_TOKENS   = $RESPONSE_OBJ.usage.cache_read_input_tokens
$CACHE_CREATE_TOKENS = $RESPONSE_OBJ.usage.cache_creation_input_tokens

$INPUT_COST    = $INPUT_TOKENS  * $INPUT_PRICE
$OUTPUT_COST   = $OUTPUT_TOKENS * $OUTPUT_PRICE
$TOTAL_COST    = $INPUT_COST + $OUTPUT_COST
$RUNNING_TOTAL += $TOTAL_COST
Set-Content $BALANCE_FILE $RUNNING_TOTAL

# Save lean history — no base64 blobs
$FILES_NOTE = ""
if ($IMAGE) { $FILES_NOTE += "[Attached image: $(Split-Path $IMAGE -Leaf)]`n" }
if ($PDF)   { $FILES_NOTE += "[Attached PDF: $(Split-Path $PDF -Leaf)]`n" }

$HISTORY = @(
    @{ role = "user";      content = "$FILES_NOTE$QUESTION" },
    @{ role = "assistant"; content = $RESPONSE_TEXT }
)
$HISTORY | ConvertTo-Json -Depth 5 | Set-Content -Path $HISTORY_JSON -Encoding UTF8

# Human-readable log
$FILES_LINE = ""
if ($IMAGE) { $FILES_LINE += "`n> Image: $(Split-Path $IMAGE -Leaf)" }
if ($PDF)   { $FILES_LINE += "`n> PDF:   $(Split-Path $PDF -Leaf)" }
$TIMESTAMP = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$LOG_ENTRY = "`n---`n## [$TIMESTAMP] USER$FILES_LINE`n$QUESTION`n`n## CLAUDE`n$RESPONSE_TEXT`n`n> in: $INPUT_TOKENS | out: $OUTPUT_TOKENS | cache_read: $CACHE_READ_TOKENS | cache_created: $CACHE_CREATE_TOKENS`n> This message: `$$("{0:F6}" -f $TOTAL_COST) (₹$("{0:F4}" -f ($TOTAL_COST * 95))) | Session total: `$$("{0:F6}" -f $RUNNING_TOTAL) (₹$("{0:F4}" -f ($RUNNING_TOTAL * 95)))`n"
Add-Content -Path $CHAT_LOG -Value $LOG_ENTRY -Encoding UTF8

Write-Host ""
Write-Host "── RESPONSE ──────────────────────────────"
Write-Host $RESPONSE_TEXT
Write-Host ""
Write-Host "── TOKEN USAGE ───────────────────────────"
Write-Host "Input tokens:        $INPUT_TOKENS"
Write-Host "Output tokens:       $OUTPUT_TOKENS"
if ($CACHE_READ_TOKENS -gt 0) {
    Write-Host "Cache read tokens:   $CACHE_READ_TOKENS  -> CACHE HIT"
} else {
    Write-Host "Cache read tokens:   0  (cache miss — content processed fresh)"
}
Write-Host "Cache created:       $CACHE_CREATE_TOKENS"
Write-Host ""
Write-Host "── COST THIS MESSAGE ─────────────────────"
Write-Host ("Input cost:   `${0:F6}" -f $INPUT_COST)
Write-Host ("Output cost:  `${0:F6}" -f $OUTPUT_COST)
Write-Host ("Total:        `${0:F6}" -f $TOTAL_COST)
Write-Host ("In INR:       ₹{0:F4}" -f ($TOTAL_COST * 95))
Write-Host ""
Write-Host "── SESSION RUNNING TOTAL ─────────────────"
Write-Host ("Session total: `${0:F6}" -f $RUNNING_TOTAL)
Write-Host ("Session INR:   ₹{0:F4}" -f ($RUNNING_TOTAL * 95))
Write-Host "Session log:   $CHAT_LOG"
Write-Host "──────────────────────────────────────────"
