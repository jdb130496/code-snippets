import polars as pl
import pandas as pd
from datetime import datetime

# Read ALL 5 tabs and process each
tabs = ['2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2025']
df_list = []

for tab in tabs:
    print(f"Processing tab: {tab}")
    # Read each tab
    tab_df = pl.from_pandas(pd.read_excel('2000-2025-new.xlsx', sheet_name=tab))
    print(f"  Raw data shape: {tab_df.shape}")
    
    # Clean column names by removing leading/trailing spaces
    tab_df.columns = [col.strip() for col in tab_df.columns]
    
    # Get all columns except Company Name
    value_cols = [col for col in tab_df.columns if col != 'Company Name']
    print(f"  Value columns count: {len(value_cols)}")
    
    # Sample of column structure
    print(f"  Sample columns: {value_cols[:5]}")
    
    # Use the standard melt/unpivot approach but with better date extraction
    melted = tab_df.unpivot(
        index=['Company Name'], 
        on=value_cols,
        variable_name='Column', 
        value_name='Value'
    )
    print(f"  After unpivot shape: {melted.shape}")
    
    # Extract month/year and metric from column headers using string operations
    # Expected format: "Jan 2000 Market Capitalisation"
    melted = melted.with_columns([
        # Extract the first two parts as date (e.g., "Jan 2000")
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        # Extract everything after the date as metric
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    # Filter out rows where date extraction failed
    melted = melted.filter(pl.col('Month_Year').is_not_null())
    print(f"  After date extraction: {melted.shape}")
    
    if melted.height == 0:
        print(f"  No data with valid dates in tab {tab}")
        continue
    
    # Show unique dates for verification
    unique_dates = melted.select('Month_Year').unique().sort('Month_Year')
    print(f"  Unique dates ({unique_dates.height}): {unique_dates.head(5).to_series().to_list()} ... {unique_dates.tail(5).to_series().to_list()}")
    
    # Pivot efficiently using Polars
    print("  Pivoting data...")
    try:
        pivoted = melted.pivot(
            values='Value',
            index=['Company Name', 'Month_Year'], 
            on='Metric'
        )
        print(f"  After pivot shape: {pivoted.shape}")
        
        # Show available metrics
        metric_cols = [col for col in pivoted.columns if col not in ['Company Name', 'Month_Year']]
        print(f"  Available metrics: {metric_cols}")
        
        df_list.append(pivoted)
        
    except Exception as e:
        print(f"  ERROR during pivot: {e}")
        continue

if len(df_list) == 0:
    print("No data to process - all tabs failed")
    exit()

print(f"\nCombining {len(df_list)} dataframes...")

# Combine data from ALL tabs with outer join to handle missing columns
df = pl.concat(df_list, how='diagonal')
print(f"Combined data shape: {df.shape}")

# Convert Month_Year to proper date and Excel serial number
print("Converting dates...")
df = df.with_columns([
    # Parse the date string to actual date, then convert to Excel serial
    pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').dt.timestamp().cast(pl.Int64).floordiv(86400000000).add(25569).alias('Date')
])

# Show date range
min_date = df.select('Date').min().item()
max_date = df.select('Date').max().item()
print(f"Date range: {min_date} to {max_date} (Excel serial)")

# Convert back to readable dates for verification
try:
    min_readable = datetime(1900, 1, 1) + pd.Timedelta(days=min_date - 2)
    max_readable = datetime(1900, 1, 1) + pd.Timedelta(days=max_date - 2)
    print(f"Date range (readable): {min_readable.strftime('%Y-%m-%d')} to {max_readable.strftime('%Y-%m-%d')}")
except:
    pass

# Check available columns
print(f"Available columns: {df.columns}")

# Map to standard column names - handle variations
column_variations = {
    'Market Capitalisation': 'Market Capitalisation',
    '365 days Low Price': '365 days Low Price', 
    'Adjusted Closing Price': 'Adjusted Closing Price',
    'Total Returns (%)': 'Total Returns (%)',
    '365 days Low Price Date': '365 days Low Price Date'
}

# Check which required columns we have
required_base_cols = ['Market Capitalisation', '365 days Low Price', 'Adjusted Closing Price']
missing_cols = [col for col in required_base_cols if col not in df.columns]

if missing_cols:
    print(f"Missing required columns: {missing_cols}")
    print("Available columns that might contain the data:")
    for col in df.columns:
        if any(keyword in col.lower() for keyword in ['market', 'cap', 'price', 'close']):
            print(f"  - {col}")
    exit()

print("Calculating ratios and filtering data...")

# Calculate the ratio
df = df.with_columns([
    (pl.col('365 days Low Price').fill_null(0) / 
     pl.when(pl.col('Adjusted Closing Price').fill_null(0) != 0)
     .then(pl.col('Adjusted Closing Price').fill_null(0))
     .otherwise(1)).alias('Ratio')
])

# Filter out invalid data
df = df.filter(
    (pl.col('Market Capitalisation').is_not_null()) &
    (pl.col('Market Capitalisation') > 0) &
    (pl.col('365 days Low Price').is_not_null()) &
    (pl.col('365 days Low Price') > 0) &
    (pl.col('Adjusted Closing Price').is_not_null()) &
    (pl.col('Adjusted Closing Price') > 0)
)

print(f"After filtering: {df.shape}")

if df.height == 0:
    print("No valid data after filtering")
    exit()

# Calculate market cap percentiles
print("Calculating percentiles...")
df = df.with_columns([
    ((pl.col('Market Capitalisation').rank() / df.height) * 100).alias('Market_Cap_Percentile')
])

# Filter to bottom 5th percentile
df_filtered = df.filter(pl.col('Market_Cap_Percentile') <= 5)
print(f"Companies in bottom 5th percentile: {df_filtered.height}")

if df_filtered.height == 0:
    print("No companies in bottom 5th percentile")
    exit()

# Process each date group to get top/bottom 30
print("Processing top/bottom 30 for each date...")
result_list = []

# Get unique dates and process each
unique_dates = df_filtered.select('Date').unique().sort('Date')
print(f"Processing {unique_dates.height} unique dates...")

for i in range(unique_dates.height):
    date_val = unique_dates.row(i)[0]
    
    # Get companies for this date
    group = df_filtered.filter(pl.col('Date') == date_val)
    
    if group.height < 2:
        continue
    
    # Sort by ratio
    sorted_group = group.sort('Ratio')
    n_companies = sorted_group.height
    
    # Get top and bottom companies
    top_n = min(30, n_companies // 2)
    bottom_n = min(30, n_companies - top_n)
    
    if top_n > 0:
        top30 = sorted_group.tail(top_n).with_columns(pl.lit('Top 30').alias('Top_Bottom_30'))
        result_list.append(top30)
    
    if bottom_n > 0:
        bottom30 = sorted_group.head(bottom_n).with_columns(pl.lit('Bottom 30').alias('Top_Bottom_30'))
        result_list.append(bottom30)
    
    # Progress indicator
    if (i + 1) % 50 == 0:
        print(f"  Processed {i + 1}/{unique_dates.height} dates...")

if len(result_list) == 0:
    print("No results generated")
    exit()

print("Combining final results...")
final_df = pl.concat(result_list)

# Prepare final output
output_cols = [
    pl.col('Company Name'),
    pl.col('Month_Year'),
    pl.col('Date').cast(pl.Int32),
    pl.col('Market Capitalisation').fill_null(0).alias('Market_Capitalization'),
    pl.col('Adjusted Closing Price').fill_null(0).alias('Adj_Close_Price'),
    pl.col('365 days Low Price').fill_null(0).alias('Low_Price'),
    pl.col('Ratio'),
    pl.col('Market_Cap_Percentile').round(2).alias('Percentile'),
    pl.col('Top_Bottom_30')
]

# Add optional columns if available
if 'Total Returns (%)' in final_df.columns:
    output_cols.insert(-2, pl.col('Total Returns (%)').fill_null(0).alias('Total_Returns'))

# Handle the problematic '365 days Low Price Date' column
if '365 days Low Price Date' in final_df.columns:
    print("Processing '365 days Low Price Date' column...")
    
    # First, let's examine what the values look like
    sample_values = final_df.select('365 days Low Price Date').filter(
        pl.col('365 days Low Price Date').is_not_null()
    ).head(5)
    print(f"Sample Low Price Date values: {sample_values}")
    
    # Try different conversion approaches based on the data format
    try:
        # Option 1: If these are already Excel serial numbers (large floats)
        # Convert directly to int, handling potential overflow
        date_col = (
            pl.when(pl.col('365 days Low Price Date').is_null())
            .then(0)
            .when(pl.col('365 days Low Price Date') > 2958465)  # Excel max date ~8000 AD
            .then(0)  # Set invalid dates to 0
            .when(pl.col('365 days Low Price Date') < 1)  # Excel min date
            .then(0)  # Set invalid dates to 0
            .otherwise(pl.col('365 days Low Price Date').round().cast(pl.Int32))
            .alias('Low_Price_Date')
        )
        
        # Test the conversion
        test_df = final_df.head(10).with_columns(date_col)
        print("Date conversion test successful - using Excel serial approach")
        
    except Exception as e1:
        print(f"Excel serial approach failed: {e1}")
        try:
            # Option 2: If these are timestamps, convert to Excel serial
            date_col = (
                pl.when(pl.col('365 days Low Price Date').is_null())
                .then(0)
                .otherwise(
                    # Convert timestamp to Excel serial (assuming milliseconds)
                    (pl.col('365 days Low Price Date').cast(pl.Int64) / 86400000 + 25569).round().cast(pl.Int32)
                )
                .alias('Low_Price_Date')
            )
            
            # Test the conversion
            test_df = final_df.head(10).with_columns(date_col)
            print("Date conversion test successful - using timestamp approach")
            
        except Exception as e2:
            print(f"Timestamp approach also failed: {e2}")
            # Option 3: Fallback - just set all to 0
            date_col = pl.lit(0).alias('Low_Price_Date')
            print("Using fallback approach - setting all Low_Price_Date to 0")
    
    output_cols.insert(-2, date_col)

# Create final output
output = final_df.select(output_cols).sort(['Date', 'Top_Bottom_30', 'Company Name'], descending=[False, True, False])

print(f"Final output shape: {output.shape}")

# Show final date range
final_min_date = output.select('Date').min().item()
final_max_date = output.select('Date').max().item()
try:
    final_min_readable = datetime(1900, 1, 1) + pd.Timedelta(days=final_min_date - 2)
    final_max_readable = datetime(1900, 1, 1) + pd.Timedelta(days=final_max_date - 2)
    print(f"Final date range: {final_min_readable.strftime('%Y-%m-%d')} to {final_max_readable.strftime('%Y-%m-%d')}")
except:
    print(f"Final date range: {final_min_date} to {final_max_date}")

# Write output
output.write_excel('processed_output.xlsx', worksheet='Summary')
print("Output written to processed_output.xlsx")

# Show sample of final data
print("\nSample of final data:")
print(output.head(10))
