import pandas as pd
import xlwings as xw
import re
@xw.func
def process_data(data):
    IDS = ['26909']
    
    # Convert the input data (list of lists) to a pandas DataFrame, using the first row as headers
    df = pd.DataFrame(data[1:], columns=data[0])

    final_results = []

    # Process each ID
    for ID1 in IDS:
        filtered_df = df[(df['ID'] == ID1) & (df['Type'] != 'Purchase Order') & (df['Type'] != 'Sales Order')] #& (df['Date'] < '2024-07-01')]
        grouped_df = filtered_df.groupby(['Type', 'Project: ID', 'Account']).agg({'Amount': lambda x: x.sum() * -1}).reset_index()
        grouped_df.rename(columns={'Amount': 'Amt'}, inplace=True)
        final_results.append(grouped_df)

    # Combine all results into a single DataFrame
    combined_results = pd.concat(final_results, ignore_index=True)

    # Sort the combined results by 'Project: ID' in ascending order
    combined_results.sort_values(by=['Project: ID', 'Amt'], inplace=True)

    # Add headers to the output data
    output_data = [combined_results.columns.tolist()] + combined_results.values.tolist()

    # Return the combined results with headers as a dynamic array
    return output_data

import re
import xlwings as xw

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXSTR(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            cell_result = cell_str
            for pattern in patterns:
                lines = cell_result.splitlines()
                maxlen = len(lines)  # Get the number of lines
                if pattern == "Country":
                    cell_result = lines[maxlen - 1].strip() if maxlen > 0 else ""
                else:
                    cell_result = lines[maxlen - 2].strip() if maxlen > 1 else cell_result
                    match = re.search(pattern, cell_result, flags=re.UNICODE | re.DOTALL)
                    if match:
                        cell_result = match.group().strip()  # Update cell_result with the matched string
                    else:
                        cell_result = ""
                        break  # If any pattern does not match, break the loop
            row_result.append(cell_result)
        result.append(row_result)
    return result

import re
import xlwings as xw
@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
#@xw.arg('replacement', ndim=0)
def REGEXREPLM2(excel_range, patterns, replacement):
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


@xw.func
def SPLIT_TEXT_2(data, delimiter):
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
