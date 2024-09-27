from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import xlwings as xw

@xw.func
@xw.arg('current_price', numbers=float, ndim=2)
@xw.arg('historical_price', numbers=float, ndim=2)
@xw.arg('current_date', ndim=2)
@xw.arg('historical_date', ndim=2)
def calculate_interest_rate(current_price, historical_price, current_date, historical_date):
    try:
        current_price = current_price[0][0]
        historical_price = historical_price[0][0]
        current_date = current_date[0][0]
        historical_date = historical_date[0][0]
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
                quarter_start = quarter_end
            return balance

        def f(interest_rate):
            return calculate_balance(interest_rate) - current_price

        max_iterations = 10000
        lower_bound = 0.0
        upper_bound = 1.0
        iterations = 0
        while abs(calculate_balance((lower_bound + upper_bound) / 2) - current_price) > 0.000000000001 and iterations < max_iterations:
            midpoint = (lower_bound + upper_bound) / 2
            if calculate_balance(midpoint) > current_price:
                upper_bound = midpoint
            else:
                lower_bound = midpoint
            iterations += 1

        if iterations == max_iterations:
            return [["Unable to find a solution"]]
#            return None

        interest_rate = (lower_bound + upper_bound) / 2

        return [[interest_rate]]
    except Exception as e:
        print(str(e))
        return [["NA"]]

@xw.func
@xw.arg('input_date', numbers=int, ndim=2)
def return_date(input_date):
    input_date = input_date[0][0]  # Flatten the input
    date = datetime(1899, 12, 30) + timedelta(days=input_date)
    return [[(date - datetime(1899, 12, 30)).days]]  # Convert the date back to Excel date serial number
