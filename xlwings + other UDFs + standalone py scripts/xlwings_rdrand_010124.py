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
dll = ffi.dlopen('D:\\dev\\rdrand_multithreaded_clang_msys.dll')
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

