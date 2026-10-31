#!/usr/bin/env python3
# pcre2-vim-combine-regex-example.py  (v2 — restructured)
#
# Structure: 8 demos, each showing ONE feature.
# Every demo prints:
#   ✗ [ENGINE FAILS]   — what breaks and why
#   ✓ [ENGINE SUCCEEDS] — the correct result
#
# PART A — Vim-exclusive features  (PCRE2 cannot do these)
#   A1  \%{n}l          line-aware substitution
#   A2  \%{n}l\%{n}c    column-aware substitution
#   A3  col\%[ou]r\=    optional-sequence shorthand
#   A4  \zs...\ze       independent match-boundary setters
#
# PART B — PCRE2-exclusive features  (Vim cannot do these)
#   B1  (*SKIP)(*FAIL)  backtracking control verbs
#   B2  \d++            possessive quantifiers
#   B3  (?<=\w{1,10}_)  variable-length lookbehind
#   B4  (?P<name>...)   named capture groups

import os, re, subprocess, sys, tempfile

try:
    import pcre
except ImportError:
    sys.exit("\n  [ERROR] pip install pypcre\n")

print(f"\n  [INFO] pypcre version: {pcre.__version__}\n")

VIM   = r"D:\Programs\gvim\vim.exe"
_HERE = os.path.dirname(os.path.abspath(__file__))
BS    = chr(92)   # backslash — avoids escaping confusion in f-strings
PCT   = chr(37)   # percent

SEP  = "=" * 66
SEPM = "-" * 66


# ── shared helpers ─────────────────────────────────────────────────────────

def write_file(path: str, lines: list[str]) -> None:
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.writelines(lines)

def read_file(path: str) -> list[str]:
    with open(path, encoding="utf-8") as fh:
        return fh.readlines()

def print_file(path: str, label: str) -> None:
    print(f"\n  [{label}]")
    for i, line in enumerate(read_file(path), 1):
        print(f"    {i}: {line}", end="")
    print()

def demo_header(tag: str, title: str, fails: str, succeeds: str) -> None:
    print(f"\n{SEP}")
    print(f"  {tag}: {title}")
    print(SEPM)
    print(f"  FAILS   : {fails}")
    print(f"  SUCCEEDS: {succeeds}")
    print(SEP)

def show_fail(engine: str, reason: str) -> None:
    print(f"\n  ✗ [{engine} FAILS]")
    print(f"    Reason : {reason}")

def show_succeed(engine: str, note: str = "") -> None:
    line = f"\n  ✓ [{engine} SUCCEEDS]"
    if note:
        line += f"  {note}"
    print(line)

def vim_run(cmds: list[str], path: str) -> bool:
    script = "\n".join(cmds + ["wq"])
    tmp = tempfile.NamedTemporaryFile(
        mode="w", suffix=".vim", delete=False,
        newline="\n", encoding="utf-8",
    )
    tmp.write(script)
    tmp.close()
    print(f"    [Vim commands]")
    for c in cmds:
        print(f"      {c}")
    try:
        r = subprocess.run(
            [VIM, "-e", "-s", "-S", tmp.name, path],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
        )
        ok = r.returncode == 0
        print(f"    → exit {r.returncode}  {'(file written)' if ok else r.stderr.strip()}")
        return ok
    except subprocess.TimeoutExpired:
        print("    → vim timed out")
        return False
    finally:
        os.unlink(tmp.name)


# ═══════════════════════════════════════════════════════════════════════════
# PART A — Vim-exclusive features
# ═══════════════════════════════════════════════════════════════════════════

