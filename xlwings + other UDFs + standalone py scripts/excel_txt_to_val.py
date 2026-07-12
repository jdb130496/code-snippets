import xlwings as xw

wb = xw.books.active
print(wb.name)

sht = wb.sheets['SBI Pension Account']   # <-- pick the exact sheet with your FD Interest data

rng = sht.range('D19:E34')              # <-- adjust to the actual range in that sheet
values = rng.value

cleaned = []
for v in values:
    if v is None:
        cleaned.append(None)
        continue
    s = str(v).strip().replace('\xa0', '').replace(',', '').replace('₹', '')
    try:
        cleaned.append(float(s))
    except ValueError:
        cleaned.append(v)  # leave unconverted values as-is so you can spot failures

rng.value = [[c] for c in cleaned]

print("Done.")
