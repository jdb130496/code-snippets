#include <windows.h>
#include <process.h> // For _beginthreadex
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>
#include <string.h>

typedef struct {
    double *array1;
    double *array2;
    const char *logical_operator;
    const char *comp_op1;
    double var1;
    const char *comp_op2;
    double var2;
    bool *result;
    int use_const1;
    int use_const2;
    int start_idx;
    int end_idx;
} thread_data;

// Comparison function for comparing values based on the operator
bool compare(double val1, const char *comp_op, double val2) {
    if (strcmp(comp_op, ">") == 0) return val1 > val2;
    if (strcmp(comp_op, "<") == 0) return val1 < val2;
    if (strcmp(comp_op, ">=") == 0) return val1 >= val2;
    if (strcmp(comp_op, "<=") == 0) return val1 <= val2;
    if (strcmp(comp_op, "==") == 0) return val1 == val2;
    if (strcmp(comp_op, "!=") == 0) return val1 != val2;
    return false;
}

// Thread function to process a portion of the arrays
unsigned __stdcall thread_func(void *args) {
    thread_data *data = (thread_data *)args;
    for (int i = data->start_idx; i < data->end_idx; ++i) {
        double val1 = data->array1[i];
        double val2 = data->array2[i];
        bool cond1, cond2;

        // Evaluate first condition (either val1 vs var1 or val1 vs val2)
        if (data->use_const1) {
            cond1 = compare(val1, data->comp_op1, data->var1);
        } else {
            cond1 = compare(val1, data->comp_op1, val2);
        }

        // Evaluate second condition (either val2 vs var2 or val2 vs val1)
        if (data->use_const2) {
            cond2 = compare(val2, data->comp_op2, data->var2);
        } else {
            cond2 = compare(val2, data->comp_op2, val1);
        }

        // Apply logical operator (either "||" or "&&")
        if (strcmp(data->logical_operator, "||") == 0) {
            data->result[i] = cond1 || cond2;
        } else if (strcmp(data->logical_operator, "&&") == 0) {
            data->result[i] = cond1 && cond2;
        } else {
            data->result[i] = false; // Invalid operator
        }
    }
    return 0;
}

// Main function to evaluate conditions and return results
__declspec(dllexport) bool* evaluate_short_circuit(double *array1, double *array2, const char *logical_operator, 
                                               const char *comp_op1, double var1, const char *comp_op2, 
                                               double var2, int size, int use_const1, int use_const2, int num_threads) {
    // Allocate memory for boolean result array
    bool *result = (bool *)malloc(size * sizeof(bool));

    // Handle single-element case
    if (size == 1) {
        bool cond1, cond2;

        // Evaluate first condition (either val1 vs var1 or val1 vs val2)
        if (use_const1) {
            cond1 = compare(array1[0], comp_op1, var1);
        } else {
            cond1 = compare(array1[0], comp_op1, array2[0]);
        }

        // Evaluate second condition (either val2 vs var2 or val2 vs val1)
        if (use_const2) {
            cond2 = compare(array2[0], comp_op2, var2);
        } else {
            cond2 = compare(array2[0], comp_op2, array1[0]);
        }

        // Apply logical operator (either "||" or "&&")
        if (strcmp(logical_operator, "||") == 0) {
            result[0] = cond1 || cond2;
        } else if (strcmp(logical_operator, "&&") == 0) {
            result[0] = cond1 && cond2;
        } else {
            result[0] = false; // Invalid operator
        }

        return result;
    }

    // Handle multithreading logic for larger arrays
    HANDLE *threads = (HANDLE *)malloc(num_threads * sizeof(HANDLE));
    thread_data *thread_params = (thread_data *)malloc(num_threads * sizeof(thread_data));

    int chunk_size = size / num_threads;

    for (int i = 0; i < num_threads; ++i) {
        thread_params[i].start_idx = i * chunk_size;
        thread_params[i].end_idx = (i == num_threads - 1) ? size : (i + 1) * chunk_size;
        thread_params[i].array1 = array1;
        thread_params[i].array2 = array2;
        thread_params[i].logical_operator = logical_operator;
        thread_params[i].comp_op1 = comp_op1;
        thread_params[i].var1 = var1;
        thread_params[i].comp_op2 = comp_op2;
        thread_params[i].var2 = var2;
        thread_params[i].result = result;
        thread_params[i].use_const1 = use_const1;
        thread_params[i].use_const2 = use_const2;

        threads[i] = (HANDLE)_beginthreadex(NULL, 0, thread_func, &thread_params[i], 0, NULL);
    }

    // Wait for all threads to complete
    WaitForMultipleObjects(num_threads, threads, TRUE, INFINITE);

    // Free thread resources
    for (int i = 0; i < num_threads; ++i) {
        CloseHandle(threads[i]);
    }
    free(threads);
    free(thread_params);

    // Return the boolean result array
    return result;
}

// Compilation VC (cl): cl short-circuit.c /LD /Fe:short-circuit.dll
