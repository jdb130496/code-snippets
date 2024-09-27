#include <pthread.h>
#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

unsigned long long *numbers;
unsigned long long N = 999999999999999; // Change this to your desired maximum number

__declspec(dllexport) int rdrand64_step(unsigned long long *rand)
{
    return _rdrand64_step(rand);
}

__declspec(dllexport) void generate_random_numbers(int num_threads, int num_numbers)
{
    unsigned long long rand;
    for (int thread_num = 0; thread_num < num_threads; thread_num++) {
        for (int i = 0; i < num_numbers / num_threads; i++) {
            do {
                if (!rdrand64_step(&rand)) {
                    printf("Failed to generate random number.\n");
                }
                rand = rand % (N + 1);
            } while (rand < 100000000000000); // Ensure the number is 15 digits long
            numbers[thread_num * num_numbers / num_threads + i] = rand;
        }
    }
}

__declspec(dllexport) unsigned long long* get_numbers()
{
    return numbers;
}

__declspec(dllexport) void allocate_memory(int num_numbers)
{
    numbers = (unsigned long long*)malloc(num_numbers * sizeof(unsigned long long));
}

__declspec(dllexport) void free_memory()
{
    free(numbers);
}

