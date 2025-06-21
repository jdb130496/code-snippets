import xlwings as xw
import pandas as pd
import numpy as np
from datetime import datetime

@xw.func
@xw.arg('data', pd.DataFrame, index=False, header=True)
def company_summary(data):
    """
    Generate company-wise summary with CAGR, Standard Deviation, and latest values
    
    Parameters:
    data: DataFrame with columns - Capitaline Code, Company Name, Date, High Price, Market Cap, Company Long Name, Debt-Equity Ratio
    
    Returns:
    DataFrame with summary statistics
    """
    
    print(f"Initial data shape: {data.shape}")
    print(f"Initial columns: {list(data.columns)}")
    
    # Check for 360 ONE before any processing
    print("\n=== DEBUGGING 360 ONE ===")
    if 'Company Name' in data.columns:
        companies_with_360 = data[data['Company Name'].astype(str).str.contains('360', na=False)]
        print(f"Rows containing '360' in Company Name: {len(companies_with_360)}")
        if len(companies_with_360) > 0:
            print("Sample rows with '360':")
            print(companies_with_360[['Capitaline Code', 'Company Name']].head())
    
    if 'Capitaline Code' in data.columns:
        code_66008_rows = data[data['Capitaline Code'].astype(str).str.contains('66008', na=False)]
        print(f"Rows with code 66008: {len(code_66008_rows)}")
        if len(code_66008_rows) > 0:
            print("Sample rows with code 66008:")
            print(code_66008_rows[['Capitaline Code', 'Company Name']].head())
    
    # Try different approaches to find the missing data
    print(f"Unique Capitaline Codes (first 20): {sorted(data['Capitaline Code'].unique())[:20]}")
    print(f"Data types: {data.dtypes}")
    
    # Check for any NaN values that might cause issues
    print(f"NaN values per column:")
    for col in data.columns:
        nan_count = data[col].isna().sum()
        if nan_count > 0:
            print(f"  {col}: {nan_count} NaN values")
    
    # Clean data more aggressively
    print("\n=== CLEANING DATA ===")
    
    # Remove rows with essential NaN values
    essential_cols = ['Capitaline Code', 'Company Name', 'Date', 'High Price']
    initial_rows = len(data)
    data = data.dropna(subset=essential_cols)
    print(f"Removed {initial_rows - len(data)} rows with NaN in essential columns")
    
    # Convert data types more carefully
    try:
        data['Capitaline Code'] = pd.to_numeric(data['Capitaline Code'], errors='coerce')
        data = data.dropna(subset=['Capitaline Code'])  # Remove rows where conversion failed
        data['Capitaline Code'] = data['Capitaline Code'].astype(int)
    except Exception as e:
        print(f"Error converting Capitaline Code: {e}")
    
    # Clean company names
    data['Company Name'] = data['Company Name'].astype(str).str.strip()
    
    # Ensure Date column is datetime
    data['Date'] = pd.to_datetime(data['Date'], errors='coerce')
    data = data.dropna(subset=['Date'])
    
    print(f"Final data shape after cleaning: {data.shape}")
    
    # Check again for 360 ONE after cleaning
    print("\n=== AFTER CLEANING ===")
    companies_with_360_clean = data[data['Company Name'].str.contains('360', na=False)]
    print(f"Rows containing '360' after cleaning: {len(companies_with_360_clean)}")
    if len(companies_with_360_clean) > 0:
        print("360 companies after cleaning:")
        print(companies_with_360_clean[['Capitaline Code', 'Company Name']].drop_duplicates())
    
    code_66008_clean = data[data['Capitaline Code'] == 66008]
    print(f"Rows with code 66008 after cleaning: {len(code_66008_clean)}")
    
    # Group by company
    grouped = data.groupby(['Capitaline Code', 'Company Name'])
    
    print(f"\nNumber of groups: {len(grouped)}")
    
    results = []
    
    for (code, company), group in grouped:
        if code == 66008 or '360' in str(company):
            print(f"*** FOUND TARGET: Code={code}, Company='{company}', Rows={len(group)} ***")
        
        # Sort by date to ensure proper ordering
        group = group.sort_values('Date')
        
        # Get earliest and latest records
        earliest_record = group.iloc[0]
        latest_record = group.iloc[-1]
        
        # Calculate CAGR using your specific formula
        latest_price = latest_record['High Price']
        earliest_price = earliest_record['High Price']
        latest_date = latest_record['Date']
        earliest_date = earliest_record['Date']
        
        # Days difference + 1
        days_diff = (latest_date - earliest_date).days + 1
        years_times_quarters = (days_diff / 365) * 4
        
        if years_times_quarters > 0 and earliest_price > 0:
            cagr = ((latest_price / earliest_price) ** (1 / years_times_quarters) - 1) * 4 * 100
        else:
            cagr = np.nan
        
        # Calculate Standard Deviation and Mean of prices
        mean_price = group['High Price'].mean()
        std_dev = group['High Price'].std()
        
        # Calculate Coefficient of Variation (COV)
        cov = std_dev / mean_price if mean_price > 0 else np.nan
        
        # Get latest values
        latest_market_cap = latest_record['Market Cap']
        latest_debt_equity = latest_record['Debt-Equity Ratio']
        
        results.append({
            'Capitaline Code': code,
            'Company Name': company,
            'Price CAGR': round(cagr, 4) if not np.isnan(cagr) else None,
            'Mean': round(mean_price, 2),
            'Standard Deviation': round(std_dev, 2),
            'COV': round(cov, 4) if not np.isnan(cov) else None,
            'Latest Price': round(latest_price, 2),
            'Latest Debt Equity Ratio': round(latest_debt_equity, 2),
            'Latest Market Cap': round(latest_market_cap, 2)
        })
    
    result_df = pd.DataFrame(results)
    print(f"\nFinal results shape: {result_df.shape}")
    
    # Check if 360 ONE is in final results
    final_360 = result_df[result_df['Company Name'].str.contains('360', na=False)]
    print(f"360 companies in final results: {len(final_360)}")
    
    return result_df

