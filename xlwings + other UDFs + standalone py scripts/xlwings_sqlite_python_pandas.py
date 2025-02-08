import pandas as pd
import xlwings as xw
import re
import numpy as np

@xw.func
def process_pandas(file_path):
    IDS = [32018, 30284, 30355, 31991, 32229, 32162, 32029, 29681, 30234, 28354, 31331, 32179, 29515, 30759, 31313, 30362, 29072, 29708, 30457, 30338, 29026, 30026, 27356, 29213, 28697, 13306, 12152]
    IDS = list(map(str,IDS))
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
        filtered_df = df[(df['ID'] == ID1) & (df['Type'] != 'Purchase Order') & (df['Type'] != 'Sales Order') & (~df['Account'].str.contains(r'(?i)advances', na=False)) & (~df['Account'].str.contains(r'(?i)payable', na=False))] #& (df['Date'] < pd.Timestamp('2024-07-01'))]
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

#import pandas as pd
#import xlwings as xw
#import numpy as np
#from numba import jit

#@jit(nopython=True)
#def sanitize_amount_qty(amounts, qtys):
#    sanitized_amounts = np.empty(len(amounts), dtype=np.float64)
#    sanitized_qtys = np.empty(len(qtys), dtype=np.float64)
    
#    for i in range(len(amounts)):
#        sanitized_amounts[i] = amounts[i]
#        sanitized_qtys[i] = qtys[i]
    
#    return sanitized_amounts, sanitized_qtys

#@xw.func
#def process_pandas_numba(file_path):
#    IDS = ['32075']
#    # Read the CSV file into a pandas DataFrame with headers and quotes set to true
#    df = pd.read_csv(file_path, header=0, quotechar='"')
#    df.columns = df.columns.str.strip()
#    df['Project: ID'] = df['Project: ID'].fillna('')

    # Create the 'ID' column using vectorized regex operations
#    id_pattern = r'(^\d+(?=\s-)|^\d+_\d+(?=\s-))'
#    df['ID'] = df['Project: ID'].str.extract(id_pattern, expand=False).fillna('')

    # Sanitize 'Amount' and 'Qty' columns
#    df['Amount'] = df['Amount'].str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
#    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')

#    df['Qty'] = df['Qty'].astype(str).str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
#    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')

    # Convert 'Amount' and 'Qty' columns to numpy arrays
#    amounts = df['Amount'].values
#    qtys = df['Qty'].values

    # Sanitize 'Amount' and 'Qty' columns using Numba
#    sanitized_amounts, sanitized_qtys = sanitize_amount_qty(amounts, qtys)
#    df['Amount'] = sanitized_amounts
#    df['Qty'] = sanitized_qtys

    # Convert 'Date' column to datetime
#    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

#    final_results = []

    # Process each ID
#    for ID1 in IDS:
#        filtered_df = df[(df['ID'] == ID1) & (df['Type'] != 'Purchase Order') & (df['Type'] != 'Sales Order')] #& (df['Date'] < pd.Timestamp('2024-07-01'))]
#        grouped_df = filtered_df.groupby(['Type', 'Project: ID', 'Account']).agg({'Amount': 'sum'}).reset_index()
#        grouped_df['Amt'] = -grouped_df['Amount'].where(grouped_df['Amount'] > 0, grouped_df['Amount'])
#        grouped_df.drop(columns=['Amount'], inplace=True)
#        final_results.append(grouped_df)

    # Combine all results into a single DataFrame
#    combined_results = pd.concat(final_results, ignore_index=True)

    # Sort the combined results by 'Project: ID' in ascending order
#    combined_results.sort_values(by=['Project: ID', 'Amt'], inplace=True)

    # Add headers to the output data
#    output_data = [combined_results.columns.tolist()] + combined_results.values.tolist()

    # Return the combined results with headers as a dynamic array
#    return output_data
#    return df

@xw.func
def Project_Billings(file_path):
#    IDS = [32018, 30284, 30355, 31991, 32229, 32162, 32029, 29681, 30234, 28354, 31331, 32179, 29515, 30759, 31313, 30362, 29072, 29708, 30457, 30338, 29026, 30026, 27356, 29213, 28697, 13306, 12152]
#    IDS = list(map(str,IDS))
    # Read the CSV file into a pandas DataFrame with headers and quotes set to true
    df = pd.read_csv(file_path, header=0, quotechar='"')
    df.columns = df.columns.str.strip()
    df['ProjectSOPO'] = df['ProjectSOPO'].fillna('')

    # Create the 'ID' column using vectorized regex operations
    id_pattern = r'(^\d+(?=\s-)|^\d+_\d+(?=\s-))'
    df['ID'] = df['ProjectSOPO'].str.extract(id_pattern, expand=False).fillna('')

    # Sanitize 'Amount' and 'Qty' columns
    df[['Amount', 'Amount Due']] = df[['Amount', 'Amount Due']].replace({r',': '', r'\$': '', r'\(': '-', r'\)': ''}, regex=True)
    df[['Amount', 'Amount Due']] = pd.to_numeric(df[['Amount', 'Amount Due']].stack(), errors='coerce').unstack()
    
