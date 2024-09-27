#include <pthread.h>
#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <time.h>

#define NUM_THREADS 4
#define NUM_NUMBERS 100000000
#define BUFFER_SIZE 1000

int rdrand64_step(unsigned long long *rand)
{
    return _rdrand64_step(rand);
}

void *generate_random_numbers(void *arg)
{
    int thread_num = *(int *)arg;
    char filename[30];
    sprintf(filename, "/dev/shm/rdrand%d.csv", thread_num);

    FILE *file = fopen(filename, "w");
    if (file == NULL) {
        printf("Failed to open file.\n");
        return NULL;
    }

    unsigned long long buffer[BUFFER_SIZE];
    int buffer_index = 0;

    for (int i = 0; i < NUM_NUMBERS / NUM_THREADS; i++) {
        if (rdrand64_step(&buffer[buffer_index])) {
            buffer_index++;
            if (buffer_index == BUFFER_SIZE) {
                for (int j = 0; j < BUFFER_SIZE; j++) {
                    fprintf(file, "%llu\n", buffer[j]);
                }
                buffer_index = 0;
            }
        } else {
            printf("Failed to generate random number.\n");
        }
    }

    // Write any remaining numbers in the buffer
    for (int j = 0; j < buffer_index; j++) {
        fprintf(file, "%llu\n", buffer[j]);
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
        char filename[30];
        sprintf(filename, "/dev/shm/rdrand%d.csv", i);

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

