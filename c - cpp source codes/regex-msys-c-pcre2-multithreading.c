#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <pthread.h>

#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>

#define MAX_THREADS 8  // You can adjust the number of threads based on the environment

// Mutex for thread synchronization
pthread_mutex_t lock;

// Data structure to pass information to each thread
typedef struct {
    const char* input_str;
    pcre2_code_8* re;
    char** output_array;
    int* match_count;
} ThreadData;

// Function to convert a string to lowercase
char* str_to_lower(const char* str) {
    char* lower_str = strdup(str);
    if (lower_str == NULL) {
        return NULL;
    }
    for (char* p = lower_str; *p; ++p) {
        *p = tolower(*p);
    }
    return lower_str;
}

// Worker function that each thread will run
void* match_pattern_worker(void* arg) {
    ThreadData* data = (ThreadData*)arg;
    pcre2_match_data_8* match_data = pcre2_match_data_create_from_pattern_8(data->re, NULL);

    char* lower_input = str_to_lower(data->input_str);
    if (lower_input == NULL) {
        pcre2_match_data_free_8(match_data);
        return NULL;
    }

    int rc = pcre2_match_8(
        data->re,                   // the compiled pattern
        (PCRE2_SPTR8)lower_input,   // the subject string
        strlen(lower_input),        // the length of the subject
        0,                          // start at offset 0 in the subject
        0,                          // default options
        match_data,                 // block for storing the result
        NULL);                      // use default match context

    free(lower_input);

    if (rc >= 0) {
        // Critical section (lock for safe write)
        pthread_mutex_lock(&lock);
        data->output_array[*data->match_count] = strdup(data->input_str);
        (*data->match_count)++;
        pthread_mutex_unlock(&lock);
    }

    pcre2_match_data_free_8(match_data);
    return NULL;
}

int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array) {
    pcre2_code_8* re;
    PCRE2_SPTR8 pattern_str = (PCRE2_SPTR8)pattern;
    int errornumber;
    PCRE2_SIZE erroroffset;
    int match_count = 0;
    
    // Compile the regular expression
    re = pcre2_compile_8(
        pattern_str,               // the pattern
        PCRE2_ZERO_TERMINATED,     // indicates pattern is zero-terminated
        0,                         // default options
        &errornumber,              // for error number
        &erroroffset,              // for error offset
        NULL);                     // use default compile context

    if (re == NULL) {
        PCRE2_UCHAR8 buffer[256];
        pcre2_get_error_message_8(errornumber, buffer, sizeof(buffer));
        fprintf(stderr, "PCRE2 compilation failed at offset %d: %s\n", (int)erroroffset, buffer);
        return 0;
    }

    // Allocate memory for the output array
    *output_array = (char**)malloc(array_length * sizeof(char*));
    if (*output_array == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        pcre2_code_free_8(re);
        return 0;
    }

    // Initialize the mutex
    pthread_mutex_init(&lock, NULL);

    // Create threads to process each string
    pthread_t threads[MAX_THREADS];
    ThreadData thread_data[MAX_THREADS];
    int thread_index = 0;

    for (int i = 0; i < array_length; i++) {
        // Prepare the data for each thread
        thread_data[thread_index].input_str = input_array[i];
        thread_data[thread_index].re = re;
        thread_data[thread_index].output_array = *output_array;
        thread_data[thread_index].match_count = &match_count;

        // Create a thread to process the input string
        pthread_create(&threads[thread_index], NULL, match_pattern_worker, &thread_data[thread_index]);

        thread_index++;

        // If the maximum number of threads is reached, wait for them to finish
        if (thread_index == MAX_THREADS || i == array_length - 1) {
            for (int j = 0; j < thread_index; j++) {
                pthread_join(threads[j], NULL);
            }
            thread_index = 0;  // Reset thread index for next batch
        }
    }

    // Clean up
    pthread_mutex_destroy(&lock);
    pcre2_code_free_8(re);

    return match_count;
}

void free_matches(char** matches, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
}
//Compilation: gcc -shared -o regex-msys-c-pcre2-multithreading.dll regex-msys-c-pcre2-multithreading.c -lpcre2-8 -lpthread
//Optimization - Reducing Size Of Compiled dll: gcc -shared -o regex-msys-c-pcre2-multithreading.dll regex-msys-c-pcre2-multithreading.c -lpcre2-8 -lpthread -O2 -s -flto -Wl,--gc-sections -fvisibility=hidden
