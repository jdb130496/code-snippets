# Building hwrng

## Requirements

- Python 3.14+
- x86_64 CPU with RDSEED support (Intel Broadwell 2014+ / AMD Zen+)
- C compiler (GCC 4.9+, Clang 3.5+, or MSVC 2019+)

---

## Vanilla Windows / Linux / macOS

Standard pip install — pulls meson, ninja, meson-python from PyPI automatically:

```bash
pip install .
```

---

## MSYS2 (ucrt64)

### Background

PyPI's `ninja` wheel is built and linked against the standard Windows CRT.
Inside MSYS2's UCRT64 environment, this binary either fails outright or
triggers a from-source rebuild that can fail depending on the local
toolchain — it is not the correct binary for this environment regardless.

The reliable fix is to use a Ninja that is natively built against the
UCRT64 toolchain, and to make sure Meson's Python detection points at
the MSYS2 Python venv rather than any Windows Python that might also be
on PATH.

There are two ways to get a UCRT64-correct Ninja: install it via pacman,
or build it from source yourself. Both are documented below — pacman is
the fast path, building from source is useful if you want full control
or hit a pacman package issue.

### Step 1 — Create and activate an MSYS2-native Python venv

This must be a venv created using MSYS2's own Python
(`/ucrt64/bin/python`), not a Windows Python interpreter. Mixing the two
is what causes `meson.build`'s Python detection to silently pick up the
wrong interpreter and produce a broken build.

```bash
# from an MSYS2 UCRT64 shell — not a plain MSYS2 or MINGW32 shell
python -m venv ~/venv-ucrt64
source ~/venv-ucrt64/bin/activate
```

Verify you're in the right environment before continuing:

```bash
which python
python -c "import sys; print(sys.prefix)"
```

`which python` should resolve to `~/venv-ucrt64/bin/python`, and
`sys.prefix` should point inside that same venv directory — not
anywhere under `/c/Users/.../AppData/Local/Programs/Python` or similar.

### Step 2 — Get a UCRT64-native Ninja

**Option A — pacman (fastest):**

```bash
pacman -S mingw-w64-ucrt-x86_64-ninja
```

**Option B — build Ninja from source (verified working as of GCC 16.1.0 / Ninja 1.13.0):**

Download the `ninja` PyPI sdist and extract it, or clone the
[scikit-build/ninja-python-distributions](https://github.com/scikit-build/ninja-python-distributions)
repo with submodules. Either way you need the bundled `ninja-upstream/`
source tree.

```bash
# from the MSYS2 UCRT64 shell — confirm the right gcc is on PATH first
which gcc
gcc --version
# should resolve to /ucrt64/bin/gcc

cd path/to/ninja-1.13.0/ninja-upstream
cmake -B build -G "MSYS Makefiles"
cmake --build build --target ninja
```

Note: build only the `ninja` target, not the default `all` target. The
full build (including `ninja_test`) currently fails on recent GCC/UCRT
combinations due to an upstream `mkdtemp` redeclaration ambiguity in
`src/test.cc` — Ninja's own MinGW-compatibility shim conflicts with a
`mkdtemp()` that newer UCRT headers now declare natively. This does not
affect the actual `ninja.exe` binary, only the test suite. The active
Python venv has no bearing on this build, since Ninja's own CMakeLists.txt
does not invoke Python at all.

Verify the result is genuinely UCRT64-linked:

```bash
ldd build/ninja.exe
./build/ninja.exe --version
```

You should see `libgcc_s_seh-1.dll`, `libwinpthread-1.dll`, and
`libstdc++-6.dll` resolving from `/ucrt64/bin/`. Lines pointing to
`C:/WINDOWS/System32/` (`ntdll.dll`, `KERNEL32.DLL`, `ucrtbase.dll`)
are expected and correct — UCRT itself is a Windows OS component since
Windows 10, not something MSYS2 bundles separately. What matters is the
*absence* of `msvcrt.dll`, which would indicate a non-UCRT (mingw64
-style) build.

Make this build available on PATH, either by copying it or referencing
it directly:

```bash
cp build/ninja.exe /ucrt64/bin/ninja.exe   # only if not already provided by pacman
```

### Step 3 — Build and install hwrng

With `venv-ucrt64` active and a working UCRT64 Ninja in place:

```bash
cd /path/to/hwrng
pip install meson meson-python --no-build-isolation
pip install . --no-build-isolation
```

For active development, use an editable install so changes to
`hwrng.c` don't require a full reinstall each time:

```bash
pip install -e . --no-build-isolation
```

### Step 4 — Verify

```bash
python -c "import hwrng; print(hwrng.has_rdseed()); print(hwrng.rdseed_raw_bytes(16).hex())"
```

Expected output: `True` followed by 32 hex characters. The resulting
wheel filename should carry the tag `mingw_x86_64_ucrt_gnu` — for
example:

```
hwrng-1.0.0-cp314-cp314-mingw_x86_64_ucrt_gnu.whl
```

If you instead see a `win_amd64` tag, the venv or Ninja in use is not
the UCRT64-native one — re-check Step 1 and Step 2 before proceeding.

On AMD Zen 5 CPUs, an `import`-time `UserWarning` about a known RDSEED
zero-return bug is expected behavior, not an error.

---

## Windows with Standalone LLVM Clang (no MSVC)

Install LLVM from https://releases.llvm.org and ensure clang is on PATH.

```bash
pip install .
```

`meson.build` detects standalone Clang (not clang-cl) and applies
GCC-compatible flags (`-mrdseed`, `-msse2`) automatically.

---

## macOS (Intel only)

Apple Silicon (M1/M2/M3) is not supported — RDSEED is an x86 instruction.
The RDSEED availability check in `meson.build` will fail with a clear
error on ARM.

```bash
pip install .
```

---

## Troubleshooting Summary

| Symptom | Likely cause | Fix |
|---|---|---|
| `pip install ninja` fails building from source on MSYS2 | PyPI ninja wheel targets Windows CRT, not UCRT | Use pacman or self-built Ninja (Step 2) |
| Wheel tag shows `win_amd64` instead of `mingw_x86_64_ucrt_gnu` | Wrong Python picked up — Windows Python instead of MSYS2 Python | Re-activate `venv-ucrt64`, recheck `sys.prefix` |
| `ninja_test` fails to compile with `mkdtemp` ambiguity | Newer UCRT headers now declare `mkdtemp()`, conflicting with Ninja's own shim | Build only the `ninja` target, skip `ninja_test` |
| `ldd build/ninja.exe` shows `msvcrt.dll` | Wrong shell used — not UCRT64 | Rebuild from the MSYS2 UCRT64 shell specifically |
