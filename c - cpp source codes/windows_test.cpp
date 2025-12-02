#include <windows.h>
#include <iostream>

int main() {
    SYSTEM_INFO si;
    GetSystemInfo(&si);
    std::cout << "Number of processors: " << si.dwNumberOfProcessors << std::endl;
    return 0;
}
