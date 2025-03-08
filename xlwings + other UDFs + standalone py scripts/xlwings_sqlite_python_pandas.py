import pandas as pd
import xlwings as xw
import re
import numpy as np
import pcre2

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
import warnings

def convert_datetime_columns(df, datetime_columns):
    for col in datetime_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce').dt.floor('us')
    return df

import pandas as pd
import xlwings as xw

@xw.func
def Project_SO_Inv_Summary(data):
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    df = convert_datetime_columns(df, ['Date'])  # Add your datetime columns here
    df_filtered = df[(df['Type'] == 'Invoice')]
    df_grouped = df_filtered.groupby(['ProjectSOPO', 'SO Amount'], dropna=False).agg({
        'Amount (Gross)': 'sum',
        'Date': 'max'
    }).reset_index()
    df_grouped.columns = ['ProjectSOPO', 'SO Amount', 'Invoice Amt', 'Last_Inv_Date']
    df_grouped['Last_Inv_Date'] = pd.to_datetime(df_grouped['Last_Inv_Date'])
    result = [df_grouped.columns.tolist()] + df_grouped.values.tolist()
    return result

@xw.func
def Customer_Invoice_Summary(data):
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    df = convert_datetime_columns(df, ['Date'])  # Add your datetime columns here
    df['ProjectSOPO'] = df['ProjectSOPO'].ffill()
    df_invoice = df[df['Type'] == 'Invoice'].groupby(['Customer', 'ProjectSOPO'], dropna=False).agg({
        'Amount (Gross)': 'sum',
        'Date': 'max'
    }).reset_index()
    df_invoice.columns = ['Customer', 'ProjectSOPO', 'Invoice Amt', 'Last_Inv_Date']
    df_received = df[df['Type'] != 'Invoice'].groupby(['Customer', 'ProjectSOPO'], dropna=False).agg({
        'Amount (Gross)': lambda x: -x.sum(),
        'Date': 'max'
    }).reset_index()
    df_received.columns = ['Customer', 'ProjectSOPO', 'Received Amt', 'Last_Rec_Date']
    df_summary = pd.merge(df_invoice, df_received, on=['Customer', 'ProjectSOPO'], how='outer')
    result = [df_summary.columns.tolist()] + df_summary.values.tolist()
    return result

@xw.func
def Project_Invoice_Summary(data):
    df = pd.DataFrame(data[1:], columns=data[0]).replace('', pd.NA)
    df = convert_datetime_columns(df, ['Last_Inv_Date', 'Last_Rec_Date'])  # Add your datetime columns here
    df = df.assign(
        **{
            'Invoice Amt': df['Invoice Amt'].astype(float),
            'Received Amt': df['Received Amt'].astype(float),
            'Last_Inv_Date': pd.to_datetime(df['Last_Inv_Date']),
            'Last_Rec_Date': pd.to_datetime(df['Last_Rec_Date'])
        }
    )
    df_grouped = df.groupby(['ProjectSOPO'], dropna=False).agg({
        'Invoice Amt': 'sum',
        'Received Amt': 'sum',
        'Last_Inv_Date': 'max',
        'Last_Rec_Date': 'max'
    }).reset_index()
    df_grouped = df_grouped[(df_grouped['Last_Rec_Date'] >= pd.to_datetime('2025-01-01')) & (df_grouped['Last_Rec_Date'] <= pd.to_datetime('2025-01-31'))]
    df_grouped['Difference'] = df_grouped['Invoice Amt'] - df_grouped['Received Amt']
    df_grouped = df_grouped[['ProjectSOPO', 'Invoice Amt', 'Received Amt', 'Difference', 'Last_Inv_Date', 'Last_Rec_Date']]
    df_grouped.columns = ['ProjectSOPO', 'INV_AMT', 'RCT_AMT', 'Difference', 'Last_Inv_Date', 'Last_Rct_Date']
    result = [df_grouped.columns.tolist()] + df_grouped.values.tolist()
    return result
import xlwings as xw
from datetime import datetime

