#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <glib.h>
#include <pthread.h> // Include the pthread library for thread-related functions

// Define thread-local storage for matches array
__thread char **matches = NULL;
__thread int match_count = 0;

// Mutex for protecting shared resources
pthread_mutex_t matches_mutex = PTHREAD_MUTEX_INITIALIZER;

// Function to match pattern in an array of strings
int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array) {
    GError *error = NULL;
    GRegex *regex = g_regex_new(pattern, 0, 0, &error);

    if (error) {
        fprintf(stderr, "Error compiling regex: %s\n", error->message);
        g_error_free(error);
        return -1;
    }

    // Initialize thread-local matches array
    matches = NULL;
    match_count = 0;

    for (int i = 0; i < array_length; i++) {
        if (g_regex_match(regex, input_array[i], 0, NULL)) {
            // Acquire the mutex before modifying shared resources
            pthread_mutex_lock(&matches_mutex);

            // Reallocate memory if needed
            if (match_count == 0) {
                matches = malloc(sizeof(char *));
            } else {
                matches = realloc(matches, (match_count + 1) * sizeof(char *));
            }

            if (!matches) {
                pthread_mutex_unlock(&matches_mutex);
                g_regex_unref(regex);
                return -1;
            }

            matches[match_count] = strdup(input_array[i]);
            if (!matches[match_count]) {
                pthread_mutex_unlock(&matches_mutex);
                g_regex_unref(regex);
                return -1;
            }

            match_count++;

            // Release the mutex after modifying shared resources
            pthread_mutex_unlock(&matches_mutex);
        }
    }

    g_regex_unref(regex);

    *output_array = matches;
    return match_count;
}

// Function to free the array of matched strings
void free_matches(char **matches, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
}

//Compilation: gcc regex-C-10072024.c -shared $(pkg-config --cflags --libs glib-2.0) -o regex-C-10072024.dll
