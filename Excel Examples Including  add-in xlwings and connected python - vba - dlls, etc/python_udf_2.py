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
from datetime import datetime
@xw.func
@xw.arg('data', ndim=2)
def calculate_tithi_excel(data):
    results = []
    for row in data:
        # Unpack the inputs from the row
        date, sun_degree, sun_minute, moon_degree, moon_minute = row
        try:
            # Debug: Print input values to verify correct reception
#            print(f"Date: {date}, Sun Degree: {sun_degree}, Sun Minute: {sun_minute}, Moon Degree: {moon_degree}, Moon Minute: {moon_minute}")
            # Check if the date is a datetime object or an Excel date float
            if isinstance(date, datetime) or isinstance(date, (float, int)):  
                # If it's a float or int, convert it to datetime
                if isinstance(date, (float, int)):
                    # Excel's base date is 1899-12-30, so we add 2 days
                    date_as_datetime = datetime.fromordinal(int(date) + 693594)
                else:
                    date_as_datetime = date  # already a datetime object
                print(f"Converted Date: {date_as_datetime}")
                # Check if sun and moon degree/minute values are numeric
                if all(isinstance(x, (int, float)) for x in [sun_degree, sun_minute, moon_degree, moon_minute]):
                    # Combine degrees and minutes for Sun and Moon
                    sun_longitude = sun_degree + (sun_minute / 60)
                    moon_longitude = moon_degree + (moon_minute / 60)
                    # Calculate the difference in longitude
                    longitude_difference = moon_longitude - sun_longitude
                    # If the difference is negative, add 360 to make it positive
                    if longitude_difference < 0:
                        longitude_difference += 360
                    # Calculate the tithi number
                    tithi_number = int(longitude_difference // 12) + 1
                    # Determine the paksha and tithi name
                    if tithi_number <= 15:
                        paksha = 'Shukla'
                    else:
                        paksha = 'Krishna'
                    tithi_names = [
                        'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
                        'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
                        'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima', 'Amavasya'
                    ]
                    # Adjust the tithi index for Krishna Paksha
                    tithi_index = (tithi_number - 1) % 15
                    # Special case for Amavasya in Krishna Paksha
                    if paksha == 'Krishna' and tithi_number == 30:
                        tithi_name = tithi_names[-1]  # Amavasya
                    else:
                        tithi_name = tithi_names[tithi_index]
                    # Append the result for the current row
                    results.append(f"{paksha} {tithi_name}")
                else:
                    # If any of the sun or moon values are not numeric, return an error
                    results.append("#INVALID_SUN_OR_MOON_VALUE")
            else:
                # If date is not valid, append an error message
                results.append("#INVALID_DATE")
        except Exception as e:
            # Catch any other exceptions and return an error message
            results.append(f"#ERROR: {str(e)}")
    return results
@xw.func
@xw.arg('rng1', ndim=2)
@xw.arg('rng2', ndim=2)
def tstrangecalc(rng1, rng2):
    # Convert single-cell ranges to 2D lists
    if not isinstance(rng1[0], list):
        rng1 = [[cell for cell in rng1]]
    if not isinstance(rng2[0], list):
        rng2 = [[rng2[0][0]] * len(rng1[0])]  # Repeat the value to match dimensions
    # Perform element-wise addition
    result1 = [[rng1[i][j] + rng2[i][j] for j in range(len(rng1[0]))] for i in range(len(rng1))]
    return result1
from datetime import datetime
import xlwings as xw
@xw.func
#@xw.arg('data1', ndim=2)
@xw.arg('data', ndim=2)
def calculate_tithi_excel_new(data):
    results = []
    for row in data:
        try:
            # Check if the row has exactly 7 elements
#            if len(row) != 7:
#                results.append("#DIMENSION_ERROR")
#                continue
            # Unpack the inputs from the row
            date, sun, moon = row
            # Debug: Print input values to verify correct reception
#            print(f"Date: {date}, Sun: {sun}, Moon: {moon}")
            # Check if the date is a datetime object or an Excel date float
            if isinstance(date, datetime) or isinstance(date, (float, int)):
                # If it's a float or int, convert it to datetime
                if isinstance(date, (float, int)):
                    # Excel's base date is 1899-12-30, so we add 2 days
                    date_as_datetime = datetime.fromordinal(int(date) + 693594)
                else:
                    date_as_datetime = date  # already a datetime object
#                print(f"Converted Date: {date_as_datetime}")
                # Combine degrees for Sun and Moon
                sun_longitude = sun
                moon_longitude = moon
                # Calculate the difference in longitude
                longitude_difference = moon_longitude - sun_longitude
                # If the difference is negative, add 360 to make it positive
                if longitude_difference < 0:
                    longitude_difference += 360
                # Calculate the tithi number
                tithi_number = int(longitude_difference // 12) + 1
                # Determine the paksha and tithi name
                if tithi_number <= 15:
                    paksha = 'Shukla'
                else:
                    paksha = 'Krishna'
                tithi_names = [
                    'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
                    'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
                    'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima', 'Amavasya'
                ]
                # Adjust the tithi index for Krishna Paksha
                tithi_index = (tithi_number - 1) % 15
                # Special case for Amavasya in Krishna Paksha
                if paksha == 'Krishna' and tithi_number == 30:
                    tithi_name = tithi_names[-1]  # Amavasya
                else:
                    tithi_name = tithi_names[tithi_index]
                # Append the result for the current row
                results.append(f"{paksha} {tithi_name}")
            else:
                # If date is not valid, append an error message
                results.append("#INVALID_DATE")
        except Exception as e:
            # Catch any other exceptions and return an error message
            results.append(f"#ERROR: {str(e)}")
    return results

