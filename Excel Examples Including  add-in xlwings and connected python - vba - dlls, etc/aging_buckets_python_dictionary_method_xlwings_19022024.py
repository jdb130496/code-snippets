import xlwings as xw
import sys
import bisect

@xw.func
@xw.arg('x', ndim=2)
def aging_buckets(x):
    aging_list = [
        (-sys.maxsize, 0, "Advance"),
        (0, 31, "Not Due"),
        (31, 61, "31-60 Days"),
        (61, 91, "61-90 Days"),
        (91, 181, "91-180 Days"),
        (181, 366, "6 Months to 1 year"),
        (366, sys.maxsize, "More than 1 year")
    ]
    result = []
    for row in x:
        temp = []
        for item in row:
            index = bisect.bisect(aging_list, (item,))
            if index:
                _, _, value = aging_list[index - 1]
                temp.append(value)
        result.append(temp)
    return result

