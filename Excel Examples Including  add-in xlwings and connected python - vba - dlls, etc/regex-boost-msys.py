import os
import xlwings as xw
import ctypes
from ctypes import c_char_p, c_int, POINTER, byref

# Set environment variables for Boost and DLL paths
os.environ['PATH'] += r';D:\Programs\Msys2\ucrt64\bin;D:\Programs\Msys2\opt\boost\lib;D:\dev\dll'

# Load the compiled DLL
dll = ctypes.CDLL(r'D:\dev\dll\regex-boost-msys-new.dll')

# Define the function signatures
dll.match_patterns.argtypes = [POINTER(c_char_p), c_int, c_char_p, POINTER(POINTER(c_char_p))]
dll.match_patterns.restype = c_int
dll.free_matches.argtypes = [POINTER(c_char_p), c_int]
dll.free_matches.restype = None

@xw.func
def REGEXMSYSB1(input_array, pattern):
    # Convert input array to ctypes array
    input_array_ctypes = (c_char_p * len(input_array))(*[s.encode('utf-8') for s in input_array])
    pattern_ctypes = pattern.encode('utf-8')
    
    # Prepare output array
    output_array_ctypes = POINTER(c_char_p)()
    
    # Call the DLL function
    num_matches = dll.match_patterns(input_array_ctypes, len(input_array), pattern_ctypes, byref(output_array_ctypes))
    
    # Convert output array to Python list
    output_array = [output_array_ctypes[i].decode('utf-8') for i in range(num_matches)]
    
    # Free the allocated memory
    dll.free_matches(output_array_ctypes, num_matches)
    
    vertical_output_array = [[item] for item in output_array]
    return vertical_output_array


