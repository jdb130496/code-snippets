#!/bin/bash
# followup.sh — Subsequent messages without files

# ── Edit these lines only ──────────────────
QUESTION="Your follow up question here"
API_KEY="YOUR_API_KEY"
BALANCE_FILE="/d/ClaudeCode/session_balance.txt"
# ──────────────────────────────────────────

# Send request
RESPONSE=$(curl -s https://api.anthropic.com/v1/messages \
  -H "x-api-key: $API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-sonnet-4-6",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "low"},
    "cache_control": {"type": "ephemeral"},
    "messages": [
      {
        "role": "user",
        "content": "'"$QUESTION"'"
      }
    ]
  }')

# Process response and display
python3 - <<EOF
import json

data         = json.loads('''$RESPONSE''')
balance_file = "$BALANCE_FILE"

# Read running total
try:
    with open(balance_file, 'r') as f:
        running_total = float(f.read().strip())
except:
    running_total = 0.0

# Response text
print("\n── RESPONSE ──────────────────────────────")
print(data['content'][0]['text'])

# Token usage
usage         = data['usage']
input_tokens  = usage.get('input_tokens', 0)
output_tokens = usage.get('output_tokens', 0)
cache_read    = usage.get('cache_read_input_tokens', 0)
cache_create  = usage.get('cache_creation_input_tokens', 0)

# Cost
input_cost    = input_tokens  * (3.00  / 1_000_000)
output_cost   = output_tokens * (15.00 / 1_000_000)
total_cost    = input_cost + output_cost
running_total += total_cost

# Save running total
with open(balance_file, 'w') as f:
    f.write(str(running_total))

print("\n── TOKEN USAGE ───────────────────────────")
print(f"Input tokens:        {input_tokens}")
print(f"Output tokens:       {output_tokens}")
print(f"Cache read tokens:   {cache_read}")
print(f"Cache created:       {cache_create}")
print("\n── COST THIS MESSAGE ─────────────────────")
print(f"Input cost:   \${input_cost:.6f}")
print(f"Output cost:  \${output_cost:.6f}")
print(f"Total:        \${total_cost:.6f}")
print(f"In INR:       ₹{total_cost * 95:.4f}")
print("\n── SESSION RUNNING TOTAL ─────────────────")
print(f"Session total: \${running_total:.6f}")
print(f"Session INR:   ₹{running_total * 95:.4f}")
print("──────────────────────────────────────────")
EOF
