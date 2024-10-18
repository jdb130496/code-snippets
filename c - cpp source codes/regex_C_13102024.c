#define PCRE2_CODE_UNIT_WIDTH 8
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pcre2.h>

int match_pattern_in_array(const char **input_array, int array_length, const char *pattern, const char ***output_array) {
    pcre2_code *re;
    PCRE2_SIZE erroffset;
    int errornumber;
    pcre2_match_data *match_data;

    PCRE2_SPTR pattern_str = (PCRE2_SPTR)pattern;
    PCRE2_UCHAR buffer[256];
    re = pcre2_compile(
        pattern_str,
        PCRE2_ZERO_TERMINATED,
        PCRE2_CASELESS,
        &errornumber,
        &erroffset,
        NULL
    );

    if (!re) {
        pcre2_get_error_message(errornumber, buffer, sizeof(buffer));
        fprintf(stderr, "Error compiling regex: %s\n", buffer);
        return -1;
    }

    match_data = pcre2_match_data_create_from_pattern(re, NULL);

    const char **matches = NULL;
    int match_count = 0;

    for (int i = 0; i < array_length; ++i) {
        PCRE2_SPTR subject = (PCRE2_SPTR)input_array[i];
        int rc = pcre2_match(
            re,
            subject,
            strlen((char*)subject),
            0,
            0,
            match_data,
            NULL
        );

        if (rc >= 0) {
            matches = realloc(matches, (match_count + 1) * sizeof(char *));
            if (!matches) {
                for (int j = 0; j < match_count; ++j) free((void *)matches[j]);
                free(matches);
                pcre2_code_free(re);
                pcre2_match_data_free(match_data);
                return -1;
            }
            matches[match_count] = strdup(input_array[i]);
            if (!matches[match_count]) {
                for (int j = 0; j < match_count; ++j) free((void *)matches[j]);
                free(matches);
                pcre2_code_free(re);
                pcre2_match_data_free(match_data);
                return -1;
            }
            match_count++;
        }
    }

    pcre2_code_free(re);
    pcre2_match_data_free(match_data);

    *output_array = matches;
    return match_count;
}

void free_matches(const char **matches, int match_count) {
    for (int i = 0; i < match_count; ++i) {
        free((void *)matches[i]);
    }
    free((void *)matches);
}

