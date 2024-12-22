import xlwings as xw
def read_excel_range_from_open_workbook(sheet_name, range_str):
    """
    Reads a specified range of data from an already open Excel sheet.
    Parameters:
        sheet_name (str): The name of the sheet to read from.
        range_str (str): The range string (e.g., "A1:B10").
    """
    # Connect to the currently active Excel application
    app = xw.apps.active  # Connect to the active Excel instance
    # Access the specific workbook and sheet
    workbook = app.books.active  # Access the active workbook
    sheet = workbook.sheets[sheet_name]
    # Read the data from the specified range
    data = sheet.range(range_str).value
    # Print the result (the data is returned as a list of lists)
    print(f"Data from range {range_str} in sheet '{sheet_name}':")
    print(data)
    # Optionally, return this data for further processing
    return data
# Example usage
sheet_name = 'Sheet1'  # Replace with the sheet you want to read
range_str = 'A1:C5'  # Adjust the range as needed
data = read_excel_range_from_open_workbook(sheet_name, range_str)
# Optionally, manipulate the data or return as needed
