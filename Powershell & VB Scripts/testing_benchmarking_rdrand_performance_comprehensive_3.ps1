# =====================================================
# Comprehensive RDRAND/RDSEED Benchmark - All Compilers
# =====================================================

Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  RDRAND/RDSEED Multi-Compiler Benchmark" -ForegroundColor Cyan
Write-Host "  Testing: MSVC, Clang (Win), Clang (GNU), GCC, MASM" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# =====================================================
# Auto-detect compiler paths
# =====================================================
$clangWinPath = "D:\Programs\clang\bin\clang.exe"
$gccPath = "D:\Programs\msys64\ucrt64\bin\gcc.exe"
$clangGnuPath = "D:\Programs\msys64\ucrt64\bin\clang.exe"

Write-Host "`nDetecting compilers..." -ForegroundColor Yellow
Write-Host "  MSVC (cl): " -NoNewline
if (Get-Command cl -ErrorAction SilentlyContinue) {
    Write-Host "Found in PATH" -ForegroundColor Green
} else {
    Write-Host "Not in PATH" -ForegroundColor Red
}

Write-Host "  Clang (Win): " -NoNewline
if (Test-Path $clangWinPath) {
    Write-Host "Found at $clangWinPath" -ForegroundColor Green
} else {
    Write-Host "Not found" -ForegroundColor Red
    $clangWinPath = $null
}

Write-Host "  GCC (MSYS2): " -NoNewline
if (Test-Path $gccPath) {
    Write-Host "Found at $gccPath" -ForegroundColor Green
} else {
    Write-Host "Not found" -ForegroundColor Red
    $gccPath = $null
}

Write-Host "  Clang (GNU): " -NoNewline
if (Test-Path $clangGnuPath) {
    Write-Host "Found at $clangGnuPath" -ForegroundColor Green
} else {
    Write-Host "Not found" -ForegroundColor Red
    $clangGnuPath = $null
}

# Create C source code with all implementations
$cCode = @'
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
'@

$cCode | Out-File -Encoding ASCII -FilePath benchmark_multi.c

# Create MASM assembly source
$asmCode = @'
.code

; RDRAND 64-bit function
public rdrand64_asm
rdrand64_asm proc
retry_rdrand:
    rdrand rax
    jnc retry_rdrand
    ret
rdrand64_asm endp

; RDSEED 64-bit function
public rdseed64_asm
rdseed64_asm proc
retry_rdseed:
    rdseed rax
    jnc retry_rdseed
    ret
rdseed64_asm endp

end
'@

$asmCode | Out-File -Encoding ASCII -FilePath rdrand_asm.asm

# Create C wrapper for MASM
$masmWrapper = @'
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
'@

$masmWrapper | Out-File -Encoding ASCII -FilePath benchmark_masm.c

# Results storage
$results = @()

