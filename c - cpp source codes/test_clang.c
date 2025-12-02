#include <stdio.h>
#include <stdint.h>
#include <stdbool.h>

int main() {
    printf("=== Clang C Compiler Test ===\n");
    printf("Compiler: %s\n", __clang_version__);
    printf("C Standard: %ld\n", __STDC_VERSION__);
    
    // Test stdint.h (Clang's built-in header)
    uint64_t big_number = UINT64_MAX;
    printf("uint64_t max value: %llu\n", big_number);
    
    // Test stdbool.h (Clang's built-in header)
    bool is_clang = true;
    printf("Using Clang: %s\n", is_clang ? "yes" : "no");
    
    // Test sizeof (built-in)
    printf("Size of pointer: %zu bytes\n", sizeof(void*));
    
    return 0;
}
