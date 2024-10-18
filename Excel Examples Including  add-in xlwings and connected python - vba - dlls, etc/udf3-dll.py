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
# Define the C function signatures and load the DLL

