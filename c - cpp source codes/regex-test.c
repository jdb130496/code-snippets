#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <windows.h>

// Function pointer types
typedef int (*match_pattern_in_array_t)(char **, int, const char *, char ***);
typedef void (*free_matches_t)(char **, int);

// Function to trim whitespace from the start and end of a string
char *trim_whitespace(char *str) {
    char *end;

    // Trim leading space
    while(isspace((unsigned char)*str)) str++;

    if(*str == 0) // All spaces
        return str;

    // Trim trailing space
    end = str + strlen(str) - 1;
    while(end > str && isspace((unsigned char)*end)) end--;

    // Write new null terminator
    *(end + 1) = 0;

    return str;
}

// Function to parse a Python-like list string into a C array of strings
int parse_list(const char *input, char ***output_array) {
    int count = 0;
    char **array = NULL;
    const char *ptr = input;

    // Count the number of items in the list
    while ((ptr = strchr(ptr, ',')) != NULL) {
        count++;
        ptr++;
    }
    count++; // for the last element

    array = malloc(count * sizeof(char *));
    if (!array) {
        return -1;
    }

    int i = 0;
    const char *start = input;
    while ((ptr = strchr(start, ',')) != NULL) {
        int length = ptr - start;
        array[i] = malloc(length + 1);
        if (!array[i]) {
            for (int j = 0; j < i; j++) {
                free(array[j]);
            }
            free(array);
            return -1;
        }
        strncpy(array[i], start, length);
        array[i][length] = '\0';
        array[i] = trim_whitespace(array[i]);
        i++;
        start = ptr + 1;
    }

    array[i] = strdup(start);
    array[i] = trim_whitespace(array[i]);

    *output_array = array;
    return count;
}

int main() {
    // Load the shared library
    HMODULE handle = LoadLibrary("regex-C-xlwings.dll");
    if (!handle) {
        fprintf(stderr, "Error loading library: %d\n", GetLastError());
        return 1;
    }

    // Load the symbols
    match_pattern_in_array_t match_pattern_in_array = (match_pattern_in_array_t) GetProcAddress(handle, "match_pattern_in_array");
    free_matches_t free_matches = (free_matches_t) GetProcAddress(handle, "free_matches");
    
    if (!match_pattern_in_array || !free_matches) {
        fprintf(stderr, "Error loading symbols: %d\n", GetLastError());
        FreeLibrary(handle);
        return 1;
    }

    // Get user input for the array and pattern
    char list_input[1024];
    char pattern[100];
    
    printf("Enter list (e.g., ['apple','banana','grapes']): ");
    if (fgets(list_input, sizeof(list_input), stdin) == NULL) {
        fprintf(stderr, "Error reading list\n");
        FreeLibrary(handle);
        return 1;
    }

    // Remove surrounding brackets and spaces
    char *list_start = strchr(list_input, '[');
    char *list_end = strrchr(list_input, ']');
    if (!list_start || !list_end || list_end <= list_start) {
        fprintf(stderr, "Invalid list format\n");
        FreeLibrary(handle);
        return 1;
    }

    *list_end = '\0';
    list_start++;
    
    char **input_array;
    int array_length = parse_list(list_start, &input_array);
    if (array_length < 0) {
        fprintf(stderr, "Error parsing list\n");
        FreeLibrary(handle);
        return 1;
    }

    printf("Enter regex pattern: ");
    if (scanf("%99s", pattern) != 1) {
        fprintf(stderr, "Error reading pattern\n");
        for (int i = 0; i < array_length; i++) {
            free(input_array[i]);
        }
        free(input_array);
        FreeLibrary(handle);
        return 1;
    }

    // Call the function from the DLL
    char **output_array;
    int match_count = match_pattern_in_array(input_array, array_length, pattern, &output_array);
    
    if (match_count < 0) {
        fprintf(stderr, "Error matching pattern\n");
        for (int i = 0; i < array_length; i++) {
            free(input_array[i]);
        }
        free(input_array);
        FreeLibrary(handle);
        return 1;
    }

    // Print the results
    printf("Matched %d items:\n", match_count);
    for (int i = 0; i < match_count; i++) {
        printf("%s\n", output_array[i]);
    }

    // Free the matches and the input array
    free_matches(output_array, match_count);
    for (int i = 0; i < array_length; i++) {
        free(input_array[i]);
    }
    free(input_array);

    // Close the shared library
    FreeLibrary(handle);

    return 0;
}

