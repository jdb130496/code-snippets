import sqlite3, os, re, shutil, time, sys

USERDATA_DIR    = r"D:\Programs\firefox-userdata"
BACKUP_ROOT     = r"D:\Programs\firefox-backups"
PREFS_JS        = os.path.join(USERDATA_DIR, "prefs.js")

def get_tampermonkey_uuid():
    with open(PREFS_JS, encoding="utf-8") as f:
        content = f.read()
    print(f"  prefs.js size: {len(content)} bytes")
    match = re.search(r'\\"firefox@tampermonkey\.net\\":\\"([a-f0-9-]+)\\"', content)
    if match:
        return match.group(1)
    raise RuntimeError("Tampermonkey UUID not found in prefs.js")

def get_scripts_dir(uuid):
    base = os.path.join(
        USERDATA_DIR, "storage", "default",
        f"moz-extension+++{uuid}^userContextId=4294967295",
        "idb"
    )
    if not os.path.exists(base):
        raise RuntimeError(f"IDB dir not found: {base}")
    for entry in os.listdir(base):
        if entry.endswith(".files"):
            return os.path.join(base, entry)
    raise RuntimeError(f"No .files dir found under {base}")

def export_scripts(scripts_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    exported = []
    for fname in sorted(os.listdir(scripts_dir)):
        if not fname.isdigit():
            continue
        fpath = os.path.join(scripts_dir, fname)
        try:
            with open(fpath, "rb") as f:
                raw = f.read()
        except PermissionError:
            print(f"  Skipping {fname} — permission denied")
            continue

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            text = raw.decode("utf-16-le")

        if "==UserScript==" not in text:
            print(f"  Skipping {fname} — not a userscript")
            continue

        name = f"script_{fname}"
        for line in text.splitlines():
            if "@name" in line:
                name = line.split("@name")[-1].strip()
                name = re.sub(r'[\\/*?:"<>|]', "_", name)
                break

        out_path = os.path.join(out_dir, f"{fname}_{name}.user.js")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        exported.append(out_path)
        print(f"  Exported: {name}")

    return exported

def backup_scripts(timestamp):
    out_dir = os.path.join(BACKUP_ROOT, f"tampermonkey_scripts_{timestamp}")
    print("Locating Tampermonkey scripts...")
    uuid = get_tampermonkey_uuid()
    print(f"  UUID: {uuid}")
    scripts_dir = get_scripts_dir(uuid)
    print(f"  Scripts dir: {scripts_dir}")
    exported = export_scripts(scripts_dir, out_dir)
    print(f"  Exported {len(exported)} scripts to {out_dir}")
    return out_dir

def backup_userdata(timestamp):
    backup_path = os.path.join(BACKUP_ROOT, f"firefox-userdata_{timestamp}")
    print(f"Backing up userdata to {backup_path} ...")

    def ignore_locks(dir, files):
        return [f for f in files if f == "parent.lock"]

    shutil.copytree(USERDATA_DIR, backup_path, ignore=ignore_locks)
    print("Userdata backup complete.")
    return backup_path

def prune_old_backups(prefixes=None):
    """Delete ALL previous backups for the given prefixes."""
    if prefixes is None:
        prefixes = ("firefox-userdata_", "tampermonkey_scripts_")
    if not os.path.exists(BACKUP_ROOT):
        print("  No backup folder found — nothing to prune.")
        return
    found_any = False
    for prefix in prefixes:
        entries = [
            e for e in os.listdir(BACKUP_ROOT)
            if e.startswith(prefix)
        ]
        if not entries:
            print(f"  No previous backups found for: {prefix}")
            continue
        for e in entries:
            full = os.path.join(BACKUP_ROOT, e)
            print(f"  Deleting old backup: {e}")
            shutil.rmtree(full, ignore_errors=True)
            found_any = True
    if not found_any:
        print("  No previous backups to prune — clean slate.")

if __name__ == "__main__":
    os.makedirs(BACKUP_ROOT, exist_ok=True)
    mode = sys.argv[1] if len(sys.argv) > 1 else "--all"
    timestamp = time.strftime("%Y%m%d_%H%M%S")  # one timestamp for both

    if mode in ("--all", "--scripts-only"):
        print("\n--- Pruning Old Script Backups ---")
        prune_old_backups(prefixes=("tampermonkey_scripts_",))

        print("\n--- Script Backup ---")
        try:
            backup_scripts(timestamp)
        except Exception as e:
            print(f"  WARNING: Script backup failed: {e}")

    if mode in ("--all", "--userdata-only"):
        print("\n--- Pruning Old Userdata Backups ---")
        prune_old_backups(prefixes=("firefox-userdata_",))

        print("\n--- Userdata Backup ---")
        try:
            backup_userdata(timestamp)
        except Exception as e:
            print(f"  WARNING: Userdata backup failed: {e}")

    print("\n=== Backup Complete ===")
