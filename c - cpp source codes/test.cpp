# Create windows_test.cpp
@"
#include <windows.h>
#include <iostream>

int main() {
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    std::cout << "Number of processors: " << si.dwNumberOfProcessors << std::endl;
    return 0;
}
"@ | Out-File -Encoding ASCII windows_test.cpp


