import rdrand
import xlwings as xw

def populate_excel(rows, cols, random_numbers):
    # Start an instance of Excel
    wb = xw.Book()
    sheet = wb.sheets[0]
    
    total_elements = rows * cols
    index = 0
    
    for i in range(rows):
        for j in range(cols):
            if index < len(random_numbers):
                sheet.cells(i + 1, j + 1).value = random_numbers[index]
                index += 1
            else:
                sheet.cells(i + 1, j + 1).value = None
@xw.func
def RDSEED_EXCEL(min_val, max_val, count, rows, cols):
    random_numbers_rdseed = []
    for _ in range(count):
        random_number_rdseed = rdrand.RdSeedom().get_bits(64) % (max_val - min_val + 1) + min_val
        random_numbers_rdseed.append(random_number_rdseed)
    return [[random_number_rdseed_1] for random_number_rdseed_1 in random_numbers_rdseed]

