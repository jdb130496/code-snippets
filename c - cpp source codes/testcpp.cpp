#include <windows.h>
#include <iostream>
#include <vector>

typedef std::vector<unsigned long long> (*GenerateRandomNumbersFunc)(int, int, int);


int main(int argc, char* argv[]) {
    HINSTANCE hGetProcIDDLL = LoadLibrary("boost_rdrand.dll");

    if (!hGetProcIDDLL) {
        std::cout << "Could not load the dynamic library." << std::endl;
        return EXIT_FAILURE;
    }

    GenerateRandomNumbersFunc generateRandomNumbers = (GenerateRandomNumbersFunc) GetProcAddress(hGetProcIDDLL, "generateRandomNumbers");

    if (!generateRandomNumbers) {
        std::cout << "Could not locate the function." << std::endl;
        return EXIT_FAILURE;
    }

    int numNumbers = std::stoi(argv[1]);
    int numWorkers = std::stoi(argv[2]);
    int numThreads = std::stoi(argv[3]);

    std::vector<unsigned long long> numbers = generateRandomNumbers(numNumbers, numWorkers, numThreads);

    for (auto num : numbers) {
        std::cout << num << std::endl;
    }

    FreeLibrary(hGetProcIDDLL);

    return EXIT_SUCCESS;
}
//Compilation: g++ -o testcpp testcpp.cpp -lboost_thread-mt -lboost_system-mt -mrdrnd
