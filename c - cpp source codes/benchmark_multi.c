#include <stdio.h>
#include <stdint.h>
#include <immintrin.h>
#include <windows.h>

#ifdef _MSC_VER
#include <intrin.h>
#endif

// CPU feature detection
int check_rdrand_support() {
    int cpuInfo[4];
#ifdef _MSC_VER
    __cpuid(cpuInfo, 1);
#else
    __asm__ __volatile__ (
        "cpuid"
        : "=a" (cpuInfo[0]), "=b" (cpuInfo[1]), "=c" (cpuInfo[2]), "=d" (cpuInfo[3])
        : "a" (1), "c" (0)
    );
#endif
    return (cpuInfo[2] & (1 << 30)) != 0;
}

int check_rdseed_support() {
    int cpuInfo[4];
#ifdef _MSC_VER
    __cpuidex(cpuInfo, 7, 0);
#else
    __asm__ __volatile__ (
        "cpuid"
        : "=a" (cpuInfo[0]), "=b" (cpuInfo[1]), "=c" (cpuInfo[2]), "=d" (cpuInfo[3])
        : "a" (7), "c" (0)
    );
#endif
    return (cpuInfo[1] & (1 << 18)) != 0;
}

// Inline assembly versions (Clang/GCC only)
#if defined(__clang__) || defined(__GNUC__)
__attribute__((noinline))
uint64_t rdrand64_inline_asm(void) {
    uint64_t result;
    int success;
    do {
        __asm__ volatile ("rdrand %0; setc %1" : "=r" (result), "=qm" (success));
    } while (!success);
    return result;
}

__attribute__((noinline))
uint64_t rdseed64_inline_asm(void) {
    uint64_t result;
    int success;
    do {
        __asm__ volatile ("rdseed %0; setc %1" : "=r" (result), "=qm" (success));
    } while (!success);
    return result;
}
#endif

// Intrinsic version (all compilers)
#ifdef _MSC_VER
__declspec(noinline)
#else
__attribute__((noinline))
#endif
uint64_t rdrand64_intrinsic(void) {
    uint64_t result;
    while (!_rdrand64_step(&result)) {
        _mm_pause();
    }
    return result;
}

#ifdef _MSC_VER
__declspec(noinline)
#else
__attribute__((noinline))
#endif
uint64_t rdseed64_intrinsic(void) {
    uint64_t result;
    while (!_rdseed64_step(&result)) {
        _mm_pause();
    }
    return result;
}

// Benchmark function
double benchmark(const char* name, uint64_t (*func)(void), int iterations, int show_progress) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    
    if (show_progress) {
        printf("  %s: ", name);
        fflush(stdout);
    }
    
    // Warmup
    for (int i = 0; i < 1000; i++) {
        func();
    }
    
    QueryPerformanceCounter(&start);
    
    uint64_t sum = 0;
    for (int i = 0; i < iterations; i++) {
        sum += func();
    }
    
    QueryPerformanceCounter(&end);
    
    double elapsed = (double)(end.QuadPart - start.QuadPart) / frequency.QuadPart;
    double ns_per_call = (elapsed * 1e9) / iterations;
    
    if (show_progress) {
        printf("%.2f ns/call (%.2f M/sec)\n", ns_per_call, iterations / elapsed / 1e6);
    }
    
    return ns_per_call;
}

int main() {
    const int RDRAND_ITERATIONS = 100000;  // Reduced from 5M to 100K
    const int RDSEED_ITERATIONS = 50000;   // Reduced from 500K to 50K
    
    printf("Compiler: ");
#ifdef _MSC_VER
    printf("MSVC %d", _MSC_VER);
#elif defined(__clang__)
    printf("Clang %s", __clang_version__);
#elif defined(__GNUC__)
    printf("GCC %d.%d.%d", __GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__);
#endif
    printf("\n");
    
    int has_rdrand = check_rdrand_support();
    int has_rdseed = check_rdseed_support();
    
    if (!has_rdrand) {
        printf("ERROR: RDRAND not supported\n");
        return 1;
    }
    
    printf("\nRDRAND Benchmarks (%d iterations):\n", RDRAND_ITERATIONS);
    double rdrand_intrinsic = benchmark("Intrinsic", rdrand64_intrinsic, RDRAND_ITERATIONS, 1);
    
#if defined(__clang__) || defined(__GNUC__)
    double rdrand_asm = benchmark("Inline ASM", rdrand64_inline_asm, RDRAND_ITERATIONS, 1);
    printf("RDRAND_ASM_SPEEDUP:%.4f\n", rdrand_intrinsic / rdrand_asm);
#endif
    
    printf("RDRAND_INTRINSIC:%.2f\n", rdrand_intrinsic);
    
    if (has_rdseed) {
        printf("\nRDSEED Benchmarks (%d iterations):\n", RDSEED_ITERATIONS);
        double rdseed_intrinsic = benchmark("Intrinsic", rdseed64_intrinsic, RDSEED_ITERATIONS, 1);
        
#if defined(__clang__) || defined(__GNUC__)
        double rdseed_asm = benchmark("Inline ASM", rdseed64_inline_asm, RDSEED_ITERATIONS, 1);
        printf("RDSEED_ASM_SPEEDUP:%.4f\n", rdseed_intrinsic / rdseed_asm);
#endif
        
        printf("RDSEED_INTRINSIC:%.2f\n", rdseed_intrinsic);
        printf("RDSEED_VS_RDRAND:%.2fx\n", rdseed_intrinsic / rdrand_intrinsic);
    }
    
    return 0;
}
