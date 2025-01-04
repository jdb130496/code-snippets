import secrets
import numpy as np
from collections import Counter
random_numbers = set()
while len(random_numbers) < 100000:
     random_number = secrets.randbelow(10000000)
     random_numbers.add(random_number)
random_numbers = np.array(list(random_numbers))
print([item for item, count in Counter(random_numbers).items() if count > 1]) #checking for duplicates
np.savetxt("sample.txt",random_numbers,fmt="%d")
