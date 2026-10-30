// hwrng: direct RDSEED hardware RNG for x86_64 (stable ABI).
// Py_LIMITED_API is injected by meson as -DPy_LIMITED_API=0x... (derived from
// the Python being built against). Do NOT define it here.
#include <Python.h>
#include <immintrin.h>
#include <stdint.h>
#include <string.h>

// 64-bit only: the 32-bit RDSEED form has the AMD Zen 5 zero-return bug.
#if !defined(__x86_64__) && !defined(_M_X64)
  #error "hwrng requires 64-bit x86_64 architecture"
#endif

// Requests up to this size skip the GIL release/reacquire, which costs more
// than the RDSEED calls themselves for small reads.
#define HWRNG_NOGIL_THRESHOLD 512
#define HWRNG_MAX_BYTES       (1024 * 1024)

// Compiler id, exposed as hwrng.__compiler__ (clang-cl also defines _MSC_VER,
// so __clang__ must be tested first).
#if defined(__clang__)
  #define HWRNG_CC "clang " __clang_version__
#elif defined(_MSC_VER)
  #define HWRNG_CC "msvc"
#else
  #define HWRNG_CC "other"
#endif

// ── CPUID (single implementation for both toolchains) ─────────────────────────

#if defined(_MSC_VER)            // MSVC and clang-cl
  #include <intrin.h>
  static void cpuid_raw(int leaf, int sub, unsigned int r[4]) {
      int i[4];
      __cpuidex(i, leaf, sub);
      r[0] = (unsigned int)i[0]; r[1] = (unsigned int)i[1];
      r[2] = (unsigned int)i[2]; r[3] = (unsigned int)i[3];
  }
#else                            // GCC / clang (GNU driver)
  #include <cpuid.h>
  static void cpuid_raw(int leaf, int sub, unsigned int r[4]) {
      __cpuid_count(leaf, sub, r[0], r[1], r[2], r[3]);
  }
#endif

static int detect_rdseed(void) {
    unsigned int r[4];
    cpuid_raw(0, 0, r);
    if (r[0] < 7) return 0;                  // leaf 7 not supported
    cpuid_raw(7, 0, r);
    return (int)((r[1] >> 18) & 1u);         // EBX bit 18 = RDSEED
}

static int detect_zen5(void) {
    unsigned int r[4];
    cpuid_raw(0, 0, r);
    // Vendor "AuthenticAMD": EBX="Auth", EDX="enti", ECX="cAMD"
    if (!(r[1] == 0x68747541u && r[3] == 0x69746E65u && r[2] == 0x444D4163u))
        return 0;
    cpuid_raw(1, 0, r);
    unsigned int base   = (r[0] >> 8)  & 0xFu;
    unsigned int ext    = (r[0] >> 20) & 0xFFu;
    unsigned int family = (base == 0xFu) ? base + ext : base;
    return family == 0x1Au;                  // AMD Zen 5
}

// Detected once at import; CPUID is slow (traps to the hypervisor in a VM).
static int g_has_rdseed = 0;

// ── Core fill loop (no Python API: safe with or without the GIL) ──────────────

static int fill_words(unsigned char *buf, Py_ssize_t n_words, int max_retries) {
    for (Py_ssize_t i = 0; i < n_words; i++) {
        unsigned long long val;              // exact type _rdseed64_step expects
        int ok = 0;
        for (int tries = max_retries; tries > 0; tries--) {
            // val == 0 with the success flag set is the Zen 5 bug signature.
            // Treat it as a failed attempt and retry. Side effect: 0 is never
            // emitted (a 2^-64 bias, accepted deliberately).
            if (_rdseed64_step(&val) && val != 0) {
                memcpy(buf + (size_t)i * sizeof(val), &val, sizeof(val));
                ok = 1;
                break;
            }
            _mm_pause();                     // Intel: pause between retries
        }
        if (!ok) return 0;
    }
    return 1;
}

// ── hwrng.has_rdseed() ────────────────────────────────────────────────────────

static PyObject *py_has_rdseed(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return PyBool_FromLong(g_has_rdseed);
}

// ── hwrng.rdseed_raw_bytes(n_bytes, max_retries=100) ──────────────────────────

