#include <stdio.h>
#include <immintrin.h>
#include <stdbool.h>
#include <stdlib.h>

#define NUM_NUMBERS 45000000

typedef struct Node {
    long long value;
    struct Node *left;
    struct Node *right;
} Node;

Node *root = NULL;

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
    FILE *file = fopen("random_numbers_example.csv", "w");
    if (file == NULL) {
        printf("Error opening file!\n");
        return 1;
    }

    long long rand;
    long long example_array[] = {5, 3, 6, 2, 4, 7, 1, 10, 3, 1, 12, 2, 5, 14, 18, 20, 1}; // example array with some duplicates
    int array_size = sizeof(example_array) / sizeof(example_array[0]);
    for (int i = 0; i < array_size; i++) {
        rand = example_array[i];
        if (!contains(root, rand)) {
            insert(&root, rand);
            fprintf(file, "%lld\n", rand);
        }
    }

    fclose(file);
    return 0;
}



