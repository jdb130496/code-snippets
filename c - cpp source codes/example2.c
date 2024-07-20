#include <windows.h>
#include <wincrypt.h>
#include <stdio.h>
#include <stdlib.h>

long long get_random_number() {
    // Returns a random number from a cryptographically secure random number generator.
    HCRYPTPROV hCryptProv;
    if (!CryptAcquireContext(&hCryptProv, NULL, NULL, PROV_RSA_FULL, 0)) {
        printf("Error acquiring cryptographic context!\n");
        exit(1);
    }
    long long number;
    if (!CryptGenRandom(hCryptProv, sizeof(number), (BYTE *)&number)) {
        printf("Error generating random number!\n");
        exit(1);
    }
    CryptReleaseContext(hCryptProv, 0);
    return llabs(number);
}

int main() {
    long long number = get_random_number();
    printf("%lld\n", number);
    return 0;
}

