import numpy as np

# Path to your file
file_path = 'D:\\dev\\examplecsv.txt'

# Read the file line by line and filter
arr = np.array([line.strip().split(';') for line in open(file_path, 'r') if len(line.strip().split(';')) == 8])

# Print first 100 entries (Sample)
print(arr[:100])
