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
    
    # Use vectorized operations
    df['ID'] = df['Project: ID'].str.extract(r'(^\d+(?=\s-)|^\d+_\d+(?=\s-))', expand=False).fillna('')
    
    # Correctly replace and convert 'Amount' column
    df['Amount'] = df['Amount'].str.replace('$', '').str.replace('(', '-').str.replace(')', '').str.replace(',', '')
    df['Amount'] = pd.to_numeric(df['Amount'].str.replace(r'[^\d.-]', ''), errors='coerce')
    
    df['Qty'] = pd.to_numeric(df['Qty'].astype(str).str.replace('$', '').str.replace('(', '-').str.replace(')', '').str.replace(',', '').str.replace(r'[^\d.-]', ''), errors='coerce')
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    
    # Filter the DataFrame before the loop
    df = df.loc[(df['Type'] != 'Purchase Order') & (df['Type'] != 'Sales Order') & (df['Date'] < pd.Timestamp('2024-07-01'))]
    
    final_results = []

    # Process each ID
    for ID1 in IDS:
        filtered_df = df.loc[df['ID'] == ID1]
        grouped_df = filtered_df.groupby(['Type', 'Project: ID', 'Account']).agg({'Amount': 'sum'}).reset_index()
        # Reverse the sign of the aggregated 'Amount' column
        grouped_df['Amount'] = grouped_df['Amount'] * -1
        grouped_df = grouped_df.rename(columns={'Amount': 'Amt'})
        final_results.append(grouped_df)

    # Combine all results into a single DataFrame
    combined_results = pd.concat(final_results, ignore_index=True)

    # Sort the combined results by 'Project: ID' in ascending order
    combined_results = combined_results.sort_values(by=['Project: ID', 'Amt'])

    # Add headers to the output data
    output_data = [combined_results.columns.tolist()] + combined_results.values.tolist()

    # Return the combined results with headers as a dynamic array
    return output_data

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
                match = re.search(pattern, cell_str,flags=re.UNICODE)
                if match:
                    cell_result.append(match.group())  # Return the matched string
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("")
        result.append(row_result)
    return result
