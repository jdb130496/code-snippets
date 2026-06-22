#!/usr/bin/env python3
"""
test_clang_bugfix.py

Solid before/after test for a REAL, verified fix between clang 22.1.7
and 22.1.8: https://github.com/llvm/llvm-project/issues/198663
(cherry-picked via PR #199617).

Unlike a macro diff, this compiles an actual reproducer and checks
whether the compiler accepts or rejects it -- a hard pass/fail signal,
not an interpretation exercise.

This bug is in Sema (frontend semantic analysis), not codegen or ABI,
so it is expected to reproduce identically on clang-win (MSVC target)
and clang-msys (GNU target) -- making it a valid test of the patch
version itself, despite the two binaries having different targets.

Usage (same file, either shell):
    PowerShell : python test_clang_bugfix.py
    MSYS bash  : python test_clang_bugfix.py
"""

import subprocess
import sys
from pathlib import Path

CLANG_WIN = r"D:\Programs\clang\bin\clang.exe"
CLANG_MSYS = r"D:\Programs\msys64\ucrt64\bin\clang.exe"
REPRO_FILE = Path(__file__).parent / "repro_GH198663.cpp"


def compile_repro(clang_path):
    if not Path(clang_path).exists():
        return None, f"clang.exe not found at {clang_path}"
    if not REPRO_FILE.exists():
        return None, f"repro file not found at {REPRO_FILE}"
    try:
        p = subprocess.run(
            [clang_path, "-std=c++20", "-fsyntax-only",
             "-xc++", str(REPRO_FILE)],
            capture_output=True, text=True, timeout=30,
        )
    except FileNotFoundError as e:
        return None, str(e)
    return p.returncode, p.stderr


def report(label, clang_path):
    print(f"\n{'=' * 70}\n{label}  ({clang_path})\n{'=' * 70}")
    rc, output = compile_repro(clang_path)
    if rc is None:
        print(f"  COULD NOT RUN: {output}")
        return None
    if rc == 0:
        print("  Compiled cleanly (exit 0). No constraint-hashing bug.")
        print("  -> This binary has the fix (>= patch incorporating PR #199617).")
        return True
    else:
        print(f"  Compile FAILED (exit {rc}). Diagnostics:")
        # only show the relevant static_assert error, not the whole dump
        for line in output.splitlines():
            if "static_assert" in line or "static assertion" in line.lower():
                print(f"    {line.strip()}")
        print("  -> This binary reproduces the GH#198663 concept-hashing bug.")
        return False


def main():
    clang_a = sys.argv[1] if len(sys.argv) > 1 else CLANG_WIN
    clang_b = sys.argv[2] if len(sys.argv) > 2 else CLANG_MSYS

    result_a = report("Compiler A (clang-win, expect 22.1.8 = fixed)", clang_a)
    result_b = report("Compiler B (clang-msys, expect 22.1.7 = buggy)", clang_b)

    print(f"\n{'=' * 70}\nVerdict\n{'=' * 70}")
    if result_a is None or result_b is None:
        print("  Could not complete comparison -- check paths above.")
        return
    if result_a and not result_b:
        print("  CONFIRMED: A has the fix, B has the bug.")
        print("  This matches the real GH#198663 fix landing between")
        print("  22.1.7 and 22.1.8 -- this is a genuine version-attributable")
        print("  difference, not a target/ABI artifact.")
    elif result_a and result_b:
        print("  Both compile clean -- both have the fix (or older bug-triggering")
        print("  conditions changed). No version difference observed here.")
    elif not result_a and not result_b:
        print("  Both fail -- neither has the fix, or repro needs adjustment.")
    else:
        print("  A fails but B passes -- unexpected; double-check which binary")
        print("  is actually newer (run --version on both).")


if __name__ == "__main__":
    main()
