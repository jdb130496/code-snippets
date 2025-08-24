#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <windows.h>
#include <wincrypt.h>
#include <boost/thread.hpp>
#include <boost/thread/mutex.hpp>
#include <boost/thread/lock_guard.hpp>
#include <iostream>
#include <vector>
#include <cstring>
#include <ctime>
#include <cstdlib>
#include <memory>
#include <stdexcept>

#pragma comment(lib, "advapi32.lib")

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

// Global instance with proper initialization
static GlobalNumbersManager g_numbersManager;

// Function to perform CPUID instruction with error handling
inline bool cpuid_safe(unsigned int op, unsigned int subfunc, unsigned int info[4]) {
    try {
        memset(info, 0, sizeof(unsigned int) * 4);
        
#ifdef _MSC_VER
        __cpuid((int*)info, op);
#elif defined(__GNUC__)
        asm volatile("cpuid"
                     : "=a"(info[0]), "=b"(info[1]), "=c"(info[2]), "=d"(info[3])
                     : "a"(op), "c"(subfunc)
                     : );
#else
        return false;
#endif
        return true;
    } catch (...) {
        return false;
    }
}

// Check if RDSEED is supported with better error handling
inline int RdSeed_cpuid(void) {
    unsigned int info[4] = {0};
    
    // Are we on an Intel or AMD processor?
    if (!cpuid_safe(0, 0, info)) {
        return 0;
    }
    
    bool isIntel = (memcmp(&info[1], "Genu", 4) == 0 &&
                    memcmp(&info[3], "ineI", 4) == 0 &&
                    memcmp(&info[2], "ntel", 4) == 0);
    
    bool isAMD = (memcmp(&info[1], "Auth", 4) == 0 &&
                  memcmp(&info[3], "enti", 4) == 0 &&
                  memcmp(&info[2], "cAMD", 4) == 0);
    
    if (!isIntel && !isAMD) {
        return 0;
    }
    
    // Do we have RDSEED?
    if (!cpuid_safe(7, 0, info)) {
        return 0;
    }
    
    return (info[1] & RDSEED_MASK) == RDSEED_MASK ? 1 : 0;
}

// Enhanced fallback random number generator
inline unsigned long long fallback_random() {
    HCRYPTPROV hCryptProv = 0;
    unsigned long long rand_val = 0;
    
    // Try Windows CryptGenRandom first
    if (CryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)) {
        BOOL success = CryptGenRandom(hCryptProv, sizeof(rand_val), (BYTE*)&rand_val);
        CryptReleaseContext(hCryptProv, 0);
        if (success) {
            return rand_val;
        }
    }
    
    // Fallback to time-based random
    static bool seed_init = false;
    if (!seed_init) {
        srand((unsigned int)time(NULL));
        seed_init = true;
    }
    
    // Create a more random value using multiple rand() calls
    rand_val = 0;
    for (int i = 0; i < 8; ++i) {
        rand_val = (rand_val << 8) | (rand() & 0xFF);
    }
    
    return rand_val;
}

// Safe RDSEED implementation with comprehensive error handling
inline bool rdseed64_step_safe(unsigned long long* dest) {
    if (!dest) return false;
    
    static int rdseed_supported = -1;
    
    // Check CPU support once
    if (rdseed_supported == -1) {
        rdseed_supported = RdSeed_cpuid();
    }
    
    // Use fallback if RDSEED is not supported
    if (!rdseed_supported) {
        *dest = fallback_random();
        return true;
    }
    
    // Try RDSEED instruction with proper error handling
    int success = 0;
    unsigned long long value = 0;
    
    try {
#if defined(__GNUC__) && (defined(__i386__) || defined(__x86_64__))
        // GCC inline assembly for RDSEED
        asm volatile(
            "rdseed %0\n\t"
            "setc %b1"
            : "=r"(value), "=q"(success)
            :
            : "cc"
        );
        
        if (success) {
            *dest = value;
            return true;
        }
#endif
    } catch (...) {
        // Assembly failed, use fallback
    }
    
    // If RDSEED failed or not available, use secure fallback
    *dest = fallback_random();
    return true;
}

// Thread-safe task class with RAII
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
                unsigned long long randomNumber = 0;
                
                // Generate random number with retry logic
                const int MAX_ATTEMPTS = 5;
                bool success = false;
                
                for (int attempt = 0; attempt < MAX_ATTEMPTS && !success; ++attempt) {
                    success = rdseed64_step_safe(&randomNumber);
                    
                    if (!success) {
                        // Small delay to prevent tight loop
                        boost::this_thread::sleep_for(boost::chrono::microseconds(1));
                    }
                }
                
                // Ensure we have a valid number
                if (!success) {
                    randomNumber = fallback_random();
                }
                
                // Scale to desired range: [100000000000000, 999999999999999]
                randomNumber = (randomNumber % 900000000000000ULL) + 100000000000000ULL;
                localNumbers.push_back(randomNumber);
            }
        } catch (const std::exception&) {
            // Ensure we don't throw from thread
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

// C interface with comprehensive error handling
extern "C" {
    
__declspec(dllexport) void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup) {
    try {
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
        
    } catch (const std::exception&) {
        // Clear on error
        g_numbersManager.clear();
    } catch (...) {
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
        // Initialize on process attach
        break;
    case DLL_THREAD_ATTACH:
    case DLL_THREAD_DETACH:
        break;
    case DLL_PROCESS_DETACH:
        // Cleanup on process detach
        g_numbersManager.clear();
        break;
    }
    return TRUE;
}

// Compilation command for MSYS2:
// g++ -std=c++14 -O2 -march=native -I/ucrt64/include -L/ucrt64/lib -lboost_thread-mt -lboost_system-mt -ladvapi32 -shared -o rdseed_boost_new_claude.dll rdseed_boost_new_claude.cpp
