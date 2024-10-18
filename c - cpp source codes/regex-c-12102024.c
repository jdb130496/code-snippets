#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pcre2.h>
#include <pthread.h>

#define OVECCOUNT 30    /* For pcre2_match() */
#define MAX_THREADS 4   /* Maximum number of threads */

/* Data passed to each thread */
typedef struct {
    char **input_array;
    char *pattern;
    char ***output_array;
    int start_idx;
    int end_idx;
} thread_data;

/* Function for each thread to execute */
void* regex_match(void* arg) {
    thread_data *data = (thread_data*) arg;

    /* Compile the pattern */
    pcre2_code *re;
    PCRE2_SPTR pattern = (PCRE2_SPTR) data->pattern;
    int errornumber;
    PCRE2_SIZE erroroffset;

    re = pcre2_compile(pattern, PCRE2_ZERO_TERMINATED, 0, &errornumber, &erroroffset, NULL);
    if (re == NULL) {
        fprintf(stderr, "PCRE2 compilation failed at offset %d\n", (int)erroroffset);
        return NULL;
    }

    for (int i = data->start_idx; i < data->end_idx; ++i) {
        PCRE2_SPTR subject = (PCRE2_SPTR) data->input_array[i];
        pcre2_match_data *match_data = pcre2_match_data_create_from_pattern(re, NULL);
        int rc = pcre2_match(re, subject, strlen((char*)subject), 0, 0, match_data, NULL);

        if (rc >= 0) {
            (*data->output_array)[i] = strdup(data->input_array[i]); /* Store matched string */
        } else {
            (*data->output_array)[i] = NULL; /* No match */
        }

        pcre2_match_data_free(match_data);
    }

    pcre2_code_free(re);
    return NULL;
}

/* The main exported function to be called from Python */
__declspec(dllexport) void regex_array_match(char **input_array, int array_size, char *pattern, char ***output_array) {
    pthread_t threads[MAX_THREADS];
    thread_data thread_args[MAX_THREADS];

    /* Allocate memory for output array */
    *output_array = (char **)malloc(array_size * sizeof(char*));
    if (*output_array == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        return;
    }

    int chunk_size = array_size / MAX_THREADS;
    int remainder = array_size % MAX_THREADS;

    for (int i = 0; i < MAX_THREADS; ++i) {
        thread_args[i].input_array = input_array;
        thread_args[i].pattern = pattern;
        thread_args[i].output_array = output_array;
        thread_args[i].start_idx = i * chunk_size;
        thread_args[i].end_idx = (i + 1) * chunk_size;

        /* Handle the remainder in the last thread */
        if (i == MAX_THREADS - 1) {
            thread_args[i].end_idx += remainder;
        }

        pthread_create(&threads[i], NULL, regex_match, &thread_args[i]);
    }

    /* Join all threads */
    for (int i = 0; i < MAX_THREADS; ++i) {
        pthread_join(threads[i], NULL);
    }
}

