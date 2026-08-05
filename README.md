# code-snippets

Last updated: 05-08-2026 (dd-mm-yyyy)

Excel 365 new functions examples / explorations - includes interfaces of excel to 
python / java / java script / c++ / c / rust / standalone python scripts, etc. - 
updated till 01-08-2026 (dd-mm-yyyy).

Excel to other languages interfaces (C / C++ / Java / Rust, etc.) are through 
python libraries as bridge.

All rdrand related folders are builds based on fork from original repository: 
https://github.com/stillson/rdrand (credit to him always!)

## rdrand port notes

Original repository has been unmaintained for 4+ years. Key changes made to port 
to Python 3.13+ on Windows:

- `_PyLong_FromByteArray` removed in Python 3.13 — replaced with 
  `PyLong_FromNativeBytes`
- `distutils` removed in Python 3.12 — replaced with `setuptools`
- All sysconfig vars (`CC`, `CXX`, `AR`, `RANLIB`, `LDSHARED`, `LDCXXSHARED`, 
  `CFLAGS`, `CCSHARED`, `SHLIB_SUFFIX`) are `None` on MSVC-built Python — 
  patched in `setup.py`
- Tested on Python 3.14.6 (MSC v.1944 64 bit AMD64) with portable LLVM/Clang
- Requires Intel/AMD CPU with RDRAND/RDSEED support (Ivy Bridge / Zen or later)
- `getrandbits(k)` returns negative values for large k due to signed integer 
  handling in C extension — mask with `& ((1 << k) - 1)` if needed

Different build flavours available in separate subfolders — each has its own 
README explaining requirements and build steps.

## hwrng alternative

As an alternative to rdrand, hwrng python library added with source Python C API 
and build files. A meson build system variant is also provided which does not 
require scikit-build-core but requires other python packages for the meson system 
— see documentation in the folder for details and usage examples.

## General

Excel to other languages interfaces (C / C++ / Java / Rust, etc.) are through 
python libraries as bridge.

Replaced token - 01-07-2026
