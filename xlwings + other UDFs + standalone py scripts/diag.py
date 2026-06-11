import ctypes, os

MSYS2_BIN = r"D:\Programs\msys64\ucrt64\bin"
os.add_dll_directory(MSYS2_BIN)
lib = ctypes.CDLL(r"D:\Programs\pcre2-gcc\bin\libpcre2-8.dll")

# Dump all exported symbols containing "next" or "match"
import subprocess
result = subprocess.run(
    ['dumpbin', '/exports', r'D:\Programs\pcre2-gcc\bin\libpcre2-8.dll'],
    capture_output=True, text=True
)
if result.returncode != 0:
    # dumpbin not available, try objdump from MSYS2
    result = subprocess.run(
        [r'D:\Programs\msys64\ucrt64\bin\objdump.exe', '-p',
         r'D:\Programs\pcre2-gcc\bin\libpcre2-8.dll'],
        capture_output=True, text=True
    )
for line in result.stdout.splitlines():
    if 'match' in line.lower() or 'next' in line.lower():
        print(line)
