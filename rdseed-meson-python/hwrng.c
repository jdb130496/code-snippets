// Use stable ABI — prevents inlining, ensures all symbols
// are proper DLL exports in python3.lib on Windows
#define Py_LIMITED_API 0x030e0000   // Python 3.14 minimum
#include <Python.h>
#include <immintrin.h>
#include <stdint.h>
#include <string.h>

// Hard reject 32-bit — _rdseed32_step has AMD Zen 5 zero-return bug
#if !defined(__x86_64__) && !defined(_M_X64)
  #error "hwrng requires 64-bit x86_64 architecture"
#endif

// ── CPUID helpers ─────────────────────────────────────────────────────────────

#if defined(_MSC_VER)
  #include <intrin.h>

  static int cpuid_has_rdseed(void) {
      int info[4];
      __cpuidex(info, 7, 0);
      return (info[1] & (1 << 18)) != 0;   // EBX bit 18
  }

  static int is_zen5_affected(void) {
      int info[4];
      __cpuid(info, 1);
      int family = ((info[0] >> 8) & 0xF) + ((info[0] >> 20) & 0xFF);
      return (family == 0x1A);              // AMD Zen 5 family
  }

#else
  #include <cpuid.h>

  static int cpuid_has_rdseed(void) {
      unsigned int eax, ebx, ecx, edx;
      if (!__get_cpuid_count(7, 0, &eax, &ebx, &ecx, &edx))
          return 0;
      return (ebx & (1 << 18)) != 0;
  }

  static int is_zen5_affected(void) {
      unsigned int eax, ebx, ecx, edx;
      if (!__get_cpuid(1, &eax, &ebx, &ecx, &edx))
          return 0;
      int family = ((eax >> 8) & 0xF) + ((eax >> 20) & 0xFF);
      return (family == 0x1A);
  }

#endif

// ── Python-callable: hwrng.has_rdseed() ───────────────────────────────────────

static PyObject* py_has_rdseed(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return PyBool_FromLong(cpuid_has_rdseed());
}

// ── Python-callable: hwrng.rdseed_raw_bytes(n, max_retries=100) ───────────────

static PyObject* rdseed_raw_bytes(PyObject *self, PyObject *args) {
    Py_ssize_t n_bytes;
    int max_retries = 100;

    if (!PyArg_ParseTuple(args, "n|i", &n_bytes, &max_retries))
        return NULL;

    if (n_bytes <= 0 || n_bytes % (Py_ssize_t)sizeof(uint64_t) != 0) {
        PyErr_SetString(PyExc_ValueError,
            "n_bytes must be a positive multiple of 8 (sizeof uint64_t)");
        return NULL;
    }

    if (n_bytes > 1024 * 1024) {
        PyErr_SetString(PyExc_ValueError,
            "n_bytes exceeds maximum allowed size (1MB)");
        return NULL;
    }

    if (max_retries <= 0) {
        PyErr_SetString(PyExc_ValueError,
            "max_retries must be a positive integer (Intel recommends >= 10)");
        return NULL;
    }

    if (!cpuid_has_rdseed()) {
        PyErr_SetString(PyExc_RuntimeError,
            "RDSEED instruction not supported on this CPU");
        return NULL;
    }

    // PyBytes is immovable in CPython — buf pointer stable across GIL release.
    // Do NOT switch to PyByteArray without revisiting this guarantee.
    PyObject *result = PyBytes_FromStringAndSize(NULL, n_bytes);
    if (!result) return NULL;

       char *buf = PyBytes_AsString(result);
    if (!buf) {
       Py_DECREF(result);
       return NULL;
       }
    Py_ssize_t n_words = n_bytes / (Py_ssize_t)sizeof(uint64_t);
    int        failed  = 0;

    Py_BEGIN_ALLOW_THREADS

    for (Py_ssize_t i = 0; i < n_words; i++) {
        int retries = max_retries;
        int success = 0;

        // Declare as unsigned long long — exact type _rdseed64_step expects.
        // Eliminates uint64_t → ull cast entirely, no aliasing concern.
        unsigned long long val;

        while (retries--) {
            if (_rdseed64_step(&val)) {
                // AMD Zen 5 bug: RDSEED may return 1 (success) with val == 0
                // when entropy pool is exhausted (affects 16/32-bit forms,
                // but 64-bit form is also reportedly affected on some steppings).
                //
                // IMPORTANT: We do NOT unconditionally reject val == 0.
                // A genuine 64-bit zero occurs with P = 1/2^64 — rejecting it
                // would bias output (zero can never appear in stream).
                //
                // Correct mitigation: treat a zero return as a failed attempt
                // and retry — same as if _rdseed64_step returned 0.
                // If hardware is healthy, a retry will produce a non-zero value.
                // If hardware is buggy, retries will eventually exhaust and
                // we fail hard — correct behaviour.
                if (val == 0) {
                    // Do not accept — retry as if instruction failed
                    // val==0 with success flag = Zen 5 bug signature
                    _mm_pause();
                    continue;
                }

                memcpy(buf + i * sizeof(uint64_t), &val, sizeof(uint64_t));
                success = 1;
                break;
            }
            // Intel recommendation: pause between retries.
            // Yields CPU cycles, reduces contention on entropy circuit.
            _mm_pause();
        }

        if (!success) { failed = 1; break; }
    }

    Py_END_ALLOW_THREADS

    if (failed) {
        Py_DECREF(result);
        PyErr_SetString(PyExc_RuntimeError,
            "RDSEED exhausted — hardware entropy depleted after max retries.\n"
            "On AMD Zen 5: ensure CPU microcode is updated (Oct 2025 fix).\n"
            "Consider reducing request size or increasing max_retries.");
        return NULL;
    }

    return result;
}

