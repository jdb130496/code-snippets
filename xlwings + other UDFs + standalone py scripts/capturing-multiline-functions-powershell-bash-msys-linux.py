import os
import re
import sys
import platform
import argparse

try:
    import pcre
    HAS_PCRE = True
except ImportError:
    HAS_PCRE = False

try:
    from rich.console import Console
    from rich.table import Table
    from rich.syntax import Syntax
    from rich.panel import Panel
    from rich.prompt import Prompt
    HAS_RICH = True
    console = Console()
except ImportError:
    HAS_RICH = False
    console = None


# ══════════════════════════════════════════════════════════════════════════════
# 1. ENVIRONMENT DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def detect_environment():
    """
    Returns a dict:
      {
        os        : 'windows' | 'linux' | 'macos'
        shell     : 'bash' | 'zsh' | 'fish' | 'powershell'
        runtime   : 'msys2' | 'wsl' | 'native'
        user      : username string
        home      : home directory path
      }
    """
    env = {}

    # ── OS ────────────────────────────────────────────────────────────────────
    system = platform.system().lower()
    if system == "windows":
        env["os"] = "windows"
    elif system == "linux":
        # WSL exposes this in /proc/version
        try:
            with open("/proc/version") as f:
                env["os"] = "wsl" if "microsoft" in f.read().lower() else "linux"
        except:
            env["os"] = "linux"
    elif system == "darwin":
        env["os"] = "macos"
    else:
        env["os"] = "unknown"

    # ── Runtime (MSYS2 / native) ───────────────────────────────────────────────
    msystem = os.environ.get("MSYSTEM", "")          # UCRT64, MINGW64, MSYS etc
    if msystem:
        env["runtime"] = "msys2"
        env["msystem"] = msystem
    elif env["os"] == "wsl":
        env["runtime"] = "wsl"
    else:
        env["runtime"] = "native"

    # ── Shell ─────────────────────────────────────────────────────────────────
    shell_env = os.environ.get("SHELL", "")          # /bin/bash, /usr/bin/zsh etc
    ps_version = os.environ.get("PSVersionTable", os.environ.get("POWERSHELL_DISTRIBUTION_CHANNEL", ""))

    if ps_version or (env["os"] == "windows" and not msystem):
        env["shell"] = "powershell"
    elif "zsh" in shell_env:
        env["shell"] = "zsh"
    elif "fish" in shell_env:
        env["shell"] = "fish"
    else:
        env["shell"] = "bash"                        # safe default for MSYS2/Linux

    # ── User & Home ───────────────────────────────────────────────────────────
    env["user"] = (
        os.environ.get("USERNAME") or
        os.environ.get("USER") or
        os.getlogin()
    )

    # Use $HOME env var first — critical for MSYS2 where expanduser returns Windows path
    env["home"] = (
        os.environ.get("HOME") or          # /home/juhi  ← MSYS2 sets this correctly
        os.path.expanduser("~")            # C:/Users/juhi ← fallback for native Windows
    )
    
    return env


# ══════════════════════════════════════════════════════════════════════════════
# 2. HISTORY FILE RESOLUTION
# ══════════════════════════════════════════════════════════════════════════════

def resolve_history_file(env, shell_override=None):
    """
    Find the right history file based on detected environment.
    shell_override lets user force --shell ps/bash/zsh/fish.
    """
    shell = shell_override or env["shell"]
    home  = env["home"]
    user  = env["user"]

    candidates = []

    if shell == "powershell":
        # Windows native path
        candidates.append(
            os.path.join(
                os.environ.get("APPDATA", rf"C:\Users\{user}\AppData\Roaming"),
                r"Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt"
            )
        )
        # Sometimes under MSYS2 with pwsh
        candidates.append(os.path.expanduser(
            "~/.local/share/powershell/PSReadLine/ConsoleHost_history.txt"
        ))

    elif shell == "zsh":
        candidates += [
            os.path.join(home, ".zsh_history"),
            os.path.expanduser("~/.zsh_history"),
        ]

    elif shell == "fish":
        candidates += [
            os.path.join(home, ".local/share/fish/fish_history"),
            os.path.expanduser("~/.local/share/fish/fish_history"),
        ]

    else:  # bash — covers MSYS2, WSL, native Linux, macOS
        histfile = os.environ.get("HISTFILE")        # /home/juhi/.bash_history — MSYS2 sets this correctly
        if histfile:
            candidates.append(histfile)
        candidates += [
            "/home/" + user + "/.bash_history",          # MSYS2 unix-style
            os.path.join(home, ".bash_history"),          # whatever ~ resolves to
            os.path.expanduser("~/.bash_history"),
        ]
        
    for path in candidates:
        if path and os.path.exists(path):
            return path, shell

    raise FileNotFoundError(
        f"No history file found for shell='{shell}' on {env['os']}/{env['runtime']}.\n"
        f"  Tried:\n" + "\n".join(f"    {p}" for p in candidates) +
        "\n  Use --history /path/to/file to specify manually."
    )


