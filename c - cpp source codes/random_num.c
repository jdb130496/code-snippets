#include <stdio.h>
#include <immintrin.h>
#include <stdbool.h>

#define MIN_VALUE 10000000
#define NUM_NUMBERS 45000000
#define TABLE_SIZE (NUM_NUMBERS * 2)

typedef struct Entry {
    unsigned int value;
    bool used;
} Entry;

Entry hash_table[TABLE_SIZE];

unsigned int hash(unsigned int value) {
    return value % TABLE_SIZE;
}

bool contains(unsigned int value) {
    unsigned int index = hash(value);
    while (hash_table[index].used) {
        if (hash_table[index].value == value) {
            return true;
        }
        index = (index + 1) % TABLE_SIZE;
    }
    return false;
}

void insert(unsigned int value) {
    unsigned int index = hash(value);
    while (hash_table[index].used) {
        index = (index + 1) % TABLE_SIZE;
    }
    hash_table[index].value = value;
    hash_table[index].used = true;
}

int main() {
    FILE *file = fopen("random_numbers.csv", "w");
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    unsigned int rand;
    for (int i = 0; i < NUM_NUMBERS; i++) {
        do {
            _rdrand32_step(&rand);
        } while (rand <= MIN_VALUE || contains(rand));
        insert(rand);
        fprintf(file, "%u\n", rand);
    }

    fclose(file);
    return 0;
}

