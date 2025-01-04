from datetime import datetime, timedelta
def add_months(start_date, months):
    month = start_date.month - 1 + months
    year = start_date.year + month // 12
    month = month % 12 + 1
    day = min(start_date.day, [31,
        29 if year % 4 == 0 and not year % 100 == 0 or year % 400 == 0 else 28,
        31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month-1])
    return start_date.replace(year=year, month=month, day=day)

def derive_annual_interest_rate(start_date, end_date, start_amount, end_amount):
    # Convert Excel serial date to datetime object
    def excel_date_to_datetime(excel_date):
        return datetime(1899, 12, 30) + timedelta(days=excel_date)
    # Convert dates from Excel serial numbers to datetime objects
    start_date = excel_date_to_datetime(start_date)
    end_date = excel_date_to_datetime(end_date)
    # Initialize variables
    low_rate = 0.0
    high_rate = 20.0  # Set a reasonable upper limit for the interest rate
    tolerance = 1e-6  # Tolerance for convergence
    max_iterations = 1000  # Maximum number of iterations to prevent infinite loop
    # Function to calculate the number of days between two dates
    def days_between(d1, d2):
        return (d2 - d1).days
    # Function to calculate the end amount given a rate
    def calculate_end_amount(rate):
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
            print(f"Current Date: {current_date}, Next Date: {next_date}, Days: {days}, Interest: {interest}, Current Amount: {current_amount}")
            current_date = next_date
        return current_amount
    # Binary search for the correct rate
    for _ in range(max_iterations):
        mid_rate = (low_rate + high_rate) / 2
        calculated_end_amount = calculate_end_amount(mid_rate)
        print(f"Mid Rate: {mid_rate}, Calculated End Amount: {calculated_end_amount}")
        if abs(calculated_end_amount - end_amount) < tolerance:
            break
        if calculated_end_amount < end_amount:
            low_rate = mid_rate
        else:
            high_rate = mid_rate
    return (low_rate + high_rate) / 2
# Example usage
start_date = 42107  # Excel serial date for 13-04-2015
end_date = 45601  # Excel serial date for 05-11-2024
start_amount = 100
end_amount = 218.5256789
annual_interest_rate = derive_annual_interest_rate(start_date, end_date, start_amount, end_amount)
print(f"The derived annual interest rate is {annual_interest_rate:.6f}%")

