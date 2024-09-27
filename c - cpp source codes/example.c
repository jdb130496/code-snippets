#include <stdio.h>
#include <stdlib.h>

#define NUM_NUMBERS 14

int contains(long long *numbers, size_t len, long long number) {
    for (size_t i = 0; i < len; i++) {
        if (numbers[i] == number) {
            return 1;
        }
    }
    return 0;
}

int main() {
    FILE *file = fopen("random_numbers.csv", "w");
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    long long input_numbers[NUM_NUMBERS] = {1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 1, 4, 5, 1};
    long long *numbers = malloc(NUM_NUMBERS * sizeof(long long));
    size_t len = 0;
    for (size_t i = 0; i < NUM_NUMBERS; i++) {
        long long number = input_numbers[i];
        if (!contains(numbers, len, number)) {
            numbers[len++] = number;
            fprintf(file, "%lld\n", number);
        }
    }

    free(numbers);
    fclose(file);
    return 0;
}

