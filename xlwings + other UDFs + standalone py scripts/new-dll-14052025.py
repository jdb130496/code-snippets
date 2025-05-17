import xlwings as xw
import time
import sys
import numpy as np
import os
from cffi import FFI

# Ensure the DLL path is in the system PATH
os.environ['PATH'] = r'D:\Programs\Msys2\ucrt64\bin;D:\dev\dll;D:\boost\stagelib\lib' + ';' + os.environ['PATH']

# Create FFI object
ffi = FFI()

# Define the C declarations - same as before since the function signatures haven't changed
ffi.cdef("""
    void generateRandomNumbersC(int numNumbers, int numThreadGroups, int numThreadsPerGroup);
    unsigned long long* getNumbersC();
    int getNumbersSizeC();
""")

# Load the new DLL
try:
    dll = ffi.dlopen('rdseed_boost_new_claude.dll')
    print("Successfully loaded rdseed_boost_new_claude.dll")
except Exception as e:
    print(f"Error loading DLL: {e}")
    # Fallback to the original DLL if the new one can't be loaded
    try:
        dll = ffi.dlopen('boost_rdseed_ucrt_new.dll')
        print("Falling back to boost_rdseed_ucrt_new.dll")
    except Exception as e2:
        print(f"Error loading fallback DLL: {e2}")
        # Set dll to None so we can check it later
        dll = None

@xw.func
@xw.arg('NUM_NUMBERS', numbers=int)
@xw.arg('NUM_THREAD_GROUPS', numbers=int)
@xw.arg('NUM_THREADS_PER_GROUP', numbers=int)
def intel_rdseed_boost_claude(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP):
    """
    Generate random numbers using RDSEED instruction with multi-threading via Claude's optimized implementation.
    
    Args:
        NUM_NUMBERS: Total number of random numbers to generate
        NUM_THREAD_GROUPS: Number of thread groups
        NUM_THREADS_PER_GROUP: Number of threads per group
        
    Returns:
        A list of random numbers
    """
    # Verify DLL was loaded
    if dll is None:
        return [["Error: DLL could not be loaded"]]
    
    # Error handling for input parameters
    if NUM_NUMBERS <= 0 or NUM_THREAD_GROUPS <= 0 or NUM_THREADS_PER_GROUP <= 0:
        return [["Error: All input parameters must be positive integers"]]
    
    try:
        # Convert input parameters to integers (needed for proper C++ function calls)
        NUM_NUMBERS = int(NUM_NUMBERS)
        NUM_THREAD_GROUPS = int(NUM_THREAD_GROUPS)
        NUM_THREADS_PER_GROUP = int(NUM_THREADS_PER_GROUP)
        
        # Start timing for performance measurement
        start_time = time.time()
        
        # Call the function to generate random numbers
        dll.generateRandomNumbersC(NUM_NUMBERS, NUM_THREAD_GROUPS, NUM_THREADS_PER_GROUP)
        
        # Get pointer to the generated numbers
        numbers_ptr = dll.getNumbersC()
        numbers_size = dll.getNumbersSizeC()
        
        # Convert C array to Python list
        numbers = [[int(numbers_ptr[i])] for i in range(numbers_size)]
        
        # Display generation time for performance monitoring
        #generation_time = time.time() - start_time
        #numbers.append([f"Generation time: {generation_time:.4f} seconds"])
        
        return numbers
    
    except Exception as e:
        return [[f"Error: {str(e)}"]]

# For testing outside of Excel
if __name__ == "__main__":
    # Simple test with small values
    test_result = intel_rdseed_boost_claude(100, 2, 2)
    print(f"Generated {len(test_result)-1} random numbers")
    if len(test_result) > 3:  # Print a sample of numbers
        print("Sample numbers:")
        for i in range(3):
            print(f"  {test_result[i][0]}")
    print(test_result[-1][0])  # Print the timing information
