import csv

# Open the CSV file
with open('d:\\dev\\days.txt', 'r') as f:
    reader = csv.reader(f)
    
    # Convert each row to a list and store in a new list
    result = [[int(row[0])] for row in reader]