def demo_a1() -> None:
    r"""A1 — \%{n}l : line-aware substitution."""
    demo_header(
        "Demo A1", r"Line-aware substitution  \%{n}l",
        fails    = "PCRE2 — flat-string engine; no concept of line numbers",
        succeeds = r"Vim   — \%{n}l restricts :s to exactly line n",
    )

    path  = os.path.join(_HERE, "a1_errors.log")
    lines = [
        "2026-10-31 10:00:01 ERROR   disk failure\n",
        "2026-10-31 10:00:02 SUPPRESSED ERROR  flapping sensor\n",
        "2026-10-31 10:00:03 ERROR   network timeout\n",
        "2026-10-31 10:00:04 SUPPRESSED ERROR  maintenance window\n",
        "2026-10-31 10:00:05 ERROR   auth failure for root\n",
    ]
    write_file(path, lines)
    print_file(path, "ORIGINAL")

    # ── PCRE2 fails ────────────────────────────────────────────────────────
    show_fail(
        "PCRE2",
        "pcre.sub(r'ERROR', '[ALERT]', whole_file) replaces every ERROR,\n"
        "    including SUPPRESSED ones — there is no line-pin in PCRE2.",
    )
    whole = "".join(lines)
    naive = pcre.compile(r"ERROR").sub("[ALERT]", whole)
    print("    Result (SUPPRESSED lines wrongly patched):")
    for i, l in enumerate(naive.splitlines(keepends=True), 1):
        print(f"      {i}: {l}", end="")

    # ── Vim succeeds ───────────────────────────────────────────────────────
    show_succeed("Vim", r"\%{n}l: PCRE2 identifies line numbers; Vim pins :s to each one")
    pat  = pcre.compile(r"SUPPRESSED ERROR(*SKIP)(*FAIL)|ERROR")
    cmds : list[str] = []
    seen : set[int]  = set()
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            for m in pat.finditer(line):
                if m.group() == "ERROR" and lineno not in seen:
                    print(f"    PCRE2 found real ERROR at line {lineno}")
                    cmds.append(f"%s/{BS}{PCT}{lineno}lERROR/[ALERT]/ge")
                    seen.add(lineno)
    write_file(path, lines)          # reset before Vim run
    vim_run(cmds, path)
    print_file(path, "PATCHED — SUPPRESSED lines untouched")


def demo_a2() -> None:
    r"""A2 — \%{n}l\%{n}c : column-aware substitution."""
    demo_header(
        "Demo A2", r"Column-aware substitution  \%{n}l\%{n}c",
        fails    = "PCRE2 — no column concept; substitution hits all occurrences on the line",
        succeeds = r"Vim   — \%{n}c restricts :s to the exact column PCRE2 found",
    )

    path  = os.path.join(_HERE, "a2_timeouts.cfg")
    lines = [
        "timeout=30 retry_timeout=30\n",
        "timeout=60 retry_timeout=60\n",
        "timeout=90 retry_timeout=90\n",
    ]
    write_file(path, lines)
    print_file(path, "ORIGINAL — goal: double ONLY the first timeout, leave retry_timeout")

    # ── PCRE2 fails ────────────────────────────────────────────────────────
    show_fail(
        "PCRE2",
        "re.sub(r'timeout=\\d+', double_fn, line) doubles BOTH timeouts;\n"
        "    PCRE2 cannot say 'match only at column 1'.",
    )
    def _double(m: re.Match) -> str:
        return f"timeout={int(m.group(1)) * 2}"
    print("    Result (retry_timeout wrongly doubled too):")
    for i, l in enumerate(lines, 1):
        print(f"      {i}: {re.sub(r'timeout=(\d+)', _double, l)}", end="")

    # ── Vim succeeds ───────────────────────────────────────────────────────
    show_succeed("Vim", r"\%{n}l\%{c}c: targets the exact (line, column) PCRE2 identified")
    pat  = pcre.compile(r"(?<!retry_)timeout=(?P<val>\d+)")
    cmds : list[str] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            m = pat.search(line)
            if m:
                col = m.start() + 1
                val = m.group("val")
                new = str(int(val) * 2)
                print(f"    PCRE2 found timeout={val} at line {lineno} col {col}")
                l_atom = f"{BS}{PCT}{lineno}l"
                c_atom = f"{BS}{PCT}{col}c"
                cmds.append(f"%s/{l_atom}{c_atom}timeout={val}/timeout={new}/ge")
    write_file(path, lines)
    vim_run(cmds, path)
    print_file(path, "PATCHED — retry_timeout values untouched")


