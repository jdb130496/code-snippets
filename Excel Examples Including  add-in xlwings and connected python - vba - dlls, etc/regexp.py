import xlwings as xw
import cffi
# Define the C function signatures and load the DLL
ffi = cffi.FFI()
ffi.cdef("""
    int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array);
    void free_matches(char **matches, int match_count);
""")
# Load the DLL
#dll = ffi.dlopen("D:\\Programs\\Msys2\\home\\dhawal123\\Downloads\\regex-C-xlwings-2.dll")
dll = ffi.dlopen("D:\\Programs\\Msys2\\home\\dhawal123\\Downloads\\regex-C-10072024.dll")
@xw.func
def match_pattern_new(input_list, pattern):
    # Replace None values with empty strings and encode all non-empty strings
    input_array = [ffi.new("char[]", (item or "").encode('utf-8')) for item in input_list]
    # Convert the list to a C array of strings
    input_array_c = ffi.new("char*[]", input_array)
    # Prepare the output array pointer
    output_array_c = ffi.new("char***")
    # Call the DLL function
    match_count = dll.match_pattern_in_array(input_array_c, len(input_list), pattern.encode('utf-8'), output_array_c)
    if match_count < 0:
        raise RuntimeError("Error matching pattern")
    # Initialize output list with None
    output_list = [None] * len(input_list)
    # Collect matched strings
    matched_strings = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(match_count)]
    # Update output_list with matched items using a list comprehension and update matched_indices
    matched_indices = {i for i, item in enumerate(input_list) if item and item in matched_strings}
    output_list = [[item if i in matched_indices else None] for i, item in enumerate(input_list)]
    # Free the output array allocated by the DLL
    dll.free_matches(output_array_c[0], match_count)
    return output_list

import xlwings as xw
import cffi
# Define the C function signatures and load the DLL
ffi = cffi.FFI()
ffi.cdef("""
    int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array);
    void free_matches(char **matches, int match_count);
""")
# Load the DLL
dll = ffi.dlopen("D:\\Programs\\Msys2\\home\\dhawal123\\Downloads\\regex-c-metaai-dll.dll")
@xw.func
def match_pattern_metaai(input_list, pattern):
    # Replace None values with empty strings and encode all non-empty strings
    input_array = [ffi.new("char[]", (item or "").encode('utf-8')) for item in input_list]
    # Convert the list to a C array of strings
    input_array_c = ffi.new("char*[]", input_array)
    # Prepare the output array pointer
    output_array_c = ffi.new("char***")
    # Call the DLL function
    match_count = dll.match_pattern_in_array(input_array_c, len(input_list), pattern.encode('utf-8'), output_array_c)
    if match_count < 0:
        raise RuntimeError("Error matching pattern")
    # Initialize output list with None
    output_list = [None] * len(input_list)
    # Collect matched strings
    matched_strings = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(match_count)]
    # Update output_list with matched items using a list comprehension and update matched_indices
    matched_indices = {i for i, item in enumerate(input_list) if item and item in matched_strings}
    output_list = [[item if i in matched_indices else None] for i, item in enumerate(input_list)]
    # Free the output array allocated by the DLL
    dll.free_matches(output_array_c[0], match_count)
    return output_list

import re
import xlwings as xw
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXFINDGROUP(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            cell_result = []
            for pattern in patterns:
                match = re.search(pattern, cell_str)
                if match:
                    cell_result.append(match.group(1))  # Extract the captured group
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("")
        result.append(row_result)
    return result
import re
import xlwings as xw
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXFINDM2(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            cell_result = []
            for pattern in patterns:
                match = re.search(pattern, cell_str, flags=re.UNICODE)
                if match:
                    cell_result.append(cell_str)  # Return the entire string
            if len(cell_result) == len(patterns) and not cell_str.isprintable():
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("")
        result.append(row_result)
    return result
import re
import xlwings as xw
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
#@xw.arg('replacement', ndim=0)
def REGEXREPLM(excel_range, patterns, replacement):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            for pattern in patterns:
                cell_str = re.sub(pattern, replacement, cell_str)  # Replace matched string with the specified replacement
            row_result.append(cell_str.strip())  # Remove leading/trailing spaces
        result.append(row_result)
    return result
import xlwings as xw
import sympy as sp
from sympy import sin, cos, log, sqrt
# Define the integration function
def indefinite_integrate(func):
    x = sp.symbols('x')
    # Convert the string function to a sympy expression
    expr = sp.sympify(func)
    # Perform the indefinite integration
    result = sp.integrate(expr, x)
    return result
# Create the UDF
@xw.func
@xw.arg('excel_range', xw.Range)  # Use xw.Range to get the actual range object
def integrate_excel(excel_range):
    # Get the address of the range directly
    range_address = excel_range.address
    # Convert Excel range to list of lists
    func_list = excel_range.value  # Use .value to get the data from the range
    # Initialize results list
    results = []
    # Iterate over each function in the list
    # Check if the range contains a single cell or multiple cells
    if len(excel_range)!=1:
#    if ":" in range_address: (Alternative to matching length == 1 as above)
        # Get the address of the first cell in the range
        first_cell_address = range_address.split(":")[0].replace("$", "")
        # Get the address of the last cell in the range
        last_cell_address = range_address.split(":")[1].replace("$", "")
        # Check if the range is horizontal or vertical
        for func in func_list:
            try:
                result = indefinite_integrate(func)  # Each func is already a single value
                results.append(str(result))
            except Exception as e:
                results.append(f"Error: {e}")
        if first_cell_address[0] != last_cell_address[0]:
            # Horizontal range
            return [results]  # Return results as a horizontal array
        else:
            # Vertical range
            return [[res] for res in results]  # Return results as a vertical array
    else:
        try:
            result = indefinite_integrate(func_list)  # Each func is already a single value
            results.append(str(result))
        except Exception as e:
            results.append(f"Error: {e}")
        # Single cell range
        return [results]


