import xlwings as xw
from datetime import datetime, timedelta

def add_months(start_date, months):
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, [31,
        29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return start_date.replace(year=year, month=month, day=day)

@xw.func
def derive_annual_interest_rates(start_dates, end_dates, start_amounts, end_amounts):
    # Convert Excel serial date to datetime object
    def excel_date_to_datetime(excel_date):
        if isinstance(excel_date, (int, float)):
            return datetime(1899, 12, 30) + timedelta(days=int(excel_date))
        return excel_date
    
    # Function to calculate the number of days between two dates
    def days_between(d1, d2):
        return (d2 - d1).days
    
    # Function to calculate the end amount given a rate
    def calculate_end_amount(rate, start_date, end_date, start_amount):
        current_amount = start_amount
        current_date = start_date
        
        while current_date < end_date:
            if current_date == start_date:
                next_date = add_months(current_date, 3)  # Add three months for the first quarter
                days = days_between(current_date, next_date) + 1  # Add one day for the first quarter
            else:
                next_date = add_months(current_date, 3)  # Add three months for subsequent quarters
                if next_date > end_date:
                    next_date = end_date
                    days = days_between(current_date, next_date) - 1  # Subtract one day for the last quarter
                else:
                    days = days_between(current_date, next_date)
            
            interest = (rate / 100) * (days / 365) * current_amount
            current_amount += interest
            
            current_date = next_date
        
        return current_amount
    
    # Ensure inputs are lists
    if not isinstance(start_dates, list):
        start_dates = [start_dates]
    if not isinstance(end_dates, list):
        end_dates = [end_dates]
    if not isinstance(start_amounts, list):
        start_amounts = [start_amounts]
    if not isinstance(end_amounts, list):
        end_amounts = [end_amounts]
    
    derived_rates = []
    
    for i in range(len(start_dates)):
        start_date = excel_date_to_datetime(start_dates[i])
        end_date = excel_date_to_datetime(end_dates[i])
        start_amount = start_amounts[i]
        end_amount = end_amounts[i]
        
        # Initialize variables
        low_rate = 0.0
        high_rate = 50.0  # Remove the upper limit for the interest rate
        tolerance = 1e-10  # Tolerance for convergence
        max_iterations = 1000  # Maximum number of iterations to prevent infinite loop
        
        # Binary search for the correct rate
        for _ in range(max_iterations):
            mid_rate = (low_rate + high_rate) / 2
            calculated_end_amount = calculate_end_amount(mid_rate, start_date, end_date, start_amount)
            
            if abs(calculated_end_amount - end_amount) < tolerance:
                break
            
            if calculated_end_amount < end_amount:
                low_rate = mid_rate
            else:
                high_rate = mid_rate
        
        derived_rate = (low_rate + high_rate) / 2
        derived_rates.append(derived_rate)
    
    return [[rate] for rate in derived_rates]


# Example usage in Excel:
# Assuming you have ranges A1:A10 for start_dates, B1:B10 for end_dates,
# C1:C10 for start_amounts, and D1:D10 for end_amounts,
# you can use the function in Excel as follows:
# =derive_annual_interest_rates(A1:A10, B1:B10, C1:C10, D1:D10)

import xlwings as xw
from datetime import datetime, timedelta
def add_months1(start_date1, months1):
    month1 = start_date1.month - 1 + months1
    year1 = start_date1.year + month1 // 12
    month1 = month1 % 12 + 1
    day1 = min(start_date1.day, [31,
        29 if year1 % 4 == 0 and not year1 % 100 == 0 or year1 % 400 == 0 else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month1-1])
    return start_date1.replace(year=year1, month=month1, day=day1)
@xw.func
def SIMPLERATEDERIVATION(start_dates1, end_dates1, start_amounts1, end_amounts1):
    # Convert Excel serial date to datetime object
    def excel_date_to_datetime1(excel_date1):
        if isinstance(excel_date1, (int, float)):
            return datetime(1899, 12, 30) + timedelta(days=int(excel_date1))
        return excel_date1
    # Function to calculate the number of days between two dates
    def days_between1(d3, d4):
        return (d4 - d3).days
    # Function to calculate the end amount given a rate
    def calculate_end_amount1(rate1, start_date1, end_date1, start_amount1):
        current_amount1 = start_amount1
        current_date1 = start_date1
        while current_date1 < end_date1:
            if current_date1 == start_date1:
                next_date1 = add_months1(current_date1, 3)  # Add three months for the first quarter
                days1 = days_between1(current_date1, next_date1)  # Add one day for the first quarter
            else:
                next_date1 = add_months1(current_date1, 3)  # Add three months for subsequent quarters
                if next_date1 > end_date1:
                    next_date1 = end_date1
                    days1 = days_between1(current_date1, next_date1)  # Subtract one day for the last quarter
                else:
                    days1 = days_between1(current_date1, next_date1)
            interest1 = (rate1 / 100) * (days1 / 365) * current_amount1
            current_amount1 += interest1
            current_date1 = next_date1
        return current_amount1
    # Ensure inputs are lists
    if not isinstance(start_dates1, list):
        start_dates1 = [start_dates1]
    if not isinstance(end_dates1, list):
        end_dates1 = [end_dates1]
    if not isinstance(start_amounts1, list):
        start_amounts1 = [start_amounts1]
    if not isinstance(end_amounts1, list):
        end_amounts1 = [end_amounts1]
    derived_rates1 = []
    for i in range(len(start_dates1)):
        start_date1 = excel_date_to_datetime1(start_dates1[i])
        end_date1 = excel_date_to_datetime1(end_dates1[i])
        start_amount1 = start_amounts1[i]
        end_amount1 = end_amounts1[i]
        # Initialize variables
        low_rate1 = 0.0
        high_rate1 = 50.0  # Remove the upper limit for the interest rate
        tolerance1 = 1e-10  # Tolerance for convergence
        max_iterations1 = 1000  # Maximum number of iterations to prevent infinite loop
        # Binary search for the correct rate
        for _ in range(max_iterations1):
            mid_rate1 = (low_rate1 + high_rate1) / 2
            calculated_end_amount1 = calculate_end_amount1(mid_rate1, start_date1, end_date1, start_amount1)
            if abs(calculated_end_amount1 - end_amount1) < tolerance1:
                break
            if calculated_end_amount1 < end_amount1:
                low_rate1 = mid_rate1
            else:
                high_rate1 = mid_rate1
        derived_rate1 = (low_rate1 + high_rate1) / 2
        derived_rates1.append(derived_rate1)
    return [[rate1] for rate1 in derived_rates1]
