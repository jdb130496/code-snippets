import numpy as np

# Read the csv file
data = [np.array(list(map(int, line.split()))) for line in open('D:\\dgbdata\\random_bytes.txt') if line.strip()]
# Concatenate the individual arrays into a single 1D array
data = np.concatenate(data)

# Reshape the data into a single column
data = data.reshape(-1, 1)
#np.savetxt('data.csv', data, delimiter='\t', fmt='%.0f')
np.savetxt('data.csv', data.astype(int), delimiter='\t', fmt='%d')
