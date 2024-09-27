#define PCRE2_CODE_UNIT_WIDTH 8
#include <iostream>
#include <cstring>
#include <vector>
#include <pcre2.h>

extern "C" {

int match_pattern_in_array(const char **input_array, int array_length, const char *pattern, const char ***output_array) {
    // Define PCRE2 constants
    #define PCRE2_CODE_UNIT_WIDTH 8
    #define MAX_MATCHES 100

    // Compile the regex pattern
    pcre2_code *re;
    PCRE2_SIZE erroffset;
    int errornumber;
    pcre2_match_data *match_data;

    // Convert pattern to PCRE2 format
    PCRE2_SPTR pattern_str = (PCRE2_SPTR)pattern;
    PCRE2_UCHAR buffer[256];

    re = pcre2_compile(
        pattern_str,                /* the pattern */
        PCRE2_ZERO_TERMINATED,      /* pattern is a zero-terminated string */
        PCRE2_CASELESS,             /* case-insensitive matching */
        &errornumber,               /* for error number */
        &erroffset,                 /* for error offset */
        NULL                        /* use default compile context */
    );

    if (!re) {
        pcre2_get_error_message(errornumber, buffer, sizeof(buffer));
        std::cerr << "Error compiling regex: " << buffer << std::endl;
        return -1;
    }

    // Prepare the match data
    match_data = pcre2_match_data_create_from_pattern(re, NULL);

    // Container for matched strings
    std::vector<std::string> matches;

    for (int i = 0; i < array_length; ++i) {
        PCRE2_SPTR subject = (PCRE2_SPTR)input_array[i];
        int rc = pcre2_match(
            re,                         /* the compiled pattern */
            subject,                    /* the subject string */
            strlen((char*)subject),     /* subject length */
            0,                          /* start at offset 0 in subject */
            0,                          /* default options */
            match_data,                 /* match data */
            NULL                        /* use default match context */
        );

        if (rc >= 0) {
            // Pattern matched, store the string
            matches.push_back(input_array[i]);
        }
    }

    // Free the PCRE2 resources
    pcre2_code_free(re);
    pcre2_match_data_free(match_data);

    // Allocate memory for output array
    *output_array = (const char **)malloc(matches.size() * sizeof(char *));
    if (*output_array == NULL) {
        return -1;
    }

    for (size_t i = 0; i < matches.size(); ++i) {
        (*output_array)[i] = strdup(matches[i].c_str());
        if ((*output_array)[i] == NULL) {
            return -1;
        }
    }

    return matches.size();
}

void free_matches(const char **matches, int match_count) {
    for (int i = 0; i < match_count; ++i) {
        free((void *)matches[i]);
    }
    free((void *)matches);
}

}

