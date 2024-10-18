#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <glib.h>

int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array) {
    GError *error = NULL;
    GRegex *regex = g_regex_new(pattern, 0, 0, &error);

    if (error) {
        fprintf(stderr, "Error compiling regex: %s\n", error->message);
        g_error_free(error);
        return -1;
    }

    char **matches = malloc(array_length * sizeof(char *));
    if (!matches) {
        g_regex_unref(regex);
        return -1;
    }

    int match_count = 0;
    for (int i = 0; i < array_length; i++) {
        if (g_regex_match(regex, input_array[i], 0, NULL)) {
            matches[match_count] = strdup(input_array[i]);
        } else {
            matches[match_count] = strdup(""); // Maintain blank cells for non-matches
        }
        if (!matches[match_count]) {
            g_regex_unref(regex);
            for (int j = 0; j < match_count; j++) {
                free(matches[j]);
            }
            free(matches);
            return -1;
        }
        match_count++;
    }

    g_regex_unref(regex);
    *output_array = matches;
    return match_count;
}

void free_matches(char **matches, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
}

// Compilation in Msys as shared dll: gcc -shared -o regex-C-xlwings.dll regex-C-xlwings.c $(pkg-config --cflags --libs glib-2.0)
