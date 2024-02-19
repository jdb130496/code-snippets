#include <regex.h>
#include <stdio.h>

int main() {
    regex_t regex;
    int ret;

    ret = regcomp(&regex, "^[a-zA-Z0-9_]*$", 0);
    if (ret) {
        printf("Could not compile regex\n");
        return 1;
    }

    ret = regexec(&regex, "test_string", 0, NULL, 0);
    if (!ret) {
        printf("Match\n");
    } else if (ret == REG_NOMATCH) {
        printf("No match\n");
    } else {
        printf("Regex match failed\n");
        return 1;
    }

    regfree(&regex);

    return 0;
}

