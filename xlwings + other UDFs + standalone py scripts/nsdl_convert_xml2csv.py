import xml.etree.ElementTree as ET
import csv
import re

# Parse the XML file
tree = ET.parse(r'D:\DGB Personal Data\personal\NSDL Account Statement 12-09-2026.xml')
root = tree.getroot()

# Output CSV path
output_csv = r'D:\DGB Personal Data\personal\NSDL Account Statement 12-09-2026.csv'

def clean_text(text):
    """Clean whitespace from text"""
    if text is None:
        return ''
    return ' '.join(text.split()).strip()

def get_cell_text(cell):
    """Extract all text from a cell including nested elements"""
    return clean_text(''.join(cell.itertext()))

rows_to_write = []

# Find all tables
tables = root.findall('.//Table')

for table_idx, table in enumerate(tables):
    # Add a blank row between tables (except before the first)
    if table_idx > 0:
        rows_to_write.append([])

    # Look for a preceding <P> tag to use as section header
    # We'll add it as a label row
    all_elements = list(root.iter())
    table_pos = all_elements.index(table)
    # Search backwards for nearest <P>
    for i in range(table_pos - 1, -1, -1):
        if all_elements[i].tag == 'P':
            p_text = clean_text(''.join(all_elements[i].itertext()))
            if p_text:
                rows_to_write.append([p_text])
            break

    for tr in table.findall('TR'):
        row = []
        for cell in tr:
            if cell.tag in ('TH', 'TD'):
                row.append(get_cell_text(cell))
        if any(row):  # skip fully empty rows
            rows_to_write.append(row)

# Write to CSV
with open(output_csv, 'w', newline='', encoding='utf-8-sig') as f:
    writer = csv.writer(f)
    writer.writerows(rows_to_write)

print(f"Done! CSV saved to: {output_csv}")
