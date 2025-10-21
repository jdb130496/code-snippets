#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <windows.h>
#include <boost/thread.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/lock_guard.hpp>
#include <iostream>
#include <vector>
#include <cstring>
#include <stdexcept>

#pragma comment(lib, "advapi32.lib")

// Masks and CPU detection from the C file
#define RDSEED_MASK 0x00040000

// Global state management with RAII
class GlobalNumbersManager {
private:
    std::vector<unsigned long long> numbers;
    mutable boost::mutex mutex;
    
public:
    void clear() {
        boost::lock_guard<boost::mutex> lock(mutex);
        numbers.clear();
    }
    
    void reserve(size_t size) {
        boost::lock_guard<boost::mutex> lock(mutex);
        numbers.reserve(size);
    }
    
    void addNumbers(const std::vector<unsigned long long>& newNumbers) {
        boost::lock_guard<boost::mutex> lock(mutex);
        numbers.insert(numbers.end(), newNumbers.begin(), newNumbers.end());
    }
    
    unsigned long long* getData() const {
        boost::lock_guard<boost::mutex> lock(mutex);
        return numbers.empty() ? nullptr : const_cast<unsigned long long*>(numbers.data());
    }
    
    size_t size() const {
        boost::lock_guard<boost::mutex> lock(mutex);
        return numbers.size();
    }
};

// Global instance
static GlobalNumbersManager g_numbersManager;

// CPUID function exactly from the C file
void cpuid(unsigned int op, unsigned int subfunc, unsigned int reg[4]) {
#ifdef _WIN64
    // For 64-bit Windows with GCC/Clang
    asm volatile("cpuid"
                 : "=a"(reg[0]), "=b"(reg[1]), "=c"(reg[2]), "=d"(reg[3])
                 : "a"(op), "c"(subfunc)
                 : );
#else
    // For 32-bit or other cases
    asm volatile("push %%rbx      \n\t" /* save %ebx */
                 "cpuid            \n\t"
                 "movl %%ebx, %1   \n\t" /* save what cpuid just put in %ebx */
                 "pop %%rbx       \n\t" /* restore the old %ebx */
                 : "=a"(reg[0]), "=r"(reg[1]), "=c"(reg[2]), "=d"(reg[3])
                 : "a"(op), "c"(subfunc)
                 : "cc");
#endif
}

// RdSeed CPU check exactly from the C file
int RdSeed_cpuid(void) {
    /*unsigned int info[4] = {-1, -1, -1, -1}; */
    unsigned int info[4];
    memset(info, 0xFF, sizeof(info));
    /* Are we on an Intel or AMD processor? */
    cpuid(0, 0, info);

    if (!(( memcmp((void *) &info[1], (void *) "Genu", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "ineI", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "ntel", 4) == 0 )
        ||
        ( memcmp((void *) &info[1], (void *) "Auth", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "enti", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "cAMD", 4) == 0 )))
        return 0;

    /* Do we have RDSEED? */
    cpuid(7, 0, info);
    int ebx = info[1];
    if ((ebx & RDSEED_MASK) == RDSEED_MASK)
        return 1;
    else
        return 0; // Return 0 instead of info[1] like in original
}

// RDSEED instruction exactly from the C file (64-bit version)
#define GETSEED(rando) asm volatile("1:\n"                    \
                                    "rdseed  %0\n"            \
                                    "jnc 1b\n"                \
                                    :"=a"(rando) : : "cc")

// Get 64 random bits using RDSEED exactly from the C file
unsigned long long get_bits_using_rdseed(void) {
    unsigned long int rando = 0;
    GETSEED(rando);
    return rando;
}

// Thread-safe task class - now only uses pure RDSEED
class RandomNumberTask {
private:
    int targetCount;
    std::vector<unsigned long long> localNumbers;
    
public:
    explicit RandomNumberTask(int count) : targetCount(count) {
        if (count <= 0) {
            throw std::invalid_argument("Count must be positive");
        }
        localNumbers.reserve(count);
    }
    