# ══════════════════════════════════════════════════════════════════════════════
# 3. CONTENT CLEANING
# ══════════════════════════════════════════════════════════════════════════════

def clean_content(content, shell):
    if shell == "zsh":
        # Strip `: timestamp:elapsed;` metadata lines
        content = re.sub(r"^: \d+:\d+;", "", content, flags=re.MULTILINE)
    elif shell == "fish":
        # Fish stores `- cmd: actual_command` blocks — extract just commands
        content = re.sub(r"^- cmd: ", "", content, flags=re.MULTILINE)
        content = re.sub(r"^\s+when:.*$", "", content, flags=re.MULTILINE)
    return content


# ══════════════════════════════════════════════════════════════════════════════
# 4. REGEX PATTERNS
# ══════════════════════════════════════════════════════════════════════════════

def build_pattern(func_name, shell):
    safe = re.escape(func_name)

    if shell == "powershell":
        pattern_str = rf"""
        function \s+ {safe}
        \s* (?:\([^)]*\))? \s*
        (?P<body>
            \{{
            (?:
                [^{{}}]+
                |
                (?P>body)
            )*
            \}}
        )
        """
    else:
        # bash / zsh / fish — both `fname()` and `function fname` styles
        pattern_str = rf"""
        (?:
            function \s+ {safe} \s* (?:\(\))? |
            {safe} \s* \(\s*\)
        )
        \s*
        (?P<body>
            \{{
            (?:
                [^{{}}]+
                |
                (?P>body)
            )*
            \}}
        )
        """

    if HAS_PCRE:
        return pcre.compile(pattern_str, pcre.IGNORECASE | pcre.DOTALL | pcre.VERBOSE)
    else:
        # Fallback without recursive brace matching
        if shell == "powershell":
            fallback = rf"function\s+{safe}\s*(?:\([^)]*\))?\s*\{{[^}}]*\}}"
        else:
            fallback = rf"(?:function\s+{safe}\s*(?:\(\))?|{safe}\s*\(\s*\))\s*\{{[^}}]*\}}"
        return re.compile(fallback, re.IGNORECASE | re.DOTALL)


# ══════════════════════════════════════════════════════════════════════════════
# 5. LIST ALL FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def list_all_functions(content, shell):
    if shell == "powershell":
        pattern = re.compile(r"function\s+([\w-]+)", re.IGNORECASE)
    else:
        pattern = re.compile(
            r"(?:function\s+([\w_-]+)|^([\w_-]+)\s*\(\s*\))",
            re.MULTILINE
        )
    found = {}
    for m in pattern.finditer(content):
        name = m.group(1) or (m.lastindex >= 2 and m.group(2))
        if name:
            found[name] = found.get(name, 0) + 1
    return found


# ══════════════════════════════════════════════════════════════════════════════
# 6. OUTPUT — RICH if available, plain fallback if not
# ══════════════════════════════════════════════════════════════════════════════

def print_header(env):
    msg = (
        f"Shell History Extractor  |  "
        f"OS={env['os']}  runtime={env['runtime']}  "
        f"shell={env['shell']}  user={env['user']}  "
        f"pcre={'yes' if HAS_PCRE else 'no'}  "
        f"rich={'yes' if HAS_RICH else 'no'}"
    )
    if HAS_RICH:
        console.rule(f"[bold cyan]{msg}[/]")
    else:
        print("=" * 70)
        print(msg)
        print("=" * 70)


def print_functions_table(funcs_dict):
    if HAS_RICH:
        table = Table(title="Functions in History", show_lines=True)
        table.add_column("Function", style="cyan bold")
        table.add_column("Occurrences", justify="center", style="magenta")
        for name, count in sorted(funcs_dict.items()):
            table.add_row(name, str(count))
        console.print(table)
    else:
        print(f"\n{'Function':<40} Occurrences")
        print("-" * 50)
        for name, count in sorted(funcs_dict.items()):
            print(f"  {name:<38} {count}")
