# Path to the file
file_path = r'D:\dev\data.txt'
# Initialize an empty list to hold the rows
data_list = []
# Open the file and read it line by line
with open(file_path, 'r', encoding='utf-8') as file:
    for line in file:
        # Strip any leading/trailing whitespace from the line
        line = line.strip()
        # If the line is not empty, split it by whitespace and append it to the list
        if line:
            # Split by whitespace or any delimiter (e.g. ',' for CSV)
            columns = line.split()
            data_list.append(columns)
# Print or return the result
print(data_list)
import ctypes
def match_patterns(input_array, pattern):
    """
    Python UDF for matching patterns in an array using a C++ DLL.
    Parameters:
    - input_array: a list of lists (each representing a row of strings from Excel, can have blanks)
    - pattern: a string regex pattern to match
    Returns:
    - List of matched strings with their original indices
    """
    # Step 1: Flatten the input list of lists into a list of strings
    flattened_input = [' '.join(item) for item in input_array]
    # Convert the flattened input array to ctypes array of c_char_p (C-style string array)
    c_array = (ctypes.c_char_p * len(flattened_input))()
    for i, val in enumerate(flattened_input):
        c_array[i] = ctypes.c_char_p(val.encode('utf-8') if val else b'')
    # Step 2: Prepare for the output arrays from the C++ DLL
    output_array = ctypes.POINTER(ctypes.c_char_p)()
    output_indices = ctypes.POINTER(ctypes.c_size_t)()
    print("Calling match_patterns with:")
    print(f"c_array: {list(c_array)}")
    print(f"pattern: {pattern}")
    # Step 3: Call the DLL function
    num_matches = cpp_dll.match_patterns(
        c_array, len(flattened_input),
        pattern.encode('utf-8'),
        ctypes.byref(output_array),
        ctypes.byref(output_indices)
    )
    print(f"num_matches: {num_matches}")
    if num_matches == 0:
        print("No matches found or error occurred.")
        return []
    # Step 4: Collect the result in a list of tuples (matched string, original index)
    result = []
    for i in range(num_matches):
        matched_str = ctypes.cast(output_array[i], ctypes.c_char_p).value.decode('utf-8')
        original_index = output_indices[i]
        result.append((matched_str, original_index))
    # Step 5: Free the allocated memory in the DLL
    cpp_dll.free_matches(output_array, output_indices, num_matches)
    return result

