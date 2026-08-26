markdown
# hwrng

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

---

# Building hwrng

> **Test coverage disclaimer**: This build has been tested exclusively on
> Windows using PowerShell with the `use-clang-win` toolchain alias,
> standalone meson (built from git source), and standalone ninja (built
> from git source). MSYS2, Linux, and macOS build paths are documented
> for reference but have not been verified by the author — use them at
> your own risk.

---

## Requirements

- Python 3.13+
- x86_64 CPU with RDSEED support (Intel Broadwell 2014+ / AMD Zen+)
- Standalone LLVM Clang at `D:\Programs\clang`
- Standalone Ninja built from git source at `D:\Programs\ninja\bin\ninja.exe`
- Standalone Meson built from git source at `D:\Programs\meson`
- PowerShell profile with toolchain aliases loaded (`use-clang-win`)
- `meson-python` pip package (the only pip-required build component)

---

## Windows — Standalone Clang + Meson + Ninja via PowerShell (tested)

### How the tool chain fits together

pip install .
→ calls mesonpy (meson-python) ← pip package, bridges pip and meson
→ calls meson-win (standalone) ← D:\Programs\meson, built from git
→ calls ninja-win (standalone)← D:\Programs\ninja, built from git
→ calls clang-cl-win ← D:\Programs\clang\bin\clang-cl.exe


`meson-python` is the only component that must come from pip — there is no
standalone alternative. Everything else (meson, ninja, clang) is your
standalone installation driven by the PowerShell profile.

### Why `--no-build-isolation`

Without this flag, pip creates an isolated build environment and downloads
its own copies of meson and ninja from PyPI, completely ignoring your
standalone tools. `--no-build-isolation` forces pip to use whatever meson
and ninja are active in PATH — which are your standalone builds via the
profile's `Get-WinNinja` and `Get-WinMeson` resolvers.

### What `meson.build` does with clang-cl

`meson.build` detects `clang-cl` via `cc.get_id() == 'clang-cl'` and applies:

/arch:AVX2 — MSVC-style vectorisation tier
/clang:-mrdseed — passes -mrdseed through clang-cl frontend,
sets RDSEED so immintrin.h exposes _rdseed64_step
/O2 — optimisation
-DPy_LIMITED_API — stable ABI, computed from Python version at build time


Note: `/arch:AVX2` alone is not sufficient for clang-cl — `/clang:-mrdseed`
is required explicitly. Pure MSVC (`cl.exe`) does not need this because
`/arch:AVX2` implicitly covers RDSEED there.

### Build steps

```powershell
# 1. Activate clang-win toolchain
use-clang-win

# 2. Confirm standalone tools are active
clang-win --version    # D:\Programs\clang\bin\clang.exe
ninja-win --version    # D:\Programs\ninja\bin\ninja.exe
meson-win --version    # D:\Programs\meson\meson.cmd or meson.pyz

# 3. Install meson-python (only pip-required piece)
pip show meson-python  # check if already installed
pip install meson-python  # install if missing

# 4. Clean any stale build artifacts
cd path\to\hwrng
Remove-Item -Recurse -Force build -ErrorAction SilentlyContinue

# 5. Build — no editable flag, no build isolation
pip install . --no-build-isolation

# 6. Verify
python -c "import hwrng; print(hwrng.has_rdseed()); print(hwrng.rdseed_raw_bytes(16).hex())"
```

Expected output: `True` followed by 32 hex characters.

---

## Important — never use editable installs

Do NOT use `pip install -e .` for normal use. Editable installs cause
meson to attempt a full recompile on every `import hwrng`. This fails
whenever the build toolchain is not active in PATH — for example when
running from Spyder, PyCharm, or any IDE that does not load your
PowerShell profile.

Symptom of an editable install problem:

ImportError: re-building the hwrng meson-python editable wheel package failed


Fix:
```powershell
pip uninstall hwrng
pip install . --no-build-isolation
```

---

## Updating standalone meson and ninja

Your PowerShell profile includes `Get-WinNinja -Update` and
`Get-WinMeson -Update` functions that rebuild from git source automatically:

```powershell
# Update ninja (rebuilds from D:\dev\ninja-src using clang-cl)
Get-WinNinja -Update

# Update meson (rebuilds zipapp from D:\dev\meson-src)
Get-WinMeson -Update
```

After updating either, rebuild hwrng:
```powershell
pip uninstall hwrng
pip install . --no-build-isolation
```

---

## MSYS2 / Linux / macOS (untested)

These platforms are not covered by the author's test matrix. The
`meson.build` has compiler branches for GCC, Apple Clang, and MSYS2
MinGW that should work in principle — refer to the original upstream
documentation or raise an issue if you attempt these builds.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `re-building editable wheel failed` on import | Editable install, toolchain not in PATH | `pip uninstall hwrng && pip install . --no-build-isolation` |
| `meson compile` fails | `use-clang-win` not activated | Run `use-clang-win` in PowerShell first |
| Wrong meson/ninja used | Build isolation active | Always pass `--no-build-isolation` |
| `_rdseed64_step` not found | `/clang:-mrdseed` missing | Should be automatic via `meson.build` clang-cl branch |
| Import works in PowerShell but fails in Spyder/PyCharm | Editable install | Reinstall without `-e` flag |
| AMD Zen 5 `UserWarning` at import | Known CPU bug, not a code error | Update CPU microcode (Oct 2025 fix) |
