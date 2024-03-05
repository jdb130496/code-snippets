import pandas as pd
from lxml import etree

def xml_to_excel(xml_file_path, excel_file_path):
    # Parse the XML file
    tree = etree.parse(xml_file_path)
    root = tree.getroot()

    # Find all 'Table' elements
    tables = root.findall('.//Table')

    # Initialize an empty list to store DataFrames
    dfs = []

    # Loop over each table
    for table in tables:
        # Find all 'TR' elements in the table
        rows = table.findall('.//TR')

        # Loop over each row
        for row in rows:
            # Find all 'TH' and 'TD' elements in the row
            cols = row.findall('.//TH') + row.findall('.//TD')

            # Get the text from each column
            cols_text = [col.text for col in cols]

            # Append the row to the list as a DataFrame
            dfs.append(pd.DataFrame([cols_text]))

    # Concatenate all DataFrames in the list
    data = pd.concat(dfs, ignore_index=True)

    # Write the data to an Excel file
    data.to_excel(excel_file_path, index=False)

# Usage
xml_to_excel('d:\\Statement1709609282764.xml', 'd:\\jio_usage.xlsx')

