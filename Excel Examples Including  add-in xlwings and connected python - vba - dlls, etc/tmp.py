import sys
import numpy as np
import pandas as pd
import dask.dataframe as dd
from dask.distributed import Client

def aging_buckets_parallel(days):
    # Start a Dask client with 4 threads
    client = Client(processes=False, threads_per_worker=4, n_workers=1)

    # Convert the input list of lists to a flat Numpy array
    days_array = np.array(days).flatten()

    # Convert the input array to a Dask DataFrame
    df = dd.from_pandas(pd.DataFrame(days_array, columns=['days']), npartitions=4)

    # Define the aging buckets
    aging_list = [
        (lambda day: -sys.maxsize <= day < 0, "Advance"),
        (lambda day: 0 <= day < 31, "Not Due"),
        (lambda day: 31 <= day < 61, "31-60 Days"),
        (lambda day: 61 <= day < 91, "61-90 Days"),
        (lambda day: 91 <= day < 181, "91-180 Days"),
        (lambda day: 181 <= day < 366, "6 Months to 1 year"),
        (lambda day: 366 <= day, "More than 1 year")
    ]

    # Apply the function to each row in parallel
    df['age_bucket'] = df['days'].map(lambda day: next((label for condition, label in aging_list if condition(day)), None), meta=('days', 'object'))

    # Compute the result
    result_df = df.compute()

    # Convert the 'age_bucket' column back to a list of lists
    result = result_df['age_bucket'].values.tolist()
    result = [[item] for item in result]

    # Close the Dask client
    client.close()

    return result

