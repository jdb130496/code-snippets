# Set initial values for the variables
basic_price = 980
tax_rate = 0.20
gross = basic_price

# Set a tolerance value for the difference between the old and new gross values
tolerance = 0.01

# Initialize a variable to track the difference between the old and new gross values
difference = float("inf")

# Initialize a variable to count the number of iterations
iteration_count = 0

# Perform the iterative calculation
while difference > tolerance:
    # Increment the iteration count
    iteration_count += 1
    
    # Calculate the tax amount and new gross value
    tax_amount = gross * tax_rate
    new_gross = basic_price + tax_amount
    
    # Calculate the difference between the old and new gross values
    difference = abs(new_gross - gross)
    
    # Update the gross value
    gross = new_gross
    basic_price = round(basic_price, 2)
    tax_rate = round(tax_rate, 2)
    tax_amount = round(tax_amount, 2)
    gross = round(gross, 2)
    # Print the values of the variables on this iteration
    print(f"Iteration {iteration_count}:")
    print(f"  Basic price: {basic_price:.2f}")
    print(f"  Tax rate: {tax_rate:.2%}")
    print(f"  Tax amount: {tax_amount:.2f}")
    print(f"  Gross: {gross:.2f}")
    print(f"  Difference: {difference:.2f}")
# Print the final values of the variables
print(f"\nFinal values:")
print(f"Basic price: {basic_price:.2f}")
print(f"Tax rate: {tax_rate:.2%}")
print(f"Tax amount: {tax_amount:.2f}")
print(f"Gross: {gross:.2f}")
print(f"Iterations: {iteration_count}")

