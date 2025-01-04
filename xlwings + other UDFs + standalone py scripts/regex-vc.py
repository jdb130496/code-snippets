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
os.environ['PATH'] = r'D:/dev/dll' + ';' + os.environ['PATH'] + ';' + r'D:\Programs\Msys2\ucrt64\bin' + ';' + r'D:\Programs\Msys2\ucrt64\lib'

dll = ffi.dlopen("regex-boost-msys.dll")

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

