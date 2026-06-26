/*
 * hwrng — Direct RDSEED hardware RNG for x86_64.
 *
 * Bypasses the OS entropy pool; outputs raw CPU thermal-noise samples.
 * This is NOT a CSPRNG and NOT conditioned. Do not feed key material
 * directly into cryptographic primitives — pass output through a proper
 * KDF (e.g. HKDF, CTR_DRBG) first.
 *
 * 64-bit form only. The _rdseed32_step path is excluded at compile time
 * because AMD Zen 5 (Family 0x1A) has a silicon bug where the 16- and
 * 32-bit RDSEED forms return 0 with CF=1 (success) when the entropy pool
 * is exhausted. AMD's own bulletin confirms the 64-bit form is unaffected.
 * We still issue a UserWarning on Zen 5 so users know to update microcode.
 */

#include <Python.h>
#include <immintrin.h>
#include <stdint.h>
#include <string.h>

#if defined(_MSC_VER)
  #include <intrin.h>
#else
  #include <cpuid.h>
#endif

/* Hard reject 32-bit builds — keeps the code simpler and the Zen 5
   mitigation reasoning valid. */
#if !defined(__x86_64__) && !defined(_M_X64)
  #error "hwrng requires 64-bit x86_64 architecture"
#endif

/* ── CPUID abstraction ──────────────────────────────────────────────────────
 *
 * A single struct + helper eliminates the MSVC/GCC duplication that was
 * scattered across every CPUID call site.  Both callers (cpuid_has_rdseed
 * and is_zen5_affected) now read the same field names.
 */

typedef struct {
    uint32_t eax, ebx, ecx, edx;
} CpuidRegs;

static void cpuid_query(CpuidRegs *r, uint32_t leaf, uint32_t subleaf) {
#if defined(_MSC_VER)
    int info[4];
    __cpuidex(info, (int)leaf, (int)subleaf);
    r->eax = (uint32_t)info[0];
    r->ebx = (uint32_t)info[1];
    r->ecx = (uint32_t)info[2];
    r->edx = (uint32_t)info[3];
#else
    /* __get_cpuid_count returns 0 if the leaf is unsupported; callers must
       check the output to decide what that means for their query. */
    if (!__get_cpuid_count(leaf, subleaf,
                           &r->eax, &r->ebx, &r->ecx, &r->edx)) {
        r->eax = r->ebx = r->ecx = r->edx = 0;
    }
#endif
}

/* ── CPUID feature / vendor queries ────────────────────────────────────────*/

static int cpuid_has_rdseed(void) {
    CpuidRegs r0, r7;

    /* Leaf 0 EAX = highest standard CPUID leaf this CPU supports.
     * The GCC/Clang path already guards against an unsupported leaf
     * (__get_cpuid_count returns failure and cpuid_query zeroes the
     * registers), but the MSVC path calls __cpuidex unconditionally
     * with no such check. Querying an unsupported leaf doesn't fault --
     * the CPU just folds back data from a lower leaf -- but that means
     * EBX bit 18 could, in principle, reflect the wrong leaf entirely.
     * Checking the max leaf first closes that gap on all compilers. */
    cpuid_query(&r0, 0, 0);
    if (r0.eax < 7) {
        return 0;  /* leaf 7 unsupported -> CPU predates RDSEED anyway */
    }

    cpuid_query(&r7, 7, 0);
    return (r7.ebx & (1u << 18)) != 0;  /* EBX bit 18 = RDSEED */
}

/*
 * is_zen5_affected — returns 1 only on a genuine AMD Zen 5 processor.
 *
 * The original code checked family == 0x1A without first verifying the
 * vendor string.  An Intel (or other) CPU with a coincidental display-family
 * of 0x1A would have triggered a spurious Zen 5 warning.  We now check the
 * vendor string from leaf 0 first.
 *
 * Vendor string layout in EBX/EDX/ECX (leaf 0):
 *   AMD:   "AuthenticAMD"  EBX=0x68747541 EDX=0x69746E65 ECX=0x444D4163
 *   Intel: "GenuineIntel"  (different values)
 */
