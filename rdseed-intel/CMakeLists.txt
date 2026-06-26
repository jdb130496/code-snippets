cmake_minimum_required(VERSION 3.30)  # gil_disabled (free-threaded) ABI detection
project(hwrng LANGUAGES C)

# Development.Module (not the full Development component) is enough to
# build an extension module -- it doesn't require linking against
# libpython, which matters on Linux and keeps this portable.
find_package(Python COMPONENTS Interpreter Development.Module REQUIRED)

# WITH_SOABI tags the output filename with the interpreter's ABI
# (e.g. hwrng.cp314-win_amd64.pyd vs hwrng.cp314t-win_amd64.pyd for the
# free-threaded build) -- this is what lets the two builds coexist and
# matches what the C source already handles via Py_GIL_DISABLED.
Python_add_library(hwrng MODULE rdseed-intel.c WITH_SOABI)

# Mirrors the old build_ext_with_rdseed_flag logic: GCC/Clang gate the
# RDSEED intrinsics behind -mrdseed; MSVC exposes them unconditionally
# on x64 via <immintrin.h>, so it must NOT get this flag.
if(NOT MSVC)
    target_compile_options(hwrng PRIVATE -mrdseed)
endif()

install(TARGETS hwrng DESTINATION .)
