import xml.etree.ElementTree as ET
import pandas as pd
import re
import csv

# Parse the XML file
xml_file = "01 January 2025- RG Glass-Regular Account-decrypted.xml"
tree = ET.parse(xml_file)

# Get the root element of the XML
root = tree.getroot()

# Initialize a list to store the rows
rows = []

# Find all 'Table' elements in the XML
for table in root.findall('.//Table'):
    # Find all 'TR' elements within each 'Table'
    for row in table.findall('.//TR'):
        for cell in row:
            if cell.text and cell.text.strip():
                rows.append(cell.text.strip())

# Create a DataFrame from the rows
df = pd.DataFrame(rows, columns=['Data'])

# Define regex patterns for dates and amounts
date_pattern = r'^\d{2}/\d{2}$'
amount_pattern = r'^-?\$?\d{1,3}(,\d{3})*(\.\d{2})$'

# Use stack and unstack to optimize and not iterate through looping
stacked_df = df.stack()
date_anchors = stacked_df[stacked_df.str.match(date_pattern)].index.get_level_values(0).tolist()
amount_anchors = stacked_df[stacked_df.str.match(amount_pattern)].index.get_level_values(0).tolist()

# Initialize lists to store the final columns
dates = []
descriptions = []
amounts = []

# Iterate over date anchors to capture descriptions between them
for i in range(len(date_anchors) - 1):
    lower_index = date_anchors[i]
    higher_index = date_anchors[i + 1]
    
    # Capture the date
    dates.append(df.iloc[lower_index]['Data'])
    
    # Initialize a list to store description parts
    description_parts = []
    
    # Initialize a variable to store the amount (only one amount per date range)
    amount_found = False
    
    # Iterate over rows between two date anchors
    for j in range(lower_index + 1, higher_index):
        data = df.iloc[j]['Data']
        if re.match(amount_pattern, data) and not amount_found:
            amounts.append(data)
            amount_found = True
        elif not re.match(amount_pattern, data):
            description_parts.append(data)
    
    # Merge description parts with ' ' space in between
    descriptions.append(' '.join(description_parts))
    
    # If no amount was found in this range, append an empty string to amounts
    if not amount_found:
        amounts.append('')

# Ensure all lists are of the same length by padding with empty strings if necessary
max_length = max(len(dates), len(descriptions), len(amounts))
dates.extend([''] * (max_length - len(dates)))
descriptions.extend([''] * (max_length - len(descriptions)))
amounts.extend([''] * (max_length - len(amounts)))

# Create the final DataFrame with dates, descriptions, and amounts
final_df = pd.DataFrame({
    'Date': dates,
    'Description': descriptions,
    'Amount': amounts
})
final_df.to_csv('final_output.csv', index=False, quoting=csv.QUOTE_ALL)
