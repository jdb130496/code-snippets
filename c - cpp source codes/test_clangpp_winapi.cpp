#include <windows.h>
#include <iostream>
#include <string>
#include <vector>
#include <memory>

class WindowsSystemInfo {
private:
    SYSTEM_INFO sysInfo;
    MEMORYSTATUSEX memInfo;
    
public:
    WindowsSystemInfo() {
        GetSystemInfo(&sysInfo);
        memInfo.dwLength = sizeof(memInfo);
        GlobalMemoryStatusEx(&memInfo);
    }
    
    void displayInfo() {
        std::cout << "=== Clang++ + Windows SDK Test (C++) ===" << std::endl;
        std::cout << "Compiler: " << __clang_version__ << std::endl;
        std::cout << "C++ Standard: " << __cplusplus << std::endl;
        
        std::cout << "\nSystem Information:" << std::endl;
        std::cout << "  Processors: " << sysInfo.dwNumberOfProcessors << std::endl;
        std::cout << "  Page size: " << sysInfo.dwPageSize << " bytes" << std::endl;
        
        std::cout << "\nMemory Information:" << std::endl;
        std::cout << "  Total RAM: " << (memInfo.ullTotalPhys / (1024 * 1024)) << " MB" << std::endl;
        std::cout << "  Available RAM: " << (memInfo.ullAvailPhys / (1024 * 1024)) << " MB" << std::endl;
        std::cout << "  Memory usage: " << memInfo.dwMemoryLoad << "%" << std::endl;
    }
    
    std::string getComputerName() {
        char name[MAX_COMPUTERNAME_LENGTH + 1];
        DWORD size = sizeof(name);
        if (GetComputerNameA(name, &size)) {
            return std::string(name);
        }
        return "Unknown";
    }
};

// Windows API: Get list of logical drives
std::vector<std::string> getLogicalDrives() {
    std::vector<std::string> drives;
    DWORD driveMask = GetLogicalDrives();
    
    for (int i = 0; i < 26; i++) {
        if (driveMask & (1 << i)) {
            char driveLetter[4] = {static_cast<char>('A' + i), ':', '\\', '\0'};
            drives.push_back(driveLetter);
        }
    }
    
    return drives;
}

int main() {
    // Test C++ class with Windows API
    auto sysInfo = std::make_unique<WindowsSystemInfo>();
    sysInfo->displayInfo();
    
    std::cout << "\nComputer name: " << sysInfo->getComputerName() << std::endl;
    
    // Test Windows API with STL
    std::cout << "\nLogical Drives:" << std::endl;
    auto drives = getLogicalDrives();
    for (const auto& drive : drives) {
        std::cout << "  " << drive << std::endl;
    }
    
    // Test Windows API: High-resolution timer
    LARGE_INTEGER frequency, start, end;
    QueryPerformanceFrequency(&frequency);
    QueryPerformanceCounter(&start);
    
    // Do some work
    int sum = 0;
    for (int i = 0; i < 1000000; i++) {
        sum += i;
    }
    
    QueryPerformanceCounter(&end);
    double elapsed = static_cast<double>(end.QuadPart - start.QuadPart) / frequency.QuadPart;
    std::cout << "\nPerformance test:" << std::endl;
    std::cout << "  Calculated sum: " << sum << std::endl;
    std::cout << "  Time elapsed: " << (elapsed * 1000) << " ms" << std::endl;
    
    std::cout << "\n=== All tests passed! ===" << std::endl;
    
    return 0;
}
