from rdrand import RdRandom
from collections import Counter
import numpy as np
r = RdRandom()
random_numbers = set()
while len(random_numbers) < 20000000:
    random_bytes = r.getrandombytes(3)
    random_int = int.from_bytes(random_bytes, byteorder='big', signed=False)
    random_numbers.append(random_int)
random_numbers=np.array(random_numbers)
print([item for item, count in Counter(random_numbers).items() if count > 1])
np.savetxt("sample.txt",random_numbers,fmt="%d")
