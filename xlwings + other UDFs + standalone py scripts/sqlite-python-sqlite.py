import sqlite3
import openpyxl
def conv_value(value, col_is_str):
if value is None:
return "NULL"
if col_is_str:
return repr(str(value))
elif isinstance(value, bool):
return 1 if value else 0
else:
return repr(value)
# Load data from the Excel file using openpyxl
file_path = 'D:\\Carvart\\OneDrive - Carvart\\tr-details-jan17-dec24.xlsm'
sheet_name = 'jan17-nov24'
wb = openpyxl.load_workbook(file_path, read_only=True)
ws = wb[sheet_name]
# Read the data from the specified range
data = []
for row in ws.iter_rows(min_row=1, max_row=431025, min_col=1, max_col=12, values_only=True):
data.append(row)
# Extract headers and data separately
headers = data[0]
values = data[1:]
# Create an in-memory SQLite database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()
# Determine column types
types = [any(isinstance(row[j], str) for row in values) for j in range(len(headers))]
# Create table with appropriate column names and types
stmt = "CREATE TABLE a (%s)" % (
", ".join(
"'%s' %s" % (col, "STRING" if typ else "REAL")
for col, typ in zip(headers, types)
)
)
cursor.execute(stmt)
# Insert values into the table
if values:
stmt = "INSERT INTO a VALUES %s" % (
", ".join(
"(%s)" % ", ".join(
conv_value(value, typ) for value, typ in zip(row, types)
)
for row in values
)
)
stmt = stmt.replace("\\'", "''")
cursor.execute(stmt)
# Commit the transaction
conn.commit()
# Define your SQL query
IDS = ['34310', '34389', '30899', '33344', '34840', '13377', '31172', '30485', '34732', '34119', '33930', '31565', '34645', '30338']
output = []
for ID1 in IDS:
query = """
SELECT a1."Type", a1."Project: ID", a1."Account", SUM(a1."Amount")*-1 AS "Amt"
FROM a AS a1
WHERE a1."ID" = ? AND a1."Type" != 'Purchase Order' AND a1."Type" != 'Sales Order'
GROUP BY a1."Type", a1."Project: ID", a1."Account"
"""
cursor.execute(query, (ID1,))
result = cursor.fetchall()
column_names = [description[0] for description in cursor.description]
output.append((ID1, column_names, result))
# Close the connection
conn.close()
# Display the result
for res in output:
print(f"ID: {res[0]}")
print("Columns:", res[1])
print("Data:", res[2])
print()