    void operator()() {
        try {
            for (int i = 0; i < targetCount; ++i) {
                // Use pure RDSEED from the C file - no fallbacks
                unsigned long long randomNumber = get_bits_using_rdseed();
                
                // Scale to desired range: [100000000000000, 999999999999999]
                randomNumber = (randomNumber % 900000000000000ULL) + 100000000000000ULL;
                localNumbers.push_back(randomNumber);
            }
        } catch (const std::exception&) {
            localNumbers.clear();
        } catch (...) {
            localNumbers.clear();
        }
    }
    
    std::vector<unsigned long long> getNumbers() const {
        return localNumbers;
    }
    
    size_t getCount() const {
        return localNumbers.size();
    }
};

// C interface
extern "C" {
    
__declspec(dllexport) int checkRdseedSupport() {
    return RdSeed_cpuid();
}

__declspec(dllexport) void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup) {
    try {
        // First check if RDSEED is supported
        if (!RdSeed_cpuid()) {
            std::cerr << "RDSEED instruction not supported on this CPU!" << std::endl;
            return;
        }
        
        // Validate input parameters
        if (numNumbers <= 0 || numThreadGroups <= 0 || numThreadsPerGroup <= 0) {
            return;
        }
        
        // Prevent excessive resource usage
        const int MAX_NUMBERS = 100000000;  // 100M max
        const int MAX_THREADS = 1000;
        
        if (numNumbers > MAX_NUMBERS) return;
        if (numThreadGroups * numThreadsPerGroup > MAX_THREADS) return;
        
        // Clear and prepare global storage
        g_numbersManager.clear();
        g_numbersManager.reserve(numNumbers);
        
        // Calculate work distribution
        int totalTasks = numThreadGroups * numThreadsPerGroup;
        int numbersPerTask = numNumbers / totalTasks;
        int remainder = numNumbers % totalTasks;
        
        // Process each thread group
        for (int group = 0; group < numThreadGroups; ++group) {
            boost::thread_group threadGroup;
            std::vector<std::unique_ptr<RandomNumberTask>> tasks;
            
            // Create tasks for this group
            for (int thread = 0; thread < numThreadsPerGroup; ++thread) {
                int taskIndex = group * numThreadsPerGroup + thread;
                int numbersForThisTask = numbersPerTask + (taskIndex < remainder ? 1 : 0);
                
                if (numbersForThisTask > 0) {
                    auto task = std::make_unique<RandomNumberTask>(numbersForThisTask);
                    auto taskPtr = task.get();
                    tasks.push_back(std::move(task));
                    
                    threadGroup.create_thread(boost::ref(*taskPtr));
                }
            }
            
            // Wait for all threads in this group
            threadGroup.join_all();
            
            // Collect results
            for (const auto& task : tasks) {
                if (task && task->getCount() > 0) {
                    g_numbersManager.addNumbers(task->getNumbers());
                }
            }
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Exception in generateRandomNumbersC: " << e.what() << std::endl;
        g_numbersManager.clear();
    } catch (...) {
        std::cerr << "Unknown exception in generateRandomNumbersC" << std::endl;
        g_numbersManager.clear();
    }
}

__declspec(dllexport) unsigned long long* getNumbersC() {
    try {
        return g_numbersManager.getData();
    } catch (...) {
        return nullptr;
    }
}

__declspec(dllexport) int getNumbersSizeC() {
    try {
        size_t size = g_numbersManager.size();
        return size > INT_MAX ? INT_MAX : static_cast<int>(size);
    } catch (...) {
        return 0;
    }
}

} // extern "C"

BOOL APIENTRY DllMain(HMODULE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
    case DLL_PROCESS_ATTACH:
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
        break;
    case DLL_PROCESS_DETACH:
        g_numbersManager.clear();
        break;
    }
    return TRUE;
}

// Compilation command for MSYS2:
// g++ -std=c++14 -O2 -march=native -I/ucrt64/include -L/ucrt64/lib -lboost_thread-mt -lboost_system-mt -ladvapi32 -shared -o rdseed_boost_pure.dll rdseed_boost_new_claude.cpp

