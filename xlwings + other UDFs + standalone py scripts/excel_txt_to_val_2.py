import xlwings as xw

wb = xw.books.active
print(wb.name)

sht = wb.sheets['BOB Savings Account']
rng = sht.range('E13:F32')
values = rng.value   # list of rows, each row is a list of column values

cleaned = []
for row in values:
    cleaned_row = []
    for v in row:
        if v is None:
            cleaned_row.append(None)
        elif isinstance(v, (int, float)):
            cleaned_row.append(v)  # already numeric, leave as-is
        else:
            s = str(v).strip().replace('\xa0', '').replace(',', '').replace('₹', '')
            if s == '':
                cleaned_row.append(None)
            else:
                try:
                    cleaned_row.append(float(s))
                except ValueError:
                    cleaned_row.append(v)  # leave unconvertible text as-is
    cleaned.append(cleaned_row)

rng.value = cleaned
print("Done.")
