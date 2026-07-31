import csv
import shutil
import os

SOURCE = r"D:\OneDrive - 0yt2k"
TARGET = r"D:\Onedrive Backup"
CSV_FILE = r"D:\dev\diff-result-sorted.csv"

def is_git_related(path):
    return ".git" in path.split(os.sep) or ".git" in path.split("/")

def main():
    copied, deleted, skipped = [], [], []

    with open(CSV_FILE, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        rel_path = row['Path']
        status = row['Status'].strip()

        if is_git_related(rel_path):
            skipped.append(rel_path)
            continue

        src_path = os.path.join(SOURCE, rel_path)
        dst_path = os.path.join(TARGET, rel_path)

        if status.startswith("Changed") or status.startswith("Added"):
            if os.path.exists(src_path):
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                try:
                    shutil.copy2(src_path, dst_path)
                    copied.append(rel_path)
                except Exception as e:
                    print(f"ERROR copying '{rel_path}': {e}")
            else:
                print(f"WARNING: source file missing, cannot copy: {src_path}")

        elif status.startswith("Deleted"):
            if os.path.exists(dst_path):
                try:
                    os.remove(dst_path)
                    deleted.append(rel_path)
                except Exception as e:
                    print(f"ERROR deleting '{rel_path}': {e}")
            else:
                print(f"NOTE: target file already absent: {dst_path}")

        else:
            print(f"WARNING: unknown status '{status}' for '{rel_path}'")

    print("\n----- SUMMARY -----")
    print(f"Copied/Updated: {len(copied)}")
    print(f"Deleted:        {len(deleted)}")
    print(f"Skipped (.git): {len(skipped)}")

    print("\nSkipped .git-related paths:")
    for p in skipped:
        print(f"  {p}")

if __name__ == "__main__":
    main()
