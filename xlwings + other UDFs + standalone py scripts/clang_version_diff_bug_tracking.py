#!/usr/bin/env python3
"""
clang_fingerprint_diff.py

Compares two clang installations by diffing their predefined macros,
target triple, and version info. Works identically under:
  - PowerShell:      python clang_fingerprint_diff.py
  - MSYS2 ucrt64:    python clang_fingerprint_diff.py   (or python3)

It does NOT try to detect "new in 22.1.8" features -- between two
x.y.Z dot releases on the same stable branch there generally aren't
any (LLVM dot releases are bug-fix-only backports; new features land
in x.y.0). What this *does* show clearly is what actually differs
between two clang binaries: version, target triple/ABI, and the full
predefined-macro set for C and C++.

Usage:
    python clang_fingerprint_diff.py [CLANG_A] [CLANG_B] [--lang c,c++]

If CLANG_A / CLANG_B are omitted, the defaults below are used.
Paths are plain Windows paths -- they work fine from MSYS2's native
ucrt64 Python too, since subprocess launches the real Win32 exe
directly (no MSYS path translation involved).
"""

import argparse
import re
import subprocess
import sys

DEFAULT_A = r"D:\Programs\clang\bin\clang.exe"          # clang-win
DEFAULT_B = r"D:\Programs\msys64\ucrt64\bin\clang.exe"   # clang-msys

KEY_MACROS = [
    "__clang_version__", "__clang_major__", "__clang_minor__",
    "__clang_patchlevel__", "__VERSION__",
    "_MSC_VER", "_MSC_FULL_VER", "_MSVC_LANG",
    "__GNUC__", "__GNUC_MINOR__", "__MINGW32__", "__MINGW64__",
    "_WIN32", "_WIN64", "__USING_UCRT__", "_UCRT",
    "__EXCEPTIONS", "__SEH__", "__STDC_VERSION__", "__cplusplus",
]


def run(cmd, **kw):
    return subprocess.run(
        cmd, capture_output=True, text=True, timeout=30, **kw
    )


def get_version_info(clang_path):
    try:
        p = run([clang_path, "--version"])
    except FileNotFoundError:
        return None
    text = p.stdout + p.stderr
    target = re.search(r"Target:\s*(\S+)", text)
    first_line = text.strip().splitlines()[0] if text.strip() else "(no output)"
    return {
        "raw": first_line,
        "target": target.group(1) if target else "(unknown)",
        "full": text,
    }


def get_macros(clang_path, lang):
    """Dump predefined macros for a given language mode (c / c++)."""
    try:
        p = run(
            [clang_path, "-dM", "-E", "-x", lang, "-"],
            input="",
        )
    except FileNotFoundError:
        return {}
    macros = {}
    for line in p.stdout.splitlines():
        m = re.match(r"#define\s+(\S+)(?:\s+(.*))?$", line)
        if m:
            macros[m.group(1)] = (m.group(2) or "").strip()
    return macros


def diff_macros(a, b):
    only_a = {k: a[k] for k in a.keys() - b.keys()}
    only_b = {k: b[k] for k in b.keys() - a.keys()}
    changed = {
        k: (a[k], b[k]) for k in a.keys() & b.keys() if a[k] != b[k]
    }
    return only_a, only_b, changed


def section(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def print_macro_dict(d, limit=400):
    if not d:
        print("  (none)")
        return
    for i, (k, v) in enumerate(sorted(d.items())):
        if i >= limit:
            print(f"  ... ({len(d) - limit} more, truncated)")
            break
        print(f"  {k} = {v}" if v else f"  {k}")


def print_changed(d, limit=400):
    if not d:
        print("  (none)")
        return
    for i, (k, (va, vb)) in enumerate(sorted(d.items())):
        if i >= limit:
            print(f"  ... ({len(d) - limit} more, truncated)")
            break
        print(f"  {k}:  A={va!r}   B={vb!r}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("clang_a", nargs="?", default=DEFAULT_A)
    ap.add_argument("clang_b", nargs="?", default=DEFAULT_B)
    ap.add_argument("--lang", default="c,c++",
                     help="comma-separated language modes to probe")
    args = ap.parse_args()

    langs = [s.strip() for s in args.lang.split(",") if s.strip()]

    section("Compiler A")
    print(f"Path: {args.clang_a}")
    va = get_version_info(args.clang_a)
    if va is None:
        sys.exit(f"ERROR: could not execute {args.clang_a!r}")
    print(va["raw"])
    print(f"Target: {va['target']}")

    section("Compiler B")
    print(f"Path: {args.clang_b}")
    vb = get_version_info(args.clang_b)
    if vb is None:
        sys.exit(f"ERROR: could not execute {args.clang_b!r}")
    print(vb["raw"])
    print(f"Target: {vb['target']}")

    same_target = va["target"] == vb["target"]
    section("Verdict")
    if same_target:
        print("Same target triple -- any macro/codegen differences below")
        print("are attributable to the actual compiler version/build.")
    else:
        print("DIFFERENT target triples (ABI) -- expect large, mostly")
        print("ABI-driven differences below. This is not a '22.1.8 added")
        print("feature X' situation; it's two different toolchains.")

    for lang in langs:
        macros_a = get_macros(args.clang_a, lang)
        macros_b = get_macros(args.clang_b, lang)
        only_a, only_b, changed = diff_macros(macros_a, macros_b)

        section(f"[{lang}] Key identity / ABI macros")
        for key in KEY_MACROS:
            in_a = key in macros_a
            in_b = key in macros_b
            if not in_a and not in_b:
                continue
            va_ = macros_a.get(key, "<undefined>")
            vb_ = macros_b.get(key, "<undefined>")
            flag = "  <-- differs" if va_ != vb_ else ""
            print(f"  {key:24s} A={va_!s:<14} B={vb_!s:<14}{flag}")

        section(f"[{lang}] Macros only defined by A ({len(only_a)})")
        print_macro_dict(only_a)

        section(f"[{lang}] Macros only defined by B ({len(only_b)})")
        print_macro_dict(only_b)

        section(f"[{lang}] Macros defined by both, different value ({len(changed)})")
        print_changed(changed)


if __name__ == "__main__":
    main()
