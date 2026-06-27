# hwrng

Below are features, methods to build this library on veraious OSs. I have tested that it built clearly on Windows, msys (python virtual environment pointing to windows python), msys (python virtual environment pointing to msys ucrt64 python) and fedora rawhide (python 3.15.0b3). Further tested it's working using some examples. One is attached here.

Python C extension exposing Intel/AMD `RDSEED` directly — raw CPU thermal noise,
no OS entropy pool, no CSPRNG conditioning.

x86_64 only. ARM is not supported and fails at build time with a clear message.

## Usage

```python
import hwrng

if not hwrng.has_rdseed():
    raise RuntimeError("CPU does not support RDSEED")

entropy = hwrng.rdseed_raw_bytes(64)
print(entropy.hex())
```

`n_bytes` must be a positive multiple of 8. Maximum 1 MB per call.

### AMD Zen 5

A known Zen 5 bug (Oct 2025) returns `0` with the success flag set when the
entropy pool is exhausted. This library retries on zero output and raises a
`UserWarning` at import time on affected hardware. Update CPU microcode to fix
at the hardware level.

## Requirements

- x86_64 CPU with RDSEED (Intel Broadwell 2014+, AMD Zen 2019+)
- Python 3.14+
- C compiler with `<immintrin.h>` support

## Building from source

### Linux

```bash
# Debian/Ubuntu
sudo apt install python3-dev ninja-build

# Arch/Manjaro
sudo pacman -S python ninja meson

pip install meson-python meson
pip install -e . --no-build-isolation
```

### macOS (Intel only)

```bash
brew install ninja meson python@3.14
pip install meson-python
pip install -e . --no-build-isolation
```

### Windows — MSYS2 UCRT64

Produces a GCC-compiled `.pyd` against UCRT64 Python.

```bash
# 1. Install deps via pacman (open UCRT64 shell)
pacman -S mingw-w64-ucrt-x86_64-python \
           mingw-w64-ucrt-x86_64-gcc \
           mingw-w64-ucrt-x86_64-meson \
           mingw-w64-ucrt-x86_64-ninja

# 2. Create a dedicated venv (note: bin/ not Scripts/ — Linux convention)
/ucrt64/bin/python -m venv ~/venv-ucrt64
source ~/venv-ucrt64/bin/activate

# 3. Install build backend (--no-build-isolation uses pacman's meson+ninja)
pip install meson-python meson --no-build-isolation

# 4. Build
pip install -e . --no-build-isolation
```

> Don't install ninja via pip under MSYS2 — it fails to build against GCC 16.
> The pacman ninja is the right one.

### Windows — MSVC

Produces an MSVC-compiled `.pyd` against python.org Python.
Requires Visual Studio 2022 Build Tools with "Desktop development with C++".

```bat
python -m venv venv
venv\Scripts\activate
pip install meson-python meson ninja
pip install -e . --no-build-isolation
```

## Troubleshooting

**`externally-managed-environment` on MSYS2** — use a venv, don't pip-install into system Python.

**`Scripts/activate: No such file or directory` on MSYS2** — UCRT64 Python uses
`bin/activate`, not `Scripts/activate`.

**`RDSEED exhausted`** — reduce request size, increase `max_retries`, or add a
delay between calls. On Zen 5, update CPU microcode.


Examples for testing the basic working:

# Basic smoke test
python -c "import hwrng; print(hwrng.has_rdseed())"

# Entropy output
python -c "import hwrng; print(hwrng.rdseed_raw_bytes(64).hex())"

# Verify it's the UCRT64 build, not Windows venv
python -c "import hwrng, importlib.util; print(importlib.util.find_spec('hwrng').origin)"

## License

MIT
