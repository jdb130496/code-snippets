import pandas as pd
import xml.etree.ElementTree as ET

def xml_to_df(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    for tallymessage in root.findall('.//TALLYMESSAGE'):
        for child in tallymessage:
            if child.tag == 'VOUCHER':
                row = {}
                first_row = {}
                for subchild in child:
                    if subchild.tag == 'ALLLEDGERENTRIES.LIST':
                        for subsubchild in subchild:
                            row[subsubchild.tag] = subsubchild.text
                        if not first_row:
                            first_row = row.copy()
                        else:
                            for key, value in first_row.items():
                                if key not in row:
                                    row[key] = value
                        data.append(row)
                        row = {}
                    else:
                        row[subchild.tag] = subchild.text
                        first_row[subchild.tag] = subchild.text
    return pd.DataFrame(data)
df = xml_to_df('D:\RR Data\Shree Mai Krupa CT\Daybook.xml')
df.to_csv('daybook.csv', index=False, sep='|')
