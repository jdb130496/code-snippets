import sys
import xlwings as xw
import numpy as np
import pandas as pd
import dask.dataframe as dd
from dask.distributed import Client

@xw.func
@xw.arg('days', ndim=2)
def aging_buckets_parallel(days_amounts):
    client = Client(processes=False, threads_per_worker=4, n_workers=4)
    days_amounts_array = np.array(days_amounts)
    df = pd.DataFrame(days_amounts_array, columns=['days', 'amount'])
    df['days_amounts'] = list(zip(df['days'], df['amount']))
    ddf = dd.from_pandas(df, npartitions=8)
    aging_list = [
        (lambda day, amount: amount < 0, "Advance"),
        (lambda day, amount: 0 <= day < 31, "Not Due"),
        (lambda day, amount: 31 <= day < 61, "31-60 Days"),
        (lambda day, amount: 61 <= day < 91, "61-90 Days"),
        (lambda day, amount: 91 <= day < 181, "91-180 Days"),
        (lambda day, amount: 181 <= day < 366, "6 Months to 1 year"),
        (lambda day, amount: 366 <= day, "More than 1 year")
    ]
    ddf['age_bucket'] = ddf['days_amounts'].map(lambda x: next((label for condition, label in aging_list if condition(*x)), None), meta=('days', 'object'))
    result_df = ddf.compute()
    result = [[item] for item in result_df['age_bucket'].values]
    client.close()
    return result

