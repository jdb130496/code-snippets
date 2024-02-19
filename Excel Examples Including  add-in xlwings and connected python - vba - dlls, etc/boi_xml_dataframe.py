import pandas as pd
import xml.etree.ElementTree as ET

def xml_to_df(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    table = root.findall('Table')[1]
    data = []
    for row in table.findall('TR'):
        data.append([cell.text for cell in row.findall('TD')])
    df = pd.DataFrame(data[1:], columns=[cell.text for cell in table.find('TR').findall('TH')])
    return df

xml_file = r'D:\RR Data\IT Return FY 2022-23\boi statement FY 2022-23.xml'

df = xml_to_df(xml_file)
df.to_csv( r'D:\RR Data\IT Return FY 2022-23\boi statement FY 2022-23.xlsx', sep='\t', index=False)
