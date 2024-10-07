#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <Windows.h>

typedef struct {
    double* array1;
    double* array2;
    int size;
    const char* logical_op;
    const char* comp_op1;
    const char* comp_op2;
    bool compare_with_constant1;
    bool compare_with_constant2;
    double constant1;
    double constant2;
    bool* result;
    int num_threads;
} ThreadData;

bool compare(double val1, const char* op, double val2) {
    if (strcmp(op, ">") == 0) return val1 > val2;
    if (strcmp(op, "<") == 0) return val1 < val2;
    if (strcmp(op, ">=") == 0) return val1 >= val2;
    if (strcmp(op, "<=") == 0) return val1 <= val2;
    if (strcmp(op, "==") == 0) return val1 == val2;
    if (strcmp(op, "!=") == 0) return val1 != val2;
    return false;  // Default to false if invalid operator
}

DWORD WINAPI thread_function(LPVOID arg) {
    ThreadData* data = (ThreadData*)arg;

    for (int i = 0; i < data->size; i++) {
        double val1 = data->array1[i];
        double val2 = data->array2[i];

        bool first_comparison;
        bool second_comparison;

        if (data->compare_with_constant1) {
            first_comparison = compare(val1, data->comp_op1, data->constant1);
        } else {
            first_comparison = compare(val1, data->comp_op1, val2);
        }

        if (data->compare_with_constant2) {
            second_comparison = compare(val2, data->comp_op2, data->constant2);
        } else {
            second_comparison = compare(val2, data->comp_op2, val1);
        }

        if (strcmp(data->logical_op, "||") == 0) {
            data->result[i] = first_comparison || second_comparison;
        } else if (strcmp(data->logical_op, "&&") == 0) {
            data->result[i] = first_comparison && second_comparison;
        }
    }

    return 0;
}

int main() {
    int size;
    printf("Enter the size of the arrays: ");
    scanf("%d", &size);

    double* array1 = (double*)malloc(size * sizeof(double));
    double* array2 = (double*)malloc(size * sizeof(double));
    bool* result = (bool*)malloc(size * sizeof(bool));

    printf("Enter values for array1 (space-separated): ");
    for (int i = 0; i < size; i++) {
        scanf("%lf", &array1[i]);
    }

    printf("Enter values for array2 (space-separated): ");
    for (int i = 0; i < size; i++) {
        scanf("%lf", &array2[i]);
    }

    char logical_op[3];
    printf("Enter the logical operator (|| or &&): ");
    scanf("%s", logical_op);

    char comp_op1[3], comp_op2[3];
    printf("Enter the first comparison operator (e.g., >, <, ==, etc.): ");
    scanf("%s", comp_op1);

    int compare_with_constant1;
    printf("Enter 1 if the first comparison is against a constant or 0 if it is against an element of array2: ");
    scanf("%d", &compare_with_constant1);

    double constant1 = 0;
    if (compare_with_constant1) {
        printf("Enter the constant value for the first comparison: ");
        scanf("%lf", &constant1);
    }

    printf("Enter the second comparison operator (e.g., >, <, ==, etc.): ");
    scanf("%s", comp_op2);

    int compare_with_constant2;
    printf("Enter 1 if the second comparison is against a constant or 0 if it is against an element of array1: ");
    scanf("%d", &compare_with_constant2);

    double constant2 = 0;
    if (compare_with_constant2) {
        printf("Enter the constant value for the second comparison: ");
        scanf("%lf", &constant2);
    }

    int num_threads;
    printf("Enter the number of threads: ");
    scanf("%d", &num_threads);

    ThreadData data = {
        .array1 = array1,
        .array2 = array2,
        .size = size,
        .logical_op = logical_op,
        .comp_op1 = comp_op1,
        .comp_op2 = comp_op2,
        .compare_with_constant1 = compare_with_constant1,
        .compare_with_constant2 = compare_with_constant2,
        .constant1 = constant1,
        .constant2 = constant2,
        .result = result,
        .num_threads = num_threads
    };

    // Create threads
    HANDLE* threads = (HANDLE*)malloc(num_threads * sizeof(HANDLE));
    for (int i = 0; i < num_threads; i++) {
        threads[i] = CreateThread(NULL, 0, thread_function, &data, 0, NULL);
    }

    // Wait for threads to finish
    WaitForMultipleObjects(num_threads, threads, TRUE, INFINITE);

    // Print results in one line as true/false space-separated
    printf("Result: ");
    for (int i = 0; i < size; i++) {
        printf("%s ", result[i] ? "true" : "false");
    }
    printf("\n");

    // Cleanup
    free(array1);
    free(array2);
    free(result);
    free(threads);

    return 0;
}
// Compilation using VC: cl test-short-circuit.c /Fe:test-short-circuit.exe (dll should be in the same folder)