#    df['Qty'] = df['Qty'].astype(str).str.replace(r',', '', regex=True).str.replace(r'\$', '', regex=True).str.replace(r'\(', '-', regex=True).str.replace(r'\)', '', regex=True)
#    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')

    # Convert 'Date' column to datetime
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    final_results = []

    # Process each ID
#    for ID1 in IDS:
    filtered_df = df[df['Date Due'] != 'Paid']
    filtered_df = df[df['Date Due'] != 'Paid'].copy()  # Add .copy() to avoid SettingWithCopyWarning
    filtered_df.loc[:, 'Date Due'] = pd.to_datetime(filtered_df['Date Due'], format='%m/%d/%Y')
    #filtered_df['Date Due'] = pd.to_datetime(filtered_df['Date Due'], format='%m/%d/%Y')
    grouped_df = filtered_df.groupby(['ProjectSOPO', 'Account', 'Type', 'Document Number', 'Date', 'Date Due', 'Amount Due']).agg({'Amount': 'sum'}).reset_index()
    #grouped_df['Amt'] = grouped_df['Amount'].where(grouped_df['Amount'] > 0, grouped_df['Amount'])
    grouped_df['Amt'] = grouped_df['Amount']
    grouped_df.drop(columns=['Amount'], inplace=True)
    grouped_df = grouped_df[grouped_df['ProjectSOPO'].str.strip().astype(bool)]
    final_results.append(grouped_df)

    # Combine all results into a single DataFrame
    combined_results = pd.concat(final_results, ignore_index=True)

    # Sort the combined results by 'Project: ID' in ascending order
    combined_results.sort_values(by=['ProjectSOPO', 'Type', 'Document Number', 'Date', 'Amt'], inplace=True)
    combined_results = combined_results[combined_results['Amount Due'] != 0]
    combined_results = combined_results[['ProjectSOPO', 'Account', 'Type', 'Document Number', 'Date', 'Date Due', 'Amt', 'Amount Due']]


    # Add headers to the output data
    output_data = [combined_results.columns.tolist()] + combined_results.values.tolist()

    # Return the combined results with headers as a dynamic array
    return output_data
import regex as re1
import xlwings as xw

