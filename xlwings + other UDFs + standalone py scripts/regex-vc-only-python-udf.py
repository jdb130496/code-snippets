import cffi
import os
import sys
# Add required directories to the PATH environment variable
os.environ['PATH'] = os.environ['PATH'] + ';' + r'D:\dev\dll' + ';' \
    + r'D:\Programs\vsbt\VC\Tools\MSVC\14.41.34120\bin\Hostx64\x64' + ';' \
    + r'D:\Programs\vsbt\Common7\IDE\VC\VCPackages' + ';' \
    + r'D:\Programs\vsbt\Common7\IDE' + ';' \
    + r'C:\Windows\System32' + ';' \
    + r'D:\Programs\java\bin' + ';' \
    + r'D:\Programs\Python' + ';' \
    + r'D:\Programs\vsbt\VC\Tools\Llvm\x64\bin'
# Initialize CFFI and load the DLL
ffi = cffi.FFI()
# Define the function signatures for the C++ functions
ffi.cdef("""
    int match_patterns(const char** input_array, int array_length, const char* pattern, char*** output_array);
    void free_matches(char** matches, int match_count);
""")
try:
    # Load the DLL (update the path to your actual DLL location)
    cpp_dll = ffi.dlopen("boost-regex-vc-20102024.dll")
except Exception as e:
    print(f"Failed to load DLL: {e}")
    sys.exit(1)
# Simple Python function to test the DLL
def match_patterns_in_python(input_array, pattern):
    """
    Function to call the C++ match_patterns function through cffi.
    :param input_array: List of strings from Python.
    :param pattern: The regex pattern to match.
    :return: List of matched strings.
    """
    # Flatten the input_array (in case it's multi-dimensional)
    flattened_input = [str(item) for item in input_array if item]
    # Convert input_array to C-style string array for C++ DLL
    try:
        input_array_c = ffi.new("char*[]", [ffi.new("char[]", item.encode('utf-8')) for item in flattened_input])
    except Exception as e:
        print(f"Error while converting input array: {e}")
        return []
    # Prepare output variable
    output_array = ffi.new("char***")
    try:
        # Call the match_patterns function
        num_matches = cpp_dll.match_patterns(input_array_c, len(flattened_input), pattern.encode('utf-8'), output_array)
    except Exception as e:
        print(f"Error while calling match_patterns: {e}")
        return []
    if num_matches == 0:
        return "No matches found."
    # Retrieve matched strings
    result = []
    try:
        for i in range(num_matches):
            matched_str = ffi.string(output_array[0][i]).decode('utf-8')
            result.append(matched_str)
        # Free memory allocated by the C++ DLL
        cpp_dll.free_matches(output_array[0], num_matches)
    except Exception as e:
        print(f"Error while processing matches: {e}")
        cpp_dll.free_matches(output_array[0], num_matches)  # Ensure we free memory even on error
        return []
    return result
# Example usage
if __name__ == "__main__":
    test_input = [
        "This is a test string",
        "Another test string",
        "Testing regex match",
        "No match here",
        "Match this test"
    ]
    regex_pattern = ".*test.*"  # Regex pattern to match strings containing 'test'
    # Call the function and print the result
    try:
        result = match_patterns_in_python(test_input, regex_pattern)
        print("Matched Results:", result)
    except Exception as e:
        print(f"Unexpected error: {e}")
