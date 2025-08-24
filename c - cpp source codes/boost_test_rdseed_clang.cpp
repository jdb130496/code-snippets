#include <windows.h>
#include <iostream>
#include <vector>

typedef void (*GenerateRandomNumbersC)(int, int, int);
typedef unsigned long long* (*GetNumbersC)();
typedef int (*GetNumbersSizeC)();

int main() {
    HINSTANCE hGetProcIDDLL = LoadLibrary("boost_rdseed_ucrt_clang.dll");

    if (!hGetProcIDDLL) {
        std::cout << "Could not load the dynamic library." << std::endl;
        return EXIT_FAILURE;
    }

    GenerateRandomNumbersC generateRandomNumbersC = (GenerateRandomNumbersC) GetProcAddress(hGetProcIDDLL, "generateRandomNumbersC");
    GetNumbersC getNumbersC = (GetNumbersC) GetProcAddress(hGetProcIDDLL, "getNumbersC");
    GetNumbersSizeC getNumbersSizeC = (GetNumbersSizeC) GetProcAddress(hGetProcIDDLL, "getNumbersSizeC");

    if (!generateRandomNumbersC || !getNumbersC || !getNumbersSizeC) {
        std::cout << "Could not locate the function." << std::endl;
        return EXIT_FAILURE;
    }

    int numNumbers, numWorkers, numThreads;
    std::cout << "Enter the number of numbers, workers, and threads: ";
    std::cin >> numNumbers >> numWorkers >> numThreads;

    generateRandomNumbersC(numNumbers, numWorkers, numThreads);

    int size = getNumbersSizeC();
    unsigned long long* numbers = getNumbersC();

    for (int i = 0; i < size; ++i) {
        std::cout << numbers[i] << std::endl;
    }

    FreeLibrary(hGetProcIDDLL);
    return EXIT_SUCCESS;
}

