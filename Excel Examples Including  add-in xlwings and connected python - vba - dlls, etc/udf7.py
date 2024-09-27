import xlwings as xw
from cffi import FFI
ffi = FFI()
# Define the C function signatures
ffi.cdef("""
    int match_pattern_in_array(char **input_array, int array_length, const char *pattern, char ***output_array);
    void free_matches(char **matches, int match_count);
""")
# Load the shared library
lib = ffi.dlopen("regex_C.dll")
def pattern_match_new(input_range, pattern):
    # Flatten the list of lists and handle None values
    input_array = [str(cell[0]) if cell and cell[0] is not None else '' for cell in input_range]
    input_array_c = ffi.new("char *[]", [ffi.new("char[]", cell.encode('utf-8')) for cell in input_array])
    output_array_c = ffi.new("char ***")
    match_count = lib.match_pattern_in_array(input_array_c, len(input_array), pattern.encode('utf-8'), output_array_c)
    if match_count < 0:
        return "Error in matching pattern"
    output_array = [ffi.string(output_array_c[0][i]).decode('utf-8') for i in range(match_count)]
    # Free the allocated memory
    lib.free_matches(output_array_c[0], match_count)
    return output_array
import xlwings as xw
@xw.func
def FILL_EMPTY(excel_range):
    filled_list = []
    last_value = ""
    for cell in excel_range:
        if cell is not None and cell != "":  # Check if the cell is not None or empty
            last_value = cell
        filled_list.append([last_value])  # Ensure each result is a list to maintain vertical format
    return filled_list
@xw.func
@xw.arg('data', ndim=1)
def SPLIT_TEXT(data, delimiter):
    try:
        if not data or all(cell is None for cell in data):
            return [""]
        # Split the text and find the maximum length of the sublists
        split_data = [cell.split(delimiter) if cell is not None else [""] for cell in data]
        max_length = max(len(sublist) for sublist in split_data)
        # Ensure all sublists have the same length by padding with empty strings
        padded_data = [sublist + [""] * (max_length - len(sublist)) for sublist in split_data]
        return padded_data
    except Exception as e:
        return str(e)
@xw.func
def EXCELORM(range1, range2, condition):
    result = []
    for val1, val2 in zip(range1, range2):
        val1 = 0 if val1 is None or val1 == "" else float(val1)
        val2 = 0 if val2 is None or val2 == "" else float(val2)
        # Use eval to dynamically evaluate the condition
        if eval(condition):
            result.append([True])
        else:
            result.append([False])
    return result
import requests
from bs4 import BeautifulSoup
import xlwings as xw
@xw.func
def get_sanskrit_mantras(url):
    # Send a GET request to the webpage
    response = requests.get(url)
    # Parse the HTML content of the webpage
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all article tags with the specified class
    articles = soup.find_all('article', class_='dpLyricsWrapper')
    # Initialize a list to store the mantras
    mantras = []
    # Iterate over each article tag
    for article in articles:
        # Find all div tags with the specified class within the article
        divs = article.find_all('div', class_='dpNameCardMantra dpFlexEqual')
        for div in divs:
            # Find the div containing the Sanskrit mantra
            mantra_div = div.find('div', class_='dpListPrimaryTitle')
            if mantra_div:
                # Extract the text and add it to the list
                mantras.append(mantra_div.get_text(strip=True))
    # Return the list of mantras in a vertical format
    return [[mantra] for mantra in mantras]
import xlwings as xw

def hex_to_rgb(hex_color):
    """Convert hex color string (#RRGGBB) to an RGB tuple."""
    hex_color = hex_color.lstrip('#')  # Remove the '#' if present
    red = int(hex_color[0:2], 16)
    green = int(hex_color[2:4], 16)
    blue = int(hex_color[4:6], 16)
    return (red, green, blue)

@xw.func
def set_cell_color(cell_address, hex_color):
    print(f"Called with cell_address: {cell_address} and hex_color: {hex_color}")

    if cell_address is None:
        return "Error: cell_address is None. Please provide a valid cell address."

    wb = xw.Book.caller()
    sheet = wb.sheets.active
    print(f"Active sheet: {sheet.name}")

    rgb_value = hex_to_rgb(hex_color)
    print(f"Converted hex '{hex_color}' to RGB tuple: {rgb_value}")

    try:
        cell = sheet.range(cell_address)
        print(f"Setting color for cell: {cell_address}")
        print(f"Current cell value: {cell.value}")
        
        # Set the interior color using an RGB tuple
        #cell.color = rgb_value
        sheet.range(cell_address).color = rgb_value
        print(f"Set color of {cell_address} to RGB {rgb_value}")
    except Exception as e:
        print(f"Error setting color: {str(e)}")
        return f"Error setting color: {str(e)}"
@xw.sub
def testcolor(cell_address):
    wb = xw.Book()
    xw.Range(cell_address).color = (255,255,234)


