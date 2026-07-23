#!/usr/bin/env python3
"""
Convert a Claude.ai OR ChatGPT chat export JSON into a Markdown transcript,
then optionally convert that Markdown into a Word-ready .docx via pandoc.

Usage:
    python json-md-docx-convert.py chat.json conversation.md

Supports:
  - Claude.ai export format  (keys: name, chat_messages[].sender/content)
  - ChatGPT IndexedDB export (keys: title, messages[].text, alternating roles)
"""

import json
import subprocess
import sys
from pathlib import Path

# --- Step 1: Validate arguments ---
if len(sys.argv) < 3:
    print("Usage: python json-md-docx-convert.py <input.json> <output.md>")
    sys.exit(1)

in_path = sys.argv[1]
out_path = sys.argv[2]

# --- Step 2: Load the JSON export ---
with open(in_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# --- Step 3: Detect format and extract messages ---

def detect_format(data):
    if "chat_messages" in data:
        return "claude"
    if "messages" in data and isinstance(data["messages"], list):
        msgs = data["messages"]
        if msgs and "text" in msgs[0] and "sender" not in msgs[0] and "role" not in msgs[0]:
            return "chatgpt"
    return "unknown"

fmt = detect_format(data)
print(f"Detected format: {fmt}")

lines = []
message_count = 0

if fmt == "claude":
    conv_name = data.get("name") or "Claude Conversation"
    lines = [f"# {conv_name}", ""]
    messages = data.get("chat_messages", [])

    for msg in messages:
        sender = msg.get("sender", "unknown")
        label = "**User**" if sender == "human" else "**Claude**"

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
            continue

        lines.append(f"## {label}")
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")
        message_count += 1

elif fmt == "chatgpt":
    conv_name = data.get("title") or "ChatGPT Conversation"
    lines = [f"# {conv_name}", ""]
    messages = data.get("messages", [])

    # Message 0 is always an empty root node — skip it.
    # Remaining messages alternate: even index = User, odd index = ChatGPT.
    content_messages = [m for m in messages if m.get("text", "").strip()]

    for i, msg in enumerate(content_messages):
        role = msg.get("role") or msg.get("author", {}).get("role", "")
        label = "**User**" if role == "user" else "**ChatGPT**"
        text = msg["text"].strip()
        #label = "**User**" if i % 2 == 0 else "**ChatGPT**"
        #text = msg["text"].strip()

        lines.append(f"## {label}")
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")
        message_count += 1

else:
    print("ERROR: Unrecognised JSON format.")
    print("Expected either Claude ('chat_messages' key) or ChatGPT ('messages' with text-only entries).")
    sys.exit(1)

# --- Step 4: Write the Markdown file ---
md_content = "\n".join(lines).replace("\\", "\\\\")
with open(out_path, "w", encoding="utf-8") as f:
    f.write(md_content)

# --- Step 5: Convert the Markdown to .docx using pandoc ---
docx_path = str(Path(out_path).with_suffix(".docx"))

import shutil
pandoc_exe = shutil.which("pandoc") or r"D:\dev\pandoc.exe"

try:
    subprocess.run(
        [pandoc_exe, "--from", "markdown-tex_math_dollars", out_path, "-o", docx_path],
        #[pandoc_exe, out_path, "-o", docx_path],
        check=True,
        capture_output=True,
        text=True,
    )
    print(f"Also wrote a Word-ready file to {docx_path}")
except FileNotFoundError:
    print(
        "Note: pandoc not found, skipping .docx conversion. "
        "Install it from https://pandoc.org/installing.html to also get a .docx file."
    )
except subprocess.CalledProcessError as e:
    print(f"Note: pandoc failed:\n{e.stderr}")
