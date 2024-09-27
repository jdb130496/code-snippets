import os
from collections import Counter
import numpy as np
random_numbers = []
for _ in range(100000):
    random_bytes = os.urandom(5)
    random_int = int.from_bytes(random_bytes, byteorder='big', signed=False)
    random_numbers.append(random_int)
random_numbers=np.array(random_numbers)
print([item for item, count in Counter(random_numbers).items() if count > 1])
np.savetxt("sample.txt",random_numbers,fmt="%d")
