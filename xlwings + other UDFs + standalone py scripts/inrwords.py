import sys
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
    
    return [[result] for result in results]

if __name__ == "__main__":
    # Get the number from command-line arguments
    number = float(sys.argv[1])
    # Call the INRWORDS function and print the result
    result = INRWORDS(number)
    print(result[0][0])

