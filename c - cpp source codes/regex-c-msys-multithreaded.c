#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <regex.h>

typedef struct {
    const char** input_array;
    int array_length;
    const char* pattern;
    char*** output_array;
    int* num_matches;
} thread_data_t;

void* match_patterns_thread(void* arg) {
    thread_data_t* data = (thread_data_t*)arg;
    regex_t regex;
    regcomp(&regex, data->pattern, REG_ICASE | REG_EXTENDED);

    int match_count = 0;
    char** matches = (char**)malloc(data->array_length * sizeof(char*));
    if (matches == NULL) {
        pthread_exit(NULL);
    }

    for (int i = 0; i < data->array_length; i++) {
        if (regexec(&regex, data->input_array[i], 0, NULL, 0) == 0) {
            matches[match_count] = strdup(data->input_array[i]);
            if (matches[match_count] == NULL) {
                for (int j = 0; j < match_count; j++) {
                    free(matches[j]);
                }
                free(matches);
                pthread_exit(NULL);
            }
            match_count++;
        }
    }

    regfree(&regex);
    *data->output_array = matches;
    *data->num_matches = match_count;
    pthread_exit(NULL);
}

__declspec(dllexport) int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array) {
    pthread_t thread;
    thread_data_t data = {input_array, array_length, pattern, output_array, 0};
    int num_matches = 0;
    data.num_matches = &num_matches;

    if (pthread_create(&thread, NULL, match_patterns_thread, &data) != 0) {
        return 0;
    }

    pthread_join(thread, NULL);
    return num_matches;
}

__declspec(dllexport) void free_matches(char** matches, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
}
//compilation in msys: gcc -shared -o regex-c-msys-multithreaded.dll regex-c-msys-multithreaded.c -lpthread -lregex
