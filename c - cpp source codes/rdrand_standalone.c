#include <stdint.h>
#include <string.h>

// Platform-specific export declarations
#ifdef _WIN32
#define EXPORT __declspec(dllexport)
#else
#define EXPORT
#endif

// Architecture detection
#ifdef _LP64
#define IS64BIT 1
#else
#define IS32BIT 1
#endif

// Compiler detection
#ifdef __GNUC__
#define USING_GCC 1
#elif __clang__
#define USING_CLANG 1
#else
#error Only support for gcc or clang currently
#endif

// CPU feature detection masks
#define RDRAND_MASK   0x40000000
#define RDSEED_MASK   0x00040000

// CPUID wrapper for different architectures
#define __cpuid(x,y,s) asm("cpuid":"=a"(x[0]),"=b"(x[1]),"=c"(x[2]),"=d"(x[3]):"a"(y),"c"(s))

void cpuid(unsigned int op, unsigned int subfunc, unsigned int reg[4])
{
#if USING_GCC && IS64BIT
    __cpuid(reg, op, subfunc);
#else
    asm volatile("pushl %%ebx      \n\t" /* save %ebx */
                 "cpuid            \n\t"
                 "movl %%ebx, %1   \n\t" /* save what cpuid just put in %ebx */
                 "popl %%ebx       \n\t" /* restore the old %ebx */
                 : "=a"(reg[0]), "=r"(reg[1]), "=c"(reg[2]), "=d"(reg[3])
                 : "a"(op), "c"(subfunc)
                 : "cc");
#endif
}

// Check if CPU supports RDRAND
EXPORT int RdRand_cpuid(void)
{
    unsigned int info[4] = {-1, -1, -1, -1};

    // Check if we're on Intel or AMD processor
    cpuid(0, 0, info);

    if (!(( memcmp((void *) &info[1], (void *) "Genu", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "ineI", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "ntel", 4) == 0 )
        ||
        ( memcmp((void *) &info[1], (void *) "Auth", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "enti", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "cAMD", 4) == 0 )))
        return 0;

    // Check for RDRAND support
    cpuid(1, 0, info);
    int ecx = info[2];
    if ((ecx & RDRAND_MASK) == RDRAND_MASK)
        return 1;
    else
        return 0;
}

// Check if CPU supports RDSEED
EXPORT int RdSeed_cpuid(void)
{
    unsigned int info[4] = {-1, -1, -1, -1};

    // Check if we're on Intel or AMD processor
    cpuid(0, 0, info);

    if (!(( memcmp((void *) &info[1], (void *) "Genu", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "ineI", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "ntel", 4) == 0 )
        ||
        ( memcmp((void *) &info[1], (void *) "Auth", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "enti", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "cAMD", 4) == 0 )))
        return 0;

    // Check for RDSEED support
    cpuid(7, 0, info);
    int ebx = info[1];
    if ((ebx & RDSEED_MASK) == RDSEED_MASK)
        return 1;
    else
        return 0;
}

// RDRAND implementations for different architectures
#if IS64BIT

#define GETRAND(rando) asm volatile("1:\n"                    \
                                    "rdrand  %0\n"            \
                                    "jnc 1b\n"                \
                                    :"=a"(rando) : : "cc")

EXPORT uint64_t get_bits_using_rdrand(void)
{
    unsigned long int rando = 0;
    GETRAND(rando);
    return rando;
}

#define GETSEED(rando) asm volatile("1:\n"                    \
                                    "rdseed  %0\n"            \
                                    "jnc 1b\n"                \
                                    :"=a"(rando) : : "cc")

EXPORT uint64_t get_bits_using_rdseed(void)
{
    unsigned long int rando = 0;
    GETSEED(rando);
    return rando;
}

#elif IS32BIT

#define GETRAND(rando) asm volatile("1:\n"                   \
                                    "rdrand %0\n"            \
                                    "jnc 1b\n"               \
                                    :"=a"(rando) : : "cc")