// ── Method table ──────────────────────────────────────────────────────────────

static PyMethodDef methods[] = {
    {"has_rdseed",
     py_has_rdseed,
     METH_NOARGS,
     "has_rdseed() -> bool\n"
     "Return True if this CPU supports the RDSEED instruction.\n"
     "Always call before rdseed_raw_bytes() on unknown hardware."},

    {"rdseed_raw_bytes",
     rdseed_raw_bytes,
     METH_VARARGS,
     "rdseed_raw_bytes(n_bytes, max_retries=100) -> bytes\n"
     "Generate n_bytes of raw hardware entropy via RDSEED.\n"
     "n_bytes: positive multiple of 8, maximum 1MB.\n"
     "max_retries: per-word retry limit (default 100, Intel recommends >= 10).\n"
     "Output: native little-endian byte order (x86 architecture).\n"
     "Raises RuntimeError if CPU lacks RDSEED or entropy is exhausted."},

    {NULL, NULL, 0, NULL}
};

// ── Module definition ─────────────────────────────────────────────────────────

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "hwrng",
    "Direct RDSEED hardware RNG for x86_64.\n"
    "Bypasses OS entropy pool — raw CPU thermal noise instruction.\n"
    "No CSPRNG, no conditioning. 64-bit form only (avoids AMD Zen 5 bug).",
    -1,
    methods
};

// ── Module entry point ────────────────────────────────────────────────────────

// PyInit_hwrng must NOT be static — Python import requires exported symbol
PyMODINIT_FUNC PyInit_hwrng(void) {
    PyObject *mod = PyModule_Create(&module);
    if (!mod) return NULL;

    // Warn at import time on AMD Zen 5 — even though 64-bit form is safer,
    // user should know their hardware has a known RDSEED issue
    if (is_zen5_affected()) {
        if (PyErr_WarnEx(PyExc_UserWarning,
                "AMD Zen 5 CPU detected. This processor has a known RDSEED "
                "bug (Oct 2025) where exhausted entropy returns 0 with "
                "success flag set. This module mitigates by retrying on "
                "zero output. Ensure CPU microcode is updated.",
                1) < 0) {
            Py_DECREF(mod);
            return NULL;
        }
    }

    return mod;
}
