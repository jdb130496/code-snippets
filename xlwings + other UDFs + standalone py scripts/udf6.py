import xlwings as xw
import pandas as pd
from ta.trend import wma_indicator
from ta.trend import sma_indicator
import os
os.environ['PATH'] = r'D:\Programs\Msys2\ucrt64\bin;D:\dev\dll'+';' + os.environ['PATH']
@xw.func
def weaverage(cls1, win123, fillna=False):
    """
    Calculate the Weighted Moving Average (WMA) for the given close prices.

    Parameters:
        cls1 (list of lists): Input range from Excel.
        win123 (int): Window size for WMA calculation.
        fillna (bool): Fill NaN values with False.

    Returns:
        list: Weighted Moving Average (WMA) series.
    """
    # Convert the list of lists to a pandas Series
    close_series = pd.Series([float(x) for x in cls1 if isinstance(x, (int, float))])
    
    # Calculate the WMA
    wma = wma_indicator(close_series, window=int(win123), fillna=fillna)
    
    # Return the WMA as a list
    return wma.tolist()

@xw.func
def smavg(cls2, win456, fillna=False):
    """
    Calculate the Weighted Moving Average (WMA) for the given close prices.

    Parameters:
        cls1 (list of lists): Input range from Excel.
        win123 (int): Window size for WMA calculation.
        fillna (bool): Fill NaN values with False.

    Returns:
        list: Weighted Moving Average (WMA) series.
    """
    # Convert the list of lists to a pandas Series
    close_series2 = pd.Series([float(x) for x in cls2 if isinstance(x, (int, float))])
    
    # Calculate the WMA
    sma = sma_indicator(close_series2, window=int(win456), fillna=fillna)
    
    # Return the WMA as a list
    return sma.tolist()
import xlwings as xw
@xw.func
def slice_text_udf(input_range):
    # Flatten the input range (list of lists) into a single string
    input_string = ''.join([str(cell) for row in input_range for cell in row])
    # Function to slice the text into chunks of 32 characters
    def slice_text(text, chunk_size):
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
    # Slice the input string into chunks of 32 characters
    chunks = slice_text(input_string, 32)
    # Return the chunks as a vertical array (dynamic array)
    return [[chunk] for chunk in chunks]
@xw.func
def hex_to_decimal_string_udf(input_range_1):
        # Flatten the input range (list of lists) into a single list of strings
    flattened_input = input_range_1
#    flattened_input = [str(cell1).strip() for row1 in input_range_1 for cell1 in row1]
#    print(flattened_input)
    # Function to convert a single hex string to a decimal string
    def hex_to_decimal_string(hex_string_1):
        hex_string_1 = hex_string_1.strip()  # Remove any leading or trailing whitespace
        if len(hex_string_1) != 32:
            return "Error: Input must be 32 characters long."
        else:
            decimal_value_1 = sum(int(char_1, 16) * (16 ** i_1) for i_1, char_1 in enumerate(reversed(hex_string_1)))
            return str(decimal_value_1)
    # Iterate over each element in the flattened input and convert to decimal string
    result_1 = []
    for hex_string_1 in flattened_input:
        if hex_string_1:  # Ensure the cell is not empty after stripping
            decimal_string_1 = hex_to_decimal_string(hex_string_1).strip()
            # Append the entire decimal string as a single element in the result list
            result_1.append([decimal_string_1])
        else:
            result_1.append(["Error: Empty cell"])
    return result_1
import math
@xw.func
def decimal_to_bits_udf(input_range_3):
    print(input_range_3)
    # Function to convert a single decimal number to the number of bits required
    def decimal_to_bits(decimal_number_input):
        try:
            decimal_number_3 = int(decimal_number_input)
        except ValueError:
            return "Invalid input"
        return str(math.ceil(math.log2(decimal_number_3)))
    # Flatten the input range (list of lists) into a single list of strings
    flattened_input_2 = input_range_3 
    # Iterate over each element in the flattened input and convert to number of bits
    result = []
    for decimal_number_2 in flattened_input_2:
        bits = decimal_to_bits(decimal_number_2)
        result.append([bits])
    return result
@xw.func
def hex_to_bits_udf(input_range_3):
    # Function to convert a single hex string to the number of bits required
    def hex_to_bits(hex_string_3):
        try:
            # Convert hex string to decimal number
            decimal_number_3 = int(hex_string_3, 16)
        except ValueError:
            return "Invalid input"
        # Calculate the number of bits required
        return str(math.ceil(math.log2(decimal_number_3)))
    # Flatten the input range (list of lists) into a single list of strings
    flattened_input_3 = input_range_3
    # Iterate over each element in the flattened input and convert to number of bits
    result = []
    for hex_string_3 in flattened_input_3:
        bits = hex_to_bits(hex_string_3)
        result.append([bits])
    return result




