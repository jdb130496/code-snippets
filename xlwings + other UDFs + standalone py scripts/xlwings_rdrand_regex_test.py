from cffi import FFI
import xlwings as xw
import regex

# Create FFI object
ffi = FFI()

# Define the C function prototype
ffi.cdef("""
    void generate_random_numbers(int num_threads, int num_numbers);
    unsigned long long* get_numbers();
    void free_numbers(unsigned long long *numbers);
""")

# Load the DLL
dll = ffi.dlopen('D:\\OneDrive - 0yt2k\\Compiled dlls & executables\\rdrand_multithreaded_clang_msys.dll')
#dll = ffi.dlopen('D:\\dev\\rdrand_multithreaded_clang_test.dll')
#dll = ffi.dlopen('D:\\Downloads\\target\\x86_64-pc-windows-gnu\\release\\rust_rand_dll_new.dll')

@xw.func
def generate_random_numbers_xlwings(num_numbers, num_threads):
    # Convert the arguments to integers
    num_numbers = int(num_numbers)
    num_threads = int(num_threads)

    # Call the DLL function
    dll.generate_random_numbers(num_threads, num_numbers)

    # Get the generated numbers
    numbers_pointer = dll.get_numbers()
    numbers = [numbers_pointer[i] for i in range(num_numbers)]

    # Convert to a list of lists
    numbers = [[number] for number in numbers]

    # Free the numbers array
    dll.free_numbers(numbers_pointer)

    return numbers
# 1st Function - REGEXFIND
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXFIND(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_result = []
            for pattern in patterns:
                match = regex.search(pattern, cell)
                if match:
                    cell_result.append(match.group())
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("Pattern Not Found")
        result.append(row_result)
    return result

import re

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
@xw.arg('replacement')
def REGEXREPLACE(excel_range, patterns, replacement):
    result = []
    if replacement is None:
        replacement = ""
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_result = cell
            for pattern in patterns:
                if re.search(pattern, cell_result):
                    cell_result = re.sub(pattern, replacement, cell_result)
            row_result.append(cell_result)
        result.append(row_result)
    return result