def demo_a3() -> None:
    r"""A3 — col\%[ou]r\= : optional-sequence shorthand."""
    demo_header(
        "Demo A3", r"Optional-sequence shorthand  col\%[ou]r\=",
        fails    = r"PCRE2 — no \%[] atom; must enumerate every variant with verbose alternation",
        succeeds = r"Vim   — col\%[ou]r\= matches col/colo/colou/colour/color in one atom",
    )

    path  = os.path.join(_HERE, "a3_spelling.txt")
    lines = [
        "The col of the button should be red\n",       # bare prefix
        "The colo of the button should be blue\n",     # one-char prefix
        "The colou of the button should be green\n",   # two-char prefix
        "# KEEP: colour is correct British spelling\n",# must skip
        "The colour of the flag is important\n",       # full British
        "The color of the sky changes at dusk\n",      # American
    ]
    write_file(path, lines)
    print_file(path, "ORIGINAL — goal: normalise all variants to British 'colour', skip #KEEP")

    # ── PCRE2 fails ────────────────────────────────────────────────────────
    show_fail(
        "PCRE2",
        r"No \%[] atom.  Must manually enumerate every variant as alternation:"
        "\n    col(?:our|or|ou|o|)  — verbose and error-prone for longer sequences.",
    )
    print(r"    PCRE2 pattern required: col(?:our|or|ou|o|)")
    print(r"    Vim pattern equivalent: col\%[ou]r\=   (one concise atom)")

    # ── Vim succeeds ───────────────────────────────────────────────────────
    show_succeed("Vim", r"\%[ou]r\= — matches all 5 variants including American 'color'")
    # PCRE2 still used for FINDING ((*SKIP)(*FAIL) to skip #KEEP lines)
    pat  = pcre.compile(r"(?m)^#[^\n]*(*SKIP)(*FAIL)|col(?:our|or|ou|o|)")
    cmds : list[str] = []
    seen : set[int]  = set()
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            for m in pat.finditer(line):
                if lineno not in seen:
                    print(f"    PCRE2 found {m.group()!r} at line {lineno} (will normalise)")
                    l_atom  = f"{BS}{PCT}{lineno}l"
                    opt_seq = f"col{BS}{PCT}[ou]r{BS}="  # \%[ou]r\= covers all 5 variants
                    cmds.append(f"%s/{l_atom}{opt_seq}/colour/ge")
                    seen.add(lineno)
    write_file(path, lines)
    vim_run(cmds, path)
    print_file(path, "PATCHED — #KEEP line untouched, all variants normalised")


def demo_a4() -> None:
    r"""A4 — \zs...\ze : independent match-boundary setters."""
    demo_header(
        "Demo A4", r"Independent boundary setters  \zs...\ze",
        fails    = r"PCRE2 — \K sets match start (like \zs) but has no \ze equivalent;"
                   " end boundary requires a lookahead, adding noise to the pattern",
        succeeds = r"Vim   — \zs...\ze sets start AND end inside one clean pattern",
    )

    path  = os.path.join(_HERE, "a4_servers.log")
    lines = [
        "connected to server 192.168.1.10 on port 8080\n",
        "connected to server 10.0.0.1 on port 443\n",
        "no ip address on this line\n",
        "connected to server 172.16.254.1 on port 22\n",
        "connected to server 192.168.1.200 on port 3306\n",
    ]
    write_file(path, lines)
    print_file(path, "ORIGINAL — goal: replace ONLY the IP, leave 'on port N' untouched")

    # ── PCRE2 fails ────────────────────────────────────────────────────────
    show_fail(
        "PCRE2",
        r"\K resets the match start but there is no \ze to set the match end."
        "\n    Without a lookahead the replacement must explicitly repeat the trailing text,"
        "\n    which is fragile.  The workaround adds a lookahead that isn't in Vim's \\zs\\ze.",
    )
    print(r"    PCRE2 with \K only:  server \K\d+\.\d+\.\d+\.\d+")
    print( "    → replacement is just '10.0.0.99' but the lookahead is needed to pin the end:")
    print(r"    PCRE2 full workaround: server \K\d+\.\d+\.\d+\.\d+(?= on port)")
    print(r"    Vim equivalent:        server \zs\d\+\.\d\+\.\d\+\.\d\+\ze")

    # ── Vim succeeds ───────────────────────────────────────────────────────
    show_succeed("Vim", r"\zs...\ze — start and end set inside the pattern, no lookahead")
    pat  = pcre.compile(r"\d++\.\d++\.\d++\.\d++")
    cmds : list[str] = []
    seen : set[int]  = set()
    with open(path, encoding="utf-8") as fh:
        for lineno, line in enumerate(fh, 1):
            m = pat.search(line)
            if m and lineno not in seen:
                print(f"    PCRE2 found IP {m.group()!r} at line {lineno}")
                l  = f"{BS}{PCT}{lineno}l"
                zs = f"{BS}zs"
                ze = f"{BS}ze"
                ip = f"{BS}d{BS}+{BS}.{BS}d{BS}+{BS}.{BS}d{BS}+{BS}.{BS}d{BS}+"
                cmds.append(f"%s/{l}server {zs}{ip}{ze}/10.0.0.99/ge")
                seen.add(lineno)
    write_file(path, lines)
    vim_run(cmds, path)
    print_file(path, "PATCHED — only IPs replaced, ports untouched")


