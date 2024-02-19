#include <pthread.h>
#include <immintrin.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define MAX_DIGITS 15

typedef struct {
    uint64_t *numbers;
    int start;
    int end;
} thread_data_t;

unsigned long long *numbers;  // Make numbers global so it can be accessed by get_numbers

__declspec(dllexport) int rdrand64_step(unsigned long long *rand)
{
    return _rdrand64_step(rand);
}

void *generate_random_numbers_thread(void *arg) {
    thread_data_t *data = (thread_data_t *)arg;
    unsigned long long rand;
    for (int i = data->start; i < data->end; i++) {
        do {
            if (!rdrand64_step(&rand)) {
                printf("Failed to generate a random number.\n");
            }
            rand = rand % (999999999999999 + 1);
        } while (rand < 100000000000000); // Ensure the number is 15 digits long
        data->numbers[i] = rand;
    }
    return NULL;
}

__declspec(dllexport) void generate_random_numbers(int num_threads, int num_numbers)
{
    pthread_t threads[num_threads];
    thread_data_t thread_data[num_threads];
    numbers = (unsigned long long*)malloc(num_numbers * sizeof(unsigned long long));
    if (numbers == NULL) {
        fprintf(stderr, "Failed to allocate memory.\n");
        return;
    }

    int numbers_per_thread = num_numbers / num_threads;
    for (int i = 0; i < num_threads; i++) {
        thread_data[i].numbers = numbers;
        thread_data[i].start = i * numbers_per_thread;
        thread_data[i].end = (i == num_threads - 1) ? num_numbers : (i + 1) * numbers_per_thread;
        if (pthread_create(&threads[i], NULL, generate_random_numbers_thread, &thread_data[i]) != 0) {
            fprintf(stderr, "Failed to create thread.\n");
            return;
        }
    }

    for (int i = 0; i < num_threads; i++) {
        if (pthread_join(threads[i], NULL) != 0) {
            fprintf(stderr, "Failed to join thread.\n");
            return;
        }
    }

    // numbers now contains your random numbers
    // don't forget to free(numbers) when you're done with it
}

__declspec(dllexport) unsigned long long* get_numbers()
{
    return numbers;
}

__declspec(dllexport) void free_numbers(unsigned long long *numbers)
{
    free(numbers);
}

