# code-snippets
Last updated: 04-09-2026 (dd-mm-yyyy)

Excel 365 new functions examples and explorations — includes interfaces to
Python, Java, JavaScript, C++, C, and Rust. Updated till 26-08-2026.
Interfaces to other languages (C / C++ / Java / Rust, etc.) are through
Python libraries as bridge.

New bash scripts and powershell scripts added. Powershell profile further enhanced and optimized.

All rdrand-related folders are builds based on a fork of:
https://github.com/stillson/rdrand (credit to the original author!)

## rdrand port notes
Original repository has been unmaintained for 4+ years. Key changes made to port
to Python 3.13+ on Windows:
- `_PyLong_FromByteArray` removed in Python 3.13 — replaced with `PyLong_FromNativeBytes`
- `distutils` removed in Python 3.12 — replaced with `setuptools`
- All sysconfig vars (`CC`, `CXX`, `AR`, `RANLIB`, `LDSHARED`, `LDCXXSHARED`,
  `CFLAGS`, `CCSHARED`, `SHLIB_SUFFIX`) are `None` on MSVC-built Python — patched in `setup.py`
- Tested on Python 3.14.6 (MSC v.1944 64 bit AMD64) with portable LLVM/Clang
- Requires Intel/AMD CPU with RDRAND/RDSEED support (Ivy Bridge / Zen or later)
- `getrandbits(k)` returns negative values for large k due to signed integer
  handling in C extension — mask with `& ((1 << k) - 1)` if needed

Different build flavours available in separate subfolders — each has its own
README explaining requirements and build steps.

## hwrng alternative
As an alternative to rdrand, a hwrng Python library is included with C API source
and build files. A Meson build system variant is also provided which does not
require scikit-build-core — see the folder documentation for details and usage examples.
