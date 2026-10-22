import subprocess, sys, shutil, os, time

def warp_connect():
    subprocess.run(["warp-cli", "connect"], capture_output=True)
    print("WARP connected.")
    time.sleep(3)

def warp_disconnect():
    subprocess.run(["warp-cli", "disconnect"], capture_output=True)
    print("WARP disconnected.")

ARIA2C_PATH = r"D:\Programs\msys64\ucrt64\bin\aria2c.exe"

def get_aria2c():
    if os.path.exists(ARIA2C_PATH):
        return ARIA2C_PATH
    found = shutil.which("aria2c")
    if found:
        return found
    return None

def disable_quick_edit():
    """Disable QuickEdit mode so clicking the console doesn't pause the process."""
    import ctypes
    try:
        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-10)  # STD_INPUT_HANDLE
        mode = ctypes.c_ulong()
        kernel32.GetConsoleMode(handle, ctypes.byref(mode))
        ENABLE_QUICK_EDIT = 0x0040
        ENABLE_EXTENDED_FLAGS = 0x0080
        new_mode = (mode.value & ~ENABLE_QUICK_EDIT) | ENABLE_EXTENDED_FLAGS
        kernel32.SetConsoleMode(handle, new_mode)
    except Exception:
        pass  # Non-Windows or no console — silently skip

def download_file(url, folder):
    os.makedirs(folder, exist_ok=True)
    filename = url.rstrip("/").split("/")[-1] or "downloaded_file"
    aria2c = get_aria2c()
    if not aria2c:
        print(f"aria2c not found — checked PATH and {ARIA2C_PATH}")
        sys.exit(1)
    print(f"Using aria2c: {aria2c}")
    disable_quick_edit()
    proc = subprocess.Popen([
        aria2c,
        "--split=4", "--max-connection-per-server=4",
        "--min-split-size=10M", "--file-allocation=none",
        "--max-tries=5", "--retry-wait=3",
        "--dir", folder, "--out", filename,
        "--console-log-level=notice", "--summary-interval=5",
        url
    ])
    proc.wait()
    if proc.returncode != 0:
        print(f"aria2c failed (exit {proc.returncode}).")
    else:
        print(f"Download complete: {os.path.join(folder, filename)}")
        
def git_clone(url, folder):
    os.makedirs(folder, exist_ok=True)
    print(f"Cloning {url} into {folder} ...")
    result = subprocess.run(["git", "clone", url, folder])
    if result.returncode == 0:
        print(f"Clone complete: {folder}")
    else:
        print("git clone failed.")

def main():
    raw = input("Enter URL (or 'git clone <url>'): ").strip()
    folder = input("Enter destination folder: ").strip()

    is_clone = raw.lower().startswith("git clone ")
    url = raw[len("git clone "):].strip() if is_clone else raw

    if not url:
        print("No URL provided. Exiting.")
        sys.exit(1)

    warp_connect()
    try:
        if is_clone:
            git_clone(url, folder)
        else:
            download_file(url, folder)
    finally:
        warp_disconnect()
        print("Done.")

if __name__ == "__main__":
    main()
