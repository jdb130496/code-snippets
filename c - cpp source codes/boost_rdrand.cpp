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

extern "C" __declspec(dllexport) std::vector<unsigned long long> generateRandomNumbers(int numNumbers, int numWorkers, int numThreads) {
    boost::thread_group threads;
    std::vector<Worker*> workers;

    for(int i = 0; i < numWorkers; ++i) {
        Worker* worker = new Worker(numNumbers);
        workers.push_back(worker);
        threads.create_thread(boost::ref(*worker));
    }

    threads.join_all();

    std::vector<unsigned long long> allNumbers;
    for(auto& worker : workers) {
        std::vector<unsigned long long> numbers = worker->getNumbers();
        allNumbers.insert(allNumbers.end(), numbers.begin(), numbers.end());
        delete worker;
    }

    return allNumbers;
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
//msys shell compilation: g++ -shared -o boost_rdrand.dll boost_rdrand.cpp -lboost_thread-mt -lboost_system-mt -mrdrnd
