import pandas as pd
import xlwings as xw
import re
@xw.func
def process_data(file_path):
    IDS = ['32075']
    # Read the CSV file into a pandas DataFrame with headers and quotes set to true
    df = pd.read_csv(file_path, header=0, quotechar='"')
    df.columns = df.columns.str.strip()
    df['Project: ID'] = df['Project: ID'].fillna('')
    # Create the 'ID' column using the regex pattern on the 'Project: ID' column
    df['ID'] = df['Project: ID'].apply(lambda x: re.search(r'^\d+(?=\s-)|^\d+_\d+(?=\s-)', x).group() if re.search(r'^\d+(?=\s-)|^\d+_\d+(?=\s-)', x) else '')
    df['Amount'] = df['Amount'].apply(lambda x: float(re.sub(r'[^\d.-]', '', x.replace('$', '').replace('(', '-').replace(')', ''))))
    df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')
    # Convert the input data (list of lists) to a pandas DataFrame, using the first row as headers
#    df = pd.DataFrame(data[1:], columns=data[0])

    final_results = []

    # Process each ID
    for ID1 in IDS:
        filtered_df = df[(df['ID'] == ID1) & (df['Type'] != 'Purchase Order') & (df['Type'] != 'Sales Order') & (df['Date'] < pd.Timestamp('2024-07-01'))]
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

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXSTR(excel_range, patterns):
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
