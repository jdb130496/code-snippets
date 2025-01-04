import pandas as pd
import sqlite3
import openpyxl

IDS = ['34310', '34389', '30899', '33344', '34840', '13377', '31172', '30485', '34732', '34119', '33930', '31565', '34645', '30338']
# Load data into a pandas DataFrame, specifying the exact range of cells and that the first row (A6) contains headers
df = pd.read_excel('D:\\Carvart\\OneDrive - Carvart\\tr-details-jan17-nov24.xlsm', sheet_name='jan17-nov24', usecols='A:L', header=0, nrows=429908)

# Create an in-memory SQLite database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Write the DataFrame to the SQLite database
df.to_sql('a', conn, index=False, if_exists='replace')

# Define your SQL query
for ID1 in IDS:
query = """
SELECT a1."Type", a1."Project: ID", a1."Account", SUM(a1."Amount")*-1 AS "Amt"
FROM a AS a1 WHERE a1."ID" = ?
GROUP BY a1."Type", a1."Project: ID", a1."Account"
HAVING a1.Type != 'Purchase Order' AND a1.Type != 'Sales Order'
"""
cursor.execute(query, (ID1,))
result = cursor.fetchall()
column_names = [description[0] for description in cursor.description]
result_df = pd.DataFrame(result, columns=column_names)
output_file_path = 'D:\\Carvart\\OneDrive - Carvart\\projectwise_profit_summary.xlsx'
with pd.ExcelWriter(output_file_path, engine='openpyxl', mode='a') as writer:
project_code = ID1
result_df.to_excel(writer, sheet_name=project_code, index=False)

# Close the connection
conn.close()

# Display the result
print(result_df)