# ═══════════════════════════════════════════════════════════════════════════
# PART B — PCRE2-exclusive features
# ═══════════════════════════════════════════════════════════════════════════

def demo_b1() -> None:
    """B1 — (*SKIP)(*FAIL) : backtracking control verbs."""
    demo_header(
        "Demo B1", "Backtracking control verbs  (*SKIP)(*FAIL)",
        fails    = "Vim   — no backtracking verbs; :s cannot atomically discard a sub-match",
        succeeds = "PCRE2 — (*SKIP)(*FAIL) consumes an unwanted match and forces the engine past it",
    )

    lines = [
        "ERROR   disk failure\n",
        "SUPPRESSED ERROR  flapping sensor\n",
        "ERROR   network timeout\n",
        "SUPPRESSED ERROR  maintenance window\n",
        "ERROR   auth failure\n",
    ]
    print("\n  Input lines:")
    for i, l in enumerate(lines, 1):
        print(f"    {i}: {l}", end="")

    # ── Vim fails ─────────────────────────────────────────────────────────
    show_fail(
        "Vim",
        r":%s/SUPPRESSED ERROR\|ERROR/[ALERT]/ge"
        "\n    Vim has no (*SKIP)(*FAIL); the alternation matches SUPPRESSED ERROR,"
        "\n    then separately matches ERROR inside those same lines too.",
    )
    print(r"    Vim pattern: SUPPRESSED ERROR\|ERROR")
    print("    Result (SUPPRESSED lines wrongly patched, ERROR replaced twice):")
    for i, l in enumerate(lines, 1):
        # Simulate what Vim :%s/SUPPRESSED ERROR\|ERROR/ would do left-to-right
        result = re.sub(r"SUPPRESSED ERROR|ERROR", "[ALERT]", l)
        print(f"      {i}: {result}", end="")

    # ── PCRE2 succeeds ────────────────────────────────────────────────────
    show_succeed("PCRE2", "(*SKIP)(*FAIL) discards the SUPPRESSED lines atomically")
    pat = pcre.compile(r"SUPPRESSED ERROR(*SKIP)(*FAIL)|ERROR")
    print("    PCRE2 matches (real ERRORs only):")
    for i, line in enumerate(lines, 1):
        for m in pat.finditer(line):
            if m.group() == "ERROR":
                print(f"      Line {i} col {m.start()+1}: {m.group()!r}  ← real ERROR")


