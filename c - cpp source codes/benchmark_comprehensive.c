#include <stdio.h>
#include <stdint.h>
#include <immintrin.h>
#include <windows.h>

// Include intrin.h for MSVC
#ifdef _MSC_VER
#include <intrin.h>
#endif

// Inline assembly versions (Clang/GCC only)
#if defined(__clang__) || defined(__GNUC__)
__attribute__((always_inline))
static inline uint64_t rdrand64_inline_asm() {
    uint64_t result;
    __asm__ volatile ("rdrand %0" : "=r" (result));
    return result;
}

__attribute__((always_inline))
static inline uint64_t rdseed64_inline_asm() {
    uint64_t result;
    __asm__ volatile ("rdseed %0" : "=r" (result));
    return result;
}
#endif

// Intrinsic version (all compilers)
#ifdef _MSC_VER
__declspec(noinline)
#else
__attribute__((noinline))
#endif
uint64_t rdrand64_intrinsic() {
    uint64_t result;
    _rdrand64_step(&result);
    return result;
}

#ifdef _MSC_VER
__declspec(noinline)
#else
__attribute__((noinline))
#endif
uint64_t rdseed64_intrinsic() {
    uint64_t result;
    _rdseed64_step(&result);
    return result;
}

// Benchmark function
double benchmark(const char* name, uint64_t (*func)(void), int iterations) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    
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
    
    printf("%s:\n", name);
    printf("  Total time: %.6f seconds\n", elapsed);
    printf("  Per call: %.2f ns\n", ns_per_call);
    printf("  Throughput: %.2f million/sec\n", iterations / elapsed / 1e6);
    printf("  Checksum: %llu (prevent optimization)\n\n", sum);
    
    return ns_per_call;
}

int main() {
    const int ITERATIONS = 10000000; // 10 million
    const int RDSEED_ITERATIONS = 1000000; // 1 million (slower)
    
    printf("====================================================\n");
    printf("     RDRAND/RDSEED Performance Benchmark\n");
    printf("====================================================\n\n");
    
    printf("Compiler: ");
#ifdef _MSC_VER
    printf("MSVC %d\n", _MSC_VER);
#elif defined(__clang__)
    printf("Clang %s\n", __clang_version__);
#elif defined(__GNUC__)
    printf("GCC %d.%d.%d\n", __GNUC__, __GNUC_MINOR__, __GNUC_PATCHLEVEL__);
#endif
    
    printf("Iterations (RDRAND): %d\n", ITERATIONS);
    printf("Iterations (RDSEED): %d\n\n", RDSEED_ITERATIONS);
    
    printf("====================================================\n");
    printf("RDRAND64 Performance\n");
    printf("====================================================\n\n");
    
    double intrinsic_time = benchmark("RDRAND64 (intrinsic _rdrand64_step)", rdrand64_intrinsic, ITERATIONS);
    
#if defined(__clang__) || defined(__GNUC__)
    double inline_asm_time = benchmark("RDRAND64 (inline assembly)", rdrand64_inline_asm, ITERATIONS);
#endif
    
    printf("====================================================\n");
    printf("RDSEED64 Performance\n");
    printf("====================================================\n\n");
    
    double rdseed_intrinsic_time = benchmark("RDSEED64 (intrinsic _rdseed64_step)", rdseed64_intrinsic, RDSEED_ITERATIONS);
    
#if defined(__clang__) || defined(__GNUC__)
    double rdseed_inline_asm_time = benchmark("RDSEED64 (inline assembly)", rdseed64_inline_asm, RDSEED_ITERATIONS);
#endif
    
    printf("====================================================\n");
    printf("Summary\n");
    printf("====================================================\n\n");
    
#if defined(__clang__) || defined(__GNUC__)
    printf("RDRAND64:\n");
    printf("  Intrinsic: %.2f ns/call\n", intrinsic_time);
    printf("  Inline ASM: %.2f ns/call\n", inline_asm_time);
    printf("  Difference: %.2f%% (%s)\n\n", 
           fabs(inline_asm_time - intrinsic_time) / intrinsic_time * 100,
           inline_asm_time < intrinsic_time ? "inline ASM faster" : "intrinsic faster");
    
    printf("RDSEED64:\n");
    printf("  Intrinsic: %.2f ns/call\n", rdseed_intrinsic_time);
    printf("  Inline ASM: %.2f ns/call\n", rdseed_inline_asm_time);
    printf("  Difference: %.2f%% (%s)\n\n", 
           fabs(rdseed_inline_asm_time - rdseed_intrinsic_time) / rdseed_intrinsic_time * 100,
           rdseed_inline_asm_time < rdseed_intrinsic_time ? "inline ASM faster" : "intrinsic faster");
    
    printf("RDRAND vs RDSEED:\n");
    printf("  RDSEED is %.2fx slower than RDRAND\n", rdseed_intrinsic_time / intrinsic_time);
#else
    printf("Note: Inline assembly comparison only available with Clang/GCC\n");
    printf("MSVC does not support inline assembly in x64 mode.\n\n");
    printf("RDRAND64 intrinsic: %.2f ns/call\n", intrinsic_time);
    printf("RDSEED64 intrinsic: %.2f ns/call\n", rdseed_intrinsic_time);
    printf("RDSEED is %.2fx slower than RDRAND\n", rdseed_intrinsic_time / intrinsic_time);
#endif
    
    return 0;
}
