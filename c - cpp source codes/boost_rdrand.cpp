#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <windows.h>
#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <iostream>
#include <vector>
#include <immintrin.h>

class Worker {
public:
    Worker(int numNumbers) : numNumbers(numNumbers) {}

    void operator()() {
        for(int i = 0; i < numNumbers; ++i) {
            unsigned long long randomNumber;
            _rdrand64_step(&randomNumber);
            randomNumber = randomNumber % 900000000000000 + 100000000000000;
            boost::lock_guard<boost::mutex> guard(mutex);
            numbers.push_back(randomNumber);
        }
    }

    std::vector<unsigned long long> getNumbers() {
        boost::lock_guard<boost::mutex> guard(mutex);
        return numbers;
    }

private:
    int numNumbers;
    std::vector<unsigned long long> numbers;
    boost::mutex mutex;
};

std::vector<unsigned long long> g_numbers;

extern "C" __declspec(dllexport) void generateRandomNumbersC(int numNumbers, int numWorkers, int numThreads) {
    // Clear the global numbers vector
    g_numbers.clear();

    boost::thread_group threads;
    std::vector<Worker*> workers;

    // Calculate the number of numbers each worker should generate
    int numNumbersPerWorker = numNumbers / numWorkers;
    int remainder = numNumbers % numWorkers;

    for(int i = 0; i < numWorkers; ++i) {
        // If there's a remainder, add one to the number of numbers for this worker
        int numNumbersThisWorker = numNumbersPerWorker + (i < remainder ? 1 : 0);
        Worker* worker = new Worker(numNumbersThisWorker);
        workers.push_back(worker);
        threads.create_thread(boost::ref(*worker));
    }

    threads.join_all();

    for(auto& worker : workers) {
        std::vector<unsigned long long> numbers = worker->getNumbers();
        g_numbers.insert(g_numbers.end(), numbers.begin(), numbers.end());
        delete worker;
    }
}

extern "C" __declspec(dllexport) unsigned long long* getNumbersC() {
    return g_numbers.data();
}

extern "C" __declspec(dllexport) int getNumbersSizeC() {
    return g_numbers.size();
}


BOOL APIENTRY DllMain(HMODULE hModule, DWORD  ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
    case DLL_PROCESS_DETACH:
        break;
    }
    return TRUE;
}