def print_function_body(match, func_name, line_no, shell, raw=False):
    body = match.group(0).strip()
    body = re.sub(r'`\s*$', '', body, flags=re.MULTILINE)  # strip backticks

    if raw:
        # Plain print — no Panel, no Syntax, no box characters
        # Completely safe to copy-paste directly into PowerShell or bash
        print(body)
        return

    lang = "powershell" if shell == "powershell" else "bash"
    if HAS_RICH:
        # Only use Panel for non-raw display
        console.print(Panel(
            Syntax(body, lang, theme="monokai", line_numbers=False),
            title=f"[green bold]{func_name}[/] — Line ~{line_no}",
            border_style="green"
        ))
    else:
        print(f"\n{'=' * 60}")
        print(body)
        print("=" * 60)

def print_summary_table(matches, content, func_name):
    if HAS_RICH:
        table = Table(title=f"Occurrences of '{func_name}'", show_lines=True)
        table.add_column("#",       justify="center", style="yellow")
        table.add_column("Line",    justify="center", style="cyan")
        table.add_column("Preview", style="white")
        for i, m in enumerate(matches, 1):
            line_no = content[:m.start()].count("\n") + 1
            preview = m.group(0).strip().splitlines()[0][:60]
            table.add_row(str(i), str(line_no), preview)
        console.print(table)
    else:
        print(f"\n  # | Line | Preview")
        print("-" * 60)
        for i, m in enumerate(matches, 1):
            line_no = content[:m.start()].count("\n") + 1
            preview = m.group(0).strip().splitlines()[0][:55]
            print(f"  {i} | {line_no:<4} | {preview}")


def save_function(match, func_name, out_dir, shell):
    ext  = ".ps1" if shell == "powershell" else ".sh"
    clean = match.group(0).strip()
    out_path = os.path.join(os.path.expanduser(out_dir), f"{func_name}{ext}")

    with open(out_path, "w", encoding="utf-8") as f:
        if shell != "powershell":
            f.write("#!/usr/bin/env bash\n\n")
        f.write(clean + "\n")

    msg = f"[+] Saved: {out_path}"
    if HAS_RICH:
        console.print(f"\n[bold green]{msg}[/]")
    else:
        print(f"\n{msg}")
    return out_path