static PyObject *rdseed_raw_bytes(PyObject *self, PyObject *args) {
    Py_ssize_t n_bytes;
    int max_retries = 100;

    if (!PyArg_ParseTuple(args, "n|i", &n_bytes, &max_retries))
        return NULL;

    if (n_bytes <= 0 || (n_bytes & 7) != 0) {
        PyErr_SetString(PyExc_ValueError,
            "n_bytes must be a positive multiple of 8");
        return NULL;
    }
    if (n_bytes > HWRNG_MAX_BYTES) {
        PyErr_SetString(PyExc_ValueError,
            "n_bytes exceeds maximum allowed size (1MB)");
        return NULL;
    }
    if (max_retries <= 0) {
        PyErr_SetString(PyExc_ValueError,
            "max_retries must be a positive integer (Intel recommends >= 10)");
        return NULL;
    }
    if (!g_has_rdseed) {
        PyErr_SetString(PyExc_RuntimeError,
            "RDSEED instruction not supported on this CPU");
        return NULL;
    }

    // PyBytes is immovable in CPython, so buf stays valid across a GIL release.
    // Do NOT switch to PyByteArray without revisiting this.
    PyObject *result = PyBytes_FromStringAndSize(NULL, n_bytes);
    if (!result) return NULL;

    unsigned char *buf = (unsigned char *)PyBytes_AsString(result);
    if (!buf) {
        Py_DECREF(result);
        return NULL;
    }

    Py_ssize_t n_words = n_bytes >> 3;
    int ok;

    if (n_bytes <= HWRNG_NOGIL_THRESHOLD) {
        ok = fill_words(buf, n_words, max_retries);
    } else {
        Py_BEGIN_ALLOW_THREADS
        ok = fill_words(buf, n_words, max_retries);
        Py_END_ALLOW_THREADS
    }

    if (!ok) {
        Py_DECREF(result);
        PyErr_SetString(PyExc_RuntimeError,
            "RDSEED exhausted: hardware entropy depleted after max retries.\n"
            "On AMD Zen 5: ensure CPU microcode is updated (Oct 2025 fix).\n"
            "Consider reducing request size or increasing max_retries.");
        return NULL;
    }
    return result;
}

// ── Method table / module ─────────────────────────────────────────────────────

static PyMethodDef methods[] = {
    {"has_rdseed", py_has_rdseed, METH_NOARGS,
     "has_rdseed() -> bool\n"
     "Return True if this CPU supports the RDSEED instruction."},

    {"rdseed_raw_bytes", rdseed_raw_bytes, METH_VARARGS,
     "rdseed_raw_bytes(n_bytes, max_retries=100) -> bytes\n"
     "Generate n_bytes of hardware entropy via RDSEED.\n"
     "n_bytes: positive multiple of 8, maximum 1MB.\n"
     "max_retries: per-word retry limit (default 100, Intel recommends >= 10).\n"
     "Output: native little-endian byte order.\n"
     "Raises RuntimeError if the CPU lacks RDSEED or entropy is exhausted."},

    {NULL, NULL, 0, NULL}
};

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "hwrng",
    "Direct RDSEED hardware RNG for x86_64.\n"
    "Bypasses the OS entropy pool. 64-bit form only (avoids AMD Zen 5 bug).",
    -1,
    methods
};

// Must NOT be static: Python import needs the exported symbol.
PyMODINIT_FUNC PyInit_hwrng(void) {
    g_has_rdseed = detect_rdseed();

    PyObject *mod = PyModule_Create(&module);
    if (!mod) return NULL;

    if (PyModule_AddStringConstant(mod, "__compiler__", HWRNG_CC) < 0) {
        Py_DECREF(mod);
        return NULL;
    }

    if (detect_zen5()) {
        if (PyErr_WarnEx(PyExc_UserWarning,
                "AMD Zen 5 CPU detected. This processor has a known RDSEED "
                "bug (Oct 2025) where exhausted entropy returns 0 with the "
                "success flag set. This module mitigates it by retrying on "
                "zero output. Ensure CPU microcode is updated.",
                1) < 0) {
            Py_DECREF(mod);
            return NULL;
        }
    }
    return mod;
}
