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

