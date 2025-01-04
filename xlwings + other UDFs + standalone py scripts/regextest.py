import re
def REGEXLATEST(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_str = str(cell)  # Convert cell to string
            for pattern in patterns:
                if re.search(pattern, cell_str):
                    row_result.append(cell_str)
                    break
            else:
                row_result.append("")
        result.append(row_result)
    return result
