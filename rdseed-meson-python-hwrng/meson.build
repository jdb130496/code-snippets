project('hwrng', 'c',
    version: '1.0.0',
    default_options: ['warning_level=2']
)

py = import('python').find_installation(pure: false)
cc = meson.get_compiler('c')
host = host_machine.system()

# ── Py_LIMITED_API: computed from the Python being built against ──────────────
# Meson dicts require string keys; minor version is converted to string for lookup.
# Maps Python minor (decimal) → two-digit hex byte for the ABI constant.
# e.g. 3.14 → minor '14' → '0e' → '0x030e0000'
#      3.15 → minor '15' → '0f' → '0x030f0000'
_py_ver_parts = py.language_version().split('.')
_py_maj       = _py_ver_parts[0].to_int()
_py_min_dec   = _py_ver_parts[1]          # keep as string — used as dict key
_hex_map = {
    '13': '0d', '14': '0e', '15': '0f',
    '16': '10', '17': '11', '18': '12', '19': '13', '20': '14',
}
if not _hex_map.has_key(_py_min_dec)
    error('Unsupported Python minor version @0@ — add it to _hex_map in meson.build'.format(_py_min_dec))
endif
_py_min_hex        = _hex_map[_py_min_dec]
py_limited_api_hex = '0x03' + _py_min_hex + '0000'
py_limited_api_def = '-DPy_LIMITED_API=' + py_limited_api_hex
py_limited_api_str = _py_maj.to_string() + '.' + _py_min_dec

message('Building for Python @0@ — Py_LIMITED_API = @1@'.format(
    py.language_version(), py_limited_api_hex))

# ── Compiler flags ────────────────────────────────────────────────────────────
if cc.get_id() == 'msvc'
    # Pure MSVC cl.exe: /arch:AVX2 covers the instruction set tier.
    # RDSEED is implicitly available via immintrin.h under AVX2.
    rdseed_args = ['/arch:AVX2', '/O2', py_limited_api_def]

elif cc.get_id() == 'clang-cl'
    # clang-cl (your clang-win alias: D:\Programs\clang\bin\clang-cl.exe).
    # /arch:AVX2 controls MSVC-style vectorisation tier but does NOT gate
    # individual intrinsics like _rdseed64_step — immintrin.h checks for
    # __RDSEED__ which is only set when -mrdseed is passed explicitly.
    # Use /clang: prefix to pass the flag through the MSVC-compatible frontend.
    rdseed_args = [
        '/arch:AVX2',
        '/clang:-mrdseed',    # enables __RDSEED__ → _rdseed64_step in immintrin.h
        '/O2',
        py_limited_api_def,
    ]

elif host == 'darwin'
    # macOS — Apple Clang requires explicit march for RDSEED.
    # This will correctly fail on Apple Silicon (arm64) at the
    # rdseed_check below — clean error before anything is built.
    rdseed_args = [
        '-mrdseed', '-msse2', '-O2',
        '-march=native',
        py_limited_api_def,
    ]

else
    # Linux GCC/Clang, MSYS2 MinGW
    rdseed_args = ['-mrdseed', '-msse2', '-O2', py_limited_api_def]
endif

# ── Verify RDSEED intrinsic compiles ─────────────────────────────────────────
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
  On Windows with clang-cl: /clang:-mrdseed must be in compiler flags
    (sets __RDSEED__ so immintrin.h exposes _rdseed64_step).
    /arch:AVX2 alone is not sufficient for clang-cl.
  On Apple Silicon (M1/M2/M3): RDSEED is an x86 instruction — not supported on ARM.
  On Intel Mac: ensure Xcode Command Line Tools are up to date.
  On Linux: compile with GCC 4.9+ or Clang 3.5+.
''')
endif

# ── Platform link args ────────────────────────────────────────────────────────
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
py.extension_module('hwrng',
    'hwrng.c',
    c_args: rdseed_args,
    link_args: py_link_args,
    limited_api: py_limited_api_str,   # e.g. '3.14' or '3.15' — derived above
    install: true,
)
