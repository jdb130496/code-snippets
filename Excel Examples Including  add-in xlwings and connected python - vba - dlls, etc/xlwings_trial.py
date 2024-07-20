import xlwings as xw
import rdrand
from randomgen import RDRAND
import sys
import numpy as np
import dask.dataframe as dd
from dask.distributed import Client
from scipy.optimize import newton
import pandas as pd
from datetime import datetime, timedelta
import calendar
from cffi import FFI
import numpy as np
import os
import csv
import time

print(sys.executable)
ffi = FFI()
#NUM_NUMBERS = 100000
#NUM_THREADS = 16

# Define the functions in the DLL
ffi.cdef("""
    int rdrand64_step(unsigned long long *rand);
    void generate_random_numbers(int num_threads, int num_numbers);
    unsigned long long* get_numbers();
    void free_numbers(unsigned long long *numbers);
""")


# Load the DLL
#C = ffi.dlopen('D:\\OneDrive - 0yt2k\\Compiled dlls & executables\\rdrand_multithreaded_new_ucrt_gcc.dll')
C = ffi.dlopen('D:\\OneDrive - 0yt2k\\Compiled dlls & executables\\rdrand_multithreaded_new.dll')
#ffi.cdef("""
#    void generateRandomNumbersC(int numNumbers, int numWorkers, int numThreads);
#    unsigned long long* getNumbersC();
#    int getNumbersSizeC();
#""")

#dll = ffi.dlopen('D:\\OneDrive - 0yt2k\\Compiled dlls & executables\\boost_rdrand.dll')

@xw.func
@xw.arg('Lst', ndim=2)
def multiply_elements(Lst):
    # Separate lists and multiply each by 5
    new_Lst = [[(element*5)+3 for element in sub_list] for sub_list in Lst]
    return new_Lst
@xw.func
@xw.arg('Lst', ndim=2)
def multiply_elements_2(Lst):
    # Separate lists and multiply each by 5
    new_Lst = [[(element*4)+8 for element in sub_list] for sub_list in Lst]
    return new_Lst
@xw.func
@xw.arg('days_amounts', ndim=2)
def aging_buckets(days_amounts):
    aging_list = [
        (lambda day, amount: amount < 0, "Advance"),
        (lambda day, amount: 0 <= day < 31, "Not Due"),
        (lambda day, amount: 31 <= day < 61, "31-60 Days"),
        (lambda day, amount: 61 <= day < 91, "61-90 Days"),
        (lambda day, amount: 91 <= day < 181, "91-180 Days"),
        (lambda day, amount: 181 <= day < 366, "6 Months to 1 year"),
        (lambda day, amount: 366 <= day, "More than 1 year")
    ]
    result = [[next((label for condition, label in aging_list if condition(day[0], day[1])), 'No Match')] for day in days_amounts if len(day) == 2]
    return result

@xw.func
@xw.arg('days_amounts', ndim=2)
def aging_buckets_parallel(days_amounts):
    client = Client(n_workers=6, threads_per_worker=4)
    df = pd.DataFrame(days_amounts, columns=['days', 'amount'])
    df['days'] = pd.to_numeric(df['days'], errors='coerce')
    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
    ddf = dd.from_pandas(df, npartitions=4)
    aging_list = [
            (lambda day, amount: int(amount) < 0, "Advance"),
            (lambda day, amount: 0 <= int(day) < 31, "Not Due"),
            (lambda day, amount: 31 <= int(day) < 61, "31-60 Days"),
            (lambda day, amount: 61 <= int(day) < 91, "61-90 Days"),
            (lambda day, amount: 91 <= int(day) < 181, "91-180 Days"),
            (lambda day, amount: 181 <= int(day) < 366, "6 Months to 1 year"),
            (lambda day, amount: 366 <= int(day), "More than 1 year")
            ]
    ddf['age_bucket'] = ddf.map_partitions(lambda df: df.apply(lambda row: next((label for condition, label in aging_list if condition(row['days'], row['amount'])), None), axis=1), meta=('days', 'object'))
    result_df = ddf.compute()
    result = [[item] for item in result_df['age_bucket'].values]
    client.close()
    return result

@xw.func
@xw.arg('date_and_months', ndim=2)
def EOMONTHM(date_and_months):
    result = []
    for row in date_and_months:
        dt = row[0]
        month_offset = int(row[1])
        year, month = divmod(dt.month - 1 + month_offset, 12)
        _, last_day = calendar.monthrange(dt.year + year, month + 1)
        eomonth = datetime(dt.year + year, month + 1, last_day)
        result.append([(eomonth - datetime(1899, 12, 30)).days])
    return result
