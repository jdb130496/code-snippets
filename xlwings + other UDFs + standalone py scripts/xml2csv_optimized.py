import xml.etree.ElementTree as ET
import re
import csv

# Parse the XML file
xml_file = "01 January 2025- RG Glass-Regular Account-decrypted.xml"
tree = ET.parse(xml_file)
root = tree.getroot()

# Initialize variables to store the data
rows = []
date_pattern = r'^\d{2}/\d{2}$'
amount_pattern = r'^-?\$?\d{1,3}(,\d{3})*(\.\d{2})$'
total_pattern = r'^Total (Deposits and Additions|Electronic Withdrawals|Other Withdrawals)'

# Find all 'Table' elements in the XML
for table in root.findall('.//Table'):
    # Find all 'TR' elements within each 'Table'
    for row in table.findall('.//TR'):
        row_data = []
        for cell in row:
            if cell.text and cell.text.strip():
                row_data.append(cell.text.strip())
        if row_data:
            rows.append(row_data)

# Initialize lists to store the final columns
dates = []
descriptions = []
amounts = []

# Iterate over the rows to capture dates, descriptions, and amounts
current_date = ""
current_description = []
current_amount = ""
last_amount = ""

for row in rows:
    for cell in row:
        if re.match(date_pattern, cell):  # Date pattern
            if current_date:
                dates.append(current_date)
                descriptions.append(" ".join(current_description))
                amounts.append(last_amount)
            current_date = cell
            current_description = []
            current_amount = ""
            last_amount = ""
        elif re.match(amount_pattern, cell):  # Amount pattern
            current_amount = cell
            last_amount = cell
        elif re.match(total_pattern, cell):  # Total pattern
            if current_date:
                dates.append(current_date)
                descriptions.append(" ".join(current_description))
                amounts.append(last_amount)
            # Reset current values after handling total line
            current_date = ""
            current_description = []
            current_amount = ""
            last_amount = ""
        else:
            current_description.append(cell)

# Append the last accumulated data
if current_date:
    dates.append(current_date)
    descriptions.append(" ".join(current_description))
    amounts.append(last_amount)

# Write the final data to a CSV file
with open('final_output.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f, delimiter=',', quoting=csv.QUOTE_ALL)
    writer.writerow(['Date', 'Description', 'Amount'])
    for date, description, amount in zip(dates, descriptions, amounts):
        writer.writerow([date, description, amount])
