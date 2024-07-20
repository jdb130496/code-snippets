import random

def generate_random_numbers():
    first_number = random.uniform(4, 8)
    numbers = [first_number]
    for i in range(9):
        number = numbers[-1] + random.uniform(-0.15 * numbers[-1], 0.15 * numbers[-1])
        while number < 4 or number > 8 or number % 5 != 0:
            number = numbers[-1] + random.uniform(-0.15 * numbers[-1], 0.15 * numbers[-1])
        numbers.append(number)
    return numbers

numbers = generate_random_numbers()
print(numbers)

