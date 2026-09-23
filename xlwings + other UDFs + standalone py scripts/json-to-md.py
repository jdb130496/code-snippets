"""
Convert Claude chat JSON export to clean Markdown.
Usage: python json_to_md.py <input.json> <output.md>
"""

import json
import re
import sys
from datetime import datetime

def format_timestamp(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return ts_str

def extract_text(message):
    parts = []
    for item in message.get("content", []):
        if item.get("type") == "text":
            text = item.get("text", "").strip()
            if text:
                parts.append(text)
    if not parts:
        text = message.get("text", "").strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)

def get_attachments(message):
    names = []
    for att in message.get("attachments", []):
        fname = att.get("file_name") or att.get("file_type", "unknown")
        fsize = att.get("file_size", 0)
        if fname:
            names.append(f"{fname} ({fsize:,} bytes)" if fsize else fname)
    return names

def fix_code_blocks(text):
    """Ensure all code blocks are properly fenced and separated."""
    # Normalize code fences — ensure blank line before and after
    text = re.sub(r'\n(```)', r'\n\n\1', text)
    text = re.sub(r'(```)\n', r'\1\n\n', text)
    # Remove excessive blank lines (more than 2)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def convert(input_path, output_path):
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    title    = data.get("name", "Claude Conversation")
    model    = data.get("model", "unknown")
    created  = format_timestamp(data.get("created_at", ""))
    updated  = format_timestamp(data.get("updated_at", ""))
    messages = data.get("chat_messages", [])

    out = []

    # Document header
    out.append(f"# {title}\n")
    out.append(f"| Field | Value |")
    out.append(f"|---|---|")
    out.append(f"| Model | {model} |")
    out.append(f"| Created | {created} |")
    out.append(f"| Updated | {updated} |")
    out.append(f"| Total messages | {len(messages)} |\n")
    out.append("\n---\n")

    msg_num = 0
    for msg in messages:
        sender    = msg.get("sender", "unknown")
        timestamp = format_timestamp(msg.get("created_at", ""))
        text      = extract_text(msg)
        atts      = get_attachments(msg)

        if not text and not atts:
            continue

        msg_num += 1

        # Clear heading per message
        if sender == "human":
            out.append(f"\n## USER — Message {msg_num}")
            out.append(f"*{timestamp}*\n")
        else:
            out.append(f"\n## CLAUDE — Message {msg_num}")
            out.append(f"*{timestamp}*\n")

        # Attachments
        if atts:
            out.append(f"> **Attached:** {', '.join(atts)}\n")

        # Message body — fix code blocks
        if text:
            out.append(fix_code_blocks(text))

        out.append("\n\n---\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(out))

    print(f"Done — {msg_num} messages written to: {output_path}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python json_to_md.py input.json output.md")
        sys.exit(1)
    convert(sys.argv[1], sys.argv[2])
