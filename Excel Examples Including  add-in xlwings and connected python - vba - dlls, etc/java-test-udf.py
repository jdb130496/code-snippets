import xlwings as xw
from py4j.java_gateway import JavaGateway
@xw.func
def convert_array_to_string(input_array):
    # Start the gateway
    gateway = JavaGateway()
    # Access the Java class
    converter = gateway.jvm.num2str()
    # Handle the case where input is None
    if input_array is None:
        return [[""]]
    # Check if the input is a single value or a range
    if isinstance(input_array, (float, int, str)):
        input_array = [[input_array]]  # Convert single value to a 2D array
    # Convert the input array to a list of lists if necessary
    if isinstance(input_array, list):
        if isinstance(input_array[0], list):
            flat_array = [item for sublist in input_array for item in sublist]
        else:
            flat_array = [item for item in input_array]
    else:
        # Handle case where input_array is not iterable
        flat_array = []
    # Define the array in Java (using Object[] to allow mixed types)
    elements = gateway.new_array(gateway.jvm.Object, len(flat_array))
    for i in range(len(flat_array)):
        elements[i] = flat_array[i]
    # Call the Java method
    java_result = converter.convertArrayToString(elements)
    # Convert the Java result array to a Python list
    result = []
    for item in java_result:
        if item.startswith("\u200B"):
            item = item[1:]  # Remove invisible character
        result.append(item)
    # Convert the result to a vertical format for Excel
    vertical_result = [[item] for item in result]
    # Shut down the gateway
    gateway.close()
    return vertical_result
@xw.func
def java_sqrt(input_array):
    gateway = JavaGateway()
    sqrt_func = gateway.jvm.Math.sqrt
    # Handle single-cell input
    if not isinstance(input_array, list):
        input_array = [input_array]
    result = []
    for value in input_array:
        try:
            if isinstance(value, (int, float)) and value >= 0:
                result.append(sqrt_func(value))
            else:
                result.append("Error")
        except Exception:
            result.append("Error")
    # Convert to vertical format for Excel
    result = [[item] for item in result]
    gateway.close()
    return result
@xw.func
def java_abs(input_array):
    gateway = JavaGateway()
    abs_func = gateway.jvm.Math.abs
    # Handle single-cell input
    if not isinstance(input_array, list):
        input_array = [input_array]
    result = []
    for value in input_array:
        try:
            if isinstance(value, (int, float)):
                result.append(abs_func(value))
            else:
                result.append("Error")
        except Exception:
            result.append("Error")
    # Convert to vertical format for Excel
    result = [[item] for item in result]
    gateway.close()
    return result
@xw.func
def java_ln(input_array):
    gateway = JavaGateway()
    ln_func = gateway.jvm.Math.log
    # Handle single-cell input
    if not isinstance(input_array, list):
        input_array = [input_array]
    result = []
    for value in input_array:
        try:
            if isinstance(value, (int, float)) and value > 0:
                result.append(ln_func(value))
            else:
                result.append("Error")
        except Exception:
            result.append("Error")
    # Convert to vertical format for Excel
    result = [[item] for item in result]
    gateway.close()
    return result

