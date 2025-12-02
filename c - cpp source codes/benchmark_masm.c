#include <stdio.h>
#include <stdint.h>
#include <windows.h>

extern uint64_t rdrand64_asm(void);
extern uint64_t rdseed64_asm(void);

double benchmark(const char* name, uint64_t (*func)(void), int iterations) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    
    printf("  %s: ", name);
    fflush(stdout);
    
    for (int i = 0; i < 1000; i++) func();
    
    QueryPerformanceCounter(&start);
    uint64_t sum = 0;
    for (int i = 0; i < iterations; i++) {
        sum += func();
    }
    QueryPerformanceCounter(&end);
    
    double elapsed = (double)(end.QuadPart - start.QuadPart) / frequency.QuadPart;
    double ns_per_call = (elapsed * 1e9) / iterations;
    
    printf("%.2f ns/call (%.2f M/sec)\n", ns_per_call, iterations / elapsed / 1e6);
    return ns_per_call;
}

int main() {
    const int RDRAND_ITERATIONS = 100000;  // Reduced from 5M to 100K
    const int RDSEED_ITERATIONS = 50000;   // Reduced from 500K to 50K
    
    printf("Compiler: MASM + MSVC\n");
    printf("\nRDRAND Benchmarks (%d iterations):\n", RDRAND_ITERATIONS);
    double rdrand = benchmark("Pure ASM", rdrand64_asm, RDRAND_ITERATIONS);
    printf("RDRAND_INTRINSIC:%.2f\n", rdrand);
    
    printf("\nRDSEED Benchmarks (%d iterations):\n", RDSEED_ITERATIONS);
    double rdseed = benchmark("Pure ASM", rdseed64_asm, RDSEED_ITERATIONS);
    printf("RDSEED_INTRINSIC:%.2f\n", rdseed);
    printf("RDSEED_VS_RDRAND:%.2fx\n", rdseed / rdrand);
    
    return 0;
}
