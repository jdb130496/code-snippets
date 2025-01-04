import xlwings as xw
from cffi import FFI

ffi = FFI()

# Load the DLL
#lib = ffi.dlopen('D:/Downloads/rust_dll/target/release/rust_rand_dll_copilot.dll')
lib = ffi.dlopen('D:/Downloads/rust_dll/target/release/rust_rand_dll_copilot_parallel.dll')
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

