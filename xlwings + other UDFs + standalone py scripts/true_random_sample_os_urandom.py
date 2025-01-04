import numpy as np
from collections import Counter
import os
ar=np.reshape(np.apply_along_axis(lambda x: int(''.join(map(str, x))), 1, np.reshape(np.array(list(os.urandom(500000))),(-1,5))),(-1)).astype('int64')
print([item for item, count in Counter(ar).items() if count > 1]) #checking for duplicates
ar=np.reshape(ar,(-1,1))
np.savetxt("sample.txt",ar,fmt="%d")
