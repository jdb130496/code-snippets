import fitz
import pandas as pd
import re

doc = fitz.open(r'D:\dgbdata\XXXXXXXXXXX7064-01-04-2022to31-03-2023.pdf')
text = ""
for page in doc:
   text += page.get_text()

lines = text.split('\n')
lines_list = [line.strip() for line in lines if line.strip()]
df=pd.DataFrame(lines_list)
with open(r"d:\dgbdata\Axis.txt", 'w', encoding='utf-8') as f:
    for row in df.itertuples(index=False):
        row = [str(x) if x != '' else ' ' for x in row]
        line = ','.join(row)
        f.write(line + '\n')

#Before going to the next phase - below - clean up the text file to delete headers, footers, titles, etc.

dates = []
descriptions = []
amounts = []
balances = []
location_codes = []

date_pattern = re.compile(r'\d{2}-\d{2}-\d{4}')
amount_pattern = re.compile(r'^\s*\d+\.\d{2}$|^\d+\.\d{2}$|^\.?\d{2}$|^\s*\.?\d{2}$')
balance_pattern = re.compile(r'^\s*\d+\.\d{2}(\s*\d*)?$|^(\d+\.\d{2}(\s*\d*)?)$')
location_code_pattern = re.compile(r'^\d*$')
amount_updated = False
try:
    with open(r"D:\dgbdata\Axis.txt", 'r', encoding='utf-8') as f:
        lines = f.readlines()
        description = ""
        location_code_updated = False
        for i, line in enumerate(lines):
            print(f"Processing line {i+1}: {line.strip()}")
            line = line.strip()
            if not line:
                continue
            if date_pattern.match(line):
                dates.append(line)
                if description:
                    descriptions.append(description)
                    description = ""
                location_code_updated = False
                balance_updated = False
            elif not amount_updated and amount_pattern.match(line):
                amounts.append(line.lstrip())
                amount_updated = True
            elif amount_updated and balance_pattern.match(line):
                parts = line.split()
                balances.append(parts[0].lstrip())
                if len(parts) > 1:
                    location_codes.append(parts[1])
                    location_code_updated = True
                else:
                    location_codes.append("")
                    location_code_updated = False
                amount_updated = False
                balance_updated = True
            elif balance_updated and location_code_pattern.match(line):
                if not location_code_updated and location_codes:
                    #location_codes.append(line.lstrip())
                    location_codes[-1] += line
                    location_code_updated = True
            else:
                if description:
                    description += " " + line
                else:
                    description = line
        if description:
            descriptions.append(description)
except Exception as e:
    print(f"Error: {e}")

data = {'Date': dates, 'Description': descriptions, 'Amount': amounts, 'Balance': balances, 'Location Code': location_codes}
df = pd.DataFrame(data)
df.to_csv("Axis.csv",index=False,sep="\t")
