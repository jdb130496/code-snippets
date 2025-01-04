import os
import xlwings as xw
import cffi

ffi = cffi.FFI()
ffi.cdef("""
int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array);
void free_matches(char **matches, int match_count);
""")

# Load the DLL
os.environ['PATH'] = r'D:\Programs\Msys2\home\j1304\Downloads' + ';' + os.environ['PATH'] + ';' + r'D:\Programs\Msys2\ucrt64\lib' + ';' + r'D:\Programs\Msys2\ucrt64\bin'
dll = ffi.dlopen("regex-C-xlwings.dll")

@xw.func
def match_pattern_udf(input_list, pattern):
    try:
        # Convert input strings into a C array
        input_array = [ffi.new("char[]", (item or "").encode('utf-8')) for item in input_list]
        input_array_c = ffi.new("char*[]", input_array)
        
        # Prepare output array (pointer to pointer)
        output_array_c = ffi.new("const char***")
        
        # Call the DLL function
        match_count = dll.match_pattern_in_array(input_array_c, len(input_list), pattern.encode('utf-8'), output_array_c)
        
        # If the match count is negative, return an empty list
        if match_count < 0:
            return [[""] for _ in input_list]  # Return an empty list vertically
        
        # Convert output back to Python
        output_list = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(match_count)]
        
        # Create a result list that matches the original input length
        final_output = [[item] if item != "" else [""] for item in output_list]  # Vertical output (column)
        
        # Free the output array allocated by the DLL
        dll.free_matches(output_array_c[0], match_count)
        
        return final_output
    except Exception as e:
        print(f"Error: {e}")
        return [[""] for _ in input_list]  # Return vertical empty list on error
from cffi import FFI
import xlwings as xw
import os
# Add MSYS2 directories to PATH
os.environ['PATH'] = (
    r'D:\dev\dll;' +
    r'D:\Programs\Msys2\ucrt64\bin;' +
    r'D:\Programs\Msys2\ucrt64\lib;' +
    r'D:\Programs\Msys2\ucrt64\include;' +
    r'D:\Programs\Msys2\ucrt64\x86_64-w64-mingw32\bin;' +
    r'D:\Programs\Msys2\ucrt64\x86_64-w64-mingw32\include;' +
    os.environ['PATH']
)
ffi201 = FFI()
#NUM_NUMBERS = 100000
#NUM_THREADS = 16

# Define the functions in the DLL
ffi201.cdef("""
    int rdrand64_step(unsigned long long *rand);
    void generate_random_numbers(int num_threads, int num_numbers);
    unsigned long long* get_numbers();
    void free_numbers(unsigned long long *numbers);
""")


# Load the DLL
#C = ffi.dlopen('D:\\OneDrive - 0yt2k\\Compiled dlls & executables\\rdrand_multithreaded_new_ucrt_gcc.dll')
C = ffi201.dlopen('rdrand_multithreaded_new.dll')
@xw.func
def generate_and_get_data(NUM_THREADS, NUM_NUMBERS):
    NUM_THREADS = int(NUM_THREADS)
    NUM_NUMBERS = int(NUM_NUMBERS)
    C.generate_random_numbers(NUM_THREADS, NUM_NUMBERS)
    numbers_ptr = C.get_numbers()
    numbers = [[int(numbers_ptr[i])] for i in range(NUM_NUMBERS)]
    C.free_numbers(numbers_ptr)
    return numbers
