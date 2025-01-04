from cffi import FFI
import xlwings as xw

# Create FFI object
ffi = FFI()

# Define the C function prototype
ffi.cdef("""
    void generate_random_numbers(int num_threads, int num_numbers);
    unsigned long long* get_numbers();
    void free_numbers(unsigned long long *numbers);
""")

# Load the DLL
dll = ffi.dlopen('D:\\dev\\rdrand_multi-threaded-new.dll')

@xw.func
def generate_random_numbers_xlwings(num_numbers, num_threads):
    num_numbers = int(num_numbers)
    num_threads = int(num_threads)
    dll.generate_random_numbers(num_threads, num_numbers)
    numbers_pointer = dll.get_numbers()
    numbers = [numbers_pointer[i] for i in range(num_numbers)]
    numbers = [[number] for number in numbers]
    dll.free_numbers(numbers_pointer)
    return numbers