@xw.func
@xw.arg('data_range', xw.Range)
@xw.arg('start_date', (str, datetime), default='2024-01-01')
@xw.arg('end_date', (str, datetime), default='2024-12-31')
def get_project_class(data_range, start_date='2024-01-01', end_date='2024-12-31'):
    """
    UDF to process data similar to the SQL query without using pandas
    Args:
        data_range: Input range containing the data (must include Type, ProjectSOPO, Date, and Class: Name columns)
        start_date: Start date for filtering (default: '2024-01-01')
        end_date: End date for filtering (default: '2024-12-31')
    Returns:
        List of lists with ProjectSOPO and Class: Name columns
    """
    try:
        # Convert the data range to a list of lists
        data = data_range.value

        # Extract headers and data rows
        headers = data[0]
        rows = data[1:]

        # Get column indices
        type_idx = headers.index('Type')
        project_sopo_idx = headers.index('ProjectSOPO')
        date_idx = headers.index('Date')
        class_name_idx = headers.index('Class: Name')

        # Convert start and end dates to datetime objects if they are strings
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        # Initialize a dictionary to store the results
        result_dict = {}

        # Iterate over the rows to filter and group data
        for row in rows:
            row_type = row[type_idx]
            row_project_sopo = row[project_sopo_idx] if row[project_sopo_idx] else 'Unknown'
            row_date = row[date_idx]
            if isinstance(row_date, str):
                row_date = datetime.strptime(row_date, '%Y-%m-%d')
            row_class_name = row[class_name_idx]

            if (row_type == 'Invoice' and
                start_date <= row_date <= end_date and
                row_class_name != 'Carvart'):
                
                key = (row_project_sopo, row_class_name)
                if key not in result_dict:
                    result_dict[key] = 1

        # Convert the result dictionary to a list of lists
        result = [[key[0], key[1]] for key in result_dict.keys()]

        # Sort the result by ProjectSOPO
        result.sort(key=lambda x: x[0])

        # Add column headers
        result.insert(0, ['ProjectSOPO', 'Class: Name'])

        return result

    except Exception as e:
        return f"Error: {str(e)}"

import xlwings as xw
from pathlib import Path

@xw.func
def SO_with_commissions(file_path):
    """
    Iterates through all worksheets in the specified Excel file,
    extracts values from column D (rows 1-10) and combines them into a single list.
    """
    try:
        # Create Path object and verify file exists
        path = Path(file_path)
        if not path.exists():
            return [["File not found"]]
            
        combined_values = []
        
        # Create new App instance and open workbook
        app = xw.App(visible=False)
        wb = app.books.open(str(path))
        
        try:
            # Iterate through sheets
            combined_values = [
                v for i in range(1, len(wb.sheets))
                for v in wb.sheets[i].range('C1:C10').value
                if v is not None and v != 'SO#'
            ]   
        finally:
            # Clean up
            wb.close()
            app.quit()
            
        # Return results as vertical array
        if combined_values:
            return [[v] for v in combined_values]
        return [["No values found"]]
        
    except Exception as e:
        return [[f"Error: {str(e)}"]]

@xw.func
def Projects_with_commissions(file_path):
    """
    Iterates through all worksheets in the specified Excel file,
    extracts values from column D (rows 1-10) and combines them into a single list.
    """
    try:
        # Create Path object and verify file exists
        path = Path(file_path)
        if not path.exists():
            return [["File not found"]]
            
        combined_values = []
        
        # Create new App instance and open workbook
        app = xw.App(visible=False)
        wb = app.books.open(str(path))
        
        try:
            # Iterate through sheets
            combined_values = [
                v for i in range(1, len(wb.sheets))
                for v in wb.sheets[i].range('D1:D10').value
                if v is not None and v != 'Project #'
            ]   
        finally:
            # Clean up
            wb.close()
            app.quit()
            
        # Return results as vertical array
        if combined_values:
            return [[v] for v in combined_values]
        return [["No values found"]]
        
    except Exception as e:
        return [[f"Error: {str(e)}"]]


@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXSTRPERL(excel_range, patterns):
    def process_cell(cell, patterns):
        cell_str = str(cell)
        lines = cell_str.splitlines()
        maxlen = len(lines)
        if maxlen == 0:
            return ""
        cell_result = lines[maxlen - 1].strip() if maxlen > 0 else ""
        for pattern in patterns:
            match = pcre2.search(pattern, cell_str, flags=pcre2.UNICODE | pcre2.DOTALL)
            if match:
                return match.group(1).strip() if match.groups() else match.group().strip()
        return ""
        
    return [[process_cell(cell, patterns) for cell in row] for row in excel_range]


