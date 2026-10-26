"""
Python 3.14 -> 3.15 Transition Script
=======================================
WORKFLOW:
  1. Run BEFORE uninstalling 3.14 to back up packages:
         D:\\Programs\\Python\\python.exe python-transition.py --backup

  2. Uninstall Python 3.14, install Python 3.15 at D:\\Programs\\Python

  3. Run AFTER installing 3.15 to restore packages:
         D:\\Programs\\Python\\python.exe python-transition.py --restore
"""

import subprocess
import sys
import os
import json
import argparse
from datetime import datetime
from pathlib import Path


# ── Configuration ─────────────────────────────────────────────────────────────

PYTHON      = r"D:\Programs\Python\python.exe"
BACKUP_DIR  = Path("py_backup")
MAX_RETRIES = 3
PIP_TIMEOUT = 120


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(cmd, timeout=PIP_TIMEOUT):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.returncode, result.stdout, result.stderr

def pip(*args):
    return run([PYTHON, "-m", "pip", *args])

def section(title):
    print(f"\n{'─' * 60}\n  {title}\n{'─' * 60}")

def color(text, code):
    return f"\033[{code}m{text}\033[0m"

ok  = lambda t: color(t, "32")
err = lambda t: color(t, "31")
wrn = lambda t: color(t, "33")
inf = lambda t: color(t, "36")


# ── Backup ────────────────────────────────────────────────────────────────────

def do_backup():
    section("Backing up installed packages from D:\\Programs\\Python")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    # Full freeze — used for restore
    code, out, errtxt = pip("freeze")
    if code != 0:
        print(err(f"  pip freeze failed: {errtxt}"))
        sys.exit(1)

    req_path = BACKUP_DIR / "requirements.txt"
    req_path.write_text(out, encoding="utf-8")
    print(ok(f"  ✓ requirements.txt      → {req_path}"))

    # JSON metadata (names + versions, human-readable)
    code2, out2, _ = pip("list", "--format=json")
    if code2 == 0:
        meta_path = BACKUP_DIR / "packages_meta.json"
        meta_path.write_text(json.dumps(json.loads(out2), indent=2), encoding="utf-8")
        print(ok(f"  ✓ packages_meta.json    → {meta_path}"))

    # Top-level only (no transitive deps) — handy reference, not used for restore
    code3, out3, _ = pip("list", "--not-required", "--format=freeze")
    if code3 == 0:
        tl_path = BACKUP_DIR / "requirements_toplevel.txt"
        tl_path.write_text(out3, encoding="utf-8")
        print(ok(f"  ✓ requirements_toplevel → {tl_path}"))

    total = len([l for l in out.splitlines() if l.strip()])
    print(inf(f"\n  {total} packages backed up to: {BACKUP_DIR.resolve()}"))
    print(wrn("\n  You can now uninstall Python 3.14 and install Python 3.15"))
    print(wrn(f"  at the same path:  {PYTHON}"))
    print(wrn(f"\n  Then run:  python python-transition.py --restore"))

# ── Restore ───────────────────────────────────────────────────────────────────

def parse_requirements(path: Path) -> list[str]:
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    ]


def do_restore():
    section("Restoring packages into D:\\Programs\\Python")

    req_path = BACKUP_DIR / "requirements.txt"
    if not req_path.exists():
        print(err(f"  Backup not found: {req_path}"))
        print(err("  Run --backup first (with the old Python)."))
        sys.exit(1)

    packages = parse_requirements(req_path)
    if not packages:
        print(wrn("  requirements.txt is empty — nothing to install."))
        sys.exit(0)

    print(inf(f"  {len(packages)} packages to install from {req_path}"))

    pending   = list(packages)
    failed    = {}          # {pkg: last_error_line}
    installed = []

    for round_num in range(1, MAX_RETRIES + 1):
        if not pending:
            break

        label = "Initial pass" if round_num == 1 else f"Retry round {round_num - 1}"
        print(inf(f"\n  [{label}] — {len(pending)} package(s)"))

        next_pending = []

        for idx, pkg in enumerate(pending, 1):
            print(f"  [{idx:>3}/{len(pending)}] {pkg} … ", end="", flush=True)
            try:
                code, _, errtxt = pip(
                    "install", pkg,
                    "--force-reinstall",
                    "--prefer-binary",   # avoid source builds for packages not yet on 3.15
                )
            except subprocess.TimeoutExpired:
                code, errtxt = -1, "Timed out"

            if code == 0:
                print(ok("✓"))
                installed.append(pkg)
                failed.pop(pkg, None)
            else:
                last_line = errtxt.strip().splitlines()[-1] if errtxt.strip() else "unknown"
                print(wrn(f"✗  deferred — {last_line[:80]}"))
                next_pending.append(pkg)
                failed[pkg] = last_line

        pending = next_pending

    # ── Summary ───────────────────────────────────────────────────────────────
    section("Summary")
    print(f"  Total   : {len(packages)}")
    print(ok(f"  OK      : {len(installed)}"))

    if failed:
        print(err(f"  Failed  : {len(failed)}"))
        print()
        for pkg, reason in failed.items():
            print(err(f"    • {pkg}"))
            print(f"      {reason}")

        failed_path = BACKUP_DIR / "requirements_failed.txt"
        failed_path.write_text("\n".join(failed.keys()), encoding="utf-8")
        print()
        print(wrn(f"  Saved failed list → {failed_path}"))
        print(wrn(f"  Retry manually:  pip install -r {failed_path}"))
    else:
        print(ok("\n  All packages restored successfully! 🎉"))

    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.system("")

    parser = argparse.ArgumentParser()
    group  = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--backup",  action="store_true", help="Back up packages (run with 3.14)")
    group.add_argument("--restore", action="store_true", help="Restore packages (run with 3.15)")
    args = parser.parse_args()

    # Only check interpreter existence during backup.
    # During restore, 3.15 is already installed at the same path — no need to validate.
    if args.backup:
        if not Path(PYTHON).exists():
            print(err(f"\n  Python not found at: {PYTHON}"))
            sys.exit(1)
        code, ver_out, _ = run([PYTHON, "--version"])
        print(inf(f"\n  Interpreter : {PYTHON}"))
        print(inf(f"  Version     : {ver_out.strip()}"))
        do_backup()
    else:
        # Python 3.15 should be at the same path now — just run restore.
        # If it's missing the pip calls will fail and tell the user clearly.
        code, ver_out, _ = run([PYTHON, "--version"])
        print(inf(f"\n  Interpreter : {PYTHON}"))
        print(inf(f"  Version     : {ver_out.strip() or 'unknown'}"))
        do_restore()

if __name__ == "__main__":
    main()
