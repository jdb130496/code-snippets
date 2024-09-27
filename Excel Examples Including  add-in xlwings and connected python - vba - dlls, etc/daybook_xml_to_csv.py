import xml.etree.ElementTree as ET
import pandas as pd
def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    for voucher in root.findall('.//VOUCHER'):
        for ledger_entries in voucher.findall('.//ALLLEDGERENTRIES.LIST'):
            row = {}
            for elem in voucher.iter():
                if elem.tag != 'ALLLEDGERENTRIES.LIST':
                    row[elem.tag] = elem.text
            for subelem in ledger_entries.iter():
                row[subelem.tag] = subelem.text
            data.append(row)
    df = pd.DataFrame(data)
    return df
xml_file = 'D:\\RR Data\\Shree Mai Krupa CT\\Final Accounts\\2023-24\\Daybook_06042024.xml'  # replace with your file path
df = parse_xml(xml_file)
df.to_csv('D:\\RR Data\\Shree Mai Krupa CT\\Final Accounts\\2023-24\\Daybook_06042024.csv', index=False, sep='|')
import xml.etree.ElementTree as ET
import pandas as pd
def parse_xml(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    data = []
    for voucher in root.findall('.//VOUCHER'):
        for ledger_entries in voucher.findall('.//ALLLEDGERENTRIES.LIST'):
            row = {}
            for elem in voucher.iter():
                if elem.tag != 'ALLLEDGERENTRIES.LIST':
                    row[elem.tag] = elem.text
            for subelem in ledger_entries.iter():
                row[subelem.tag] = subelem.text
            data.append(row)
    df = pd.DataFrame(data)
    return df
xml_file = 'D:\\RR Data\\Shree Mai Krupa CT\\Final Accounts\\2023-24\\Daybook_06042024.xml'  # replace with your file path
df = parse_xml(xml_file)
df.to_csv('D:\\RR Data\\Shree Mai Krupa CT\\Final Accounts\\2023-24\\Daybook_06042024.csv', index=False, sep='|')
import pandas as pd

@xw.func
@xw.arg('dates', ndim=2)
def quarter_buckets(dates):
    df = pd.DataFrame(dates, columns=['date'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    quarter_list = [
            (lambda date: 4 <= date.month <= 6, "Q1"),
            (lambda date: 7 <= date.month <= 9, "Q2"),
            (lambda date: 10 <= date.month <= 12, "Q3"),
            (lambda date: 1 <= date.month <= 3, "Q4")
            ]
    df['quarter'] = df['date'].apply(lambda date: next((label for condition, label in quarter_list if condition(date)), None))
    result = [[item] for item in df['quarter'].values]
    return result