@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
@xw.arg('replacement', ndim=0)
def REGEXREPLMPERL(excel_range, patterns, replacement):
    def process_cell(cell, patterns, replacement):
        cell_str = str(cell)
        for pattern in patterns:
            cell_str = pcre2.sub(pattern, replacement, cell_str)
        return cell_str.strip()

    return [[process_cell(cell, patterns, replacement) for cell in row] for row in excel_range]

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
@xw.arg('group_index', default=0)
@xw.arg('is_date_pattern', default=True)
def REGEXGRPPERL(excel_range, patterns, group_index=0, is_date_pattern=True):
    def process_cell(cell, patterns, group_index):
        cell_str = str(cell)
        if not cell_str:
            return ""
        
        # Process each pattern
        for pattern in patterns:
            try:
                match = pcre2.search(pattern, cell_str, flags=pcre2.UNICODE | pcre2.DOTALL)
                if match:
                    #print(f"cell_str: {cell_str}")
                    #print(f"pattern: {pattern}")
                    #print(f"match: {match}")
                    # Get the matched text
                    matched_text = match.group(group_index) if group_index != 0 else match.group()
                    if is_date_pattern:
                        # Clean up the matched text
                        if ('/' in matched_text and '-' in matched_text):
                            # If both separators exist, keep only up to the last separator
                            last_slash = matched_text.rfind('/')
                            last_hyphen = matched_text.rfind('-')
                            last_separator = max(last_slash, last_hyphen)
                            if last_separator > 0:
                                # Keep only the part before the last separator
                                matched_text = matched_text[:last_separator]
                    
                    return matched_text.strip()
            except Exception as e:
                return f"Error: {str(e)}"
        
        # No match found
        return ""
        
    return [[process_cell(cell, patterns, group_index) for cell in row] for row in excel_range]

import pcre2
import xlwings as xw

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
@xw.arg('group_index', default=0)
@xw.arg('is_date_pattern', default=True)
@xw.arg('replacement', default=None)
def REGEXGRPREPLPERL(excel_range, patterns, group_index=0, is_date_pattern=True, replacement=None):
    def process_cell(cell, patterns, group_index, is_date_pattern, replacement):
        cell_str = str(cell) if cell is not None else ""
        if not cell_str:
            return ""
        
        # Process each pattern
        for pattern in patterns:
            try:
                match = pcre2.search(pattern, cell_str, flags=pcre2.UNICODE | pcre2.DOTALL)
                if match:
                    # Get the matched text
                    matched_text = match.group(group_index) if group_index != 0 else match.group()
                    
                    if is_date_pattern:
                        # Clean up the matched text
                        if '/' in matched_text and '-' in matched_text:
                            # If both separators exist, keep only up to the last separator
                            last_slash = matched_text.rfind('/')
                            last_hyphen = matched_text.rfind('-')
                            last_separator = max(last_slash, last_hyphen)
                            if last_separator > 0:
                                # Keep only the part before the last separator
                                matched_text = matched_text[:last_separator]
                    
                    # If a replacement string is provided, replace the matched text
                    if replacement is not None:
                        return cell_str.replace(matched_text, replacement).strip()
                    
                    return matched_text.strip()
            except Exception as e:
                return f"Error: {str(e)}"
        
        # No match found, return the original cell content
        return cell_str
        
    return [[process_cell(cell, patterns, group_index, is_date_pattern, replacement) for cell in row] for row in excel_range]

# Grok AI (3.0) Chat Session
import xlwings as xw
import pcre2

@xw.func
def perform_substitution_array(range_input, pattern, replacement, group_to_replace=None):
    """
    Performs pcre2 regex substitution on a single-column range and returns an array.
    Args:
        range_input: Single-column Excel range (e.g., G7:G10) as a 1D list
        pattern: Regular expression pattern (string from M5)
        replacement: String to replace the matched pattern or group (e.g., "00")
        group_to_replace: Optional integer specifying which group to replace (default None)
    Returns:
        A 1D list with substituted values for single-column output
    """
    try:
        regex = pcre2.compile(pattern.encode('utf-8'))
        # Treat range_input as a 1D list directly
        input_texts = [str(text) if text is not None else "" for text in range_input]

        result_array = []
        for text in input_texts:
            if group_to_replace is not None and group_to_replace != 0:
                group_to_replace = int(group_to_replace)
                def replacement_builder(match):
                    groups = [match[i].decode('utf-8') if match[i] is not None else ''
                              for i in range(match.group_count() + 1)]
                    if group_to_replace < len(groups):
                        groups[group_to_replace] = replacement
                    return ''.join(groups[0:1] + [f"{groups[i]}" for i in range(1, len(groups))])
                result = regex.sub(lambda m: replacement_builder(m).encode('utf-8'),
                                 text.encode('utf-8')).decode('utf-8')
            else:
                result = regex.sub(replacement.encode('utf-8'),
                                 text.encode('utf-8')).decode('utf-8')
            result_array.append(result)  # Append as single value, not list
        # Convert horizontal 1D list to vertical 2D list using list comprehension
        return [[result] for result in result_array]
    except Exception as e:
        return [f"Error: {str(e)}"]  # Return 1D list with error

