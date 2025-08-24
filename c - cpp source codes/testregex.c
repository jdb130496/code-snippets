#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pcre2.h>

#define OVECCOUNT 30    /* Number of output vector elements for PCRE2 */
#define BUFFER_SIZE 1024

void read_file_and_apply_regex(const char *filename, const char *pattern) {
    FILE *file = fopen(filename, "r");
    if (file == NULL) {
        perror("Failed to open file");
        return;
    }

    char buffer[BUFFER_SIZE];
    char *lines[10000];   // Assuming max 10,000 lines in file
    int line_count = 0;

    // Reading the file line-by-line
    while (fgets(buffer, sizeof(buffer), file)) {
        // Remove trailing newline character if exists
        buffer[strcspn(buffer, "\r\n")] = 0;
        if (strlen(buffer) > 0) {
            lines[line_count] = strdup(buffer);
            line_count++;
        }
    }
    fclose(file);

    // Setup PCRE2
    pcre2_code *re;
    PCRE2_SPTR pattern_str = (PCRE2_SPTR)pattern;
    int errornumber;
    PCRE2_SIZE erroroffset;

    re = pcre2_compile(pattern_str, PCRE2_ZERO_TERMINATED, PCRE2_CASELESS, &errornumber, &erroroffset, NULL);
    if (re == NULL) {
        PCRE2_UCHAR buffer[256];
        pcre2_get_error_message(errornumber, buffer, sizeof(buffer));
        printf("PCRE2 compilation failed at offset %d: %s\n", (int)erroroffset, buffer);
        return;
    }

    // Context and output vector
    pcre2_match_data *match_data = pcre2_match_data_create(OVECCOUNT, NULL);
    int match_count = 0;

    // Iterate over the lines and apply the regex
    for (int i = 0; i < line_count; i++) {
        PCRE2_SPTR subject = (PCRE2_SPTR)lines[i];
        PCRE2_SIZE subject_length = strlen((char *)subject);

        int rc = pcre2_match(re, subject, subject_length, 0, 0, match_data, NULL);

        if (rc >= 0) {
            printf("Matched Line: %s\n", lines[i]);
            match_count++;
        }

        free(lines[i]);  // Free the memory used for each line
    }

    printf("Total matches: %d\n", match_count);

    // Clean up
    pcre2_match_data_free(match_data);   // Release memory used for the match data
    pcre2_code_free(re);                 // Release memory used for the compiled pattern
}

int main() {
    const char *filename = "C:\\Users\\j1304\\Desktop\\data.txt";
    const char *pattern = "(?i)(^\\d{6}((?=.*direct)|(?=.*growth)|(?=.*gold)|(?=.*silver))((?!(equity|cap|hybrid|Solution Oriented|FOF|elss|regular|idcw|dividend|div|hybrid|balanced advantage|index|nifty)).)*$)";

    read_file_and_apply_regex(filename, pattern);

    return 0;
}

