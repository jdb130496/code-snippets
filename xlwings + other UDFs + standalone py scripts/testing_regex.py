import xlwings as xw
import regex

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
def REGEXFIND(excel_range, patterns):
    result = []
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_result = []
            for pattern in patterns:
                match = regex.search(pattern, cell)
                if match:
                    cell_result.append(match.group())
            if len(cell_result) == len(patterns):
                row_result.append(" ".join(cell_result))
            else:
                row_result.append("Pattern Not Found")
        result.append(row_result)
    return result

import re

@xw.func
@xw.arg('excel_range', ndim=2)
@xw.arg('patterns', ndim=1)
@xw.arg('replacement')
def REGEXREPLACE(excel_range, patterns, replacement):
    result = []
    if replacement is None:
        replacement = ""
    for row in excel_range:
        row_result = []
        for cell in row:
            cell_result = cell
            for pattern in patterns:
                if re.search(pattern, cell_result):
                    cell_result = re.sub(pattern, replacement, cell_result)
            row_result.append(cell_result)
        result.append(row_result)
    return result
