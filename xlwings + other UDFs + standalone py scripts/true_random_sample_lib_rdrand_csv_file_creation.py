from rdrand import RdRandom
import numpy as np
import pandas as pd
from collections import Counter
from scipy.stats import rankdata
import random
import openpyxl
r = RdRandom()
ar1=np.sort(np.array(random.sample(range(10000000,500000001),45000000),dtype='int64'))
random_numbers = set()
while len(random_numbers) < 45000000:
    random_bytes = r.getrandbytes(5)
    random_int = int.from_bytes(random_bytes, byteorder='big', signed=False)
    random_numbers.add(random_int)
random_numbers = np.array(list(random_numbers)).astype('int64')
print([item for item, count in Counter(random_numbers).items() if count > 1]) #checking for duplicates
ar2=(rankdata(random_numbers)-1).astype('int64')
ar3=np.column_stack((ar1,random_numbers,ar2))
df = pd.DataFrame(ar3, columns=['Doc No', 'Random Number', 'Rank'])
df2=df[df['Rank']<=4999999]
df2.to_csv('random_sample.csv',sep='\t',index=True, index_label='Index')
