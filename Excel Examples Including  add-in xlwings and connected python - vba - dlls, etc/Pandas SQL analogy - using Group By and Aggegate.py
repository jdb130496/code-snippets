import pandas as pd
import openpyxl

# Define the range of columns as per Excel notation
cols = 'A:AS'

# Define the number of rows
nrows = 6525

df = pd.read_excel('D:\\dev\\nuv_dataset_sql_xlwings.xlsx', sheet_name='nuv_dataset', usecols=cols, nrows=nrows, header=0)

result = df.groupby('Industry').agg({'Industry': 'count', 'Amount(INR Cr)': 'sum'})

# Rename the index
result.index.name = 'Industry Group'

# Reset the index
result.reset_index(inplace=True)

result.columns = ['Industry', 'COUNT(Industry)', 'SUM(Amount(INR Cr))']
print(result)

