#!/usr/bin/env python3
"""
Convert a Claude.ai chat export JSON into a Markdown transcript,
then convert that Markdown into a Word-ready .docx via pandoc.

Usage:
    python json_to_md.py chat.json conversation.md
"""

import json
import subprocess
import sys
from pathlib import Path

# --- Step 1: Validate arguments ---
if len(sys.argv) < 3:
    print("Usage: python json_to_md.py <input.json> <output.md>")
    sys.exit(1)

in_path = sys.argv[1]
out_path = sys.argv[2]

# --- Step 2: Load the JSON export ---
with open(in_path, "r", encoding="utf-8") as f:
    data = json.load(f)

messages = data.get("chat_messages", [])
conv_name = data.get("name") or "Claude Conversation"

# --- Step 3: Build the Markdown content, message by message ---
lines = [f"# {conv_name}", ""]

for msg in messages:
    sender = msg.get("sender", "unknown")
    label = "User" if sender == "human" else "Claude"

    # Collect all text parts for this message
    parts = []

    for block in msg.get("content", []):
        if block.get("type") == "text" and block.get("text"):
            parts.append(block["text"])

    if not parts and msg.get("text"):
        parts.append(msg["text"])

    for att in msg.get("attachments", []):
        extracted = att.get("extracted_content")
        if extracted:
            fname = att.get("file_name") or "attachment"
            parts.append(f"**[Attachment: {fname}]**\n```\n{extracted}\n```")

    for file_entry in msg.get("files_v2", []) or []:
        fname = file_entry.get("file_name")
        if fname:
            parts.append(f"**[Uploaded file: {fname}]**")

    text = "\n\n".join(parts).strip()

    if not text:
        continue  # skip empty messages

    lines.append(f"## {label}")
    lines.append("")
    lines.append(text)
    lines.append("")
    lines.append("---")
    lines.append("")

# --- Step 4: Write the Markdown file ---
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print(f"Done. Wrote {len(messages)} messages to {out_path}")

# --- Step 5: Convert the Markdown to .docx using pandoc ---
docx_path = str(Path(out_path).with_suffix(".docx"))

pandoc_exe = "pandoc"

try:
    subprocess.run(
        [pandoc_exe, out_path, "-o", docx_path],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"Also wrote a Word-ready file to {docx_path}")
except FileNotFoundError:
    print(
        "Note: pandoc not found, skipping .docx conversion. "
        "Install it (e.g. 'brew install pandoc' / 'sudo apt install pandoc') "
        "to also get a Word-ready .docx file."
    )
except subprocess.CalledProcessError as e:
    print(f"Note: pandoc failed to convert to .docx:\n{e.stderr}")
