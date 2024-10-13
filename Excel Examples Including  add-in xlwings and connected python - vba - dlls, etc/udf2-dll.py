from cffi import FFI
import xlwings as xw
# Initialize FFI
ffi = FFI()
# Define the C function signature
ffi.cdef("""
    bool* evaluate_short_circuit(double *array1, double *array2, const char *logical_operator,
                                 const char *comp_op1, double var1, const char *comp_op2,
                                 double var2, int size, int use_const1, int use_const2, int num_threads);
""")
# Load the DLL (ensure the correct path to the DLL)
lib = ffi.dlopen(r'D:\dev\dll\short-circuit.dll')
@xw.func
@xw.arg('array1', ndim=1)  # Treat array1 as 1D array, even if a single element
@xw.arg('array2', ndim=1)  # Treat array2 as 1D array, even if a single element
def Short_Circuit(array1, array2, logical_op, comp1, is_const1, const1, comp2, is_const2, const2, num_threads):
    #if isinstance(array1, float):
    #    array1 = [array1]
    #if isinstance(array2, float):
    #    array2 = [array2]
    # Convert input arrays to float and handle None values
    array1 = [float(i) if i is not None else 0.0 for i in array1]
    array2 = [float(i) if i is not None else 0.0 for i in array2]
    # Convert Python lists to C arrays (double arrays)
    c_array1 = ffi.new("double[]", array1)
    c_array2 = ffi.new("double[]", array2)
    # Convert comparison constants and thread count to integers
    is_const1 = int(is_const1)
    is_const2 = int(is_const2)
    num_threads = int(num_threads)
    const1 = float(const1)
    const2 = float(const2)
    # Call the C function, which returns a pointer to a boolean array
    c_result = lib.evaluate_short_circuit(c_array1, c_array2,
                                          ffi.new("char[]", logical_op.encode()),
                                          ffi.new("char[]", comp1.encode()),
                                          const1,
                                          ffi.new("char[]", comp2.encode()),
                                          const2,
                                          len(array1),
                                          is_const1,
                                          is_const2,
                                          num_threads)
    # Convert the result from the C boolean array to a Python list
    output = [[c_result[i]] for i in range(len(array1))]
    # Return the output directly as a list of TRUE/FALSE values
    return output

# Initialize FFI for C function interaction
ffi1 = FFI()

# Load the DLL (Ensure the DLL path is correct)
dll = ffi1.dlopen(r"D:\dev\dll\short-circuit-simple.dll")

# Define the function prototype from the DLL
ffi1.cdef("""
    bool* evaluate_short_circuit_multithread(double* array1, double* array2, 
                                             const char* logical_op, const char* comp_op1, 
                                             const char* comp_op2, double constant1, 
                                             double constant2, int size, int num_threads);
""")

def evaluate_condition(val1, val2, condition, constant1=None, constant2=None):
    """
    Dynamically evaluate the given condition. Constants are used when comparison strings
    contain placeholders like 'constant1' or 'constant2'.
    """
    # Replace 'val1' and 'val2' with actual values
    condition = condition.replace('val1', str(val1))
    condition = condition.replace('val2', str(val2))

    # Use constant1 and constant2 if present in the condition string
    if 'constant1' in condition and constant1 is not None:
        condition = condition.replace('constant1', str(constant1))
    if 'constant2' in condition and constant2 is not None:
        condition = condition.replace('constant2', str(constant2))

    # Evaluate the condition dynamically
    try:
        return eval(condition)
    except Exception as e:
        raise ValueError(f"Error in condition evaluation: {condition}. Error: {str(e)}")

@xw.func
@xw.arg('array1', ndim=1)  # Input array1 as a standard Python list
@xw.arg('array2', ndim=1)  # Input array2 as a standard Python list
@xw.arg('logical_op', str)  # Logical operator (|| or &&)
@xw.arg('comp_op1', str)    # First comparison operation (e.g., 'val1 > constant1')
@xw.arg('comp_op2', str)    # Second comparison operation (e.g., 'val2 < constant2')
@xw.arg('constant1', float) # First constant
@xw.arg('constant2', float) # Second constant
@xw.arg('num_threads', int) # Number of threads for parallel execution
def short_circuit_simple(array1, array2, logical_op, comp_op1, comp_op2, constant1, constant2, num_threads):
    """
    Evaluate flexible comparisons between two arrays and constants using short-circuit logic.
    """
    try:
        # Ensure both arrays are of the same size
        size = len(array1)
        if size != len(array2):
            return "Array sizes do not match"

        # Convert Python lists to C-compatible arrays
        array1_c = ffi1.new("double[]", array1)
        array2_c = ffi1.new("double[]", array2)

        # Prepare results array for storing C results
        results_c = ffi1.new("bool[]", size)

        # Loop through each element to evaluate conditions
        for i in range(size):
            val1 = array1[i]
            val2 = array2[i]
            
            # Evaluate the first condition
            cond1 = evaluate_condition(val1, val2, comp_op1, constant1, constant2)
            # Evaluate the second condition
            cond2 = evaluate_condition(val1, val2, comp_op2, constant1, constant2)

            # Apply logical operation
            if logical_op == "||":
                results_c[i] = cond1 or cond2
            elif logical_op == "&&":
                results_c[i] = cond1 and cond2
            else:
                raise ValueError("Invalid logical operator. Use '||' or '&&'.")

        # Convert results from C array to Python list
        results = [[bool(results_c[i])] for i in range(size)]
        
        # Return the results as a list
        return results
    
    except Exception as e:
        # Return error message to Excel
        return f"Error: {str(e)}"
import os
import xlwings as xw
import cffi

# Define the C function signatures and load the DLL
ffi = cffi.FFI()
ffi.cdef("""
    int match_patterns(const char **input_array, int array_length, const char *pattern, char ***output_array);
    void free_matches(char **matches_array, int match_count);
""")

# Load the new DLL (adjust the path to where your new DLL is located)
os.environ['PATH'] = r'D:\dev\dll' + ';' + os.environ['PATH']+';'+r'D:\boost\stagelib\lib'
dll = ffi.dlopen("regex-boost-vc.dll")

@xw.func
def REGEXVC(input_list, pattern):
    try:
        # Convert input strings into a C array
        input_array = [ffi.new("char[]", (item or "").encode('utf-8')) for item in input_list]
        input_array_c = ffi.new("char*[]", input_array)
        
        # Prepare output array (pointer to pointer for output)
        output_array_c = ffi.new("char***")
        
        # Call the DLL function
        match_count = dll.match_patterns(input_array_c, len(input_list), pattern.encode('utf-8'), output_array_c)
        
        # If the match count is negative, return an empty string ("" for no match)
        if match_count < 0:
            return ["" for _ in input_list]  # Return an empty list
        
        # Convert output back to Python
        output_list = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(match_count)]
        
        # Create a result list matching the original input length
        final_output = [item if item in output_list else "" for item in input_list]
        
        # Free the output array allocated by the DLL
        dll.free_matches(output_array_c[0], match_count)
        # Return a vertical array by making each element a separate list (for vertical orientation)
        return [[item] for item in final_output]
    
    except Exception as e:
        # Handle any errors gracefully by returning a list of empty strings
        print(f"Error: {e}")
        return ["" for _ in input_list]

