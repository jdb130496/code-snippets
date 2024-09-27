from datetime import datetime
from dateutil.relativedelta import relativedelta

def calculate_interest_rate(current_price, historical_price, current_date, historical_date):
    current_date = datetime.strptime(current_date, '%d-%m-%Y').date()
    historical_date = datetime.strptime(historical_date, '%d-%m-%Y').date()
    difference = relativedelta(current_date, historical_date)
    years_elapsed = difference.years + difference.months/12 + difference.days/365.25
    quarters_elapsed = int(years_elapsed * 4) + 1

    def calculate_balance(interest_rate):
        balance = historical_price
        quarter_start = historical_date
        for quarter in range(quarters_elapsed):
            quarter_end = quarter_start + relativedelta(months=3)
            if quarter == quarters_elapsed - 1 and current_date < quarter_end:
                days = (current_date - quarter_start).days
            else:
                days = (quarter_end - quarter_start).days
            if quarter == 0:
                days += 1
            interest = balance * interest_rate * (days / 365)
            balance += interest
#            print(f"Quarter start: {quarter_start.strftime('%d-%m-%Y')}, Quarter end: {quarter_end.strftime('%d-%m-%Y')}, Balance: {balance:.4f}")
            quarter_start = quarter_end
        return balance

    def f(interest_rate):
        return calculate_balance(interest_rate) - current_price

    max_iterations = 10000
    lower_bound = 0.0
    upper_bound = 1.0
    iterations = 0
    while abs(calculate_balance((lower_bound + upper_bound) / 2) - current_price) > 0.0000001 and iterations < max_iterations:
        midpoint = (lower_bound + upper_bound) / 2
        if calculate_balance(midpoint) > current_price:
            upper_bound = midpoint
        else:
            lower_bound = midpoint
        iterations += 1

    if iterations == max_iterations:
        print("Unable to find a solution")
        return None

    interest_rate = (lower_bound + upper_bound) / 2

    return interest_rate

current_price = float(input("Enter the current price: "))
historical_price = float(input("Enter the historical price: "))
current_date = input("Enter the current date (dd-mm-yyyy): ")
historical_date = input("Enter the historical date (dd-mm-yyyy): ")

interest_rate = calculate_interest_rate(current_price, historical_price, current_date, historical_date)

print(f"The annualized interest rate compounded quarterly is: {interest_rate * 100:.4f}%")

