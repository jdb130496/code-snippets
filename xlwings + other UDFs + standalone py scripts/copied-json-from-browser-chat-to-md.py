#!/usr/bin/env python3
"""
Convert a Claude.ai chat export JSON (chat_messages format) into a
readable Markdown transcript, labeling each turn as User or Claude.

Markdown avoids all the escaping fragility of RTF (curly braces,
backslashes, etc. common in code/log content need no escaping here).

Usage:
    python json_to_md.py chat.json conversation.md
"""

import json
import sys


def extract_message_text(msg: dict) -> str:
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

    for f in msg.get("files_v2", []) or []:
        fname = f.get("file_name")
        if fname:
            parts.append(f"**[Uploaded file: {fname}]**")

    return "\n\n".join(parts).strip()


def main():
    if len(sys.argv) < 3:
        print("Usage: python json_to_md.py <input.json> <output.md>")
        sys.exit(1)

    in_path, out_path = sys.argv[1], sys.argv[2]

    with open(in_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = data.get("chat_messages", [])
    conv_name = data.get("name") or "Claude Conversation"

    lines = [f"# {conv_name}", ""]

    for msg in messages:
        sender = msg.get("sender", "unknown")
        label = "User" if sender == "human" else "Claude"

        text = extract_message_text(msg)
        if not text:
            continue

        lines.append(f"## {label}")
        lines.append("")
        lines.append(text)
        lines.append("")
        lines.append("---")
        lines.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Done. Wrote {len(messages)} messages to {out_path}")


if __name__ == "__main__":
    main()
