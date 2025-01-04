current_price = float(input("Enter the current price: "))
historical_price = float(input("Enter the historical price: "))
years_elapsed = float(input("Enter the number of years elapsed: "))

annualized_interest_rate = (((current_price / historical_price) ** ((1 / (years_elapsed*4)))) - 1) * 4

print(f"The annualized interest rate compounded quarterly is: {annualized_interest_rate * 100:.4f}%")

