#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <glib.h>

// Function to match pattern in an array of strings
int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array, GError **error) {
    GRegex *regex = g_regex_new(pattern, 0, 0, error);
    if (*error) {
        fprintf(stderr, "Error compiling regex: %s\n", (*error)->message);
        return -1;
    }

    int match_count = 0;
    char **matches = NULL;

    for (int i = 0; i < array_length; i++) {
        if (g_regex_match(regex, input_array[i], 0, NULL)) {
            matches = realloc(matches, (match_count + 1) * sizeof(char *));
            if (!matches) {
                g_regex_unref(regex);
                return -1;
            }
            matches[match_count] = input_array[i]; // Store pointers, no duplication
            match_count++;
        }
    }

    g_regex_unref(regex);
    *output_array = matches;
    return match_count;
}

// Function to free the array of matched strings
void free_matches(char **matches) {
    free(matches);
}

// Example usage
int main() {
    GError *error = NULL;
    char *input_array[] = {"string1", "string2", "string3"};
    int array_length = sizeof(input_array) / sizeof(input_array[0]);
    const char *pattern = "string"; // Example pattern
    char **matches;

    int match_count = match_pattern_in_array(input_array, array_length, pattern, &matches, &error);
    if (match_count == -1) {
        // Handle error
    } else {
        for (int i = 0; i < match_count; i++) {
            printf("Matched string: %s\n", matches[i]);
        }
        free_matches(matches);
    }

    return 0;
}