# Test locally
if __name__ == "__main__":
    test_input = ["PO 27007 - FRB 30325 - Shipped Glasmrte PO 26561", "", "Dec electric - 12/03/24- 01/03-25", ""]
    test_pattern = r"(?<!\d)(?:0?[1-9]|1[0-2])(?:\/|\-)(?:0?[1-9]|[12]\d|3[01])(?:(?:\/|\-)\d{2,4})?(?!\d)"
    test_replacement = "00"
    test_group = 0
    result = perform_substitution_array(test_input, test_pattern, test_replacement, test_group)
    print("Test result:")
    print(result)

@xw.func
def process_pandas_full_data(file_path):
    # Define column dtypes for efficient reading
    dtype_dict = {
        'Project': str,
        'Class: Name': str,
        'Type': str,
        'Document Number': str,
        'Name': str,
        'Memo': str,
        'Account': str,
        'Clr': str,
        'Split': str,
        'Qty': str,
        'Amount': str
    }

    # Read the CSV
    df = pd.read_csv(file_path, header=0, quotechar='"', dtype=dtype_dict)
    
    # Clean column names
    df.columns = df.columns.str.strip()

    #Sanitise Memo
    if 'Memo' in df.columns:
        df['Memo'] = df['Memo'].str.replace(r'\\', ' ', regex=True)
    
    # Convert Date column to datetime and then to Excel date number
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
        # Convert to Excel date number (number of days since 1900-01-01)
        df['Date'] = (df['Date'] - pd.Timestamp('1899-12-30')).dt.days
    
    # Clean numeric columns (Qty and Amount)
    numeric_cols = ['Qty', 'Amount']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = (df[col].astype(str)
                      .replace({
                          r',': '',
                          r'\$': '',
                          r'\(': '-',
                          r'\)': '',
                          r'[^\d.-]': ''
                      }, regex=True)
                      .pipe(pd.to_numeric, errors='coerce')
                      .astype(float))
    
    # Convert to output format
    output_data = [df.columns.tolist()] + df.values.tolist()
    
    return output_data

@xw.func
def process_pyarrow_chunks(file_path):
    import pyarrow as pa
    import pyarrow.csv as csv
    import pyarrow.compute as pc
    import pandas as pd
    import numpy as np
    
    try:
        # Define read options for PyArrow
        read_options = csv.ReadOptions(
            block_size=10 * 1024 * 1024,
            use_threads=True
        )
        
        parse_options = csv.ParseOptions(
            delimiter=',',
            quote_char='"'
        )
        
        convert_options = csv.ConvertOptions(
            strings_can_be_null=True,
            include_columns=None
        )
        
        batches = []
        batch_count = 0
        
        with csv.open_csv(
            file_path,
            read_options=read_options,
            parse_options=parse_options,
            convert_options=convert_options
        ) as reader:
            for batch in reader:
                batch_count += 1
                df = batch.to_pandas()
                
                # Clean column names - remove extra spaces
                df.columns = df.columns.str.strip()
                
                # Process Memo (appears to be all None in sample)
                if 'Memo' in df.columns:
                    df['Memo'] = df['Memo'].fillna('').astype(str)
                    df.loc[df['Memo'] == 'None', 'Memo'] = ''
                    df['Memo'] = (df['Memo']
                                 .str.replace('\\', ' ', regex=False)
                                 .str.replace(r'\s+', ' ', regex=True)
                                 .str.strip())
                
                # Process Date (format: M/D/YYYY)
                if 'Date' in df.columns:
                    try:
                        df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y', errors='coerce')
                        df['Date'] = (df['Date'] - pd.Timestamp('1899-12-30')).dt.days
                    except Exception as e:
                        print(f"Date conversion error: {e}")
                
                # Process Amount (format: $0.00)
                if 'Amount' in df.columns:
                    df['Amount'] = (df['Amount']
                                  .fillna('$0.00')
                                  .astype(str)
                                  .str.replace('$', '', regex=False)
                                  .str.replace(',', '', regex=False)
                                  .str.replace('(', '-', regex=False)
                                  .str.replace(')', '', regex=False)
                                  .str.strip())
                    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
                
                # Process Qty (already numeric but as string)
                if 'Qty' in df.columns:
                    df['Qty'] = pd.to_numeric(df['Qty'], errors='coerce')
                
                # Handle None values in other columns
                for col in df.columns:
                    if col not in ['Date', 'Amount', 'Qty']:
                        df[col] = df[col].fillna('').astype(str)
                        df.loc[df[col] == 'None', col] = ''
                
                # Convert back to PyArrow and append
                processed_batch = pa.Table.from_pandas(df)
                batches.append(processed_batch)
        
        if batches:
            result_table = pa.concat_tables(batches)
            result_df = result_table.to_pandas()
            
            # Debug: Print sample of processed data
            print("\nProcessed data sample:")
            print(result_df.head())
            print("\nColumn dtypes:")
            print(result_df.dtypes)
            
            return [result_df.columns.tolist()] + result_df.values.tolist()
        return [["No data found"]]
        
    except Exception as e:
        print(f"Error in processing: {e}")
        return [["Error: " + str(e)]]

