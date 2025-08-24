#include <stdio.h>
#include <stdlib.h>

__declspec(dllimport) unsigned long long* generate_random_numbers(int num_numbers, int num_threads);
__declspec(dllimport) void free_numbers();

int main() {
    int num_numbers = 10;
    int num_threads = 2;

    unsigned long long* numbers = generate_random_numbers(num_numbers, num_threads);
    if (numbers == NULL) {
        fprintf(stderr, "Failed to generate random numbers.\n");
        return 1;
    }

    for (int i = 0; i < num_numbers; i++) {
        printf("%llu\n", numbers[i]);
    }

    // Free the allocated memory
    free_numbers();

    return 0;
}

