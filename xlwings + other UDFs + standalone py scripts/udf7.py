from cffi import FFI
import xlwings as xw
import os
@xw.func
def FILL_EMPTY(excel_range):
    filled_list = []
    last_value = ""
    for cell in excel_range:
        if cell is not None and cell != "":  # Check if the cell is not None or empty
            last_value = cell
        filled_list.append([last_value])  # Ensure each result is a list to maintain vertical format
    return filled_list
@xw.func
@xw.arg('data', ndim=1)
def SPLIT_TEXT(data, delimiter):
    try:
        if not data or all(cell is None for cell in data):
            return [""]
        # Split the text and find the maximum length of the sublists
        split_data = [cell.split(delimiter) if cell is not None else [""] for cell in data]
        max_length = max(len(sublist) for sublist in split_data)
        # Ensure all sublists have the same length by padding with empty strings
        padded_data = [sublist + [""] * (max_length - len(sublist)) for sublist in split_data]
        return padded_data
    except Exception as e:
        return str(e)
@xw.func
def EXCELORM(range1, range2, condition):
    result = []
    for val1, val2 in zip(range1, range2):
        val1 = 0 if val1 is None or val1 == "" else float(val1)
        val2 = 0 if val2 is None or val2 == "" else float(val2)
        # Use eval to dynamically evaluate the condition
        if eval(condition):
            result.append([True])
        else:
            result.append([False])
    return result
import requests
from bs4 import BeautifulSoup
import xlwings as xw
@xw.func
def get_sanskrit_mantras(url):
    # Send a GET request to the webpage
    response = requests.get(url)
    # Parse the HTML content of the webpage
    soup = BeautifulSoup(response.content, 'html.parser')
    # Find all article tags with the specified class
    articles = soup.find_all('article', class_='dpLyricsWrapper')
    # Initialize a list to store the mantras
    mantras = []
    # Iterate over each article tag
    for article in articles:
        # Find all div tags with the specified class within the article
        divs = article.find_all('div', class_='dpNameCardMantra dpFlexEqual')
        for div in divs:
            # Find the div containing the Sanskrit mantra
            mantra_div = div.find('div', class_='dpListPrimaryTitle')
            if mantra_div:
                # Extract the text and add it to the list
                mantras.append(mantra_div.get_text(strip=True))
    # Return the list of mantras in a vertical format
    return [[mantra] for mantra in mantras]
@xw.func
def EXCELXORM(range1, range2, condition1, condition2):
    result = []
    for val1, val2 in zip(range1, range2):
        # Handle empty or None values as 0
        val1 = 0 if val1 is None or val1 == "" else float(val1)
        val2 = 0 if val2 is None or val2 == "" else float(val2)
        # Replace 'val1' and 'val2' in the condition strings with actual values
        condition1_eval = condition1.replace('val1', str(val1)).replace('val2', str(val2))
        condition2_eval = condition2.replace('val1', str(val1)).replace('val2', str(val2))
        # Evaluate the conditions dynamically using eval
        cond1_result = eval(condition1_eval)
        cond2_result = eval(condition2_eval)
        # Perform XOR: True if exactly one condition is True, False otherwise
        if (cond1_result and not cond2_result) or (not cond1_result and cond2_result):
            result.append([True])
        else:
            result.append([False])
    return result
from rdrand import RdRandom
import string
import xlwings as xw
def generate_password(length=12):
    r = RdRandom()
    char_set = string.ascii_letters + string.digits + '?@$#^&*'
    special_chars = '?@$#^&*'
    # Ensure at least one uppercase, one lowercase, and one special character
    password = [
        r.choice(string.ascii_uppercase),
        r.choice(string.ascii_lowercase),
        r.choice(special_chars)
    ]
    # Fill the rest of the password length with random characters
    while len(password) < length:
        char = r.choice(char_set)
        # Ensure no more than two special characters
        if char in special_chars and sum(c in special_chars for c in password) >= 2:
            continue
        password.append(char)
    # Shuffle to avoid predictable patterns using rdrand
    for i in range(len(password)):
        j = r.randint(0, len(password) - 1)
        password[i], password[j] = password[j], password[i]
    # Ensure the password does not start with a special character
    while password[0] in special_chars:
        for i in range(len(password)):
            j = r.randint(0, len(password) - 1)
            password[i], password[j] = password[j], password[i]
    return ''.join(password)
@xw.func
def PASSRDRAND(dummy=None):
    return generate_password()

import xlwings as xw

# Dictionaries for number to words conversion
units = {0: "", 1: "One", 2: "Two", 3: "Three", 4: "Four", 5: "Five", 6: "Six", 7: "Seven", 8: "Eight", 9: "Nine"}
teens = {11: "Eleven", 12: "Twelve", 13: "Thirteen", 14: "Fourteen", 15: "Fifteen", 16: "Sixteen", 17: "Seventeen", 18: "Eighteen", 19: "Nineteen"}
tens = {10: "Ten", 20: "Twenty", 30: "Thirty", 40: "Forty", 50: "Fifty", 60: "Sixty", 70: "Seventy", 80: "Eighty", 90: "Ninety"}
thousands = {1_000: "Thousand", 100_000: "Lakh", 10_000_000: "Crore"}

