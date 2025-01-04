import xlwings as xw
import ctypes

# Load the DLL (adjust the path if needed)
random_numbers_dll = ctypes.CDLL("D:\\dev\\rdrand_bard.dll")

# Define the function prototype
generate_random_numbers = random_numbers_dll.generate_random_numbers
generate_random_numbers.argtypes = [ctypes.c_uint]
generate_random_numbers.restype = ctypes.POINTER(ctypes.c_ulonglong)

@xw.func
def generate_random_numbers_xlwings(input_value):
    """Generates random numbers using a C DLL and returns them to Excel.

    Args:
        input_value (xw.Range or number): A cell reference, a range
            containing a single value, or a number directly representing
            the number of random numbers to generate.

    Returns:
        list: A list of lists, where each inner list contains a single
            random number.
    """

    if isinstance(input_value, xw.Range):
        value = input_value.value[0][0]
    elif isinstance(input_value, (int, float)):
        value = input_value
    else:
        raise ValueError("Input value must be a number, a cell reference, or a range containing a number.")

    num_numbers = int(value)  # Ensure it's an integer
    random_array = generate_random_numbers(num_numbers)
    random_list = [random_array[i] for i in range(num_numbers)]

    # Check for exactly 15 digits (including trailing zeros)
    for num in random_list:
        assert len(str(num)) == 15

    output_list = [[num] for num in random_list]  # Create a list of lists

    return output_list

