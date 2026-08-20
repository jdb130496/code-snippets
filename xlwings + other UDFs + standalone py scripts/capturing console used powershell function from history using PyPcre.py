import os
import pcre

# ── 1. Find the PowerShell history file ──────────────────────────────────────
history_file = None
search_root = r"C:\Users\juhi"

for dirpath, dirnames, filenames in os.walk(search_root):
    dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", "__pycache__", "venv", ".venv")]
    if "ConsoleHost_history.txt" in filenames:
        history_file = os.path.join(dirpath, "ConsoleHost_history.txt")
        break

if not history_file:
    raise FileNotFoundError("ConsoleHost_history.txt not found under " + search_root)

print(f"[+] Found history at: {history_file}")

with open(history_file, "r", encoding="utf-8", errors="replace") as fh:
    content = fh.read()

print(f"[+] History file: {len(content)} chars, ~{content.count(chr(10))} lines")

# ── 2. Regex with PCRE recursive balanced-brace matching ─────────────────────
pattern_str = r"""
function \s+ watch[-_]BuildPriority
\s*
(?:\([^)]*\))?
\s*
(?P<body>
    \{
    (?:
        [^{}]+
        |
        (?P>body)
    )*
    \}
)
"""

regex = pcre.compile(pattern_str, pcre.IGNORECASE | pcre.DOTALL | pcre.VERBOSE)

# ── 3. Search and report ──────────────────────────────────────────────────────
matches = list(regex.finditer(content))

if not matches:
    print("[-] Function watch-BuildPriority / watch_BuildPriority not found in history.")
else:
    print(f"[+] Found {len(matches)} occurrence(s). Showing the most recent one:\n")
    m = matches[-1]
    line_no = content[:m.start()].count("\n") + 1
    print(f"  Line ~{line_no} | chars {m.start()}–{m.end()}")
    print("=" * 60)
    print(m.group(0))
    print("=" * 60)

    if len(matches) > 1:
        print(f"\n[i] {len(matches)-1} earlier definition(s) also found. Access via matches[0..{len(matches)-2}].")

    # ── 4. Save most recent version to .ps1 ──────────────────────────────────
    clean = m.group(0).replace('`\n', '\n').replace('`\r\n', '\r\n')

    out_path = r"C:\Users\juhi\Watch-BuildPriority.ps1"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(clean)

    print(f"\n[+] Saved clean .ps1 to: {out_path}")