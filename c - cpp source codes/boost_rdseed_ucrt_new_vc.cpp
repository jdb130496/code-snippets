#define BOOST_ALL_NO_LIB
#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <windows.h>
#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <iostream>
#include <vector>
#include <immintrin.h>

class Task {
public:
    Task(int numNumbers) : numNumbers(numNumbers) {}

    void operator()() {
        for(int i = 0; i < numNumbers; ++i) {
            unsigned long long randomNumber;
            _rdseed64_step(&randomNumber);
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

extern "C" __declspec(dllexport) void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup) {
    // Clear the global numbers vector
    g_numbers.clear();

    // Calculate the number of numbers each task should generate
    int numNumbersPerTask = numNumbers / (numThreadGroups * numThreadsPerGroup);
    int remainder = numNumbers % (numThreadGroups * numThreadsPerGroup);

    for(int i = 0; i < numThreadGroups; ++i) {
        boost::thread_group threadGroup;
        std::vector<Task*> tasks;

        for(int j = 0; j < numThreadsPerGroup; ++j) {
            // If there's a remainder, add one to the number of numbers for this task
            int numNumbersThisTask = numNumbersPerTask + ((i * numThreadsPerGroup + j) < remainder ? 1 : 0);
            Task* task = new Task(numNumbersThisTask);
            tasks.push_back(task);
            threadGroup.create_thread(boost::ref(*task));
        }

        threadGroup.join_all();

        for(auto& task : tasks) {
            std::vector<unsigned long long> numbers = task->getNumbers();
            g_numbers.insert(g_numbers.end(), numbers.begin(), numbers.end());
            delete task;
        }
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
//Compilation using g++ in Msys2: g++ boost_rdseed_ucrt_new.cpp -std=c++26 -march=native -lpthread -lboost_thread-mt -shared -o boost_rdseed_ucrt_new.dll
//Compilation using clang in Msys2: clang boost_rdseed_ucrt_new.cpp -march=native -lstdc++ -lpthread -lboost_thread-mt -shared -o boost_rdseed_ucrt_clang_new.dll
//Compilation Under Windows (VC):
//cl boost_rdseed_ucrt_new_vc.cpp /LD /EHsc /MD /link /LIBPATH:D:\Programs\vsbt\VC\Tools\MSVC\14.41.34120\lib\x64 /LIBPATH:D:\boost\lib /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\um\x64" /LIBPATH:"C:\Program Files (x86)\Windows Kits\10\Lib\10.0.26100.0\ucrt\x64" libboost_thread-vc143-mt-x64-1_86.lib
