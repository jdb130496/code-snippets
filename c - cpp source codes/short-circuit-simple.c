#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>
#include <windows.h>

__declspec(dllexport) bool* evaluate_short_circuit_multithread(double* array1, double* array2, const char* logical_op, const char* comp_op1, const char* comp_op2, double constant1, double constant2, int size, int num_threads);

// Function to compare two values based on the comparison operator
bool compare(double a, double b, const char* comp_op) {
    if (strcmp(comp_op, ">") == 0) {
        return a > b;
    } else if (strcmp(comp_op, "<") == 0) {
        return a < b;
    } else if (strcmp(comp_op, ">=") == 0) {
        return a >= b;
    } else if (strcmp(comp_op, "<=") == 0) {
        return a <= b;
    } else if (strcmp(comp_op, "==") == 0) {
        return a == b;
    } else if (strcmp(comp_op, "!=") == 0) {
        return a != b;
    }
    return false;  // Invalid comparison operator
}

__declspec(dllexport) bool* evaluate_short_circuit_multithread(
    double* array1, double* array2, const char* logical_op, const char* comp_op1, const char* comp_op2, 
    double constant1, double constant2, int size, int num_threads) {

    // Allocate memory for the results array
    bool* results = (bool*)malloc(size * sizeof(bool));
    if (!results) {
        printf("Memory allocation failed!\n");
        return NULL;
    }

    // Loop through each element of the arrays
    for (int i = 0; i < size; i++) {
        double val1 = array1[i];
        double val2 = array2[i];

        // First set of comparisons
        bool cond1 = false;
        cond1 = compare(val1, val2, comp_op1) ||  // val1 [operator] val2
                compare(val2, val1, comp_op1) ||  // val2 [operator] val1
                compare(val1, constant1, comp_op1) ||  // val1 [operator] constant1
                compare(constant1, val1, comp_op1) ||  // constant1 [operator] val1
                compare(val2, constant1, comp_op1) ||  // val2 [operator] constant1
                compare(constant1, val2, comp_op1);    // constant1 [operator] val2

        // Second set of comparisons
        bool cond2 = false;
        cond2 = compare(val1, val2, comp_op2) ||  // val1 [operator] val2
                compare(val2, val1, comp_op2) ||  // val2 [operator] val1
                compare(val1, constant2, comp_op2) ||  // val1 [operator] constant2
                compare(constant2, val1, comp_op2) ||  // constant2 [operator] val1
                compare(val2, constant2, comp_op2) ||  // val2 [operator] constant2
                compare(constant2, val2, comp_op2);    // constant2 [operator] val2

        // Combine the conditions based on the logical operator
        if (strcmp(logical_op, "||") == 0) {
            results[i] = cond1 || cond2;
        } else if (strcmp(logical_op, "&&") == 0) {
            results[i] = cond1 && cond2;
        } else {
            printf("Invalid logical operator!\n");
            results[i] = false;
        }

        // Debugging output
        printf("Index %d: val1 = %.2f, val2 = %.2f, cond1 = %s, cond2 = %s, result = %s\n",
            i, val1, val2, cond1 ? "true" : "false", cond2 ? "true" : "false", results[i] ? "true" : "false");
    }

    return results;
}

