#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <windows.h>
#include <string.h>

// Declare the function from the DLL
typedef bool* (*EvaluateFunc)(double*, double*, const char*, const char*, const char*, double, double, int, int);

// Function to get array input from user
void get_array_input(double* array, int size, const char* array_name) {
    printf("Enter elements for %s (separated by space):\n", array_name);
    for (int i = 0; i < size; i++) {
        scanf("%lf", &array[i]);
    }
}

// Function to evaluate a condition based on the provided operator
bool evaluate_condition(double val1, double val2, const char* operator) {
    if (strcmp(operator, ">") == 0) {
        return val1 > val2;
    } else if (strcmp(operator, "<") == 0) {
        return val1 < val2;
    } else if (strcmp(operator, "==") == 0) {
        return val1 == val2;
    } else if (strcmp(operator, "!=") == 0) {
        return val1 != val2;
    } else if (strcmp(operator, ">=") == 0) {
        return val1 >= val2;
    } else if (strcmp(operator, "<=") == 0) {
        return val1 <= val2;
    }
    return false; // Invalid operator
}

int main() {
    HINSTANCE hDLL;
    EvaluateFunc evaluate_short_circuit_multithread;

    // Load the DLL
    hDLL = LoadLibrary(TEXT("short-circuit-simple.dll"));
    if (hDLL == NULL) {
        printf("Could not load the DLL! Error code: %ld\n", GetLastError());
        return 1;
    }

    // Get the function address from the DLL
    evaluate_short_circuit_multithread = (EvaluateFunc)GetProcAddress(hDLL, "evaluate_short_circuit_multithread");
    if (!evaluate_short_circuit_multithread) {
        printf("Could not locate the function in DLL! Error code: %ld\n", GetLastError());
        FreeLibrary(hDLL);
        return 1;
    }

    // Input: size of arrays
    int size;
    printf("Enter the size of the arrays: ");
    scanf("%d", &size);

    // Dynamically allocate memory for arrays
    double* array1 = (double*)malloc(size * sizeof(double));
    double* array2 = (double*)malloc(size * sizeof(double));
    if (array1 == NULL || array2 == NULL) {
        printf("Memory allocation failed!\n");
        return 1;
    }

    // Get user input for the arrays
    get_array_input(array1, size, "Array1");
    get_array_input(array2, size, "Array2");

    // Input: short-circuit operator (|| or &&)
    char logical_op[3];
    printf("Enter the short-circuit operator (|| or &&): ");
    scanf("%s", logical_op);

    // Input: comparison for the first condition
    char comp1_input[100];
    printf("Enter the first comparison (e.g., 'val1 > val2', 'val1 < 10', '25 < val2'): ");
    getchar();  // Consume the leftover newline
    fgets(comp1_input, sizeof(comp1_input), stdin);
    comp1_input[strcspn(comp1_input, "\n")] = 0;  // Remove newline character

    // Input: comparison for the second condition
    char comp2_input[100];
    printf("Enter the second comparison (e.g., 'val1 > val2', 'val1 < 10', '25 < val2'): ");
    fgets(comp2_input, sizeof(comp2_input), stdin);
    comp2_input[strcspn(comp2_input, "\n")] = 0;  // Remove newline character

    // Input: number of threads
    int num_threads;
    printf("Enter the number of threads: ");
    scanf("%d", &num_threads);

    // Call the function from the DLL
    bool* results = evaluate_short_circuit_multithread(array1, array2, logical_op, comp1_input, comp2_input, 0, 0, size, num_threads);

    if (results == NULL) {
        printf("Failed to evaluate short-circuit logic!\n");
        free(array1);
        free(array2);
        FreeLibrary(hDLL);
        return 1;
    }

    // Output results
    printf("Results:\n");
    for (int i = 0; i < size; i++) {
        printf("Result for index %d: %s\n", i, results[i] ? "true" : "false");
    }

    // Free allocated memory
    free(array1);
    free(array2);
    free(results);
    FreeLibrary(hDLL);
    return 0;
}

