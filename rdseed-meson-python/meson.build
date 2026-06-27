project('hwrng', 'c',
    version: '1.0.0',
    default_options: ['warning_level=2']
)

py = import('python').find_installation(pure: false)
cc = meson.get_compiler('c')
host = host_machine.system()

# ── Compiler flags ────────────────────────────────────────────────────────────
if cc.get_id() == 'msvc' or cc.get_id() == 'clang-cl'
    # Windows MSVC or clang-cl frontend
    rdseed_args = ['/arch:AVX2', '/O2', '/DPy_LIMITED_API=0x030e0000']

elif host == 'darwin'
    # macOS — Apple Clang requires explicit march for RDSEED
    # This will correctly fail on Apple Silicon (arm64) at the
    # rdseed_check below — clean error before anything is built
    rdseed_args = [
        '-mrdseed', '-msse2', '-O2',
        '-march=native',              # Apple Clang needs this for intrinsics
        '-DPy_LIMITED_API=0x030e0000'
    ]

else
    # Linux GCC/Clang, MSYS2 MinGW
    rdseed_args = ['-mrdseed', '-msse2', '-O2', '-DPy_LIMITED_API=0x030e0000']
endif

# ── Verify RDSEED intrinsic compiles ─────────────────────────────────────────
# On Apple Silicon this will fail here with a clear message
# On unsupported Linux targets same
rdseed_check = cc.compiles(
    '''
    #include <immintrin.h>
    int main(void) {
        unsigned long long val;
        return _rdseed64_step(&val) ? 0 : 1;
    }
    ''',
    args: rdseed_args,
    name: 'RDSEED intrinsic available'
)

if not rdseed_check
    error('''
RDSEED intrinsic not available.
  On Apple Silicon (M1/M2/M3): RDSEED is an x86 instruction — not supported on ARM.
  On Intel Mac: ensure Xcode Command Line Tools are up to date.
  On Linux: compile with GCC 4.9+ or Clang 3.5+.
''')
endif

# ── Platform link args ────────────────────────────────────────────────────────
# Windows: must link python3.lib (stable ABI stub)
# Linux / macOS: no explicit python link — resolved from interpreter at load time
if cc.get_id() == 'msvc' or cc.get_id() == 'clang-cl'
    py_link_args = [
        '/LIBPATH:' + py.get_path('data') / 'libs',
        'python3.lib',
    ]
else
    py_link_args = []
endif

# ── Build extension ───────────────────────────────────────────────────────────
# py.extension_module handles correct filename per platform:
#   Windows:  hwrng.cp314-win_amd64.pyd
#   Linux:    hwrng.cpython-314-x86_64-linux-gnu.so
#   macOS:    hwrng.cpython-314-darwin.so
#   MSYS2:    hwrng.cp314-win_amd64.pyd
#
# limited_api:'3.14' — links python3.lib on Windows, tags .abi3 for distribution
py.extension_module('hwrng',
    'hwrng.c',
    c_args: rdseed_args,
    link_args: py_link_args,
    limited_api: '3.14',
    install: true,
)
