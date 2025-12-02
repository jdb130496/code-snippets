#include <stdio.h>
#include <immintrin.h>
#include <intrin.h>
#include <windows.h>

void test_rdrand_sizes() {
    unsigned short r16;
    unsigned int r32;
    unsigned long long r64;
    
    printf("=== Testing RDRAND (all sizes) ===\n");
    
    // 16-bit
    if (_rdrand16_step(&r16)) {
        printf("RDRAND16: 0x%04X (%u)\n", r16, r16);
    }
    
    // 32-bit
    if (_rdrand32_step(&r32)) {
        printf("RDRAND32: 0x%08X (%u)\n", r32, r32);
    }
    
    // 64-bit
    if (_rdrand64_step(&r64)) {
        printf("RDRAND64: 0x%016llX (%llu)\n", r64, r64);
    }
}

void test_rdseed_sizes() {
    unsigned short r16;
    unsigned int r32;
    unsigned long long r64;
    
    printf("\n=== Testing RDSEED (all sizes) ===\n");
    
    // 16-bit
    if (_rdseed16_step(&r16)) {
        printf("RDSEED16: 0x%04X (%u)\n", r16, r16);
    }
    
    // 32-bit
    if (_rdseed32_step(&r32)) {
        printf("RDSEED32: 0x%08X (%u)\n", r32, r32);
    }
    
    // 64-bit
    if (_rdseed64_step(&r64)) {
        printf("RDSEED64: 0x%016llX (%llu)\n", r64, r64);
    }
}

int main() {
    // Check if CPU supports RDRAND/RDSEED
    int cpuInfo[4];
    __cpuid(cpuInfo, 1);
    
    int hasRDRAND = (cpuInfo[2] & (1 << 30)) != 0;
    
    __cpuid(cpuInfo, 7);
    int hasRDSEED = (cpuInfo[1] & (1 << 18)) != 0;
    
    printf("CPU Support:\n");
    printf("  RDRAND: %s\n", hasRDRAND ? "YES" : "NO");
    printf("  RDSEED: %s\n\n", hasRDSEED ? "YES" : "NO");
    
    if (hasRDRAND) {
        test_rdrand_sizes();
    } else {
        printf("RDRAND not supported on this CPU\n");
    }
    
    if (hasRDSEED) {
        test_rdseed_sizes();
    } else {
        printf("RDSEED not supported on this CPU\n");
    }
    
    return 0;
}