def number_to_words(n):
    if n in units:
        return units[n]
    if n in teens:
        return teens[n]
    if n in tens:
        return tens[n]
    
    for key in sorted(thousands.keys(), reverse=True):
        if n >= key:
            higher = n // key
            lower = n % key
            return number_to_words(higher) + " " + thousands[key] + ((" " + number_to_words(lower)) if lower > 0 else "")
    
    if n < 100:
        return tens[(n // 10) * 10] + " " + units[n % 10]
    if n < 1000:
        return units[n // 100] + " Hundred " + number_to_words(n % 100)
    
@xw.func
def INRWORDS(numbers):
    # Handle the case where numbers is a single element
    if isinstance(numbers, (int, float)):
        numbers = [numbers]

    results = []
    for number in numbers:
        rupees = int(number)
        paise = round((number - rupees) * 100)
        if rupees == 0 and paise == 0:
            word = "Rupees Zero And Paise Zero Only"
        elif rupees == 0 and paise > 0:
            word = f"Paise {number_to_words(paise)} Only"
        else:
            word = f"Rupee {number_to_words(rupees)}" if rupees == 1 else f"Rupees {number_to_words(rupees)}"
            if paise > 0:
                word += f" And Paise {number_to_words(paise)} Only"
            else:
                word += " Only"
        results.append(word)
    
    # Transpose the results to a vertical array
    return [[result] for result in results]
from rdrand import RdSeedom
import string
import xlwings as xw
def generate_password_rdseed(length1=12):
    r1 = RdSeedom()
    char_set1 = string.ascii_letters + string.digits + '?@$#^&*'
    special_chars1 = '?@$#^&*'
    # Ensure at least one uppercase, one lowercase, and one special character
    password1 = [
        r1.choice(string.ascii_uppercase),
        r1.choice(string.ascii_lowercase),
        r1.choice(special_chars1)
    ]
    # Fill the rest of the password length with random characters
    while len(password1) < length1:
        char1 = r1.choice(char_set1)
        # Ensure no more than two special characters
        if char1 in special_chars1 and sum(c1 in special_chars1 for c1 in password1) >= 2:
            continue
        password1.append(char1)
    # Shuffle to avoid predictable patterns using rdrand
    for i1 in range(len(password1)):
        j1 = r1.randint(0, len(password1) - 1)
        password1[i1], password1[j1] = password1[j1], password1[i1]
    # Ensure the password does not start with a special character
    while password1[0] in special_chars1:
        for i1 in range(len(password1)):
            j1 = r1.randint(0, len(password1) - 1)
            password1[i1], password1[j1] = password1[j1], password1[i1]
    return ''.join(password1)
@xw.func
def PASSRDSEED(dummy=None):
    return generate_password_rdseed()

from rdrand import RdSeedom
import string
import xlwings as xw

def generate_passwords(num_passwords, length1=12):
    num_passwords = int(num_passwords)
    r1 = RdSeedom()
    char_set1 = string.ascii_letters + string.digits + '?@$#^&*'
    special_chars1 = '?@$#^&*'
    
    def generate_password():
        # Ensure at least one uppercase, one lowercase, and two unique special characters
        password1 = [
            r1.choice(string.ascii_uppercase),
            r1.choice(string.ascii_lowercase),
            r1.choice(special_chars1)
        ]
        used_special_chars = set(password1[-1])
        
        # Add a second unique special character
        while len(used_special_chars) < 2:
            char1 = r1.choice(special_chars1)
            if char1 not in used_special_chars:
                password1.append(char1)
                used_special_chars.add(char1)
        
        # Fill the rest of the password length with random characters
        while len(password1) < length1:
            char1 = r1.choice(char_set1)
            # Ensure no more than two special characters
            if char1 in special_chars1 and char1 in used_special_chars:
                continue
            password1.append(char1)
        
        # Shuffle to avoid predictable patterns using rdrand
        for i1 in range(len(password1)):
            j1 = r1.randint(0, len(password1) - 1)
            password1[i1], password1[j1] = password1[j1], password1[i1]
        
        # Ensure the password does not start with a special character
        while password1[0] in special_chars1:
            for i1 in range(len(password1)):
                j1 = r1.randint(0, len(password1) - 1)
                password1[i1], password1[j1] = password1[j1], password1[i1]
        
        # Check for repetition of special characters and replace if necessary
        special_char_count = {char: password1.count(char) for char in special_chars1}
        for i1, char1 in enumerate(password1):
            if char1 in special_chars1 and special_char_count[char1] > 1:
                new_char = char1
                while new_char == char1 or new_char in used_special_chars:
                    new_char = r1.choice(special_chars1)
                password1[i1] = new_char
                special_char_count[char1] -= 1
                special_char_count[new_char] = special_char_count.get(new_char, 0) + 1
                used_special_chars.add(new_char)
        
        return ''.join(password1)
    
    passwords = [generate_password() for _ in range(num_passwords)]
    return [[p1] for p1 in passwords]

@xw.func
def RDSEEDMULTIPW(num_passwords):
    #return generate_passwords(num_passwords)
    return [[password] for password in generate_passwords(num_passwords)]

import rdrand
import xlwings as xw

@xw.func
def RDSEED_MATRIX(min_val, max_val, count, rows, cols):
    count=int(count)
    rows=int(rows)
    cols=int(cols)
    random_numbers_rdseed = []
    for _ in range(count):
        random_number_rdseed = rdrand.RdSeedom().get_bits(64) % (max_val - min_val + 1) + min_val
        random_numbers_rdseed.append(random_number_rdseed)
    
    # Create a 2D array to hold the random numbers
    matrix = []
    index = 0
    for i in range(rows):
        row = []
        for j in range(cols):
            if index < len(random_numbers_rdseed):
                row.append(random_numbers_rdseed[index])
                index += 1
            else:
                row.append(None)  # Fill with None if there are not enough random numbers
        matrix.append(row)
    
    return matrix
import xlwings as xw
import string
from rdrand import RdSeedom

# Function to generate passwords
def generate_passwords(num_passwords):
    try:
        # Convert the input to an integer
        num_passwords = int(num_passwords)
    except (ValueError, TypeError):
        return "Input must be a positive integer."

    # Validate the converted number
    if num_passwords <= 0:
        return "Input must be a positive integer."

    # Helper function to generate one password
    def generate_password():
        special_characters = "?@$#^&*"
        letters_and_digits = (
            string.ascii_uppercase + string.ascii_lowercase + string.digits
        )
        all_characters = letters_and_digits + special_characters

        # Instantiate the RdSeedom object
        seed = RdSeedom()

        while True:
            # Select required characters
            upper = seed.choice(string.ascii_uppercase)
            lower = seed.choice(string.ascii_lowercase)
            digit = seed.choice(string.digits)
            specials = seed.sample(special_characters, 2)  # Pick exactly 2 special characters

            # Remaining characters should come only from letters and digits
            others = seed.sample(letters_and_digits, 7)  # To ensure no extra special characters

            # Combine all characters
            password_list = [upper, lower, digit] + specials + others

            # Shuffle using RdSeedom
            for i in range(len(password_list) - 1, 0, -1):
                j = seed.randrange(0, i + 1)
                password_list[i], password_list[j] = password_list[j], password_list[i]

            password = ''.join(password_list)

            # Ensure it doesn't start with a special character
            if not password[0] in special_characters:
                return password

    # Generate the requested number of passwords
    passwords = [generate_password() for _ in range(num_passwords)]
    return passwords

# Excel UDF
@xw.func
def xl_generate_passwords(num_passwords):
    #return generate_passwords(num_passwords)
    return [[password] for password in generate_passwords(num_passwords)]

@xw.func
def PRIME(lower, upper):
    lower = int(lower)
    upper = int(upper)
    
    def is_prime(n):
        if n <= 1:
            return False
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False
        return True

    primes = [num for num in range(lower, upper + 1) if is_prime(num)]
    return [[prime] for prime in primes]

@xw.func
def IS_PRIME_WITH_DIVISOR(number):
    number = int(number)
    
    def is_prime(n):
        if n <= 1:
            return False, 1
        for i in range(2, int(n**0.5) + 1):
            if n % i == 0:
                return False, i
        return True, 1

    prime, divisor = is_prime(number)
    return ["Yes" if prime else "No", divisor]

import xlwings as xw
import math

@xw.func
def prime_factors(n):
    """Returns all prime factors (including duplicates)"""
    if isinstance(n, list):
        results = []
        max_length = 0
        for num in n:
            factors = _calculate_prime_factors(num)
            results.append(factors)
            if len(factors) > max_length:
                max_length = len(factors)
        
        # Pad each list to the max length
        for i in range(len(results)):
            results[i] += [None] * (max_length - len(results[i]))
        
        return results
    else:
        return _calculate_prime_factors(n)

def _calculate_prime_factors(n):
    if n <= 1:
        return [n]  # Return the number itself if it's <= 1
    
    # Get prime factors with duplicates
    prime_factors = []
    remaining = n
    i = 2
    while i * i <= remaining:
        while remaining % i == 0:
            prime_factors.append(i)
            remaining = remaining // i
        i += 1
    if remaining > 1:
        prime_factors.append(remaining)
    
    # Return prime factors without the highest prime factor
    return prime_factors

# Function to apply prime_factors to a range
def apply_prime_factors_to_range():
    wb = xw.Book.caller()  # Connect to the calling Excel workbook
    sheet = wb.sheets[0]  # Use the first sheet
    input_range = sheet.range('A1:A16')  # Adjust the range as needed
    output_range = sheet.range('B1:B16')  # Adjust the output range as needed
    
    for i, cell in enumerate(input_range):
        number = cell.value
        factors = prime_factors(number)
        output_range[i].value = factors

# Call the function when the script is run
if __name__ == "__main__":
    xw.Book("YourWorkbookName.xlsx").set_mock_caller()
    apply_prime_factors_to_range()


