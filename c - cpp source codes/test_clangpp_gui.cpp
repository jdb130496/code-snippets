#include <windows.h>
#include <iostream>
#include <string>
#include <sstream>

int main() {
    std::cout << "=== Clang++ + Windows SDK + GUI Test ===" << std::endl;
    
    // Get system info
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    
    // Build message
    std::ostringstream message;
    message << "Clang++ with Windows SDK is working!\n\n"
            << "Compiler: " << __clang_version__ << "\n"
            << "Processors: " << si.dwNumberOfProcessors << "\n"
            << "Architecture: x64";
    
    std::cout << "Showing MessageBox..." << std::endl;
    
    // Show Windows MessageBox
    int result = MessageBoxA(
        NULL,
        message.str().c_str(),
        "Clang++ + Windows SDK Test",
        MB_OKCANCEL | MB_ICONINFORMATION
    );
    
    if (result == IDOK) {
        std::cout << "User clicked OK" << std::endl;
    } else {
        std::cout << "User clicked Cancel" << std::endl;
    }
    
    return 0;
}
