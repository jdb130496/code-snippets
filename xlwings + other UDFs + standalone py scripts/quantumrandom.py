import quantumrandom
import numpy as np
random_numbers = set()
while len(random_numbers) <= 100000:
    random_number = quantumrandom.randint(1, 100000000)
    random_numbers.add(random_number)
random_numbers = list(random_numbers)
print(random_numbers)
