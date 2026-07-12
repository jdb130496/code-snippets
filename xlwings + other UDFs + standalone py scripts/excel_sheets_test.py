import xlwings as xw

wb = xw.books.active
print(wb.name)                          # confirm correct workbook
print([s.name for s in wb.sheets])       # see actual sheet names

sht = wb.sheets.active                  # use whichever sheet is currently active/visible
