#include <iostream>
#include <string>
#include <windows.h>
#include <limits>  // Include this for std::numeric_limits

typedef int(__cdecl *MYPROC)(LPWSTR);
typedef void(__cdecl *MYPROC2)(int, int);
typedef void(__cdecl *MYPROC3)(int);
typedef unsigned long long*(__cdecl *MYPROC4)();
typedef void(__cdecl *MYPROC5)();

int read_input(std::string prompt) {
    while (true) {
        std::cout << prompt;
        int num;
        std::cin >> num;
        if (std::cin.fail()) {
            std::cin.clear();
            std::cin.ignore(std::numeric_limits<std::streamsize>::max(), '\n');
            std::cout << "Please enter a valid number!" << std::endl;
        } else {
            return num;
        }
    }
}

int main() {
    HINSTANCE hinstLib;
    MYPROC ProcAdd;
    MYPROC2 ProcAdd2;
    MYPROC3 ProcAdd3;
    MYPROC4 ProcAdd4;
    MYPROC5 ProcAdd5;
    BOOL fFreeResult, fRunTimeLinkSuccess = FALSE;

    // Get a handle to the DLL module.
    hinstLib = LoadLibrary(TEXT("D:/Downloads/rust_dll/target/release/rust_rand_dll_copilot.dll"));

    // If the handle is valid, try to get the function address.
    if (hinstLib != NULL) {
        ProcAdd = (MYPROC)GetProcAddress(hinstLib, "rdrand64_step");
        ProcAdd2 = (MYPROC2)GetProcAddress(hinstLib, "generate_random_numbers");
        ProcAdd3 = (MYPROC3)GetProcAddress(hinstLib, "allocate_memory");
        ProcAdd4 = (MYPROC4)GetProcAddress(hinstLib, "get_numbers");
        ProcAdd5 = (MYPROC5)GetProcAddress(hinstLib, "free_memory");

        // If the function address is valid, call the function.
        if (NULL != ProcAdd && NULL != ProcAdd2 && NULL != ProcAdd3 && NULL != ProcAdd4 && NULL != ProcAdd5) {
            fRunTimeLinkSuccess = TRUE;
            int num_threads = read_input("Enter the number of threads: ");
            int num_numbers = read_input("Enter the number of random numbers: ");
            ProcAdd3(num_numbers);
            ProcAdd2(num_threads, num_numbers);
            unsigned long long* numbers = ProcAdd4();
            std::cout << "Generated random numbers: ";
            for (int i = 0; i < num_numbers; i++) {
                std::cout << numbers[i] << " ";
            }
            std::cout << std::endl;
            ProcAdd5();
        }
        // Free the DLL module.
        fFreeResult = FreeLibrary(hinstLib);
    }

    // If unable to call the DLL function, use an alternative.
    if (!fRunTimeLinkSuccess)
        printf("Message printed from executable\n");

    return 0;
}

