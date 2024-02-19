#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>

int rdrand64_step(unsigned long long *rand)
{
    return _rdrand64_step(rand);
}

int main() {
    unsigned long long rand;
    FILE *file = fopen("rdrand.csv", "w");
    if (file == NULL) {
        printf("Failed to open file.\n");
        return 1;
    }

    for (int i = 0; i < 100000000; i++) {
        if (rdrand64_step(&rand)) {
            fprintf(file, "%llu\n", rand);
        } else {
            printf("Failed to generate random number.\n");
        }
    }

    fclose(file);
    return 0;
}

