import pandas as pd
pd.set_option('display.max_rows', None)
import sys

def aging_buckets(x):
    aging_dict = {
        range(-sys.maxsize, 0): "Advance",
        range(0, 31): "Not Due",
        range(31, 61): "31-60 Days",
        range(61, 91): "61-90 Days",
        range(91, 181): "91-180 Days",
        range(181, 366): "6 Months to 1 year",
        range(366, sys.maxsize): "More than 1 year"
    }
    for r, value in aging_dict.items():
        if x in r:
            return value

df = pd.read_csv('d:\\dev\\days.txt', header=None, names=['Days'])
df['Aging Buckets'] = df['Days'].apply(aging_buckets)
print(df)

