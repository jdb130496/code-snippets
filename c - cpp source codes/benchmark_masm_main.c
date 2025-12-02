#include <stdio.h>
#include <stdint.h>
#include <windows.h>

extern uint64_t rdrand64_masm(void);
extern uint64_t rdseed64_masm(void);

double benchmark(const char* name, uint64_t (*func)(void), int iterations) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    
    for (int i = 0; i < 1000; i++) func();
    
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
    printf("  Checksum: %llu\n\n", sum);
    
    return ns_per_call;
}

int main() {
    printf("====================================================\n");
    printf("     Pure MASM Performance Benchmark\n");
    printf("====================================================\n\n");
    
    printf("Assembler: Microsoft MASM (ml64)\n");
    printf("Iterations (RDRAND): 10000000\n");
    printf("Iterations (RDSEED): 1000000\n\n");
    
    printf("====================================================\n");
    printf("RDRAND64 Performance\n");
    printf("====================================================\n\n");
    benchmark("RDRAND64 (pure MASM)", rdrand64_masm, 10000000);
    
    printf("====================================================\n");
    printf("RDSEED64 Performance\n");
    printf("====================================================\n\n");
    benchmark("RDSEED64 (pure MASM)", rdseed64_masm, 1000000);
    
    return 0;
}
