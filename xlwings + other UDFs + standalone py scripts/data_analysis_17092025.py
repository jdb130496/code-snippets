#%% Cell 1: Import libraries and set file path
import pandas as pd
import numpy as np

# File path
file_path = r"D:\NMIMS\All data 2.csv"

#%% Cell 2: Read the CSV file
print("Step 1: Reading CSV file...")
df = pd.read_csv(file_path)
print(f"Original shape: {df.shape}")
print(f"Columns: {len(df.columns)}")
print("\nFirst few rows:")
print(df.head())

#%% Cell 3: Examine the data structure
print("\n" + "="*50)
print("Step 2: Examining data structure...")
print("First 10 rows of first 5 columns:")
print(df.iloc[:10, :5])

# Find the company column (should be first column)
company_col = df.columns[0]
print(f"\nCompany column name: '{company_col}'")

#%% Cell 4: Identify company rows
print("\n" + "="*50)
print("Step 4: Finding company rows...")
company_mask = df[company_col].notna() & (df[company_col].astype(str).str.strip() != '')
companies_found = df[company_mask][company_col].tolist()
print(f"Number of companies found: {len(companies_found)}")
print("First 5 companies:")
for i, company in enumerate(companies_found[:5]):
    print(f"{i+1}. {company}")

#%% Cell 5: Find date patterns
print("\n" + "="*50)
print("Step 5: Looking for date patterns...")
date_patterns = []
for idx, row in df.iterrows():
    row_values = row.astype(str).tolist()
    jan_values = [val for val in row_values if 'Jan-' in str(val)]
    if len(jan_values) > 5:  # If this row has many date entries
        print(f"Found date row at index {idx}")
        date_patterns = row.tolist()
        break

if date_patterns:
    print("Sample dates found:", [d for d in date_patterns[:10] if 'Jan-' in str(d)])
else:
    print("No clear date row found, will use column positions")

#%% Cell 6: Find financial particulars
print("\n" + "="*50)
print("Step 6: Looking for financial particulars...")
particulars_row = []
for idx, row in df.iterrows():
    row_values = row.astype(str).tolist()
    if any('profit before' in str(val).lower() for val in row_values):
        print(f"Found particulars row at index {idx}")
        particulars_row = row.tolist()
        break

if particulars_row:
    print("Sample particulars found:")
    unique_particulars = list(set([p for p in particulars_row[1:11] if str(p) != 'nan']))
    for i, particular in enumerate(unique_particulars[:5]):
        print(f"{i+1}. {particular}")

#%% Cell 7: Create column mappings
print("\n" + "="*50)
print("Step 7: Creating column mappings...")

# Extract dates and particulars from the identified rows
if date_patterns:
    dates_list = date_patterns[1:]  # Skip first column (company name)
else:
    # Generate generic dates if not found
    dates_list = []
    for i in range(len(df.columns) - 1):
        year = 11 + (i // 6)  # Assuming 6 metrics per year starting from 2011
        dates_list.append(f"Jan-{year}")

if particulars_row:
    particulars_list = particulars_row[1:]  # Skip first column (company name)
else:
    # Generate generic particulars if not found
    base_metrics = [
        "Total profit before prior period items, exceptional items, extraordinary items and tax",
        "Equity", 
        "Long term Borrowings",
        "Short Term Borrowings", 
        "Assets", 
        "Net Fixed Assets"
    ]
    particulars_list = []
    for i in range(len(df.columns) - 1):
        particulars_list.append(base_metrics[i % len(base_metrics)])

print(f"Number of date entries: {len(dates_list)}")
print(f"Number of particular entries: {len(particulars_list)}")

#%% Cell 8: Transform the data
print("\n" + "="*50)
print("Step 8: Transforming data...")

transformed_records = []
total_records_processed = 0

for company in companies_found:
    if pd.isna(company) or str(company).strip() == '':
        continue
    
    # Find the row for this company
    company_row_mask = df[company_col] == company
    if not company_row_mask.any():
        continue
    
    company_row_idx = df[company_row_mask].index[0]
    company_data = df.iloc[company_row_idx].tolist()
    
    print(f"Processing: {company}")
    company_record_count = 0
    
    # Process each data column
    for col_idx in range(1, len(company_data)):  # Skip company name column
        value = company_data[col_idx]
        
        # Skip empty/null values
        if pd.isna(value) or str(value).strip() == '':
            continue
        
        # Get corresponding date and particular
        list_idx = col_idx - 1  # Adjust for 0-based indexing
        
        date = dates_list[list_idx] if list_idx < len(dates_list) else f"Period_{list_idx}"
        particular = particulars_list[list_idx] if list_idx < len(particulars_list) else f"Metric_{list_idx}"
        
        # Create record
        record = {
            'Company Name': company,
            'Month': str(date).strip(),
            'Particulars': str(particular).strip(),
            'Values': value
        }
        
        transformed_records.append(record)
        company_record_count += 1
    
    total_records_processed += company_record_count
    print(f"  → {company_record_count} records added")

print(f"\nTotal records created: {len(transformed_records)}")

#%% Cell 9: Create DataFrame and clean data
print("\n" + "="*50)
print("Step 9: Creating final DataFrame...")

result_df = pd.DataFrame(transformed_records)
print(f"DataFrame created with shape: {result_df.shape}")

# Clean the Values column
print("\nCleaning Values column...")
original_count = len(result_df)

# Convert to numeric, invalid values become NaN
result_df['Values'] = pd.to_numeric(result_df['Values'], errors='coerce')

# Remove rows with NaN values
result_df = result_df.dropna(subset=['Values'])
print(f"Removed {original_count - len(result_df)} rows with invalid values")

#%% Cell 10: Display sample results
print("\n" + "="*50)
print("Step 10: Sample results...")
print("\nFirst 10 records:")
print(result_df.head(10).to_string(index=False))

print(f"\nFinal DataFrame shape: {result_df.shape}")
print(f"Unique companies: {result_df['Company Name'].nunique()}")
print(f"Unique months: {result_df['Month'].nunique()}")
print(f"Unique particulars: {result_df['Particulars'].nunique()}")

#%% Cell 11: Save the results
print("\n" + "="*50)
print("Step 11: Saving results...")

output_file = r"D:\NMIMS\Transformed_Data.csv"
result_df.to_csv(output_file, index=False)
print(f"Data saved to: {output_file}")

#%% Cell 12: Summary statistics and completion
print("\n" + "="*50)
print("Step 12: Summary Statistics...")
print("\nUnique Months:")
print(sorted(result_df['Month'].unique()))

print("\nUnique Particulars:")
unique_particulars = result_df['Particulars'].unique()
for i, particular in enumerate(unique_particulars, 1):
    print(f"{i}. {particular}")

print("\nValue Statistics:")
print(result_df['Values'].describe())

print("\n" + "="*50)
print("TRANSFORMATION COMPLETE!")
print(f"Input file: {file_path}")
print(f"Output file: {output_file}")
print(f"Total records: {len(result_df)}")

