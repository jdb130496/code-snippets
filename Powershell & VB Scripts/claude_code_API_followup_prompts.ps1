# followup_prompt.ps1 — Continues CURRENT session with full context
# Run first_prompt.ps1 first to start a session.
# To start a new topic, run first_prompt.ps1 instead of this.

# ── Edit these lines only ──────────────────
$QUESTION   = "Your follow up question here"
$ATTACH     = ""     # optional file. Leave "" for none.
                     # Supports: .png .jpg .gif .webp .pdf .txt .csv .md .xlsx .xls .docx
$API_KEY    = "YOUR_API_KEY"
$CLAUDE_DIR = "D:\ClaudeCode"
# ──────────────────────────────────────────

$INPUT_PRICE  = 3.00  / 1000000
$OUTPUT_PRICE = 15.00 / 1000000
$BALANCE_FILE = "$CLAUDE_DIR\session_balance.txt"
$SESSION_FILE = "$CLAUDE_DIR\current_session.txt"

if (-not (Test-Path $SESSION_FILE)) {
    Write-Host "ERROR: No active session found."
    Write-Host "Run first_prompt.ps1 to start one."
    exit 1
}

$SESSION_ID   = Get-Content $SESSION_FILE
$SESSION_DIR  = "$CLAUDE_DIR\$SESSION_ID"
$HISTORY_JSON = "$SESSION_DIR\history.json"
$CHAT_LOG     = "$SESSION_DIR\chat_log.md"
Write-Host "── CONTINUING SESSION: $SESSION_ID ──────────"

$RUNNING_TOTAL = if (Test-Path $BALANCE_FILE) { [decimal](Get-Content $BALANCE_FILE) } else { 0 }

# Load history + attach optional file + send full context — all in Python
$PY_RESPONSE = python3 - @"
import json, urllib.request, base64, os, sys

history_json = r"$HISTORY_JSON"
question     = """$QUESTION"""
api_key      = "$API_KEY"
attach       = r"$ATTACH".strip()

# Load full conversation history — this is what gives Claude memory
with open(history_json, 'r', encoding='utf-8') as f:
    history = json.load(f)

user_content = []

if attach:
    ext  = os.path.splitext(attach)[1].lower().lstrip('.')
    name = os.path.basename(attach)

    if ext in ('png', 'jpg', 'jpeg', 'gif', 'webp'):
        mime = 'image/jpeg' if ext == 'jpg' else f'image/{ext}'
        with open(attach, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        user_content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": mime, "data": b64},
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        })

    elif ext == 'pdf':
        with open(attach, 'rb') as f:
            b64 = base64.b64encode(f.read()).decode()
        user_content.append({
            "type": "document",
            "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        })

    elif ext in ('txt', 'csv', 'md'):
        with open(attach, 'r', encoding='utf-8') as f:
            content = f.read()
        user_content.append({
            "type": "text",
            "text": f"[File: {name}]\n{content}",
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        })

    elif ext in ('xlsx', 'xls'):
        import pandas as pd
        df = pd.read_excel(attach)
        user_content.append({
            "type": "text",
            "text": f"[Excel: {name}]\n{df.to_csv(index=False)}",
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        })

    elif ext == 'docx':
        import docx
        doc = docx.Document(attach)
        text = '\n'.join(p.text for p in doc.paragraphs if p.text.strip())
        user_content.append({
            "type": "text",
            "text": f"[Word: {name}]\n{text}",
            "cache_control": {"type": "ephemeral", "ttl": "1h"}
        })

    else:
        print(f"WARNING: Unsupported file type .{ext} — sending question only", file=sys.stderr)

# Question always last — cache_control caches everything above including full history
user_content.append({
    "type": "text",
    "text": question,
    "cache_control": {"type": "ephemeral", "ttl": "1h"}
})

# Append new turn — history now contains all prior exchanges plus this new one
history.append({"role": "user", "content": user_content})

payload = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "low"},
    "messages": history    # full conversation history sent automatically
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

# Update history.json — store lean text, not base64 blobs
$ATTACH_NOTE = if ($ATTACH) { "[Attached: $(Split-Path $ATTACH -Leaf)]`n" } else { "" }
python3 - @"
import json

history_json  = r"$HISTORY_JSON"
question      = """$QUESTION"""
response_text = """$RESPONSE_TEXT"""
attach_note   = """$ATTACH_NOTE"""

with open(history_json, 'r', encoding='utf-8') as f:
    history = json.load(f)

# Replace last entry (had full content blocks with b64) with lean text version
history[-1] = {"role": "user",      "content": attach_note + question}
history.append({"role": "assistant", "content": response_text})

with open(history_json, 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)
"@

# Human-readable log
$ATTACH_LINE = if ($ATTACH) { "`n> Attached: $(Split-Path $ATTACH -Leaf)" } else { "" }
$TIMESTAMP   = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
$LOG_ENTRY   = "`n---`n## [$TIMESTAMP] USER$ATTACH_LINE`n$QUESTION`n`n## CLAUDE`n$RESPONSE_TEXT`n`n> in: $INPUT_TOKENS | out: $OUTPUT_TOKENS | cache_read: $CACHE_READ_TOKENS | cache_created: $CACHE_CREATE_TOKENS`n> This message: `$$("{0:F6}" -f $TOTAL_COST) (₹$("{0:F4}" -f ($TOTAL_COST * 95))) | Session total: `$$("{0:F6}" -f $RUNNING_TOTAL) (₹$("{0:F4}" -f ($RUNNING_TOTAL * 95)))`n"
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
    Write-Host "Cache read tokens:   0  (cache miss — history reprocessed)"
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
