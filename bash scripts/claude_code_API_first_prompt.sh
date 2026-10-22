#!/bin/bash
# first_prompt.sh — Starts a NEW session
# Usage: set variables below and run. Starts fresh context, new log file.

# ── Edit these lines only ──────────────────
IMAGE="/c/Users/YourName/Pictures/screenshot.png"   # leave empty "" if no image
PDF="/c/Users/YourName/Documents/report.pdf"         # leave empty "" if no PDF
QUESTION="Analyse both files"
API_KEY="YOUR_API_KEY"
CLAUDE_DIR="/d/ClaudeCode"
# ──────────────────────────────────────────

BALANCE_FILE="$CLAUDE_DIR/session_balance.txt"
SESSION_FILE="$CLAUDE_DIR/current_session.txt"

# Create new session folder
SESSION_ID=$(date +"%Y-%m-%d_%H-%M")
echo "$SESSION_ID" > "$SESSION_FILE"
SESSION_DIR="$CLAUDE_DIR/$SESSION_ID"
mkdir -p "$SESSION_DIR"
HISTORY_JSON="$SESSION_DIR/history.json"
CHAT_LOG="$SESSION_DIR/chat_log.md"

echo "[]" > "$HISTORY_JSON"
cat > "$CHAT_LOG" <<HEADER
# Claude Session — $SESSION_ID
> Started: $(date "+%Y-%m-%d %H:%M:%S")

HEADER
echo "── NEW SESSION STARTED: $SESSION_ID ──────────"

# Build and send first message — Python handles file detection and API call
RESPONSE=$(python3 - <<PYEOF
import json, urllib.request, base64, os, sys

question  = """$QUESTION"""
api_key   = "$API_KEY"
image     = """$IMAGE""".strip()
pdf       = """$PDF""".strip()

user_content = []

# Attach image if provided
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

# Attach PDF if provided
if pdf:
    with open(pdf, 'rb') as f:
        b64 = base64.b64encode(f.read()).decode()
    user_content.append({
        "type": "document",
        "source": {"type": "base64", "media_type": "application/pdf", "data": b64},
        "cache_control": {"type": "ephemeral", "ttl": "1h"}
    })

# Question text — cache_control here tells server to cache everything above
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
PYEOF
)

# Process response
python3 - <<EOF
import json, os
from datetime import datetime

data          = json.loads('''$RESPONSE''')
balance_file  = "$BALANCE_FILE"
history_json  = "$HISTORY_JSON"
chat_log      = "$CHAT_LOG"
question      = """$QUESTION"""
image         = """$IMAGE""".strip()
pdf           = """$PDF""".strip()

try:
    with open(balance_file, 'r') as f:
        running_total = float(f.read().strip())
except:
    running_total = 0.0

# Extract response text — skip thinking blocks
response_text = ""
for block in data.get('content', []):
    if block.get('type') == 'text':
        response_text = block['text']
        break

if 'error' in data:
    print(f"API ERROR: {data['error']}")
    exit(1)

usage         = data['usage']
input_tokens  = usage.get('input_tokens', 0)
output_tokens = usage.get('output_tokens', 0)
cache_read    = usage.get('cache_read_input_tokens', 0)
cache_create  = usage.get('cache_creation_input_tokens', 0)

input_cost    = input_tokens  * (3.00  / 1_000_000)
output_cost   = output_tokens * (15.00 / 1_000_000)
total_cost    = input_cost + output_cost
running_total += total_cost

with open(balance_file, 'w') as f:
    f.write(str(running_total))

# Save history as lean text — no base64 blobs stored
# Files are re-sent fresh on each call if needed; storing b64 would balloon history.json
files_note = ""
if image: files_note += f"[Attached image: {os.path.basename(image)}]\n"
if pdf:   files_note += f"[Attached PDF: {os.path.basename(pdf)}]\n"

history = [
    {"role": "user",      "content": files_note + question},
    {"role": "assistant", "content": response_text}
]
with open(history_json, 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# Human-readable log
files_line = ""
if image: files_line += f"\n> Image: {os.path.basename(image)}"
if pdf:   files_line += f"\n> PDF:   {os.path.basename(pdf)}"
timestamp  = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_entry  = f"""
---
## [{timestamp}] USER{files_line}
{question}

## CLAUDE
{response_text}

> in: {input_tokens} | out: {output_tokens} | cache_read: {cache_read} | cache_created: {cache_create}
> This message: \${total_cost:.6f} (₹{total_cost * 95:.4f}) | Session total: \${running_total:.6f} (₹{running_total * 95:.4f})
"""
with open(chat_log, 'a', encoding='utf-8') as f:
    f.write(log_entry)

print("\n── RESPONSE ──────────────────────────────")
print(response_text)
print("\n── TOKEN USAGE ───────────────────────────")
print(f"Input tokens:        {input_tokens}")
print(f"Output tokens:       {output_tokens}")
if cache_read > 0:
    print(f"Cache read tokens:   {cache_read}  ✓ CACHE HIT")
else:
    print(f"Cache read tokens:   0  (cache miss — content processed fresh)")
print(f"Cache created:       {cache_create}")
print("\n── COST THIS MESSAGE ─────────────────────")
print(f"Input cost:   \${input_cost:.6f}")
print(f"Output cost:  \${output_cost:.6f}")
print(f"Total:        \${total_cost:.6f}")
print(f"In INR:       ₹{total_cost * 95:.4f}")
print("\n── SESSION RUNNING TOTAL ─────────────────")
print(f"Session total: \${running_total:.6f}")
print(f"Session INR:   ₹{running_total * 95:.4f}")
print(f"Session log:   {chat_log}")
print("──────────────────────────────────────────")
EOF
