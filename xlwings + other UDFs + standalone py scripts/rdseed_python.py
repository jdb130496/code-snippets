from rdrand import RdSeedom
import xlwings as xw
@xw.func
def generate_random_numbers(n):
    s = RdSeedom()
    random_numbers = []
    while len(random_numbers) < n:
        # Generate a random float and convert it to a 15-digit integer
        num = int(s.random() * 1e15)
        # Check if the number is in the desired range
        if 100000000000000 <= num <= 999999999999999:
            # Append the number as a list to create a list of lists
            random_numbers.append([num])
    return random_numbers



