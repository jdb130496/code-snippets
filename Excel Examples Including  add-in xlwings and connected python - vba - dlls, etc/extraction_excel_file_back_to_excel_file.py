import pandas as pd
import openpyxl

# Load spreadsheet
xl = pd.read_excel('d:\\dgbdata\\Prices (1).xlsx', sheet_name='Daily')

# Define the ranges you want to read
range1 = 'D9:D11585'
range2 = 'K9:K11585'

# Read the data from the specified ranges
data1 = pd.read_excel('d:\\dgbdata\\Prices.xlsx', sheet_name='Daily', usecols='D', skiprows= lambda x: x<8 or x >12000)
data2 = pd.read_excel('d:\\dgbdata\\Prices.xlsx', sheet_name='Daily',  usecols='K', skiprows= lambda x: x<8 or x >12000)

# Combine the data from the two ranges
df = pd.concat([data1, data2], axis=1)
df.to_excel("d:\\dgbdata\\gold_prices.xlsx")

