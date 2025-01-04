import os
import ctypes
import xlwings as xw

# Add the directory containing the DLL to the DLL search path
os.add_dll_directory('D:\\Programs\\mingw64\\bin')

# Load the DLL
dll = ctypes.CDLL('D:\\dev\\rdrand_multi-threaded-new.dll')

# Define the function prototype
dll.generate_random_numbers.argtypes = [ctypes.c_int, ctypes.c_int]
dll.generate_random_numbers.restype = ctypes.POINTER(ctypes.c_ulonglong)
dll.free_numbers.argtypes = [ctypes.POINTER(ctypes.c_ulonglong)]
dll.generate_random_numbers.__stdcall = True

@xw.func
def generate_random_numbers_xlwings(num_numbers, num_threads):
    num_numbers = int(num_numbers)
    num_threads = int(num_threads)
    numbers_pointer = (ctypes.c_ulonglong * num_numbers)()
    numbers_pointer = dll.generate_random_numbers(num_numbers, num_threads)
    numbers = [numbers_pointer[i] for i in range(num_numbers)]
    dll.free_numbers(numbers_pointer)
    numbers = [num for num in numbers if num >= 100000000000000]
    numbers = [[number] for number in numbers]
    return numbers

