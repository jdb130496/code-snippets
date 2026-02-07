#include <iostream>
#include <string>

int main() {
    std::cout << "================================" << std::endl;
    std::cout << "  Build Test Successful!" << std::endl;
    std::cout << "================================" << std::endl;
    
    // Display compiler info
#if defined(_MSC_VER)
    std::cout << "Compiler: MSVC " << _MSC_VER << std::endl;
#elif defined(__clang__)
    std::cout << "Compiler: Clang " << __clang_major__ << "." << __clang_minor__ << "." << __clang_patchlevel__ << std::endl;
    #if defined(_MSC_VER)
        std::cout << "Frontend: clang-cl (MSVC-compatible)" << std::endl;
    #else
        std::cout << "Frontend: clang (GNU-compatible)" << std::endl;
    #endif
#elif defined(__GNUC__)
    std::cout << "Compiler: GCC " << __GNUC__ << "." << __GNUC_MINOR__ << "." << __GNUC_PATCHLEVEL__ << std::endl;
#else
    std::cout << "Compiler: Unknown" << std::endl;
#endif

    // Display platform
#if defined(_WIN32)
    std::cout << "Platform: Windows" << std::endl;
#elif defined(__linux__)
    std::cout << "Platform: Linux" << std::endl;
#else
    std::cout << "Platform: Unknown" << std::endl;
#endif

    // Display architecture
#if defined(_M_X64) || defined(__x86_64__)
    std::cout << "Architecture: x64" << std::endl;
#elif defined(_M_IX86) || defined(__i386__)
    std::cout << "Architecture: x86" << std::endl;
#else
    std::cout << "Architecture: Unknown" << std::endl;
#endif

    std::cout << "================================" << std::endl;
    
    return 0;
}
