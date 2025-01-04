import ctypes
from ctypes import c_char_p, c_int, POINTER, byref
import xlwings as xw

# Load the DLL
dll = ctypes.CDLL(r'D:\dev\dll\regex-c-vc.dll')

# Define the function signatures
dll.match_patterns.argtypes = [POINTER(c_char_p), c_int, c_char_p, POINTER(POINTER(c_char_p))]
dll.match_patterns.restype = c_int

dll.free_matches.argtypes = [POINTER(c_char_p), c_int]
dll.free_matches.restype = None

def match_patterns(input_array, pattern):
    # Convert input_array to a list of byte strings
    input_array_c = (c_char_p * len(input_array))(*[s.encode('utf-8') for s in input_array])
    output_array_c = POINTER(c_char_p)()
    num_matches = dll.match_patterns(input_array_c, len(input_array), pattern.encode('utf-8'), byref(output_array_c))

    if num_matches == 0:
        return []

    matches = [output_array_c[i].decode('utf-8') for i in range(num_matches)]
    dll.free_matches(output_array_c, num_matches)
    return matches

@xw.func
@xw.arg('input_array', ndim=1)
@xw.ret(expand='table')
def REGEXVCCPP(input_array, pattern):
    # Convert input_array to a list of strings
    input_list = [str(item) for item in input_array]
    matches = match_patterns(input_list, pattern)
    return matches

