#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <glib.h>

// Custom implementation of getline
ssize_t my_getline(char **lineptr, size_t *n, FILE *stream) {
    if (lineptr == NULL || n == NULL || stream == NULL) {
        return -1;
    }

    char *buf = *lineptr;
    if (buf == NULL) {
        *n = 128;
        buf = malloc(*n);
        if (buf == NULL) {
            return -1;
        }
    }

    size_t pos = 0;
    int c;
    while ((c = fgetc(stream)) != EOF) {
        if (pos + 1 >= *n) {
            *n *= 2;
            buf = realloc(buf, *n);
            if (buf == NULL) {
                return -1;
            }
        }
        buf[pos++] = c;
        if (c == '\n') {
            break;
        }
    }

    if (pos == 0 && c == EOF) {
        return -1;
    }

    buf[pos] = '\0';
    *lineptr = buf;

    return pos;
}

void match_pattern_in_file(const char *filename, const char *pattern) {
    GError *error = NULL;
    GRegex *regex = g_regex_new(pattern, 0, 0, &error);
    
    if (error) {
        fprintf(stderr, "Error compiling regex: %s\n", error->message);
        g_error_free(error);
        return;
    }

    FILE *file = fopen(filename, "r");
    if (!file) {
        perror("Error opening file");
        g_regex_unref(regex);
        return;
    }

    char *line = NULL;
    size_t len = 0;
    ssize_t read;

    while ((read = my_getline(&line, &len, file)) != -1) {
        if (g_regex_match(regex, line, 0, NULL)) {
            printf("%s", line);
        }
    }

    free(line);
    fclose(file);
    g_regex_unref(regex);
}

int main() {
    char filename[256];

    printf("Enter the filename: ");
    if (scanf("%255s", filename) != 1) {
        fprintf(stderr, "Failed to read filename.\n");
        return 1;
    }

    // Clear the input buffer
    int c;
    while ((c = getchar()) != '\n' && c != EOF) {}

    printf("Enter the pattern: ");
    char *pattern = NULL;
    size_t pattern_len = 0;
    ssize_t pattern_read = my_getline(&pattern, &pattern_len, stdin);
    if (pattern_read == -1) {
        fprintf(stderr, "Failed to read pattern.\n");
        free(pattern);
        return 1;
    }

    // Remove the newline character at the end of the pattern, if any
    if (pattern[pattern_read - 1] == '\n') {
        pattern[pattern_read - 1] = '\0';
    }

    match_pattern_in_file(filename, pattern);

    free(pattern);
    return 0;
}
//Compilation on Msys2: gcc regex_example.c `pkg-config --cflags --libs glib-2.0` -o regex_example
