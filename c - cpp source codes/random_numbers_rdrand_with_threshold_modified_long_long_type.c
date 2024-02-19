#include <stdio.h>
#include <immintrin.h>
#include <stdbool.h>

#define MIN_VALUE 1000000000
#define NUM_NUMBERS 45000000
#define TABLE_SIZE (NUM_NUMBERS * 2)

typedef struct Entry {
    long long value;
    bool used;
} Entry;

Entry hash_table[TABLE_SIZE];

long long hash(long long value) {
    return value % TABLE_SIZE;
}

bool contains(long long value) {
    long long index = hash(value);
    while (hash_table[index].used) {
        if (hash_table[index].value == value) {
            return true;
        }
        index = (index + 1) % TABLE_SIZE;
    }
    return false;
}

void insert(long long value) {
    long long index = hash(value);
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

    long long rand;
    for (int i = 0; i < NUM_NUMBERS; i++) {
        do {
            _rdrand64_step(&rand);
        } while (rand <= MIN_VALUE || contains(rand));
        insert(rand);
        fprintf(file, "%llu\n", rand);
    }

    fclose(file);
    return 0;
}