static int is_zen5_affected(void) {
    CpuidRegs r0, r1;

    /* Leaf 0: vendor string */
    cpuid_query(&r0, 0, 0);

    /* "AuthenticAMD" as little-endian uint32: Auth=0x68747541,
       enti=0x69746E65, cAMD=0x444D4163 */
    if (r0.ebx != 0x68747541u ||
        r0.edx != 0x69746E65u ||
        r0.ecx != 0x444D4163u) {
        return 0;  /* Not AMD — no Zen 5 bug possible */
    }

    /* Leaf 1: display family */
    cpuid_query(&r1, 1, 0);
    uint32_t base_family     = (r1.eax >> 8)  & 0xFu;
    uint32_t extended_family = (r1.eax >> 20) & 0xFFu;
    uint32_t display_family  = (base_family == 0xFu)
                               ? (extended_family + base_family)
                               : base_family;

    return (display_family == 0x1Au);  /* AMD Zen 5 */
}

/* ── Python-callable: hwrng.has_rdseed() ───────────────────────────────────*/

static PyObject *py_has_rdseed(PyObject *self, PyObject *Py_UNUSED(ignored)) {
    return PyBool_FromLong(cpuid_has_rdseed());
}

/* ── Python-callable: hwrng.rdseed_raw_bytes(n, max_retries=100) ───────────
 *
 * Fills n_bytes of raw hardware entropy via _rdseed64_step.
 *
 * The function accepts any positive n_bytes (not just multiples of 8).
 * Internally it fills 8 bytes at a time and truncates to n_bytes.  The
 * trailing bytes of the last word are written via memcpy so that only the
 * requested count is exposed — no information about the next word leaks.
 *
 * GIL handling: PyBytes_FromStringAndSize(NULL, n) allocates an
 * uninitialized buffer of n bytes under the GIL. CPython guarantees that a
 * PyBytes object's internal buffer is immovable for its lifetime, so we can
 * safely release the GIL and write into it directly afterward.
 *
 * Zen 5 note: AMD's errata affects only the 16- and 32-bit RDSEED forms.
 * The 64-bit form (_rdseed64_step) is documented as unaffected.  We do NOT
 * reject val == 0 here because:
 *   (a) the bug does not apply to the 64-bit path, and
 *   (b) rejecting zero would introduce a tiny bias (P = 1/2^64).
 */
