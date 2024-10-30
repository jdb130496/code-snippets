#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#define PCRE2_CODE_UNIT_WIDTH 8
#include <pcre2.h>

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

int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array) {
    pcre2_code *re;
    PCRE2_SPTR pattern_str = (PCRE2_SPTR)pattern;
    int errornumber;
    PCRE2_SIZE erroroffset;
    pcre2_match_data *match_data;
    int match_count = 0;

    // Compile the regular expression
    re = pcre2_compile(
        pattern_str,               // the pattern
        PCRE2_ZERO_TERMINATED,     // indicates pattern is zero-terminated
        0,                         // default options
        &errornumber,              // for error number
        &erroroffset,              // for error offset
        NULL);                     // use default compile context

    if (re == NULL) {
        PCRE2_UCHAR buffer[256];
        pcre2_get_error_message(errornumber, buffer, sizeof(buffer));
        fprintf(stderr, "PCRE2 compilation failed at offset %d: %s\n", (int)erroroffset, buffer);
        return 0;
    }

    // Allocate memory for the output array
    *output_array = (char**)malloc(array_length * sizeof(char*));
    if (*output_array == NULL) {
        fprintf(stderr, "Memory allocation failed\n");
        pcre2_code_free(re);
        return 0;
    }

    // Match the pattern against each input string
    match_data = pcre2_match_data_create_from_pattern(re, NULL);
    for (int i = 0; i < array_length; i++) {
        char* lower_input = str_to_lower(input_array[i]);
        if (lower_input == NULL) {
            continue;
        }
        int rc = pcre2_match(
            re,                   // the compiled pattern
            (PCRE2_SPTR)lower_input, // the subject string
            strlen(lower_input),  // the length of the subject
            0,                    // start at offset 0 in the subject
            0,                    // default options
            match_data,           // block for storing the result
            NULL);                // use default match context

        free(lower_input);
        if (rc >= 0) {
            (*output_array)[match_count] = strdup(input_array[i]);
            match_count++;
        }
    }

    // Free the compiled regular expression and match data
    pcre2_match_data_free(match_data);
    pcre2_code_free(re);

    return match_count;
}

void free_matches(char** matches, int match_count) {
    for (int i = 0; i < match_count; i++) {
        free(matches[i]);
    }
    free(matches);
}
//Compilation Msys2:  gcc -shared -o regex-c-msys-single-threading.dll regex-c-msys-single-threading.c -lpcre2-8
