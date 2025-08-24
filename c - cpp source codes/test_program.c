#include <stdio.h>
#include <stdlib.h>

__declspec(dllimport) void generate_random_numbers(int num_threads, int num_numbers);
__declspec(dllimport) unsigned long long* get_numbers();
__declspec(dllimport) void free_numbers();

int main() {
    int num_numbers = 100000;
    int num_threads = 4;

    generate_random_numbers(num_threads, num_numbers);

    // Retrieve the generated numbers
    unsigned long long* numbers = get_numbers();
    if (numbers == NULL) {
        fprintf(stderr, "Failed to retrieve random numbers.\n");
        return 1;
    }

    // Print the generated numbers
    for (int i = 0; i < num_numbers; i++) {
        printf("%llu\n", numbers[i]);
    }

    // Free the allocated memory
    free_numbers();

    return 0;
}

