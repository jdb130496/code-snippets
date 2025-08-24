#include <windows.h>
#include <immintrin.h>
#include <stdint.h>

#define MIN_15_DIGITS 100000000000000ULL  // Largest 14-digit number
#define MAX_15_DIGITS 999999999999999ULL  // Largest 15-digit number

__declspec(dllexport) uint64_t *generate_random_numbers(unsigned int num_numbers) {
    uint64_t *random_array = (uint64_t *)malloc(num_numbers * sizeof(uint64_t));
    unsigned int generated_numbers = 0;

    for (unsigned int i = 0; i < num_numbers;) {
        uint64_t random_number;
        while (!_rdrand64_step(&random_number)) {
            // Retry if RDRAND fails temporarily
        }

        if (random_number >= MIN_15_DIGITS && random_number <= MAX_15_DIGITS) {
            random_array[i] = random_number;
            i++;
            generated_numbers++;
        }
    }

    random_array = (uint64_t *)realloc(random_array, generated_numbers * sizeof(uint64_t));

    return random_array;
}

