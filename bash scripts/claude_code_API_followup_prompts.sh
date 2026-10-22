#!/bin/bash
# followup_prompt.sh — Continues CURRENT session with full context
# Run first_prompt.sh first to start a session.
# To start a new topic, run first_prompt.sh instead of this.

# ── Edit these lines only ──────────────────
QUESTION="Your follow up question here"
ATTACH=""    # optional: any file path. Leave "" for no attachment.
             # Supports: .png .jpg .gif .webp .pdf .txt .csv .md .xlsx .xls .docx
API_KEY="YOUR_API_KEY"
CLAUDE_DIR="/d/ClaudeCode"
# ──────────────────────────────────────────

BALANCE_FILE="$CLAUDE_DIR/session_balance.txt"
SESSION_FILE="$CLAUDE_DIR/current_session.txt"

if [ ! -f "$SESSION_FILE" ]; then
    echo "ERROR: No active session found."
    echo "Run first_prompt.sh to start one."
    exit 1
fi

SESSION_ID=$(cat "$SESSION_FILE")
SESSION_DIR="$CLAUDE_DIR/$SESSION_ID"
HISTORY_JSON="$SESSION_DIR/history.json"
CHAT_LOG="$SESSION_DIR/chat_log.md"
echo "── CONTINUING SESSION: $SESSION_ID ──────────"

# Load history + attach optional file + send full context — all in Python
RESPONSE=$(python3 - <<PYEOF
import json, urllib.request, base64, os, sys

history_json = "$HISTORY_JSON"
question     = """$QUESTION"""
api_key      = "$API_KEY"
attach       = """$ATTACH""".strip()

# Load full conversation history
with open(history_json, 'r', encoding='utf-8') as f:
    history = json.load(f)

# Build new user content block
user_content = []

# Handle optional file attachment
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

# Question text always last — cache_control caches full history prefix above
user_content.append({
    "type": "text",
    "text": question,
    "cache_control": {"type": "ephemeral", "ttl": "1h"}
})

# Append new turn to history and send complete context
history.append({"role": "user", "content": user_content})

payload = {
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "low"},
    "messages": history    # ← full conversation history sent automatically
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
attach        = """$ATTACH""".strip()

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

# Update history with lean text — replace last entry (had content blocks)
# with plain text summary so history.json never stores repeated base64 blobs
with open(history_json, 'r', encoding='utf-8') as f:
    history = json.load(f)

attach_note = f"[Attached: {os.path.basename(attach)}]\n" if attach else ""
history[-1] = {"role": "user",      "content": attach_note + question}
history.append({"role": "assistant", "content": response_text})

with open(history_json, 'w', encoding='utf-8') as f:
    json.dump(history, f, ensure_ascii=False, indent=2)

# Human-readable log
attach_line = f"\n> Attached: {os.path.basename(attach)}" if attach else ""
timestamp   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log_entry   = f"""
---
## [{timestamp}] USER{attach_line}
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
    print(f"Cache read tokens:   0  (cache miss — history reprocessed)")
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
