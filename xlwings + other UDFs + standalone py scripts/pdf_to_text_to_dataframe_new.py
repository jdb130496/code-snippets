#pyMUPDF library - pip install pyMUPDF
import fitz
import pandas as pd
doc = fitz.open(r'D:\DGB Personal Data\juhi all documents\IT Return FY 2022-23\XXXXXXXXXXX7064-01-04-2022to31-03-2023.pdf')
text = ""
for page in doc:
   text += page.get_text()

lines = text.split('\n')
lines_list = [line for line in lines]
df=pd.DataFrame(lines_list)
with open(r"D:\DGB Personal Data\juhi all documents\IT Return FY 2022-23\pdftext.txt", 'w', encoding='utf-8') as f:
    for row in df.itertuples(index=False):
        row = [str(x) if x != '' else ' ' for x in row]
        line = ','.join(row)
        f.write(line + '\n')

# Before going to the next phase, open text file as above, clean up all headers, titles and footers that come in between the data patttrn as under and where the first character is $ (in any line), replace with null. gvim editor is very handy here.

import re

date_pattern = r'\d{2}/\d{2}\n'
amount_pattern = r'\d{1,3}(?:,\d{3})*\.\d{2}\n'

dates = []
descriptions = []
amounts = []

with open(r'd:\dgbdata\pdftext.txt', 'r') as f:
    lines = f.readlines()
    description = ''
    for line in lines:
        if re.match(date_pattern, line):
            dates.append(line.strip())
            if description:
                descriptions.append(' '.join(description.split()))
                description = ''
        elif re.search(amount_pattern, line):
            amounts.append(re.search(amount_pattern, line).group().strip())
            #description += line.replace(re.search(amount_pattern, line).group(), '').strip() + ' '
        else:
            description += line.strip() + ' '
    if description:
        descriptions.append(' '.join(description.split()))

data = {'Date': dates, 'Description': descriptions, 'Amount': amounts}
df = pd.DataFrame(data)
df.to_csv(r"D:\dgbdata\bank_statement.csv",index=False,sep="\t")
