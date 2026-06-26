"""
Build script for hwrng.

Compiler-flag note
-------------------
MSVC exposes _rdseed64_step via <immintrin.h> unconditionally on x64 — no
extra compiler switch needed.

GCC and Clang gate the RDSEED intrinsics behind target-feature attributes.
Without -mrdseed, _rdseed64_step is undeclared and the build fails with a
hard compile error (not a silent miscompile) on Linux *and* on MSYS2/
MinGW-w64, since both use the GCC/Clang front end. We add -mrdseed only
when the active compiler is not MSVC.

Free-threaded Python (3.13+/3.14 python3.14t, 3.15 python3.15t) note
---------------------------------------------------------------------
The free-threaded build uses its own ABI (tagged e.g. cp314t vs cp314) and
is a SEPARATE build of the extension from the normal GIL-enabled build —
running `setup.py build_ext --inplace` under a regular `python3.14` will
not produce something importable from `python3.14t`, and vice versa. If
you need both, run this build once under each interpreter. The C source
itself (rdseed-intel.c) handles both automatically via the Py_GIL_DISABLED
guard at the bottom of PyInit_hwrng — no source changes are needed between
the two builds, only running setup.py under the right interpreter.
"""

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext


class build_ext_with_rdseed_flag(build_ext):
    def build_extensions(self):
        # Verified against setuptools._distutils.ccompiler.compiler_class:
        # the only registered types are 'unix' (native gcc/clang on Linux/
        # macOS), 'msvc' (cl.exe), 'mingw32' (MSYS2/MinGW-w64 gcc), and
        # 'cygwin'. Every non-MSVC type here is a GCC/Clang front end, so
        # all of them need -mrdseed; only 'msvc' must not get it.
        compiler_type = self.compiler.compiler_type
        for ext in self.extensions:
            if compiler_type != "msvc":
                ext.extra_compile_args = list(ext.extra_compile_args or []) + ["-mrdseed"]
        super().build_extensions()


hwrng_ext = Extension(
    name="hwrng",
    sources=["rdseed-intel.c"],
    # extra_compile_args populated per-compiler in build_ext_with_rdseed_flag
)

setup(
    name="hwrng",
    version="0.1.0",
    description="Direct RDSEED hardware RNG for x86_64 (Windows / MSYS2 / Linux)",
    ext_modules=[hwrng_ext],
    cmdclass={"build_ext": build_ext_with_rdseed_flag},
    python_requires=">=3.8",
)
