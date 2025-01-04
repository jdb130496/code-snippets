import xlwings as xw
import ctypes

# Load the shared library
dll_path = r"D:\dev\dll\regex-boost-vc.dll"  # Update with your DLL path
cpp_dll = ctypes.CDLL(dll_path)

# Define the function signatures
cpp_dll.match_patterns.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_int, ctypes.c_char_p, ctypes.POINTER(ctypes.POINTER(ctypes.c_char_p))]
cpp_dll.match_patterns.restype = ctypes.c_int
cpp_dll.free_matches.argtypes = [ctypes.POINTER(ctypes.c_char_p), ctypes.c_int]
cpp_dll.free_matches.restype = None

@xw.func
@xw.arg('input_range', xw.Range, ndim=2)
@xw.arg('pattern', str)
@xw.ret(expand='table')
def match_patterns_vc_new(input_range, pattern):
    # Flatten the input range and filter out blank cells
    input_list = [str(cell) for row in input_range for cell in row if cell]
    
    # Convert the input list to a C-style array
    input_array = (ctypes.c_char_p * len(input_list))(*[s.encode('utf-8') for s in input_list])
    
    # Prepare output variables
    output_array = ctypes.POINTER(ctypes.c_char_p)()
    
    # Call the match_patterns function
    num_matches = cpp_dll.match_patterns(input_array, len(input_list), pattern.encode('utf-8'), ctypes.byref(output_array))
    
    if num_matches == 0:
        return []  # No matches or error occurred
    
    # Retrieve matched strings
    result = []
    for i in range(num_matches):
        result.append(output_array[i].decode('utf-8'))
    
    # Free memory allocated by the C++ DLL
    cpp_dll.free_matches(output_array, num_matches)
    
    return result

# Example usage in Excel:
# =match_patterns_vc_new(A1:F30, CONCAT(N1))

