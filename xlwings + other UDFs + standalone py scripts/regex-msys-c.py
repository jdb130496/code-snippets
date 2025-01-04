import os
import cffi
import xlwings as xw

# Add MSYS2 UCRT library path to the system PATH
msys2_ucrt_lib_path = r'D:\dev\dll;D:\Programs\Msys2\ucrt64\bin;D:\Programs\Msys2\ucrt64\lib'  # Adjust this path to your MSYS2 UCRT bin directory
os.environ['PATH'] = msys2_ucrt_lib_path + os.pathsep + os.environ['PATH']

# Define the full path to the DLL file (adjust as necessary)
dll_path = r'regex-c-msys-single-threading.dll'

# Initialize cffi
ffi = cffi.FFI()

# Define the C function signatures
ffi.cdef("""
    int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array);
    void free_matches(char** matches, int match_count);
""")

# Load the compiled DLL
dll = ffi.dlopen(dll_path)

# Define a Python function to interact with the DLL
def match_patterns(input_array, pattern):
    # Convert Python strings to C-compatible strings (list of C char pointers)
    input_array_c = [ffi.new("char[]", s.encode('utf-8')) for s in input_array]  # Create a new cdata for each string
    input_array_ptrs = ffi.new("const char*[]", input_array_c)  # Create a pointer array

    # Prepare output for the matched patterns
    output_array_c = ffi.new("char***")
    
    # Call the C function from the DLL
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
#@xw.ret(expand='vertical')
def REGEXMSYSC(input_array, pattern):
    # Convert Excel input to a list of Python strings
    input_list = [str(item) for item in input_array]
    
    # Call the match_patterns function and return the matches
    matches = match_patterns(input_list, pattern)
    
    return [[match] for match in matches]