@xw.func
@xw.arg('excel_range', ndim=2)  # Expecting a 2D Excel range
@xw.arg('patterns', ndim=1)    # Expecting a 1D list of patterns
def REGEXSTR2(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert the cell content to string
            cell_result = []
            for pattern in patterns:
                try:
                    # Use regex module for variable-length lookbehind
                    match = re1.search(pattern, cell_str, flags=re.UNICODE)
                    if match:
                        cell_result.append(match.group(2))  # Add the matched string
                except re.error as e:
                    # Handle invalid regex pattern errors
                    return f"Regex Error: {e}"
            # Join matches only if all patterns are matched, otherwise return empty
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("")
        result.append(row_result)
    return result

import pandas as pd
import xlwings as xw

@xw.func
def fill_project_and_so_amount(data):
    # Convert the input data to a pandas DataFrame, treating empty cells as NaN
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    
    # Fill the missing 'ProjectSOPO' values with the previous non-missing value
    df['ProjectSOPO'] = df['ProjectSOPO'].ffill()
    
    # Fill the 'SO Amount' values only if the project name is the same as the row above and 'SO Amount' is missing
    mask = (df['ProjectSOPO'] == df['ProjectSOPO'].shift(1)) & (df['SO Amount'].isna())
    df.loc[mask, 'SO Amount'] = df['SO Amount'].shift(1)
    
    # Include headers in the output
    result = [data[0]] + df.values.tolist()
    
    return result

import pandas as pd
import xlwings as xw

@xw.func
def Project_SO_Inv_Summary(data):
    # Convert the input data to a pandas DataFrame, treating empty cells as NaN
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    
    # Filter the DataFrame for rows where Type is 'Invoice'
    df_filtered = df[(df['Type'] == 'Invoice')]
    
    # Group by 'ProjectSOPO' and 'SO Amount', and calculate the sum of 'Amount' and max of 'Date'
    df_grouped = df_filtered.groupby(['ProjectSOPO', 'SO Amount'], dropna=False).agg({
        'Amount (Gross)': 'sum',
        'Date': 'max'
    }).reset_index()
    
    # Rename the columns
    df_grouped.columns = ['ProjectSOPO', 'SO Amount', 'Invoice Amt', 'Last_Inv_Date']
    
    # Format the 'Last_Inv_Date' column as '%m/%d/%Y'
    df_grouped['Last_Inv_Date'] = pd.to_datetime(df_grouped['Last_Inv_Date'])
    
    # Include headers in the output
    result = [df_grouped.columns.tolist()] + df_grouped.values.tolist()
    
    return result

import pandas as pd
import xlwings as xw

@xw.func
def Customer_Invoice_Summary(data):
    # Convert the input data to a pandas DataFrame, treating empty cells as NaN
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    
    # Fill the missing 'ProjectSOPO' values with the previous non-missing value
    df['ProjectSOPO'] = df['ProjectSOPO'].ffill()
    
    # Filter the DataFrame for rows where Type is 'Invoice' and calculate the sum of 'Amount' and max of 'Date'
    df_invoice = df[df['Type'] == 'Invoice'].groupby(['Customer', 'ProjectSOPO'], dropna=False).agg({
        'Amount (Gross)': 'sum',
        'Date': 'max'
    }).reset_index()
    
    # Rename the columns for invoice summary
    df_invoice.columns = ['Customer', 'ProjectSOPO', 'Invoice Amt', 'Last_Inv_Date']
    
    # Filter the DataFrame for rows where Type is not 'Invoice' and calculate the sum of 'Amount' and max of 'Date'
    df_received = df[df['Type'] != 'Invoice'].groupby(['Customer', 'ProjectSOPO'], dropna=False).agg({
        'Amount (Gross)': lambda x: -x.sum(),
        'Date': 'max'
    }).reset_index()
    
    # Rename the columns for received summary
    df_received.columns = ['Customer', 'ProjectSOPO', 'Received Amt', 'Last_Rec_Date']
    
    # Merge the invoice and received summaries on 'ProjectSOPO'
    df_summary = pd.merge(df_invoice, df_received, on=['Customer', 'ProjectSOPO'], how='outer')
    
    # Include headers in the output
    result = [df_summary.columns.tolist()] + df_summary.values.tolist()
    
    return result

import pandas as pd
import xlwings as xw

@xw.func
def Project_Invoice_Summary(data):
    # Convert the input data to a pandas DataFrame, treating empty cells as NaN
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    
    # Ensure 'Invoice Amt' and 'Received Amt' are floats and 'Last_Rec_Date' is datetime
    df = df.assign(
        **{
            'Invoice Amt': df['Invoice Amt'].astype(float),
            'Received Amt': df['Received Amt'].astype(float),
            'Last_Inv_Date': pd.to_datetime(df['Last_Inv_Date']),
            'Last_Rec_Date': pd.to_datetime(df['Last_Rec_Date'])
        }
    )
    
    # Group by 'ProjectSOPO', and calculate the sum of 'Invoice Amt', sum of 'Received Amt', difference, and max of 'Last_Rec_Date'
    df_grouped = df.groupby(['ProjectSOPO'], dropna=False).agg({
        'Invoice Amt': 'sum',
        'Received Amt': 'sum',
        'Last_Inv_Date': 'max',
        'Last_Rec_Date': 'max'
    }).reset_index()
    
    # Filter the DataFrame for dates between 01/01/2025 and 01/31/2025
    #start_date = pd.to_datetime('2025-01-01')
    #end_date = pd.to_datetime('2025-01-31')
    df_grouped = df_grouped[(df_grouped['Last_Rec_Date'] >= pd.to_datetime('2025-01-01')) & (df_grouped['Last_Rec_Date'] <= pd.to_datetime('2025-01-31'))]
    # Calculate the difference
    df_grouped['Difference'] = df_grouped['Invoice Amt'] - df_grouped['Received Amt']
    
    # Rename the columns
    df_grouped = df_grouped[['ProjectSOPO', 'Invoice Amt', 'Received Amt', 'Difference', 'Last_Inv_Date', 'Last_Rec_Date']]
    df_grouped.columns = ['ProjectSOPO', 'INV_AMT', 'RCT_AMT', 'Difference', 'Last_Inv_Date', 'Last_Rct_Date']
    
    # Include headers in the output
    result = [df_grouped.columns.tolist()] + df_grouped.values.tolist()
    
    return result




