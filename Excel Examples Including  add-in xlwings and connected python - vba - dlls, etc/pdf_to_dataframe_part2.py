import pandas as pd
import re

first_array = []
second_array = []
third_array = []

with open(r'D:\dgbdata\extracted_text.txt', 'r') as f:
    lines = f.readlines()
    for line in lines:
        if re.match(r'\d{2}/\d{2}\s*\n', line) or line == '\n':
            first_array.append(line.strip())
        else:
            break
    first_count = len(first_array)
    for line in lines[first_count:first_count * 2]:
        second_array.append(line.strip())
    for line in lines[first_count * 2:first_count * 3]:
        third_array.append(line.strip())
        
df = pd.DataFrame({'First Array': first_array, 'Second Array': second_array, 'Third Array': third_array})

i = 0
while i < len(df):
    if df.loc[i, 'Third Array'] == '':
        row_to_update = i - 1
        description = df.loc[i - 1, 'Second Array']
        while i < len(df) and df.loc[i, 'Third Array'] == '':
            description += ' ' + df.loc[i, 'Second Array']
            i += 1
        df.loc[row_to_update, 'Second Array'] = description
        df.drop(range(row_to_update + 1, i), inplace=True)
        df.reset_index(drop=True, inplace=True)
        i = row_to_update + 1
    else:
        i += 1
        
df.to_csv('output.csv', sep='\t', index=False)

