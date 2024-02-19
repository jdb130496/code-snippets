#include <windows.h>
#include <wincrypt.h>
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

#define NUM_NUMBERS 45000000

typedef struct node {
    long long key;
    struct node *left;
    struct node *right;
} node;

node *root = NULL;

node *new_node(long long key) {
    node *n = malloc(sizeof(node));
    n->key = key;
    n->left = NULL;
    n->right = NULL;
    return n;
}

void insert(node **n, long long key) {
    if (*n == NULL) {
        *n = new_node(key);
        return;
    }
    if (key < (*n)->key) {
        insert(&(*n)->left, key);
    } else {
        insert(&(*n)->right, key);
    }
}

bool contains(node *n, long long key) {
    if (n == NULL) {
        return false;
    }
    if (key == n->key) {
        return true;
    }
    if (key < n->key) {
        return contains(n->left, key);
    } else {
        return contains(n->right, key);
    }
}

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
    FILE *file = fopen("random_numbers.csv", "w");
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    size_t len = 0;
    while (len < NUM_NUMBERS) {
        long long number = get_random_number();
        if (!contains(root, number)) {
            insert(&root, number);
            len++;
            fprintf(file, "%lld\n", number);
        }
    }

    fclose(file);
    return 0;
}

