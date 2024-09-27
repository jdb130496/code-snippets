#include <immintrin.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>

#define NUM_NUMBERS 45000000

typedef struct Node {
    long long value;
    struct Node *left;
    struct Node *right;
} Node;

Node *new_node(long long value) {
    Node *node = malloc(sizeof(Node));
    node->value = value;
    node->left = NULL;
    node->right = NULL;
    return node;
}

void insert(Node **node, long long value) {
    if (*node == NULL) {
        *node = new_node(value);
        return;
    }
    if (value < (*node)->value) {
        insert(&(*node)->left, value);
    } else {
        insert(&(*node)->right, value);
    }
}

bool contains(Node *node, long long value) {
    if (node == NULL) {
        return false;
    }
    if (value == node->value) {
        return true;
    }
    if (value < node->value) {
        return contains(node->left, value);
    } else {
        return contains(node->right, value);
    }
}

int main() {
    FILE *file = fopen("random_numbers.csv", "w");
    Node *root = NULL;
    for (int i = 0; i < NUM_NUMBERS; i++) {
        unsigned long long rand_u64 = 0;
        long long rand_i64;
        while (true) {
            _rdrand64_step(&rand_u64);
            rand_i64 = __builtin_bswap64(rand_u64);
            rand_i64 = llabs(rand_i64);
            if (!contains(root, rand_i64)) {
                break;
            }
        }
        insert(&root, rand_i64);
        fprintf(file, "%lld\n", rand_i64);
    }

    fclose(file);
}