EXPORT uint64_t get_bits_using_rdrand(void)
{
    register unsigned int pre_rand;
    union{
       uint64_t rando;
       struct {
          uint32_t rando1;
          uint32_t rando2;
       } i;
    } un;

    GETRAND(pre_rand);
    un.i.rando1 = pre_rand;
    GETRAND(pre_rand);
    un.i.rando2 = pre_rand;

    return un.rando;
}

#define GETSEED(rando) asm volatile("1:\n"                    \
                                    "rdseed %0\n"            \
                                    "jnc 1b\n"                \
                                    :"=a"(rando) : : "cc")

EXPORT uint64_t get_bits_using_rdseed(void)
{
    unsigned int prerand;
    union{
       uint64_t rando;
       struct {
          uint32_t rando1;
          uint32_t rando2;
       } i;
    } un;

    GETSEED(prerand);
    un.i.rando1 = prerand;

    GETSEED(prerand);
    un.i.rando2 = prerand;

    return un.rando;
}

#endif

// Higher-level functions for range generation
EXPORT uint64_t rdrand_range(uint64_t min_val, uint64_t max_val)
{
    if (min_val > max_val) {
        return min_val; // Error case
    }
    
    if (min_val == max_val) {
        return min_val;
    }
    
    uint64_t range_size = max_val - min_val + 1;
    uint64_t max_valid = (UINT64_MAX / range_size) * range_size;
    
    uint64_t raw_val;
    do {
        raw_val = get_bits_using_rdrand();
    } while (raw_val >= max_valid);
    
    return min_val + (raw_val % range_size);
}

EXPORT uint64_t rdseed_range(uint64_t min_val, uint64_t max_val)
{
    if (min_val > max_val) {
        return min_val; // Error case
    }
    
    if (min_val == max_val) {
        return min_val;
    }
    
    uint64_t range_size = max_val - min_val + 1;
    uint64_t max_valid = (UINT64_MAX / range_size) * range_size;
    
    uint64_t raw_val;
    do {
        raw_val = get_bits_using_rdseed();
    } while (raw_val >= max_valid);
    
    return min_val + (raw_val % range_size);
}

// Generate random bytes
EXPORT void rdrand_bytes(unsigned char *buffer, uint32_t length)
{
    uint32_t i;
    uint64_t rando;
    
    // Fill 8 bytes at a time
    for (i = 0; i < length / 8; i++) {
        rando = get_bits_using_rdrand();
        memcpy(buffer + i * 8, &rando, 8);
    }
    
    // Handle remaining bytes
    uint32_t remainder = length % 8;
    if (remainder > 0) {
        rando = get_bits_using_rdrand();
        memcpy(buffer + i * 8, &rando, remainder);
    }
}

EXPORT void rdseed_bytes(unsigned char *buffer, uint32_t length)
{
    uint32_t i;
    uint64_t rando;
    
    // Fill 8 bytes at a time
    for (i = 0; i < length / 8; i++) {
        rando = get_bits_using_rdseed();
        memcpy(buffer + i * 8, &rando, 8);
    }
    
    // Handle remaining bytes
    uint32_t remainder = length % 8;
    if (remainder > 0) {
        rando = get_bits_using_rdseed();
        memcpy(buffer + i * 8, &rando, remainder);
    }
}

// Double precision random float [0, 1)
EXPORT double rdrand_double(void)
{
    uint64_t raw = get_bits_using_rdrand();
    return (double)raw / (double)UINT64_MAX;
}

EXPORT double rdseed_double(void)
{
    uint64_t raw = get_bits_using_rdseed();
    return (double)raw / (double)UINT64_MAX;
}

// Random float in range [min_val, max_val)
EXPORT double rdrand_double_range(double min_val, double max_val)
{
    double normalized = rdrand_double();
    return min_val + normalized * (max_val - min_val);
}

EXPORT double rdseed_double_range(double min_val, double max_val)
{
    double normalized = rdseed_double();
    return min_val + normalized * (max_val - min_val);
}