# Test MSVC
Write-Host "`n[1/6] Testing MSVC..." -ForegroundColor Yellow
$null = cl /O2 /nologo benchmark_multi.c /link /OUT:benchmark_msvc.exe 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Compilation: OK" -ForegroundColor Green
    Write-Host "  Running benchmark (this may take 10-30 seconds)..." -ForegroundColor Cyan
    
    # Run with timeout
    $job = Start-Job -ScriptBlock { & ".\benchmark_msvc.exe" 2>&1 }
    $completed = Wait-Job $job -Timeout 60
    
    if ($completed) {
        $output = Receive-Job $job | Out-String
        Remove-Job $job
        Write-Host $output
        
        $rdrand = if ($output -match "RDRAND_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        $rdseed = if ($output -match "RDSEED_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        
        if ($rdrand -gt 0) {
            $results += [PSCustomObject]@{
                Compiler = "MSVC"
                Method = "Intrinsic"
                RDRAND_ns = $rdrand
                RDSEED_ns = $rdseed
            }
        }
    } else {
        Remove-Job $job -Force
        Write-Host "  Execution: TIMEOUT (hung for >60 seconds)" -ForegroundColor Red
        Write-Host "  This likely means RDRAND is very slow or not working properly on your CPU" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Compilation: FAILED" -ForegroundColor Red
}

# Test Clang (Windows - MSVC ABI)
Write-Host "`n[2/6] Testing Clang (Windows/MSVC ABI)..." -ForegroundColor Yellow
$null = clang -O3 -march=native benchmark_multi.c -o benchmark_clang_win.exe 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  Compilation: OK" -ForegroundColor Green
    $output = & .\benchmark_clang_win.exe 2>&1 | Out-String
    Write-Host $output
    
    $rdrand = if ($output -match "RDRAND_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
    $rdseed = if ($output -match "RDSEED_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
    $rdrand_asm_speedup = if ($output -match "RDRAND_ASM_SPEEDUP:([\d.]+)") { [double]$matches[1] } else { 1 }
    $rdseed_asm_speedup = if ($output -match "RDSEED_ASM_SPEEDUP:([\d.]+)") { [double]$matches[1] } else { 1 }
    
    $results += [PSCustomObject]@{
        Compiler = "Clang (Win)"
        Method = "Intrinsic"
        RDRAND_ns = $rdrand
        RDSEED_ns = $rdseed
    }
    
    if ($rdrand_asm_speedup -ne 1) {
        $results += [PSCustomObject]@{
            Compiler = "Clang (Win)"
            Method = "Inline ASM"
            RDRAND_ns = ($rdrand / $rdrand_asm_speedup)
            RDSEED_ns = ($rdseed / $rdseed_asm_speedup)
        }
    }
} else {
    Write-Host "  Compilation: FAILED (Clang not found or not in PATH)" -ForegroundColor Red
}

# Test Clang (MSYS2/GNU toolchain)
Write-Host "`n[3/6] Testing Clang (MSYS2/GNU toolchain)..." -ForegroundColor Yellow
if ($clangGnuPath -and (Test-Path $clangGnuPath)) {
    # Set up MSYS2 library paths
    $env:PATH = "D:\Programs\msys64\ucrt64\bin;$env:PATH"
    
    Write-Host "  Compiling with $clangGnuPath..." -ForegroundColor Cyan
    $compileOutput = & $clangGnuPath -O3 -march=native benchmark_multi.c -o benchmark_clang_gnu.exe 2>&1
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path "benchmark_clang_gnu.exe")) {
        Write-Host "  Compilation: OK" -ForegroundColor Green
        Write-Host "  Running benchmark..." -ForegroundColor Cyan
        
        $output = & .\benchmark_clang_gnu.exe 2>&1 | Out-String
        Write-Host $output
            
        $rdrand = if ($output -match "RDRAND_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        $rdseed = if ($output -match "RDSEED_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        $rdrand_asm_speedup = if ($output -match "RDRAND_ASM_SPEEDUP:([\d.]+)") { [double]$matches[1] } else { 1 }
        $rdseed_asm_speedup = if ($output -match "RDSEED_ASM_SPEEDUP:([\d.]+)") { [double]$matches[1] } else { 1 }
        
        if ($rdrand -gt 0) {
            $results += [PSCustomObject]@{
                Compiler = "Clang (GNU)"
                Method = "Intrinsic"
                RDRAND_ns = $rdrand
                RDSEED_ns = $rdseed
            }
            
            if ($rdrand_asm_speedup -ne 1) {
                $results += [PSCustomObject]@{
                    Compiler = "Clang (GNU)"
                    Method = "Inline ASM"
                    RDRAND_ns = ($rdrand / $rdrand_asm_speedup)
                    RDSEED_ns = ($rdseed / $rdseed_asm_speedup)
                }
            }
        }
    } else {
        Write-Host "  Compilation: FAILED" -ForegroundColor Red
        Write-Host "  Error output:" -ForegroundColor Yellow
        Write-Host $compileOutput -ForegroundColor Gray
    }
} else {
    Write-Host "  SKIPPED (Clang not found at $clangGnuPath)" -ForegroundColor Yellow
}

# Test GCC (MinGW/MSYS2)
Write-Host "`n[4/6] Testing GCC (GNU toolchain)..." -ForegroundColor Yellow
if ($gccPath -and (Test-Path $gccPath)) {
    # Set up MSYS2 library paths
    $env:PATH = "D:\Programs\msys64\ucrt64\bin;$env:PATH"
    
    Write-Host "  Compiling with $gccPath..." -ForegroundColor Cyan
    $compileOutput = & $gccPath -O3 -march=native benchmark_multi.c -o benchmark_gcc.exe 2>&1
    
    if ($LASTEXITCODE -eq 0 -and (Test-Path "benchmark_gcc.exe")) {
        Write-Host "  Compilation: OK" -ForegroundColor Green
        Write-Host "  Running benchmark..." -ForegroundColor Cyan
        
        $output = & .\benchmark_gcc.exe 2>&1 | Out-String
        Write-Host $output
            
        $rdrand = if ($output -match "RDRAND_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        $rdseed = if ($output -match "RDSEED_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        $rdrand_asm_speedup = if ($output -match "RDRAND_ASM_SPEEDUP:([\d.]+)") { [double]$matches[1] } else { 1 }
        $rdseed_asm_speedup = if ($output -match "RDSEED_ASM_SPEEDUP:([\d.]+)") { [double]$matches[1] } else { 1 }
        
        if ($rdrand -gt 0) {
            $results += [PSCustomObject]@{
                Compiler = "GCC"
                Method = "Intrinsic"
                RDRAND_ns = $rdrand
                RDSEED_ns = $rdseed
            }
            
            if ($rdrand_asm_speedup -ne 1) {
                $results += [PSCustomObject]@{
                    Compiler = "GCC"
                    Method = "Inline ASM"
                    RDRAND_ns = ($rdrand / $rdrand_asm_speedup)
                    RDSEED_ns = ($rdseed / $rdseed_asm_speedup)
                }
            }
        }
    } else {
        Write-Host "  Compilation: FAILED" -ForegroundColor Red
        Write-Host "  Error output:" -ForegroundColor Yellow
        Write-Host $compileOutput -ForegroundColor Gray
    }
} else {
    Write-Host "  SKIPPED (GCC not found at $gccPath)" -ForegroundColor Yellow
}

# Test MASM
Write-Host "`n[5/6] Testing MASM (Pure Assembly)..." -ForegroundColor Yellow
$null = ml64 /c /nologo rdrand_asm.asm 2>&1
if ($LASTEXITCODE -eq 0) {
    $null = cl /O2 /nologo benchmark_masm.c rdrand_asm.obj /link /OUT:benchmark_masm.exe 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "  Compilation: OK" -ForegroundColor Green
        $output = & .\benchmark_masm.exe 2>&1 | Out-String
        Write-Host $output
        
        $rdrand = if ($output -match "RDRAND_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        $rdseed = if ($output -match "RDSEED_INTRINSIC:([\d.]+)") { [double]$matches[1] } else { 0 }
        
        $results += [PSCustomObject]@{
            Compiler = "MASM"
            Method = "Pure ASM"
            RDRAND_ns = $rdrand
            RDSEED_ns = $rdseed
        }
    } else {
        Write-Host "  Linking: FAILED" -ForegroundColor Red
    }
} else {
    Write-Host "  Assembly: FAILED (MASM not found)" -ForegroundColor Red
}

# Display Results Table
Write-Host "`n=====================================================" -ForegroundColor Cyan
Write-Host "  BENCHMARK RESULTS SUMMARY" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

if ($results.Count -gt 0) {
    Write-Host "`nRDRAND Performance (lower is better):" -ForegroundColor Yellow
    $results | Where-Object { $_.RDRAND_ns -gt 0 } | Sort-Object RDRAND_ns | Format-Table -Property Compiler, Method, @{Label="RDRAND (ns)";Expression={"{0:N2}" -f $_.RDRAND_ns};Align="Right"}, @{Label="Speed (M/s)";Expression={"{0:N2}" -f (1000/$_.RDRAND_ns)};Align="Right"} -AutoSize
    
    Write-Host "`nRDSEED Performance (lower is better):" -ForegroundColor Yellow
    $results | Where-Object { $_.RDSEED_ns -gt 0 } | Sort-Object RDSEED_ns | Format-Table -Property Compiler, Method, @{Label="RDSEED (ns)";Expression={"{0:N2}" -f $_.RDSEED_ns};Align="Right"}, @{Label="Speed (M/s)";Expression={"{0:N2}" -f (1000/$_.RDSEED_ns)};Align="Right"} -AutoSize
    
    # Find fastest
    $fastest_rdrand = $results | Where-Object { $_.RDRAND_ns -gt 0 } | Sort-Object RDRAND_ns | Select-Object -First 1
    $fastest_rdseed = $results | Where-Object { $_.RDSEED_ns -gt 0 } | Sort-Object RDSEED_ns | Select-Object -First 1
    
    Write-Host "=====================================================" -ForegroundColor Cyan
    Write-Host "Fastest RDRAND: $($fastest_rdrand.Compiler) ($($fastest_rdrand.Method)) - $("{0:N2}" -f $fastest_rdrand.RDRAND_ns) ns/call" -ForegroundColor Green
    if ($fastest_rdseed) {
        Write-Host "Fastest RDSEED: $($fastest_rdseed.Compiler) ($($fastest_rdseed.Method)) - $("{0:N2}" -f $fastest_rdseed.RDSEED_ns) ns/call" -ForegroundColor Green
    }
    Write-Host "=====================================================" -ForegroundColor Cyan
} else {
    Write-Host "`nNo successful compilations!" -ForegroundColor Red
}

Write-Host "`nDone! Executables and source files saved in current directory." -ForegroundColor Cyan
