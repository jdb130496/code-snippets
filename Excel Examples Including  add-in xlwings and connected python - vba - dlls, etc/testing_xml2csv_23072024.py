import xml.etree.ElementTree as ET
import pandas as pd
def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    for voucher in root.findall('.//VOUCHER'):
        for ledger_entries in voucher.findall('.//*'):
            if ledger_entries.tag.endswith('.LIST'):
                row = {}
                for elem in voucher.iter():
                    if elem.tag != ledger_entries.tag:
                        row[elem.tag] = elem.text
                for subelem in ledger_entries.iter():
                    row[subelem.tag] = subelem.text
                data.append(row)
    df = pd.DataFrame(data)
    return df
xml_file = 'D:\\RR Data\\Shree Mai Krupa CT\\Final Accounts\\2023-24\\Daybook_11042024.xml'  # replace with your file path
df = parse_xml(xml_file)
# Remove duplicate rows
df = df.drop_duplicates()
# Compare AMOUNT field with the previous row
df = df.reset_index(drop=True)
rows_to_remove = []
for index, row in df.iterrows():
    if index < len(df) - 1 and row.get('AMOUNT') == df.loc[index + 1, 'AMOUNT']:
        if row.get('ISPARTYLEDGER') == 'No':
            rows_to_remove.append(index)
df.drop(rows_to_remove, inplace=True)# Remove marked rows
df = df.reset_index(drop=True)
df.to_csv('D:\\RR Data\\Shree Mai Krupa CT\\Final Accounts\\2023-24\\Daybook_230724.csv', index=False, sep='|')

