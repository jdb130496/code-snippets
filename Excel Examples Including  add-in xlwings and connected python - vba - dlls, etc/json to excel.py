import json
import xlsxwriter
from typing import List, Dict

def flatten_json(nested_json: Dict, delimiter: str = '_') -> Dict:
    """Flatten a nested json file"""
    out = {}

    def flatten(x: (List, Dict, str), name: str = ''):
        if type(x) is dict:
            for a in x:
                flatten(x[a], name + a + delimiter)
        elif type(x) is list:
            i = 0
            for a in x:
                flatten(a, name + str(i) + delimiter)
                i += 1
        else:
            out[name[:-1]] = x

    flatten(nested_json)
    return out

# Load the JSON file
with open(r'D:\RR Data\IT Return FY 2022-23\AHKPR9873R_upload_2023-24_08-07-2023-18-22.json', 'r') as f:
    data = json.load(f)

# Flatten the JSON data
flat_data = flatten_json(data)

# Create a new Excel file and add a worksheet
workbook = xlsxwriter.Workbook('itr1_json_to_excel.xlsx')
worksheet = workbook.add_worksheet()

# Write the data to the worksheet
row = 0
for key, value in flat_data.items():
    worksheet.write(row, 0, key)
    worksheet.write(row, 1, value)
    row += 1

# Close the workbook
workbook.close()

