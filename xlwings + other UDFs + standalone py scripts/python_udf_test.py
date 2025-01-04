from rdrand import RdSeedom
import xlwings as xw
@xw.func
def generate_random_numbers(n):
    s = RdSeedom()
    random_numbers = []
    n = int(n)
    while len(random_numbers) < n:
        # Generate a random integer with exactly 15 digits
        num = s.randint(100000000000000, 999999999999999)
        # Append the number as a list to create a list of lists
        random_numbers.append([num])
    return random_numbers

