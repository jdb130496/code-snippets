# =====================================================
# Create Enhanced Benchmark with CPU Detection
# =====================================================

@"
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
    __cpuid(cpuInfo, 1);
    return (cpuInfo[2] & (1 << 30)) != 0;
}

int check_rdseed_support() {
    int cpuInfo[4];
    __cpuidex(cpuInfo, 7, 0);
    return (cpuInfo[1] & (1 << 18)) != 0;
}

// Intrinsic version with limited retries
uint64_t rdrand64_intrinsic(void) {
    uint64_t result;
    int retries = 0;
    while (!_rdrand64_step(&result)) {
        retries++;
        if (retries > 100) {
            fprintf(stderr, "ERROR: RDRAND failed after 100 retries\n");
            return 0;
        }
    }
    return result;
}

uint64_t rdseed64_intrinsic(void) {
    uint64_t result;
    int retries = 0;
    while (!_rdseed64_step(&result)) {
        retries++;
        if (retries > 1000) {
            fprintf(stderr, "ERROR: RDSEED failed after 1000 retries\n");
            return 0;
        }
        _mm_pause();
    }
    return result;
}

// Benchmark function with progress indicators
double benchmark(const char* name, uint64_t (*func)(void), int iterations) {
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    
    printf("%s:\n", name);
    printf("  Warming up (1000 calls)...");
    fflush(stdout);
    
    for (int i = 0; i < 1000; i++) {
        uint64_t val = func();
        if (val == 0 && i < 10) {
            printf("\n  ERROR: Function returned 0 during warmup\n");
            return -1.0;
        }
    }
    printf(" done\n");
    fflush(stdout);
    
    printf("  Running benchmark...");
    fflush(stdout);
    
    QueryPerformanceCounter(&start);
    
    uint64_t sum = 0;
    int progress_interval = iterations / 10;
    
    for (int i = 0; i < iterations; i++) {
        sum += func();
        
        if (progress_interval > 0 && i > 0 && i % progress_interval == 0) {
            printf(".");
            fflush(stdout);
        }
    }
    
    QueryPerformanceCounter(&end);
    
    printf(" done\n");
    
    double elapsed = (double)(end.QuadPart - start.QuadPart) / frequency.QuadPart;
    double ns_per_call = (elapsed * 1e9) / iterations;
    
    printf("  Total time: %.6f seconds\n", elapsed);
    printf("  Per call: %.2f ns\n", ns_per_call);
    printf("  Throughput: %.2f million/sec\n", iterations / elapsed / 1e6);
    printf("  Checksum: %llu\n\n", sum);
    
    return ns_per_call;
}

int main() {
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
    
    printf("\nChecking CPU features...\n");
    int has_rdrand = check_rdrand_support();
    int has_rdseed = check_rdseed_support();
    
    printf("  RDRAND support: %s\n", has_rdrand ? "YES" : "NO");
    printf("  RDSEED support: %s\n\n", has_rdseed ? "YES" : "NO");
    
    if (!has_rdrand) {
        printf("ERROR: Your CPU does not support RDRAND instruction!\n");
        printf("This benchmark requires a CPU with RDRAND support.\n");
        return 1;
    }
    
    printf("====================================================\n");
    printf("Testing RDRAND (quick test)\n");
    printf("====================================================\n\n");
    
    printf("Generating 10 random values...\n");
    for (int i = 0; i < 10; i++) {
        uint64_t val = rdrand64_intrinsic();
        printf("  %2d: 0x%016llX\n", i + 1, val);
    }
    printf("\n");
    
    const int RDRAND_ITERATIONS = 1000000;  // Start with 1 million
    const int RDSEED_ITERATIONS = 100000;   // Start with 100k
    
    printf("====================================================\n");
    printf("RDRAND64 Performance (%d iterations)\n", RDRAND_ITERATIONS);
    printf("====================================================\n\n");
    
    double rdrand_time = benchmark("RDRAND64 (intrinsic _rdrand64_step)", 
                                    rdrand64_intrinsic, RDRAND_ITERATIONS);
    
    if (rdrand_time < 0) {
        printf("ERROR: RDRAND benchmark failed!\n");
        return 1;
    }
    
    if (has_rdseed) {
        printf("====================================================\n");
        printf("RDSEED64 Performance (%d iterations)\n", RDSEED_ITERATIONS);
        printf("====================================================\n\n");
        
        double rdseed_time = benchmark("RDSEED64 (intrinsic _rdseed64_step)", 
                                        rdseed64_intrinsic, RDSEED_ITERATIONS);
        
        if (rdseed_time > 0) {
            printf("====================================================\n");
            printf("Summary\n");
            printf("====================================================\n\n");
            printf("RDRAND64: %.2f ns/call\n", rdrand_time);
            printf("RDSEED64: %.2f ns/call\n", rdseed_time);
            printf("RDSEED is %.2fx slower than RDRAND\n", rdseed_time / rdrand_time);
        }
    } else {
        printf("====================================================\n");
        printf("Note: RDSEED not supported on this CPU\n");
        printf("====================================================\n\n");
        printf("RDRAND64: %.2f ns/call\n", rdrand_time);
    }
    
    return 0;
}
"@ | Out-File -Encoding ASCII benchmark_comprehensive_fixed.c

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "  Enhanced RDRAND/RDSEED Benchmark" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Test with MSVC
Write-Host "`n=== Compiling with MSVC ===" -ForegroundColor Yellow
cl /O2 benchmark_comprehensive_fixed.c /Fe:benchmark_msvc_fixed.exe /nologo 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] MSVC compilation successful" -ForegroundColor Green
    Write-Host "`nRunning MSVC benchmark..." -ForegroundColor Cyan
    Write-Host "(Press Ctrl+C if it hangs)" -ForegroundColor Yellow
    .\benchmark_msvc_fixed.exe
} else {
    Write-Host "[ERROR] MSVC compilation failed" -ForegroundColor Red
}
