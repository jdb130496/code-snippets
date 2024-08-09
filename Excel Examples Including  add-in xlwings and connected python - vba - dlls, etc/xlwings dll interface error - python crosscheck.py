import numpy as np
import cffi
# Define the C function signatures and load the DLL
ffi = cffi.FFI()
ffi.cdef("""
    int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array);
    void free_matches(char **matches, int match_count);
""")
# Load the DLL
#dll = ffi.dlopen("D:\\Programs\\Msys2\\home\\dhawal123\\Downloads\\regex-C-xlwings-2.dll")
dll = ffi.dlopen("D:\\Programs\\Msys2\\home\\dhawal123\\Downloads\\regex-C-10072024.dll")
def match_pattern_new(input_list, pattern):
    # Replace None values with empty strings and encode all non-empty strings
    input_array = [ffi.new("char[]", (item or "").encode('utf-8')) for item in input_list]
    # Convert the list to a C array of strings
    input_array_c = ffi.new("char*[]", input_array)
    # Prepare the output array pointer
    output_array_c = ffi.new("char***")
    # Call the DLL function
    match_count = dll.match_pattern_in_array(input_array_c, len(input_list), pattern.encode('utf-8'), output_array_c)
    if match_count < 0:
        raise RuntimeError("Error matching pattern")
    # Initialize output list with None
    output_list = [None] * len(input_list)
    # Collect matched strings
    matched_strings = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(match_count)]
    # Update output_list with matched items using a list comprehension and update matched_indices
    matched_indices = {i for i, item in enumerate(input_list) if item and item in matched_strings}
    output_list = [[item if i in matched_indices else None] for i, item in enumerate(input_list)]
    # Free the output array allocated by the DLL
    dll.free_matches(output_array_c[0], match_count)
    return output_list
pattern = '(?i)(^\d{6}((?=.*direct)|(?=.*growth)|(?=.*gold)|(?=.*silver))((?!(equity|hybrid|Solution Oriented|FOF|elss|regular|idcw|dividend|div|hybrid|balanced advantage|index|nifty)).)*$)'
# Read the file
with open('D:\\dev\\examplecsv.txt', 'r') as file:
    lines = file.readlines()
data = [line.strip() for line in lines if line.strip() and not line.startswith('Column1')]
array = np.array(data)
result = [str(item) for sublist in match_pattern_new(array,pattern) for item in sublist if item is not None]
print(result)
