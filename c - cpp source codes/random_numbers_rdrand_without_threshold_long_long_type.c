#include <stdio.h>
#include <immintrin.h>
#include <stdbool.h>
#include <stdlib.h>

#define NUM_NUMBERS 45000000
#define TABLE_SIZE (NUM_NUMBERS * 2)

typedef struct Entry {
    long long value;
    bool used;
} Entry;

Entry hash_table[TABLE_SIZE];

long long hash(long long value) {
    return value % TABLE_SIZE;
     /*printf("value\n",value);*/
}

bool contains(long long value) {
   long long index = hash(value);
    while (hash_table[index].used) {
        /*printf("while (hash_table[index].used) being executed\n");*/
        if (hash_table[index].value == value) {
             /*printf("Contains Function loop ending with return true condition\n");*/
            return true;
        }
         /*printf("index = (index + 1) % TABLE_SIZE;\n");*/
	index = (index + 1) % TABLE_SIZE;
    }
     /*printf("Contains Function loop ending with return false condition\n");*/
    return false;
}

void insert(long long value) {
     /*printf("insert function being executed\n");*/
    long long index = hash(value);
     /*printf("hash(value: %11d\n");*/
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
	    rand = llabs(rand);
        } while (contains(rand));
        insert(llabs(rand));
        fprintf(file, "%llu\n", rand);
    }

    fclose(file);
    return 0;
}

