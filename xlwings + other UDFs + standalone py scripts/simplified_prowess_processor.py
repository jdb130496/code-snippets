import pandas as pd

def process_excel(file_path):
    xls = pd.ExcelFile(file_path)
    all_sheets = xls.sheet_names
    final_summary = pd.DataFrame()

    for sheet in all_sheets:
        df = pd.read_excel(file_path, sheet_name=sheet)
        df.columns = df.columns.str.strip()
        df.rename(columns={
            'Company Name': 'Company',
            'Date': 'Date',
            'Adjusted Closing Price': 'Adj_Close',
            'Market Capitalization': 'Market_Cap',
            'Total Returns': 'Total_Returns',
            '365 Days Low Price': 'Low_Price',
            '365 Days Low Price Date': 'Low_Price_Date'
        }, inplace=True)

        df['Ratio'] = df['Low_Price'] / df['Adj_Close']
        percentile_5 = df['Market_Cap'].quantile(0.05)
        filtered_df = df[df['Market_Cap'] < percentile_5]
        top_30 = filtered_df.nlargest(30, 'Ratio')
        bottom_30 = filtered_df.nsmallest(30, 'Ratio')
        combined_df = pd.concat([top_30, bottom_30])
        final_summary = pd.concat([final_summary, combined_df])

    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a') as writer:
        final_summary.to_excel(writer, sheet_name='Summary', index=False)

    print("Processing complete. Summary saved to 'Summary' sheet.")

# Define the file path
file_path = '2000-2025-new.xlsx'

# Process the Excel file
process_excel(file_path)

