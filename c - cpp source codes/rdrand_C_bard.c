#include <stdio.h>
#include <immintrin.h>
#include <stdlib.h>

int main() {
    unsigned int num_numbers;
    printf("Enter the number of random numbers to generate: ");
    scanf("%u", &num_numbers);

    FILE *fp = fopen("random_numbers.txt", "w");
    if (fp == NULL) {
        printf("Error opening file.\n");
        return 1;
    }

    for (unsigned int i = 0; i < num_numbers; i++) {
        unsigned long long random_value;
        while (!_rdrand64_step(&random_value)) {
            // Retry if RDRAND fails temporarily
        }
        fprintf(fp, "%llu\n", random_value);
    }

    fclose(fp);
    printf("Random numbers generated and saved to random_numbers.txt\n");

    return 0;
}

