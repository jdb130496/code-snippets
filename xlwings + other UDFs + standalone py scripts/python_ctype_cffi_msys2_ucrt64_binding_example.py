"""
compare_bindings.py
===================
Demonstrates three ways to interact with libclang from Python:
  1. python-clang  (mingw-w64-ucrt-x86_64-python-clang MSYS2 package)
  2. ctypes        (manual raw bindings)
  3. cffi          (manual C-declaration bindings)

All three parse the same inline C source and extract function names.

Requirements (UCRT64 MSYS2):
  pacman -S mingw-w64-ucrt-x86_64-python-clang
  pacman -S mingw-w64-ucrt-x86_64-python-cffi   # for cffi demo
"""

import os
import sys
import tempfile

# ── Path to libclang.dll in UCRT64 ──────────────────────────────────────────
#LIBCLANG_PATH = r"C:\msys64\ucrt64\bin\libclang.dll"
# Replace the hardcoded LIBCLANG_PATH line with:
import clang.cindex as cx
LIBCLANG_PATH = cx.conf.get_filename()   # points to the dll bundled by pip's libclang

# ── The C source we will parse in all three approaches ──────────────────────
C_SOURCE = """\
int add(int a, int b)          { return a + b; }
void greet(char* name)         { }
float multiply(float x, float y) { return x * y; }
"""

BANNER = "=" * 60

def section(title):
    print(f"\n{BANNER}")
    print(f"  {title}")
    print(BANNER)

def write_temp_c_file():
    """Write C_SOURCE to a temp file so parsers can read it from disk."""
    tmp = tempfile.NamedTemporaryFile(suffix=".c", delete=False, mode="w")
    tmp.write(C_SOURCE)
    tmp.flush()
    tmp.close()
    return tmp.name


# ════════════════════════════════════════════════════════════════════════════
# APPROACH 1 — python-clang  (MSYS2 package: mingw-w64-ucrt-x86_64-python-clang)
# ════════════════════════════════════════════════════════════════════════════
def demo_python_clang(c_file):
    section("APPROACH 1 — python-clang  (MSYS2 UCRT64 package)")
    print("  Package : mingw-w64-ucrt-x86_64-python-clang")
    print("  Under hood: wraps libclang via ctypes — but all done for you")
    print()

    try:
        import clang.cindex as cx
    except ImportError:
        print("  [SKIP] clang.cindex not found.")
        print("         Run: pacman -S mingw-w64-ucrt-x86_64-python-clang")
        return

    # Tell the binding where libclang.dll lives
    cx.Config.set_library_file(LIBCLANG_PATH)

    index = cx.Index.create()
    tu    = index.parse(c_file)

    print("  [python-clang] Call chain:")
    print("    cx.Index.create()         → Python object (Index)")
    print("    index.parse('test.c')     → Python object (TranslationUnit)")
    print("    tu.cursor.walk_preorder() → Python iterator of Cursor objects")
    print()
    print("  [python-clang] Functions found:")

    for node in tu.cursor.walk_preorder():
        if node.kind == cx.CursorKind.FUNCTION_DECL:
            print(f"    ✔ {node.result_type.spelling:8s}  {node.spelling}()")

    print()
    print("  [python-clang] No manual memory management needed — GC handles it.")


# ════════════════════════════════════════════════════════════════════════════
# APPROACH 2 — ctypes  (stdlib, no extra install needed)
# ════════════════════════════════════════════════════════════════════════════
def demo_ctypes(c_file):
    section("APPROACH 2 — ctypes  (Python stdlib, manual raw bindings)")
    print("  Package : built-in (no install)")
    print("  You must: declare every function signature yourself")
    print()

    import ctypes
    import ctypes.util

    if not os.path.exists(LIBCLANG_PATH):
        print(f"  [SKIP] libclang.dll not found at:\n         {LIBCLANG_PATH}")
        return

    lib = ctypes.CDLL(LIBCLANG_PATH)
    print("  [ctypes] Loaded DLL:", LIBCLANG_PATH)

    # ── You must manually declare EVERY function you want to call ───────────
    lib.clang_createIndex.restype  = ctypes.c_void_p
    lib.clang_createIndex.argtypes = [ctypes.c_int, ctypes.c_int]

    lib.clang_parseTranslationUnit.restype  = ctypes.c_void_p
    lib.clang_parseTranslationUnit.argtypes = [
        ctypes.c_void_p,   # CXIndex
        ctypes.c_char_p,   # source filename
        ctypes.c_void_p,   # command_line_args
        ctypes.c_int,      # num_command_line_args
        ctypes.c_void_p,   # unsaved_files
        ctypes.c_uint,     # num_unsaved_files
        ctypes.c_uint,     # options
    ]

    lib.clang_disposeTranslationUnit.argtypes = [ctypes.c_void_p]
    lib.clang_disposeIndex.argtypes           = [ctypes.c_void_p]

    print("  [ctypes] Call chain (raw):")
    print("    lib.clang_createIndex(0, 0)            → raw c_void_p (memory address)")
    print("    lib.clang_parseTranslationUnit(...)     → raw c_void_p (memory address)")
    print("    # To walk AST you need clang_visitChildren + a C callback — ~200 more lines")
    print()

    index  = lib.clang_createIndex(0, 0)
    tu_ptr = lib.clang_parseTranslationUnit(
        index,
        c_file.encode(),
        None, 0, None, 0, 0
    )

    print(f"  [ctypes] CXIndex  handle  = {index}   ← raw integer pointer")
    print(f"  [ctypes] CXTranslationUnit= {tu_ptr}  ← raw integer pointer")
    print()
    print("  [ctypes] Cannot easily walk AST here without 200+ more lines.")
    print("           You manage memory manually:")

    lib.clang_disposeTranslationUnit(tu_ptr)
    lib.clang_disposeIndex(index)

    print("    lib.clang_disposeTranslationUnit(tu_ptr)  ← manual free")
    print("    lib.clang_disposeIndex(index)             ← manual free")


