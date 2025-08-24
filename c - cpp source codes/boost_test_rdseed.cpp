#include <windows.h>
#include <iostream>
#include <vector>

typedef void (*GenerateRandomNumbersC)(int, int, int);
typedef unsigned long long* (*GetNumbersC)();
typedef int (*GetNumbersSizeC)();

int main() {
    HINSTANCE hinstLib = LoadLibrary(TEXT("boost_rdseed_ucrt.dll"));
    if (hinstLib == NULL) {
        std::cerr << "Unable to load DLL!" << std::endl;
        return 1;
    }

    GenerateRandomNumbersC generateRandomNumbersC = (GenerateRandomNumbersC) GetProcAddress(hinstLib, "generateRandomNumbersC");
    GetNumbersC getNumbersC = (GetNumbersC) GetProcAddress(hinstLib, "getNumbersC");
    GetNumbersSizeC getNumbersSizeC = (GetNumbersSizeC) GetProcAddress(hinstLib, "getNumbersSizeC");

    if (generateRandomNumbersC == NULL || getNumbersC == NULL || getNumbersSizeC == NULL) {
        std::cerr << "Unable to get DLL functions!" << std::endl;
        FreeLibrary(hinstLib);
        return 1;
    }

    int numNumbers, numThreadGroups, numThreadsPerGroup;
    std::cout << "Enter the number of random numbers to generate: ";
    std::cin >> numNumbers;
    std::cout << "Enter the number of thread groups: ";
    std::cin >> numThreadGroups;
    std::cout << "Enter the number of threads per group: ";
    std::cin >> numThreadsPerGroup;

    generateRandomNumbersC(numNumbers, numThreadGroups, numThreadsPerGroup);

    int size = getNumbersSizeC();
    unsigned long long* numbers = getNumbersC();
    for (int i = 0; i < size; ++i) {
        std::cout << numbers[i] << std::endl;
    }

    FreeLibrary(hinstLib);
    return 0;
}

