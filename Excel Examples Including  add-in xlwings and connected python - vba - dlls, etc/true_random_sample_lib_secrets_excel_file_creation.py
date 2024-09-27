import secrets
import numpy as np
import pandas as pd
from collections import Counter
from scipy.stats import rankdata
import random
import openpyxl
ar1=np.sort(np.array(random.sample(range(10000000,500000001),20000000),dtype='int64'))
random_numbers = set()
while len(random_numbers) < 20000000:
     random_number = secrets.randbelow(1000000000)
     random_numbers.add(random_number)
random_numbers = np.array(list(random_numbers)).astype('int64')
print([item for item, count in Counter(random_numbers).items() if count > 1]) #checking for duplicates
ar2=(rankdata(random_numbers)-1).astype('int64')
ar3=np.column_stack((ar1,random_numbers,ar2))
df = pd.DataFrame(ar3, columns=['Doc No', 'Random Number', 'Rank'])
df2=df[df['Rank']<=4999999]
df2.to_csv('random_sample.csv',sep='\t',index=True, index_label='Index')