@xw.func
def process_pyarrow_chunks_new(file_path):
    import pyarrow as pa
    import pyarrow.csv as csv
    import pyarrow.compute as pc
    import pandas as pd
    import numpy as np
    
    # Define read options for PyArrow
    read_options = csv.ReadOptions(
        block_size=10 * 1024 * 1024,  # 10MB chunks
        use_threads=True
    )
    
    parse_options = csv.ParseOptions(
        delimiter=',',
        quote_char='"'
    )
    
    convert_options = csv.ConvertOptions(
        strings_can_be_null=True,
        include_columns=None  # Read all columns
    )
    
    # Read the CSV file in batches
    batches = []
    batch_size = 500000  # Process in large batches
    batch_count = 0
    
    # Create a reader for the CSV file
    with csv.open_csv(
        file_path,
        read_options=read_options,
        parse_options=parse_options,
        convert_options=convert_options
    ) as reader:
        schema = reader.schema
        
        # Clean column names (remove trailing spaces)
        cleaned_names = {name.strip(): name for name in schema.names}
        
        # Get column indices using cleaned names
        memo_idx = schema.get_field_index(cleaned_names.get('Memo')) if 'Memo' in cleaned_names else -1
        date_idx = schema.get_field_index(cleaned_names.get('Date')) if 'Date' in cleaned_names else -1
        qty_idx = schema.get_field_index(cleaned_names.get('Qty')) if 'Qty' in cleaned_names else -1
        amount_idx = schema.get_field_index(cleaned_names.get('Amount')) if 'Amount' in cleaned_names else -1
        
        # Process each batch
        for batch in reader:
            batch_count += 1
            print(f"Processing batch {batch_count}")
            
            # Convert to dictionary for column-wise processing
            batch_dict = batch.to_pydict()
            
            # Process Memo column
            if memo_idx >= 0:
                original_memo_name = cleaned_names.get('Memo')
                memo_array = batch.column(memo_idx)
                if memo_array.null_count < len(memo_array):
                    if not pa.types.is_string(memo_array.type):
                        memo_array = pc.cast(memo_array, pa.string())
                    memo_array = pc.replace_substring_regex(memo_array, r'\\', ' ')
                    batch_dict[original_memo_name] = memo_array.to_pylist()
            
            # Process Date column
            if date_idx >= 0:
                original_date_name = cleaned_names.get('Date')
                date_array = batch.column(date_idx)
                dates = pd.Series(date_array.to_pandas())
                dates = pd.to_datetime(dates, errors='coerce')
                excel_dates = (dates - pd.Timestamp('1899-12-30')).dt.days
                batch_dict[original_date_name] = excel_dates.tolist()
            
            # Process numeric columns
            for col_name, col_idx in [('Qty', qty_idx), ('Amount', amount_idx)]:
                if col_idx >= 0:
                    original_col_name = cleaned_names.get(col_name)
                    col_array = batch.column(col_idx)
                    
                    if not pa.types.is_string(col_array.type):
                        col_array = pc.cast(col_array, pa.string())
                    
                    col_array = pc.replace_substring_regex(col_array, r',', '')
                    col_array = pc.replace_substring_regex(col_array, r'\$', '')
                    col_array = pc.replace_substring_regex(col_array, r'\(', '-')
                    col_array = pc.replace_substring_regex(col_array, r'\)', '')
                    
                    numeric_values = pd.to_numeric(
                        pd.Series(col_array.to_pandas()), 
                        errors='coerce'
                    )
                    
                    batch_dict[original_col_name] = numeric_values.tolist()
            
            # Create a new table from the processed dictionary
            processed_batch = pa.Table.from_pydict(batch_dict)
            batches.append(processed_batch)
            
            # Free memory
            del batch
            del batch_dict
    
    # Combine all batches
    if batches:
        result_table = pa.concat_tables(batches)
        
        # Convert to pandas for output
        result_df = result_table.to_pandas()
        
        # Convert to output format
        output_data = [result_df.columns.tolist()] + result_df.values.tolist()
        
        return output_data
    else:
        return [["No data found"]]

