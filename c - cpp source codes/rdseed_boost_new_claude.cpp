#define BOOST_BIND_GLOBAL_PLACEHOLDERS
#include <windows.h>
#include <boost/thread.hpp>
#include <boost/bind.hpp>
#include <iostream>
#include <vector>
#include <cstring>
#include <ctime>  // for time() function
#include <cstdlib> // for srand() and rand() functions
// Removed the immintrin.h include since we're using inline assembly instead

#define RDSEED_MASK 0x00040000

// Function to perform CPUID instruction
inline void cpuid(unsigned int op, unsigned int subfunc, unsigned int info[4]) {
#ifdef _MSC_VER
    __cpuid((int*)info, op);
#else
    asm volatile("cpuid"
                 : "=a"(info[0]), "=b"(info[1]), "=c"(info[2]), "=d"(info[3])
                 : "a"(op), "c"(subfunc));
#endif
}

// Check if RDSEED is supported
inline int RdSeed_cpuid(void) {
    unsigned int info[4] = {0};
    
    // Are we on an Intel or AMD processor?
    cpuid(0, 0, info);
    if (!(( memcmp((void *) &info[1], (void *) "Genu", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "ineI", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "ntel", 4) == 0 )
        ||
        ( memcmp((void *) &info[1], (void *) "Auth", 4) == 0 &&
        memcmp((void *) &info[3], (void *) "enti", 4) == 0 &&
        memcmp((void *) &info[2], (void *) "cAMD", 4) == 0 )))
        return 0;
    
    // Do we have RDSEED?
    cpuid(7, 0, info);
    int ebx = info[1];
    if ((ebx & RDSEED_MASK) == RDSEED_MASK)
        return 1;
    else
        return 0;
}

// Fallback random number generator using less secure but more available methods
inline unsigned long long fallback_random() {
    // Use Windows API for random numbers as fallback
    HCRYPTPROV hCryptProv = 0;
    unsigned long long rand_val = 0;
    
    if (CryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, CRYPT_VERIFYCONTEXT)) {
        CryptGenRandom(hCryptProv, sizeof(rand_val), (BYTE*)&rand_val);
        CryptReleaseContext(hCryptProv, 0);
    } else {
        // If CryptGenRandom fails, use a very simple fallback (not recommended for production)
        rand_val = ((unsigned long long)rand() << 32) | rand();
    }
    
    return rand_val;
}

// Custom replacement for _rdseed64_step function
inline int rdseed64_step_replacement(unsigned long long* dest) {
    // Check if RDSEED is supported
    static int rdseed_supported = -1;
    
    // Only check CPU support once
    if (rdseed_supported == -1) {
        rdseed_supported = RdSeed_cpuid();
    }
    
    // Use fallback if RDSEED is not supported
    if (!rdseed_supported) {
        *dest = fallback_random();
        return 1; // Always return success for fallback method
    }
    
    int success;
    asm volatile(
        "1:\n"
        "rdseed %0\n"
        "jc 2f\n"        // Jump if carry flag is set (indicating success)
        "xor %1, %1\n"   // Set success to 0 (failed)
        "jmp 3f\n"
        "2:\n"
        "mov $1, %1\n"   // Set success to 1 (success)
        "3:\n"
        : "=r"(*dest), "=r"(success)
        :
        : "cc"
    );
    return success;
}

class Task {
public:
    Task(int numNumbers) : numNumbers(numNumbers) {}
    void operator()() {
        for(int i = 0; i < numNumbers; ++i) {
            unsigned long long randomNumber;
            
            // Try up to MAX_ATTEMPTS times to get a valid random number
            const int MAX_ATTEMPTS = 10;
            int attempts = 0;
            bool success = false;
            
            do {
                success = rdseed64_step_replacement(&randomNumber);
                if (!success) {
                    // Add a small delay if needed to prevent tight loop
                    asm volatile("pause" ::: "memory");
                    
                    // After several failed attempts, just use the fallback
                    if (++attempts >= MAX_ATTEMPTS) {
                        randomNumber = fallback_random();
                        success = true;
                    }
                }
            } while (!success);
            
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
    // Initialize random seed for fallback generator
    srand((unsigned int)time(NULL));
    
    // Check if RDSEED is supported
    int rdseed_supported = RdSeed_cpuid();
    if (!rdseed_supported) {
        std::cerr << "Warning: RDSEED instruction not supported by this CPU. Using fallback random generator." << std::endl;
    }
    
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
//Compilation in Msys: clang rdseed_boost_new_claude.cpp -march=native -lstdc++ -lpthread -lboost_thread-mt -shared -o rdseed_boost_new_claude.dll