@xw.func
@xw.arg('date_and_months', ndim=2)
def EDATEM(date_and_months):
    result = []
    for row in date_and_months:
        # The date is already a datetime.datetime object
        dt = row[0]
        month_offset = int(row[1])
        # Add the month offset to the current month and adjust the year if necessary
        year, month = divmod(dt.month - 1 + month_offset, 12)
        edate = datetime(dt.year + year, month + 1, dt.day)
        # Convert the datetime.datetime object back to an Excel date (ordinal)
        result.append([(edate - datetime(1899, 12, 30)).days])
    return result
@xw.func
def generate_and_get_data(NUM_THREADS, NUM_NUMBERS):
    NUM_THREADS = int(NUM_THREADS)
    NUM_NUMBERS = int(NUM_NUMBERS)
    C.generate_random_numbers(NUM_THREADS, NUM_NUMBERS)
    numbers_ptr = C.get_numbers()
    numbers = [[int(numbers_ptr[i])] for i in range(NUM_NUMBERS)]
    C.free_numbers(numbers_ptr)
    return numbers

@xw.func
@xw.arg('numbers', ndim=2)
def check_duplicates(numbers):
    # Flatten the list of lists
    numbers = [num for sublist in numbers for num in sublist]
    
    if len(numbers) == len(set(numbers)):
        return "No duplicates found."
    else:
        return "Duplicates found."
@xw.func
def generate_random_numbers(n):
    # Convert n to an integer
    n = int(n)

    # Create a new RDRAND generator
    rg = RDRAND()

    # Generate n random numbers, each composed of three 5-digit numbers
    numbers = [int((rg.random_raw() % 90000 + 10000) * 1e10 + (rg.random_raw() % 90000 + 10000) * 1e5 + (rg.random_raw() % 90000 + 10000)) for _ in range(n)]

    # Convert the list to a list of lists for xlwings
    numbers_list = [[number] for number in numbers]

    # Return the list of lists
    return numbers_list
rng = rdrand.RdRandom()
@xw.func
def generate_random_numbers_rdrand(num):
    # Generate the random numbers
    random_numbers = [[int(rng.random() % (10**15 - 10**14)) + 10**14] for _ in range(int(num))]
    return random_numbers

@xw.func
@xw.arg('x_values', ndim=2)
@xw.arg('z_values', ndim=2)
@xw.arg('target', numbers=float)
def wa_return(x_values, z_values, target):
    # Convert input lists of lists to numpy arrays
    x_values = np.array(x_values)
    z_values = np.array(z_values)

    # Define the function for which we want to find the root
    def func(y):
        return np.sum(x_values * ((1 + y / 4) ** z_values)) - target

    # Use the Newton-Raphson method to find the root
    y_initial_guess = 0.5
    y_solution = newton(func, y_initial_guess)

    return y_solution

#@xw.func
#def intel_rdrand_boost(NUM_NUMBERS, NUM_WORKERS, NUM_THREADS):
#    NUM_NUMBERS = int(NUM_NUMBERS)
#    NUM_WORKERS = int(NUM_WORKERS)
#    NUM_THREADS = int(NUM_THREADS)
#    numbers_ptr = dll.generateRandomNumbers(NUM_NUMBERS, NUM_WORKERS, NUM_THREADS)
#    numbers = [[int(numbers_ptr[i])] for i in range(NUM_NUMBERS)]
#    return numbers

import pandas as pd

@xw.func
@xw.arg('dates', ndim=2)
def date_buckets(dates):
    df = pd.DataFrame(dates, columns=['date'])
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    date_list = [
            (lambda date: (date.month == 4 and date.day >= 1) or (date.month == 5) or (date.month == 6 and date.day <= 15), "01/04 To 15/06"),
            (lambda date: (date.month == 6 and date.day >= 16) or (date.month == 7) or (date.month == 8) or (date.month == 9 and date.day <= 15), "16/06 To 15/09"),
            (lambda date: (date.month == 9 and date.day >= 16) or (date.month == 10) or (date.month == 11) or (date.month == 12 and date.day <= 15), "16/09 To 15/12"),
            (lambda date: (date.month == 12 and date.day >= 16) or (date.month == 1) or (date.month == 2) or (date.month == 3 and date.day <= 15), "16/12 To 15/03"),
            (lambda date: (date.month == 3 and date.day >= 16 and date.day <= 31), "16/03 To 31/03")
            ]
    df['bucket'] = df['date'].apply(lambda date: next((label for condition, label in date_list if condition(date)), None))
    result = [[item] for item in df['bucket'].values]
    return result