static PyObject *rdseed_raw_bytes(PyObject *self, PyObject *args) {
    Py_ssize_t n_bytes;
    int        max_retries = 100;

    if (!PyArg_ParseTuple(args, "n|i", &n_bytes, &max_retries))
        return NULL;

    if (n_bytes <= 0) {
        PyErr_SetString(PyExc_ValueError, "n_bytes must be a positive integer");
        return NULL;
    }

    if (n_bytes > 1024 * 1024) {
        PyErr_SetString(PyExc_ValueError,
            "n_bytes exceeds maximum allowed size (1 MiB)");
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

    PyObject *result = PyBytes_FromStringAndSize(NULL, n_bytes);
    if (!result) return NULL;

    char      *buf    = PyBytes_AS_STRING(result);
    Py_ssize_t n_full = n_bytes / (Py_ssize_t)sizeof(uint64_t);
    Py_ssize_t tail   = n_bytes % (Py_ssize_t)sizeof(uint64_t);
    int        failed = 0;

    Py_BEGIN_ALLOW_THREADS

    /* Fill complete 8-byte words. */
    for (Py_ssize_t i = 0; i < n_full; i++) {
        unsigned long long val;
        int retries = max_retries;
        int success = 0;

        while (retries--) {
            if (_rdseed64_step(&val)) {
                memcpy(buf + i * sizeof(uint64_t), &val, sizeof(uint64_t));
                success = 1;
                break;
            }
            _mm_pause();
        }

        if (!success) { failed = 1; goto done; }
    }

    /* Fill the partial trailing word, if any. */
    if (tail > 0) {
        unsigned long long val;
        int retries = max_retries;
        int success = 0;

        while (retries--) {
            if (_rdseed64_step(&val)) {
                /* Copy only the requested tail bytes — avoids leaking the
                   remainder of the hardware word past the buffer end. */
                memcpy(buf + n_full * sizeof(uint64_t), &val, (size_t)tail);
                success = 1;
                break;
            }
            _mm_pause();
        }

        if (!success) { failed = 1; }
    }

done:
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

/* ── Method table ───────────────────────────────────────────────────────────*/

static PyMethodDef methods[] = {
    {
        "has_rdseed",
        py_has_rdseed,
        METH_NOARGS,
        "has_rdseed() -> bool\n"
        "Return True if this CPU supports the RDSEED instruction.\n"
        "Always call before rdseed_raw_bytes() on unknown hardware."
    },
    {
        "rdseed_raw_bytes",
        rdseed_raw_bytes,
        METH_VARARGS,
        "rdseed_raw_bytes(n_bytes, max_retries=100) -> bytes\n"
        "\n"
        "Generate n_bytes of raw hardware entropy via the RDSEED instruction.\n"
        "\n"
        "Parameters\n"
        "----------\n"
        "n_bytes     : positive int, maximum 1 MiB (1048576).\n"
        "              Any value is accepted — not just multiples of 8.\n"
        "max_retries : per-word retry limit (default 100; Intel recommends >= 10).\n"
        "\n"
        "Returns\n"
        "-------\n"
        "bytes of length n_bytes in native little-endian byte order (x86).\n"
        "\n"
        "Raises\n"
        "------\n"
        "RuntimeError  if the CPU lacks RDSEED or the entropy pool is exhausted.\n"
        "ValueError    if arguments are out of range.\n"
        "\n"
        "Security notice\n"
        "---------------\n"
        "Output is RAW and UNCONDITIONED.  It is not a CSPRNG output.\n"
        "Do NOT use directly as key material.  Pass through a KDF\n"
        "(e.g. HKDF, CTR_DRBG) before using in any cryptographic context."
    },
    {NULL, NULL, 0, NULL}
};

/* ── Module definition ──────────────────────────────────────────────────────*/

static struct PyModuleDef module = {
    PyModuleDef_HEAD_INIT,
    "hwrng",
    "Direct RDSEED hardware RNG for x86_64.\n"
    "Bypasses OS entropy pool — raw CPU thermal noise instruction.\n"
    "No CSPRNG, no conditioning. 64-bit form only (avoids AMD Zen 5 bug).",
    -1,
    methods
};

/* ── Module entry point ─────────────────────────────────────────────────────
 *
 * PyInit_hwrng must NOT be static — Python's import machinery requires the
 * symbol to be exported from the shared library.
 */
PyMODINIT_FUNC PyInit_hwrng(void) {
    PyObject *mod = PyModule_Create(&module);
    if (!mod) return NULL;

    /*
     * Free-threading (PEP 703 / PEP 779) support.
     *
     * Python 3.13+ free-threaded builds (python3.14t and later) silently
     * re-enable the GIL for the whole process when importing any C
     * extension that hasn't declared itself thread-safe. This module has
     * no global mutable state — every Py_BEGIN_ALLOW_THREADS section below
     * only touches stack-local variables and a freshly allocated, not-yet-
     * shared bytes buffer — so it is safe to declare GIL-not-needed.
     *
     * PyUnstable_Module_SetGIL is the correct call for single-phase init
     * (PyModule_Create, as used here); the alternative Py_mod_gil slot is
     * only for multi-phase init (PyModuleDef_Init), which this module does
     * not use. The function only exists in free-threaded builds, hence the
     * Py_GIL_DISABLED guard — this is a no-op on a normal GIL build and on
     * any Python older than 3.13.
     */
#ifdef Py_GIL_DISABLED
    PyUnstable_Module_SetGIL(mod, Py_MOD_GIL_NOT_USED);
#endif

    /*
     * Warn at import time on AMD Zen 5 hardware.
     *
     * Even though the 64-bit RDSEED form is not affected by the silicon bug,
     * the warning is useful: the user's hardware has a known errata, and they
     * should update microcode regardless of which RDSEED width they use.
     *
     * If the caller has turned warnings into errors (warnings.simplefilter
     * ('error')), PyErr_WarnEx returns -1 and we propagate the exception.
     * The module object is released here; this is acceptable — a module that
     * fails to import cleanly does not need a valid reference outstanding.
     */
    if (is_zen5_affected()) {
        if (PyErr_WarnEx(PyExc_UserWarning,
                "AMD Zen 5 CPU detected. This processor has a known RDSEED "
                "errata (Oct 2025) where the 16- and 32-bit forms may return "
                "0 with the success flag set when the entropy pool is "
                "exhausted. The 64-bit form used by this module is unaffected. "
                "Updating CPU microcode is still recommended.",
                1) < 0) {
            Py_DECREF(mod);
            return NULL;
        }
    }

    return mod;
}
