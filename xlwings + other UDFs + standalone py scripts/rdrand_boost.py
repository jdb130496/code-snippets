import xlwings as xw
from cffi import FFI
import os

os.environ['PATH'] = r'D:\\Programs\\Msys2\\mingw64\\bin;' + os.environ['PATH']

# Create FFI object
ffi = FFI()

# Define the C declarations
ffi.cdef("""
    void generateRandomNumbersC(int numNumbers, int numWorkers, int numThreads);
    unsigned long long* getNumbersC();
    int getNumbersSizeC();
""")

# Load the DLL
dll = ffi.dlopen('D:\\Dev\\boost_rdrand.dll')

@xw.func
def intel_rdrand_boost(NUM_NUMBERS, NUM_WORKERS, NUM_THREADS):
    # Convert input parameters to integers
    NUM_NUMBERS = int(NUM_NUMBERS)
    NUM_WORKERS = int(NUM_WORKERS)
    NUM_THREADS = int(NUM_THREADS)

    # Call the functions
    dll.generateRandomNumbersC(NUM_NUMBERS, NUM_WORKERS, NUM_THREADS)
    numbers_ptr = dll.getNumbersC()
    numbers_size = dll.getNumbersSizeC()

    # Get the numbers
    numbers = [[int(numbers_ptr[i])] for i in range(numbers_size)]
    return numbers

