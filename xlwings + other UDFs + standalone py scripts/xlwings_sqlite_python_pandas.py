import pandas as pd
import xlwings as xw
import re
import numpy as np

@xw.func
def process_pandas(file_path):
    IDS = ['32075']
    # Read the CSV file into a pandas DataFrame with headers and quotes set to true
    df = pd.read_csv(file_path, header=0, quotechar='"')
    df.columns = df.columns.str.strip()
    df['Project: ID'] = df['Project: ID'].fillna('')

    # Create the 'ID' column using vectorized regex operations
    id_pattern = r'(^\d+(?=\s-)|^\d+_\d+(?=\s-))'
    df['ID'] = df['Project: ID'].str.extract(id_pattern, expand=False).fillna('')

    # Sanitize 'Amount' and 'Qty' columns
    df['Amount'] = df['Amount'].str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    df['Qty'] = df['Qty'].astype(str).str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')

    # Convert 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    final_results = []

    # Process each ID
    for ID1 in IDS:
        filtered_df = df[(df['ID'] == ID1) & (df['Type'] != 'Purchase Order') & (df['Type'] != 'Sales Order')] #& (df['Date'] < pd.Timestamp('2024-07-01'))]
        grouped_df = filtered_df.groupby(['Type', 'Project: ID', 'Account']).agg({'Amount': 'sum'}).reset_index()
        grouped_df['Amt'] = -grouped_df['Amount'].where(grouped_df['Amount'] > 0, grouped_df['Amount'])
        grouped_df.drop(columns=['Amount'], inplace=True)
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
def REGEXSTR2(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            cell_result = []
            for pattern in patterns:
                match = re.search(pattern, cell_str, flags=re.UNICODE)
                if match:
                    cell_result.append(match.group())  # Return the matched string
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("")
        result.append(row_result)
    return result

import pandas as pd
import xlwings as xw
import numpy as np
from numba import jit

@jit(nopython=True)
def sanitize_amount_qty(amounts, qtys):
    sanitized_amounts = np.empty(len(amounts), dtype=np.float64)
    sanitized_qtys = np.empty(len(qtys), dtype=np.float64)
    
    for i in range(len(amounts)):
        sanitized_amounts[i] = amounts[i]
        sanitized_qtys[i] = qtys[i]
    
    return sanitized_amounts, sanitized_qtys

@xw.func
def process_pandas_numba(file_path):
    IDS = ['32075']
    # Read the CSV file into a pandas DataFrame with headers and quotes set to true
    df = pd.read_csv(file_path, header=0, quotechar='"')
    df.columns = df.columns.str.strip()
    df['Project: ID'] = df['Project: ID'].fillna('')

    # Create the 'ID' column using vectorized regex operations
    id_pattern = r'(^\d+(?=\s-)|^\d+_\d+(?=\s-))'
    df['ID'] = df['Project: ID'].str.extract(id_pattern, expand=False).fillna('')

    # Sanitize 'Amount' and 'Qty' columns
    df['Amount'] = df['Amount'].str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

    df['Qty'] = df['Qty'].astype(str).str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')

    # Convert 'Amount' and 'Qty' columns to numpy arrays
    amounts = df['Amount'].values
    qtys = df['Qty'].values

    # Sanitize 'Amount' and 'Qty' columns using Numba
    sanitized_amounts, sanitized_qtys = sanitize_amount_qty(amounts, qtys)
    df['Amount'] = sanitized_amounts
    df['Qty'] = sanitized_qtys

    # Convert 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    # Restrict results to 20 rows
    df = df.tail(20)

    #final_results = []
    # Further processing can be added here

    return df