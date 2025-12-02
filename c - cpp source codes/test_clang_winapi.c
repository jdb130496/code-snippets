#include <windows.h>
#include <stdio.h>
#include <stdint.h>

int main() {
    printf("=== Clang + Windows SDK Test (C) ===\n");
    printf("Compiler: %s\n", __clang_version__);
    
    // Windows API: Get system info
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    printf("\nSystem Information:\n");
    printf("  Number of processors: %lu\n", si.dwNumberOfProcessors);
    printf("  Page size: %lu bytes\n", si.dwPageSize);
    printf("  Processor architecture: ");
    switch(si.wProcessorArchitecture) {
        case PROCESSOR_ARCHITECTURE_AMD64:
            printf("x64 (AMD64)\n");
            break;
        case PROCESSOR_ARCHITECTURE_INTEL:
            printf("x86 (Intel)\n");
            break;
        case PROCESSOR_ARCHITECTURE_ARM64:
            printf("ARM64\n");
            break;
        default:
            printf("Unknown\n");
    }
    
    // Windows API: Get computer name
    char computerName[MAX_COMPUTERNAME_LENGTH + 1];
    DWORD size = sizeof(computerName);
    if (GetComputerNameA(computerName, &size)) {
        printf("  Computer name: %s\n", computerName);
    }
    
    // Windows API: Get Windows directory
    char winDir[MAX_PATH];
    GetWindowsDirectoryA(winDir, MAX_PATH);
    printf("  Windows directory: %s\n", winDir);
    
    // Windows API: Memory status
    MEMORYSTATUSEX memStatus;
    memStatus.dwLength = sizeof(memStatus);
    if (GlobalMemoryStatusEx(&memStatus)) {
        printf("\nMemory Status:\n");
        printf("  Total physical memory: %llu MB\n", memStatus.ullTotalPhys / (1024 * 1024));
        printf("  Available physical memory: %llu MB\n", memStatus.ullAvailPhys / (1024 * 1024));
        printf("  Memory in use: %lu%%\n", memStatus.dwMemoryLoad);
    }
    
    return 0;
}