# ══════════════════════════════════════════════════════════════════════════════
# 7. MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Extract shell functions from history — works on Bash/Zsh/PowerShell/MSYS2/WSL/Linux"
    )
    parser.add_argument("func_name", nargs="?",   help="Function name to extract")
    parser.add_argument("--shell",   choices=["bash","zsh","fish","powershell"],
                                                   help="Force a specific shell (auto-detected if omitted)")
    parser.add_argument("--history", metavar="PATH", help="Path to history file (auto-detected if omitted)")
    parser.add_argument("--list",    action="store_true", help="List all functions found in history")
    parser.add_argument("--all",     action="store_true", help="Extract ALL functions to --out directory")
    parser.add_argument("--out",     default="~",  help="Output directory (default: home)")
    parser.add_argument("--show",    action="store_true", help="Print only, do not save")
    parser.add_argument("--env",     action="store_true", help="Print detected environment and exit")
    args = parser.parse_args()

    env = detect_environment()
    print_header(env)

    # ── Debug mode ────────────────────────────────────────────────────────────
    if args.env:
        for k, v in env.items():
            print(f"  {k:<12} {v}")
        return

    # ── Resolve history file ──────────────────────────────────────────────────
    try:
        history_file, shell = resolve_history_file(env, args.shell)
    except FileNotFoundError as e:
        print(str(e)); sys.exit(1)

    msg = f"History: {history_file}"
    print(f"\n[dim]{msg}[/]" if HAS_RICH else f"\n{msg}")

    with open(history_file, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    content = clean_content(content, shell)
    msg2 = f"{len(content)} chars  ~{content.count(chr(10))} lines"
    print(f"[dim]{msg2}[/]\n" if HAS_RICH else f"{msg2}\n")

    # ── List mode ─────────────────────────────────────────────────────────────
    if args.list:
        funcs = list_all_functions(content, shell)
        if funcs:
            print_functions_table(funcs)
        else:
            print("No functions found in history.")
        return

    # ── Extract all mode ──────────────────────────────────────────────────────
    if args.all:
        funcs = list_all_functions(content, shell)
        print(f"Extracting {len(funcs)} functions...")
        for fn in funcs:
            matches = list(build_pattern(fn, shell).finditer(content))
            if matches:
                save_function(matches[-1], fn, args.out, shell)
        return

    # ── Interactive fallback if no name given ─────────────────────────────────
    if not args.func_name:
        funcs = list_all_functions(content, shell)
        print_functions_table(funcs)
        if HAS_RICH:
            args.func_name = Prompt.ask("\n[cyan]Enter function name to extract[/]")
        else:
            args.func_name = input("\nEnter function name to extract: ").strip()

    # ── Single function ───────────────────────────────────────────────────────
    matches = list(build_pattern(args.func_name, shell).finditer(content))

    if not matches:
        msg = f"[-] '{args.func_name}' not found. Run --list to see what's recoverable."
        print(f"[red]{msg}[/]" if HAS_RICH else msg)
        return

    m = matches[-1]
    body = m.group(0).strip()
    body = re.sub(r'`\s*$', '', body, flags=re.MULTILINE)  # strip backticks

    if args.show:
        # Pure plain print — no Rich, no Panel, no box chars, safe to copy-paste
        print(body)
        return

    # Only show tables and panels if NOT in --show mode
    print_summary_table(matches, content, args.func_name)
    line_no = content[:m.start()].count("\n") + 1
    print_function_body(m, args.func_name, line_no, shell)

    if not args.show:
        save_function(m, args.func_name, args.out, shell)

    if len(matches) > 1:
        msg = f"[i] {len(matches)-1} earlier definition(s) also in history."
        print(f"\n[dim]{msg}[/]" if HAS_RICH else f"\n{msg}")

def expand_oneliner(cmd):
    """
    Expands collapsed bash one-liners back to readable multiline.
    Handles for/while/if/do/then/else/fi/done/{ }
    """
    openers  = {'do', 'then', 'else', '{'}
    closers  = {'done', 'fi', 'esac', '}'}
    midwords = {'elif', 'else'}
    tokens = re.split(r';\s*', cmd)
    result = []
    indent = 0
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        word = token.split()[0] if token.split() else ''
        if word in closers:
            indent = max(0, indent - 1)
            result.append('    ' * indent + token)
        elif word in midwords:
            indent = max(0, indent - 1)
            result.append('    ' * indent + token)
            indent += 1
        else:
            # Split 'do cmd' into two tokens if do is at start
            if word == 'do' and len(token.split(None, 1)) > 1:
                result.append('    ' * indent + 'do')
                indent += 1
                rest = token.split(None, 1)[1].strip()
                result.append('    ' * indent + rest)
            else:
                result.append('    ' * indent + token)
                if word in openers or token.rstrip().endswith('do') or token.rstrip().endswith('then'):
                    indent += 1
    return '\n'.join(result)

def main():
    parser = argparse.ArgumentParser(
        description="Extract shell functions from history — works on Bash/Zsh/PowerShell/MSYS2/WSL/Linux"
    )
    parser.add_argument("func_name", nargs="?",   help="Function name to extract")
    parser.add_argument("--shell",   choices=["bash","zsh","fish","powershell"],
                                                   help="Force a specific shell (auto-detected if omitted)")
    parser.add_argument("--history", metavar="PATH", help="Path to history file (auto-detected if omitted)")
    parser.add_argument("--list",    action="store_true", help="List all functions found in history")
    parser.add_argument("--all",     action="store_true", help="Extract ALL functions to --out directory")
    parser.add_argument("--out",     default="~",  help="Output directory (default: home)")
    parser.add_argument("--show",    action="store_true", help="Print only, do not save")
    parser.add_argument("--env",     action="store_true", help="Print detected environment and exit")
    parser.add_argument("--expand",  metavar="CMD", help="Expand a collapsed one-liner into multiline")
    parser.add_argument("--search",  metavar="KEYWORD", help="Search history for a keyword and expand matches")
    args = parser.parse_args()

    # ── Expand mode ───────────────────────────────────────────────────────────
    if args.expand:
        print(expand_oneliner(args.expand))
        return

    # ── Search mode ───────────────────────────────────────────────────────────
    if args.search:
        env = detect_environment()
        history_file, shell = resolve_history_file(env, args.shell)
        with open(history_file, "r", encoding="utf-8", errors="replace") as fh:
            raw = fh.read()
        content = clean_content(raw, shell)
        keyword = args.search.lower()

        # ── Join continuation lines first ──────────────────────────────────
        # Bash history stores multiline commands with \ at end of each line
        # Join them back into single logical lines before searching
        joined_lines = []
        buffer = ""
        for line in content.splitlines():
            if line.endswith("\\"):
                buffer += line[:-1] + " "   # strip \ and join
            else:
                buffer += line
                joined_lines.append(buffer)
                buffer = ""
        if buffer:
            joined_lines.append(buffer)

        # ── Search and display ─────────────────────────────────────────────
        matches = [l for l in joined_lines if keyword in l.lower()]
        if not matches:
            print(f"[-] No history lines containing '{args.search}' found.")
            return

        for i, line in enumerate(matches, 1):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            first_word = stripped.split()[0] if stripped.split() else ''
            if '=' in first_word or not first_word:
                continue
            # Skip lines that are just searching for this keyword
            if any(cmd in stripped for cmd in ['grep', '--search', 'history']):
                continue
            
            # Collapse multiple spaces/tabs introduced by joined continuation lines
            import re as _re
            stripped = _re.sub(r'[ \t]{2,}', ' ', stripped)

            print(f"\n--- Match {i} ---")
            if '; ' in stripped and any(stripped.startswith(kw) for kw in ('for ', 'while ', 'if ')):
                print(expand_oneliner(stripped))
            else:
                print(stripped)
        return    
    
    # ── Header ────────────────────────────────────────────────────────────────
    env = detect_environment()
    print_header(env)

    # ── Debug mode ────────────────────────────────────────────────────────────
    if args.env:
        for k, v in env.items():
            print(f"  {k:<12} {v}")
        return

    # ── Resolve history file ──────────────────────────────────────────────────
    try:
        history_file, shell = resolve_history_file(env, args.shell)
    except FileNotFoundError as e:
        print(str(e)); sys.exit(1)

    msg = f"History: {history_file}"
    print(f"\n[dim]{msg}[/]" if HAS_RICH else f"\n{msg}")

    with open(history_file, "r", encoding="utf-8", errors="replace") as fh:
        content = fh.read()

    content = clean_content(content, shell)
    msg2 = f"{len(content)} chars  ~{content.count(chr(10))} lines"
    print(f"[dim]{msg2}[/]\n" if HAS_RICH else f"{msg2}\n")

    # ── List mode ─────────────────────────────────────────────────────────────
    if args.list:
        funcs = list_all_functions(content, shell)
        if funcs:
            print_functions_table(funcs)
        else:
            print("No functions found in history.")
        return

    # ── Extract all mode ──────────────────────────────────────────────────────
    if args.all:
        funcs = list_all_functions(content, shell)
        print(f"Extracting {len(funcs)} functions...")
        for fn in funcs:
            matches = list(build_pattern(fn, shell).finditer(content))
            if matches:
                save_function(matches[-1], fn, args.out, shell)
        return

    # ── Interactive fallback if no name given ─────────────────────────────────
    if not args.func_name:
        funcs = list_all_functions(content, shell)
        print_functions_table(funcs)
        if HAS_RICH:
            args.func_name = Prompt.ask("\n[cyan]Enter function name to extract[/]")
        else:
            args.func_name = input("\nEnter function name to extract: ").strip()

    # ── Single function ───────────────────────────────────────────────────────
    matches = list(build_pattern(args.func_name, shell).finditer(content))

    if not matches:
        msg = f"[-] '{args.func_name}' not found. Run --list to see what's recoverable."
        print(f"[red]{msg}[/]" if HAS_RICH else msg)
        return

    m = matches[-1]
    body = m.group(0).strip()
    body = re.sub(r'`\s*$', '', body, flags=re.MULTILINE)  # strip backticks

    if args.show:
        print(body)
        return

    # Only show tables and panels if NOT in --show mode
    print_summary_table(matches, content, args.func_name)
    line_no = content[:m.start()].count("\n") + 1
    print_function_body(m, args.func_name, line_no, shell)

    save_function(m, args.func_name, args.out, shell)

    if len(matches) > 1:
        msg = f"[i] {len(matches)-1} earlier definition(s) also in history."
        print(f"\n[dim]{msg}[/]" if HAS_RICH else f"\n{msg}")


if __name__ == "__main__":
    main()

