import os
import cffi
import xlwings as xw

# Add MSYS2 UCRT library path to the system PATH
msys2_ucrt_lib_path = r'D:\dev\dll;D:\Programs\Msys2\ucrt64\bin;D:\Programs\Msys2\ucrt64\lib'  # Adjust this path to your MSYS2 UCRT bin directory
os.environ['PATH'] = msys2_ucrt_lib_path + os.pathsep + os.environ['PATH']

# Define the full path to the multithreaded DLL file (adjust as necessary)
dll_path = r'regex-msys-c-pcre2-multithreading.dll'  # Updated DLL
# Initialize cffi

ffi = cffi.FFI()

# Define the C function signatures (same as single-threaded, no changes here)
ffi.cdef("""
    int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array);
    void free_matches(char** matches, int match_count);
""")

# Load the compiled multithreaded DLL
dll = ffi.dlopen(dll_path)

# Define a Python function to interact with the DLL
def match_patterns(input_array, pattern):
    # Convert Python strings to C-compatible strings (list of C char pointers)
    input_array_c = [ffi.new("char[]", s.encode('utf-8')) for s in input_array]  # Create a new cdata for each string
    input_array_ptrs = ffi.new("const char*[]", input_array_c)  # Create a pointer array

    # Prepare output for the matched patterns
    output_array_c = ffi.new("char***")
    
    # Call the C function from the DLL (same as single-threaded code)
    num_matches = dll.match_patterns(input_array_ptrs, len(input_array), pattern.encode('utf-8'), output_array_c)
    
    if num_matches == 0:
        return []
    
    # Convert the C output array back to a Python list of strings
    matches = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(num_matches)]
    
    # Free the memory allocated by the DLL
    dll.free_matches(output_array_c[0], num_matches)
    
    return matches

# Define the Excel UDF
@xw.func
@xw.arg('input_array', ndim=1)
#@xw.ret(expand='vertical')  # Ensures the results are outputted vertically in Excel
def REGEXMSYSC2(input_array, pattern):
    # Convert Excel input to a list of Python strings
    input_list = [str(item) for item in input_array]
    
    # Call the match_patterns function and return the matches
    matches = match_patterns(input_list, pattern)
    
    return [[match] for match in matches]  # Wrap each match in its own list to return a vertical array
import xlwings as xw
from cffi import FFI
import os

ffi = FFI()

# Define the C function signature
ffi.cdef("void compare_custom(double* arr1, double* arr2, int length, bool* result);")

os.environ['PATH'] = r'D:\dev\dll;D:\Programs\Msys2\ucrt64\bin;D:\Programs\Msys2\ucrt64\lib'+ os.pathsep + os.environ['PATH']

# Load the shared DLL
lib = ffi.dlopen(r'customoperator.dll')

@xw.func
def compare_custom_operator(values):
    arr1 = [row[0] for row in values]
    arr2 = [row[1] for row in values]
    length = len(arr1)

    arr1_c = ffi.new("double[]", arr1)
    arr2_c = ffi.new("double[]", arr2)
    result_c = ffi.new("bool[]", length)

    # Call the DLL function
    lib.compare_custom(arr1_c, arr2_c, length, result_c)

    # Convert the C result to Python list
    result = [[bool(result_c[i])] for i in range(length)]
    return result

