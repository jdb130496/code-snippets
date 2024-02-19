#include <pthread.h>
#include <immintrin.h>
#include <cstdint>
#include <cstdio>
#include <ctime>

#define NUM_THREADS 4
#define NUM_NUMBERS 100000000

int rdrand64_step(unsigned long long *rand)
{
    return _rdrand64_step(rand);
}

void *generate_random_numbers(void *arg)
{
    int thread_num = *(int *)arg;
    char filename[20];
    sprintf(filename, "rdrand%d.csv", thread_num);

    FILE *file = fopen(filename, "w");
    if (file == NULL) {
        printf("Failed to open file.\n");
        return NULL;
    }

    for (int i = 0; i < NUM_NUMBERS / NUM_THREADS; i++) {
        unsigned long long rand;
        if (rdrand64_step(&rand)) {
            fprintf(file, "%llu\n", rand);
        } else {
            printf("Failed to generate random number.\n");
        }
    }

    fclose(file);
    return NULL;
}

int main()
{
    time_t start_time = time(NULL);

    pthread_t threads[NUM_THREADS];
    int thread_nums[NUM_THREADS];
    for (int i = 0; i < NUM_THREADS; i++) {
        thread_nums[i] = i;
        pthread_create(&threads[i], NULL, generate_random_numbers, &thread_nums[i]);
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }

    // Merge files
    FILE *file = fopen("rdrand.csv", "w");
    if (file == NULL) {
        printf("Failed to open file.\n");
        return 1;
    }

    for (int i = 0; i < NUM_THREADS; i++) {
        char filename[20];
        sprintf(filename, "rdrand%d.csv", i);

        FILE *input_file = fopen(filename, "r");
        if (input_file == NULL) {
            printf("Failed to open file.\n");
            return 1;
        }

        char line[256];
        while (fgets(line, sizeof(line), input_file)) {
            fprintf(file, "%s", line);
        }

        fclose(input_file);

        // Delete the temporary file
        remove(filename);
    }

    fclose(file);

    time_t end_time = time(NULL);
    double time_spent = difftime(end_time, start_time);

    int minutes = time_spent / 60;
    int seconds = (int)time_spent % 60;

    printf("Time spent: %d minutes and %d seconds\n", minutes, seconds);

    return 0;
}