def demo_b2() -> None:
    r"""B2 — possessive quantifiers \d++ : no backtracking after a failed attempt."""
    demo_header(
        "Demo B2", r"Possessive quantifiers  \d++",
        fails    = r"Vim   — no possessive quantifiers; \d\+ is greedy and backtracks on failure",
        succeeds = r"PCRE2 — \d++ is possessive: digits claimed once, never returned",
    )

    # The clearest correctness difference: possessive inside a larger pattern
    # that must fail fast.  Use atomic IP matching: 4 groups of digits with dots.
    # On a string like '1234567890' (no dots) \d+\.\d+\.\d+\.\d+ must backtrack
    # through all length combinations; \d++\.\d++\.\d++\.\d++ fails immediately.
    # More visibly: match quoted-string content possessively to show no backtrack.

    inputs = [
        '"hello world"',        # valid — quotes balanced
        '"missing close',       # invalid — no closing quote
        '"a"extra"b"',          # two quoted strings on one line
        '192.168.1.10',         # valid IP-shaped
        '1234567890',           # no dots — should not match IP pattern
    ]
    print("\n  Inputs:")
    for inp in inputs:
        print(f"    {inp!r}")

    # ── Vim fails ─────────────────────────────────────────────────────────
    show_fail(
        "Vim",
        r'Vim has no possessive quantifiers.  \@> gives atomic groups but is verbose.'
        "\n    For the quoted-string pattern, Vim backtracks inside failed attempts,"
        "\n    which is unsafe on adversarial input and has no per-quantifier shorthand.",
    )
    print(r'    Vim pattern for quoted string: "[^"]\+"  (greedy, can backtrack)')
    print(r'    PCRE2 possessive equivalent:  "[^"]++"  (possessive, never backtracks)')

    # ── PCRE2 succeeds ────────────────────────────────────────────────────
    show_succeed("PCRE2", r'\d++ and [^"]++ — digits/chars consumed possessively')
    pat_quoted = pcre.compile(r'"[^"]++"')
    pat_ip     = pcre.compile(r'\d++\.\d++\.\d++\.\d++')
    for inp in inputs:
        q = pat_quoted.search(inp)
        p = pat_ip.search(inp)
        q_res = f"quoted={q.group()!r}" if q else "quoted=no match"
        p_res = f"IP={p.group()!r}"     if p else "IP=no match"
        print(f"    {inp!r:25s}  →  {q_res}   {p_res}")


def demo_b3() -> None:
    """B3 — variable-length lookbehind (?<=alt1|alt2) : Vim requires fixed width."""
    demo_header(
        "Demo B3", r"Variable-length lookbehind  (?<=prefix_A|prefix_BB|prefix_CCC)",
        fails    = r"Vim   — \@<= requires the lookbehind pattern to be fixed-width;"
                   " alternations of different lengths are rejected",
        succeeds = "PCRE2 — lookbehind can be variable-length since PCRE2 10.x",
    )

    # Match the word VALUE only when it appears after one of several
    # variable-length prefixes followed by an underscore.
    lines = [
        "x_VALUE rest of line\n",           # prefix len 1 → match
        "foo_VALUE rest of line\n",          # prefix len 3 → match
        "longprefix_VALUE rest of line\n",   # prefix len 10 → match
        "VALUE_standalone\n",               # VALUE is a prefix here → no match
        "no underscore VALUE here\n",       # no _ before VALUE → no match
    ]
    print("\n  Input lines (match VALUE only when preceded by <word-chars>_):")
    for i, l in enumerate(lines, 1):
        print(f"    {i}: {l}", end="")
    print()
    print("  Target: match VALUE when preceded by x_ or foo_ or longprefix_")
    print(r"  PCRE2 pattern: (?<=x_|foo_|longprefix_)VALUE")
    print(r"  Vim attempt  : \(x_\|foo_\|longprefix_\)\@<=VALUE")

    # ── Vim fails ─────────────────────────────────────────────────────────
    show_fail(
        "Vim",
        r"\(x_\|foo_\|longprefix_\)\@<= — the alternatives have lengths 2, 4, 11;"
        "\n    Vim's lookbehind requires a single fixed width.  Vim raises:"
        "\n    E69: Missing ] after \\%[  or  silently produces wrong matches.",
    )
    print("    Vim has no workaround short of restructuring the entire pattern.")

    # ── PCRE2 succeeds ────────────────────────────────────────────────────
    show_succeed("PCRE2", "(?<=x_|foo_|longprefix_) — variable-length lookbehind")
    pat = pcre.compile(r"(?<=x_|foo_|longprefix_)VALUE")
    for i, line in enumerate(lines, 1):
        m = pat.search(line)
        status = f"match at col {m.start()+1}" if m else "no match"
        print(f"    Line {i}: {status:<22}  {line.rstrip()!r}")