# ════════════════════════════════════════════════════════════════════════════
# APPROACH 3 — cffi  (pacman -S mingw-w64-ucrt-x86_64-python-cffi)
# ════════════════════════════════════════════════════════════════════════════
def demo_cffi(c_file):
    section("APPROACH 3 — cffi  (manual C-declaration bindings)")
    print("  Package : mingw-w64-ucrt-x86_64-python-cffi")
    print("  You must: paste C header declarations as a string")
    print()

    try:
        from cffi import FFI
    except ImportError:
        print("  [SKIP] cffi not found.")
        print("         Run: pacman -S mingw-w64-ucrt-x86_64-python-cffi")
        return

    if not os.path.exists(LIBCLANG_PATH):
        print(f"  [SKIP] libclang.dll not found at:\n         {LIBCLANG_PATH}")
        return

    ffi = FFI()

    # ── You must paste C declarations as a raw string ────────────────────────
    ffi.cdef("""
        typedef void* CXIndex;
        typedef void* CXTranslationUnit;

        CXIndex clang_createIndex(int excludeDeclarationsFromPCH,
                                  int displayDiagnostics);

        CXTranslationUnit clang_parseTranslationUnit(
            CXIndex CIdx,
            const char *source_filename,
            const char *const *command_line_args,
            int num_command_line_args,
            void *unsaved_files,
            unsigned num_unsaved_files,
            unsigned options
        );

        void clang_disposeTranslationUnit(CXTranslationUnit);
        void clang_disposeIndex(CXIndex);
    """)

    lib = ffi.dlopen(LIBCLANG_PATH)
    print("  [cffi] Loaded DLL:", LIBCLANG_PATH)
    print("  [cffi] Call chain (typed cdata, not raw integers):")
    print("    lib.clang_createIndex(0, 0)         → <cdata 'void *'>")
    print("    lib.clang_parseTranslationUnit(...)  → <cdata 'void *'>")
    print("    # AST walking still needs manual clang_visitChildren binding")
    print()

    index  = lib.clang_createIndex(0, 0)
    tu_ptr = lib.clang_parseTranslationUnit(
        index,
        c_file.encode(),
        ffi.NULL, 0, ffi.NULL, 0, 0
    )

    print(f"  [cffi] CXIndex  handle   = {index}")
    print(f"  [cffi] CXTranslationUnit = {tu_ptr}")
    print()
    print("  [cffi] cffi gives typed cdata (safer than ctypes raw int),")
    print("         but you still manage memory and declare all signatures.")

    lib.clang_disposeTranslationUnit(tu_ptr)
    lib.clang_disposeIndex(index)

    print("    lib.clang_disposeTranslationUnit(tu_ptr)  ← manual free")
    print("    lib.clang_disposeIndex(index)             ← manual free")


# ════════════════════════════════════════════════════════════════════════════
# SUMMARY TABLE
# ════════════════════════════════════════════════════════════════════════════
def print_summary():
    section("SUMMARY — Key differences at a glance")
    rows = [
        ("Feature",            "python-clang",        "ctypes",             "cffi"),
        ("-" * 22,             "-" * 22,              "-" * 22,             "-" * 22),
        ("MSYS2 install",      "python-clang pkg",    "built-in stdlib",    "python-cffi pkg"),
        ("Signatures",         "pre-written for you", "you write each one", "you paste C headers"),
        ("Return values",      "Python objects",      "raw int pointers",   "typed cdata pointers"),
        ("AST traversal",      "walk_preorder() ✔",   "200+ lines needed",  "150+ lines needed"),
        ("Memory management",  "automatic (GC)",      "manual dispose*()",  "manual dispose*()"),
        ("Lines for task",     "~6 lines",            "200+ lines",         "150+ lines"),
        ("Under the hood",     "ctypes internally",   "direct DLL calls",   "direct DLL calls"),
    ]
    col = [24, 24, 24, 24]
    for row in rows:
        print("  " + "".join(str(v).ljust(col[i]) for i, v in enumerate(row)))
    print()


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    print(f"\n{'#' * 60}")
    print(f"#  libclang binding comparison: python-clang vs ctypes vs cffi")
    print(f"{'#' * 60}")
    print(f"\n  Parsing this C source:\n")
    for line in C_SOURCE.strip().splitlines():
        print(f"    {line}")

    c_file = write_temp_c_file()
    print(f"\n  Temp file: {c_file}")

    try:
        demo_python_clang(c_file)
        demo_ctypes(c_file)
        demo_cffi(c_file)
        print_summary()
    finally:
        os.unlink(c_file)
