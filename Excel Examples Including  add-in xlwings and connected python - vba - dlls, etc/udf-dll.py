import xlwings as xw
import rdrand
import sys
import numpy as np
import dask.dataframe as dd
from dask.distributed import Client
from scipy.optimize import newton
import pandas as pd
from datetime import datetime, timedelta
import calendar
from cffi import FFI
import numpy as np
import os
import csv
import time
import os
os.environ['PATH'] = r'D:\Programs\Msys2\ucrt64\bin;D:\dev\dll'+';' + os.environ['PATH']

# Create FFI object
ffi1 = FFI()
# Define the C declarations
ffi1.cdef("""
    void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup);
    unsigned long long* getNumbersC();
    int getNumbersSizeC();
""")
# Load the DLL
dll1 = ffi1.dlopen('boost_rdseed_ucrt_new.dll')
@xw.func
def intel_rdrand_boost(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP):
    # Convert input parameters to integers
    NUM_NUMBERS = int(NUM_NUMBERS)
    NUM_THREAD_GROUPS = int(NUM_THREAD_GROUPS)
    NUM_THREADS_PER_GROUP = int(NUM_THREADS_PER_GROUP)
    # Call the functions
    dll1.generateRandomNumbersC(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP)
    numbers_ptr = dll1.getNumbersC()
    numbers_size = dll1.getNumbersSizeC()
    # Get the numbers
    numbers = [[int(numbers_ptr[i])] for i in range(numbers_size)]
    return numbers
# Create FFI object
ffi2 = FFI()
# Define the C declarations
ffi2.cdef("""
    void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup);
    unsigned long long* getNumbersC();
    int getNumbersSizeC();
""")
# Load the DLL
dll2 = ffi2.dlopen('boost_rdseed_ucrt_clang_new.dll')
@xw.func
def intel_rdrand_boost_clang(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP):
    # Convert input parameters to integers
    NUM_NUMBERS = int(NUM_NUMBERS)
    NUM_THREAD_GROUPS = int(NUM_THREAD_GROUPS)
    NUM_THREADS_PER_GROUP = int(NUM_THREADS_PER_GROUP)
    # Call the functions
    dll2.generateRandomNumbersC(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP)
    numbers_ptr = dll2.getNumbersC()
    numbers_size = dll2.getNumbersSizeC()
    # Get the numbers
    numbers = [[int(numbers_ptr[i])] for i in range(numbers_size)]
    return numbers
import ctypes
# Load the DLL
dll3 = ctypes.CDLL('D:\\dev\\dll\\boost_rdseed_ucrt_clang_new.dll')
# Define the function types
dll3.generateRandomNumbersC.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
dll3.getNumbersC.restype = ctypes.POINTER(ctypes.c_ulonglong)
dll3.getNumbersSizeC.restype = ctypes.c_int
@xw.func
def intel_ctypes_clang_dll(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP):
    # Convert input parameters to integers
    NUM_NUMBERS = int(NUM_NUMBERS)
    NUM_THREAD_GROUPS = int(NUM_THREAD_GROUPS)
    NUM_THREADS_PER_GROUP = int(NUM_THREADS_PER_GROUP)
    # Call the functions
    dll3.generateRandomNumbersC(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP)
    numbers_ptr = dll3.getNumbersC()
    numbers_size = dll3.getNumbersSizeC()
    # Get the numbers
    numbers = [[numbers_ptr[i]] for i in range(numbers_size)]
    return numbers
# Load the DLL
dll5 = ctypes.CDLL('D:\\dev\\dll\\boost_rdseed_ucrt_new.dll')
# Define the function types
dll5.generateRandomNumbersC.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
dll5.getNumbersC.restype = ctypes.POINTER(ctypes.c_ulonglong)
dll5.getNumbersSizeC.restype = ctypes.c_int
@xw.func
def intel_ctypes_dll(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP):
    # Convert input parameters to integers
    NUM_NUMBERS = int(NUM_NUMBERS)
    NUM_THREAD_GROUPS = int(NUM_THREAD_GROUPS)
    NUM_THREADS_PER_GROUP = int(NUM_THREADS_PER_GROUP)
    # Call the functions
    dll5.generateRandomNumbersC(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP)
    numbers_ptr = dll5.getNumbersC()
    numbers_size = dll5.getNumbersSizeC()
    # Get the numbers
    numbers = [[numbers_ptr[i]] for i in range(numbers_size)]
    return numbers
from cffi import FFI
import regex
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
from cffi import FFI
ffi = FFI()
# Load the DLL
#lib = ffi.dlopen('D:/Downloads/rust_dll/target/release/rust_rand_dll_copilot.dll')
dll_dir = r'D:\Downloads\rust_dll\target\release'
os.environ['PATH'] = dll_dir + ';' + os.environ['PATH']
lib = ffi.dlopen('rust_rand_dll_copilot_parallel.dll')
# Define the C signatures of the functions
ffi.cdef("""
    int rdrand64_step(unsigned long long *rand);
    void generate_random_numbers(int num_threads, int num_numbers);
    void allocate_memory(int num_numbers);
    unsigned long long* get_numbers();
    void free_memory();
""")
@xw.func
@xw.arg('num_threads', numbers=int)  # Use @xw.arg to specify the type of the argument
@xw.arg('num_numbers', numbers=int)
def rust_dll_rdrand(num_threads, num_numbers):
    # Allocate memory for the numbers
    lib.allocate_memory(num_numbers)
    # Generate random numbers
    lib.generate_random_numbers(num_threads, num_numbers)
    # Retrieve the generated numbers
    numbers_ptr = lib.get_numbers()
    numbers = [[numbers_ptr[i]] for i in range(num_numbers)]  # Return as list of lists
    # Free the allocated memory
    lib.free_memory()
    return numbers
# Create FFI object
ffi100 = FFI()
# Define the C declarations
ffi100.cdef("""
    void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup);
    unsigned long long* getNumbersC();
    int getNumbersSizeC();
""")
# Load the DLL
dll100 = ffi100.dlopen('boost_rdseed_ucrt_new_vc.dll')
@xw.func
def intel_rdseed_boost_vc(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP):
    # Convert input parameters to integers
    NUM_NUMBERS = int(NUM_NUMBERS)
    NUM_THREAD_GROUPS = int(NUM_THREAD_GROUPS)
    NUM_THREADS_PER_GROUP = int(NUM_THREADS_PER_GROUP)
    # Call the functions
    dll100.generateRandomNumbersC(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP)
    numbers_ptr = dll100.getNumbersC()
    numbers_size = dll100.getNumbersSizeC()
    # Get the numbers
    numbers = [[int(numbers_ptr[i])] for i in range(numbers_size)]
    return numbers