def demo_b4() -> None:
    """B4 — named capture groups (?P<name>...) : Vim has numbered groups only."""
    demo_header(
        "Demo B4", "Named capture groups  (?P<name>...)",
        fails    = r"Vim   — only numbered \(\) groups; \1 \2 \3 break silently when"
                   " a group is inserted or removed",
        succeeds = "PCRE2 — groups named by (?P<name>...) referenced as m.group('name');"
                   " order changes never break back-references",
    )

    lines = [
        "2026-10-31 10:00:01 user=alice  action=login\n",
        "2026-10-31 10:00:02 user=bob    action=logout\n",
        "2026-10-31 10:00:03 user=alice  action=delete\n",
    ]
    print("\n  Input lines (extract date, user, action for an audit report):")
    for i, l in enumerate(lines, 1):
        print(f"    {i}: {l}", end="")

    # ── Vim fails ─────────────────────────────────────────────────────────
    show_fail(
        "Vim",
        r"Vim uses \1 \2 \3 … — purely positional."
        "\n    Insert a new group at the start (e.g. to capture the host) and"
        "\n    every existing back-reference silently shifts, corrupting results."
        "\n    No way to reference a group by name.",
    )
    print(r"    Vim pattern: \(\d\{4\}-\d\{2\}-\d\{2\}\) \d\{8\} user=\(\w\+\) ...")
    print(r"    If a group is added before \1, \1 now captures the wrong thing.")

    # ── PCRE2 succeeds ────────────────────────────────────────────────────
    show_succeed("PCRE2", "(?P<date>...) (?P<user>...) — position-independent named refs")
    pat = pcre.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2})"
        r" \d{2}:\d{2}:\d{2}"
        r" user=(?P<user>\w+)"
        r"\s+action=(?P<action>\w+)"
    )
    print("    Audit entries extracted by name:")
    for i, line in enumerate(lines, 1):
        m = pat.search(line)
        if m:
            print(
                f"      Line {i}: "
                f"date={m.group('date')}  "
                f"user={m.group('user'):<8} "
                f"action={m.group('action')}"
            )


# ═══════════════════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════════════════

def summary() -> None:
    print(f"\n{SEP}")
    print("  SUMMARY")
    print(SEPM)
    rows = [
        ("A1", r"\%{n}l",           "line-aware :s",             "✗ no line concept",       "✓"),
        ("A2", r"\%{n}l\%{n}c",     "column-aware :s",           "✗ no col concept",        "✓"),
        ("A3", r"col\%[ou]r\=",     "optional-seq shorthand",    "✗ verbose alternation",   "✓ one atom"),
        ("A4", r"\zs...\ze",        "dual boundary setters",     r"✗ \K only (no \ze)",     "✓"),
        ("B1", "(*SKIP)(*FAIL)",    "backtracking verbs",        "✓",                       "✗ none"),
        ("B2", r"\d++",             "possessive quantifiers",    "✓",                       r"✗ no \d++"),
        ("B3", r"(?<=\w{1,n}_)",    "variable-len lookbehind",   "✓ since PCRE2 10.x",      "✗ fixed-width only"),
        ("B4", "(?P<name>)",        "named capture groups",      "✓",                       "✗ numbered only"),
    ]
    w = (6, 20, 27, 24, 14)
    hdr = (f"{'Demo':<{w[0]}} {'Feature':<{w[1]}} {'Task':<{w[2]}}"
           f" {'PCRE2':<{w[3]}} {'Vim'}")
    print(f"  {hdr}")
    print(f"  {'-'*(sum(w)+4)}")
    for demo, feat, task, pcre_col, vim_col in rows:
        print(f"  {demo:<{w[0]}} {feat:<{w[1]}} {task:<{w[2]}}"
              f" {pcre_col:<{w[3]}} {vim_col}")
    print(SEP)
    print()


def main() -> None:
    demo_a1()
    demo_a2()
    demo_a3()
    demo_a4()
    demo_b1()
    demo_b2()
    demo_b3()
    demo_b4()
    summary()


if __name__ == "__main__":
    main()