@xw.func
@xw.arg('range_data', xw.Range)
def company_summary_from_range(range_data):
    """
    Alternative function that takes a range as input
    Usage: =company_summary_from_range(A1:G100)
    """
    
    # Convert range to DataFrame
    data = range_data.options(pd.DataFrame, header=1, index=False).value
    
    # Rename columns to match expected format
    expected_columns = ['Capitaline Code', 'Company Name', 'Date', 'High Price', 'Market Cap', 'Company Long Name', 'Debt-Equity Ratio']
    data.columns = expected_columns[:len(data.columns)]
    
    return company_summary(data)

# Additional helper function for Excel usage
@xw.func
def calculate_price_cagr(latest_price, earliest_price, latest_date, earliest_date):
    """
    Calculate CAGR using your specific formula
    Usage: =calculate_price_cagr(latest_price, earliest_price, latest_date, earliest_date)
    """
    try:
        # Convert dates to datetime if they're not already
        if isinstance(latest_date, str):
            latest_date = pd.to_datetime(latest_date)
        if isinstance(earliest_date, str):
            earliest_date = pd.to_datetime(earliest_date)
        
        days_diff = (latest_date - earliest_date).days + 1
        years_times_quarters = (days_diff / 365) * 4
        
        if years_times_quarters > 0 and earliest_price > 0:
            cagr = ((latest_price / earliest_price) ** (1 / years_times_quarters) - 1) * 4 * 100
            return round(cagr, 4)
        else:
            return None
    except:
        return None

# Simple debugging function to check data
@xw.func
@xw.arg('range_data', xw.Range)
def debug_companies(range_data):
    """
    Debug function to check what companies are in the data
    Usage: =debug_companies(A1:G100)
    """
    try:
        # Convert range to DataFrame
        data = range_data.options(pd.DataFrame, header=1, index=False).value
        
        # Check if we have the expected columns
        print("Columns in data:", list(data.columns))
        
        # Rename columns to match expected format
        expected_columns = ['Capitaline Code', 'Company Name', 'Date', 'High Price', 'Market Cap', 'Company Long Name', 'Debt-Equity Ratio']
        data.columns = expected_columns[:len(data.columns)]
        
        # Clean and check unique companies
        data['Company Name'] = data['Company Name'].astype(str).str.strip()
        data['Capitaline Code'] = data['Capitaline Code'].astype(int)
        
        unique_companies = data[['Capitaline Code', 'Company Name']].drop_duplicates().sort_values('Capitaline Code')
        
        print("Unique companies found:")
        for _, row in unique_companies.iterrows():
            print(f"Code: {row['Capitaline Code']}, Name: '{row['Company Name']}'")
        
        # Check specifically for 360 ONE
        filtered_360 = data[data['Company Name'].str.contains('360', na=False)]
        print(f"\nRows containing '360': {len(filtered_360)}")
        if len(filtered_360) > 0:
            print("Sample 360 rows:")
            print(filtered_360[['Capitaline Code', 'Company Name']].head())
        
        return f"Found {len(unique_companies)} unique companies. Check console for details."
        
    except Exception as e:
        return f"Error: {str(e)}"
def setup_xlwings():
    """
    Setup function to establish xlwings connection
    Run this in Python before using UDFs in Excel
    """
    # This will start the Excel connection
    wb = xw.Book.caller()  # Connect to the calling workbook
    return wb

if __name__ == "__main__":
    # For testing purposes - you can run this to test the function
    # Create sample data similar to your example
    sample_data = pd.DataFrame({
        'Capitaline Code': [66008, 66008, 66008, 107, 107, 107],
        'Company Name': ['360 ONE', '360 ONE', '360 ONE', 'A B Real Estate', 'A B Real Estate', 'A B Real Estate'],
        'Date': ['2023-07-12', '2023-07-13', '2023-07-14', '2022-06-16', '2022-06-17', '2022-06-20'],
        'High Price': [505, 506.85, 514.85, 787, 761, 750.75],
        'Market Cap': [17937.68, 17916.26, 18228.64, 8401.75, 8319.65, 8154.34],
        'Company Long Name': ['360 ONE WAM Ltd', '360 ONE WAM Ltd', '360 ONE WAM Ltd', 'Aditya Birla Real Estate Ltd', 'Aditya Birla Real Estate Ltd', 'Aditya Birla Real Estate Ltd'],
        'Debt-Equity Ratio': [0.43, 0.43, 0.43, 0.27, 0.27, 0.27]
    })
    
    result = company_summary(sample_data)
    print(result)
