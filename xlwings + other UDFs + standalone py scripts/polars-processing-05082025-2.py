import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import calendar
import time

# Configuration
file_path = "2000-2025-22072025.xlsx"
output_file = 'ranking_results_04082025.xlsx'

print("Starting Excel processing...")

# Add after line: print("Starting Excel processing...")
start_time = time.time()
print(f"Script started at: {time.strftime('%H:%M:%S')}")

# STEP 1: Load Excel file and identify tabs to process
print("\nSTEP 1: Loading Excel file and identifying tabs...")
excel_file = pd.ExcelFile(file_path)
print(f"Available tabs: {excel_file.sheet_names}")

tabs_to_process = []
expected_tabs = ['2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2025']

for expected in expected_tabs:
    if expected in excel_file.sheet_names:
        tabs_to_process.append(expected)
        print(f"Found exact match: {expected}")
    else:
        # Look for similar tab names
        similar = [tab for tab in excel_file.sheet_names if expected.replace('-', '') in tab.replace('-', '')]
        if similar:
            tabs_to_process.append(similar[0])
            print(f"Found similar tab: {similar[0]} for expected {expected}")

print(f"Tabs to process: {tabs_to_process}")

# STEP 2: Load and combine data from all tabs
print("\nSTEP 2: Loading and combining data from all tabs...")
all_tab_data = []

for tab in tabs_to_process:
    print(f"Processing tab: {tab}")
    try:
        # Read tab data
        tab_df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
        
        if tab_df.height == 0:
            print(f"  - Tab {tab} is empty, skipping")
            continue
        
        # Clean column names
        tab_df.columns = [col.strip() for col in tab_df.columns]
        
        # Add source tab information
        tab_df = tab_df.with_columns(pl.lit(tab).alias('Source_Tab'))
        
        # Identify value columns (all except Company Name and Source_Tab)
        value_cols = [col for col in tab_df.columns if col not in ['Company Name', 'Source_Tab']]
        print(f"  - Value columns found: {len(value_cols)}")
        
        # Melt the dataframe (unpivot)
        melted = tab_df.unpivot(
            index=['Company Name', 'Source_Tab'], 
            on=value_cols, 
            variable_name='Column', 
            value_name='Value'
        )
        
        all_tab_data.append(melted)
        print(f"  - Successfully processed {melted.height} rows from {tab}")
        
    except Exception as e:
        print(f"  - Error processing tab {tab}: {e}")
        continue

if not all_tab_data:
    raise ValueError("No data found in any tabs")

# Combine all tab data
print("Combining all tab data...")
combined_df = pl.concat(all_tab_data)
print(f"Total combined rows: {combined_df.height}")

step2_time = time.time()
print(f"⏱️  Step 2 completed in: {(step2_time - start_time)/60:.2f} minutes")

# STEP 3: Parse month/year and metrics from column names
print("\nSTEP 3: Parsing month/year and metrics from column names...")

# Extract month/year pattern (e.g., "Mar 2000") from column names
df = combined_df.with_columns([
    pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
    pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
]).filter(pl.col('Month_Year').is_not_null())

print(f"Rows after parsing month/year: {df.height}")
unique_months = df.select('Month_Year').unique().sort('Month_Year')
print(f"Unique months found: {unique_months.height}")

# STEP 4: Pivot data to get metrics as columns
print("\nSTEP 4: Pivoting data to get metrics as columns...")
pivoted = df.pivot(
    values='Value', 
    index=['Company Name', 'Month_Year', 'Source_Tab'], 
    on='Metric'
)
print(f"Pivoted data shape: {pivoted.height} rows x {len(pivoted.columns)} columns")
print(f"Available columns: {pivoted.columns}")
# Add after: print(f"Available columns: {pivoted.columns}")
step4_time = time.time()
print(f"⏱️  Step 4 (Pivoting) completed in: {(step4_time - step2_time)/60:.2f} minutes")

# STEP 5: Handle date column conversions
print("\nSTEP 5: Converting date columns...")

if 'Date' in pivoted.columns:
    print("Converting main Date column...")
    pivoted = pivoted.with_columns([
        pl.when(pl.col('Date').is_not_null())
        .then(
            pl.when(pl.col('Date').cast(pl.Float64) > 1e15)
            .then((pl.col('Date').cast(pl.Float64) / 86400000000000).cast(pl.Int64) + 25569)
            .when(pl.col('Date').cast(pl.Float64) > 1e12)
            .then((pl.col('Date').cast(pl.Float64) / 86400000).cast(pl.Int64) + 25569)
            .when(pl.col('Date').cast(pl.Float64) > 1e9)
            .then((pl.col('Date').cast(pl.Float64) / 86400).cast(pl.Int64) + 25569)
            .when((pl.col('Date').cast(pl.Float64) >= 1) & (pl.col('Date').cast(pl.Float64) <= 100000))
            .then(pl.col('Date').cast(pl.Int64))
            .otherwise(pl.col('Date').cast(pl.Int64))
        ).otherwise(pl.col('Date')).alias('Date')
    ])

# Handle other date columns (365 days low price date)
date_columns = [col for col in pivoted.columns if '365 days low price date' in col.lower()]
print(f"Found {len(date_columns)} additional date columns: {date_columns}")

for date_col in date_columns:
    print(f"Converting date column: {date_col}")
    pivoted = pivoted.with_columns([
        pl.when(pl.col(date_col).is_not_null())
        .then(
            pl.when(pl.col(date_col).cast(pl.Float64) > 1e15)
            .then((pl.col(date_col).cast(pl.Float64) / 86400000000000).cast(pl.Int64) + 25569)
            .when(pl.col(date_col).cast(pl.Float64) > 1e12)
            .then((pl.col(date_col).cast(pl.Float64) / 86400000).cast(pl.Int64) + 25569)
            .when(pl.col(date_col).cast(pl.Float64) > 1e9)
            .then((pl.col(date_col).cast(pl.Float64) / 86400).cast(pl.Int64) + 25569)
            .when((pl.col(date_col).cast(pl.Float64) >= 1) & (pl.col(date_col).cast(pl.Float64) <= 100000))
            .then(pl.col(date_col).cast(pl.Int64))
            .otherwise(pl.col(date_col).cast(pl.Int64))
        ).otherwise(pl.col(date_col)).alias(date_col)
    ])

if 'Date' not in pivoted.columns:
    print("ERROR: No Date column found!")
    exit(1)

# STEP 6: Identify required columns
print("\nSTEP 6: Identifying required columns...")

adj_close_candidates = [col for col in pivoted.columns if any(pattern in col.lower() for pattern in ['adjusted closing price', '30 days avg. closing'])]
low_price_candidates = [col for col in pivoted.columns if '365 days low price' in col.lower() and 'date' not in col.lower()]
low_price_date_candidates = [col for col in pivoted.columns if '365 days low price date' in col.lower()]
market_cap_candidates = [col for col in pivoted.columns if any(pattern in col.lower() for pattern in ['market capitalisation', '30 days avg. market cap.'])]

#adj_close_candidates = [col for col in pivoted.columns if 'adjusted closing price' in col.lower()]
#low_price_candidates = [col for col in pivoted.columns if '365 days low price' in col.lower() and 'date' not in col.lower()]
#low_price_date_candidates = [col for col in pivoted.columns if '365 days low price date' in col.lower()]
#market_cap_candidates = [col for col in pivoted.columns if 'market capitalisation' in col.lower()]

print(f"Adjusted close candidates: {adj_close_candidates}")
print(f"Low price candidates: {low_price_candidates}")
print(f"Low price date candidates: {low_price_date_candidates}")
print(f"Market cap candidates: {market_cap_candidates}")

if not adj_close_candidates or not low_price_candidates or not market_cap_candidates:
    print("ERROR: Required columns not found!")
    print(f"Available columns: {pivoted.columns}")
#    step6_time = time.time()
#    print(f"⏱️  Step 6 (Pivoting) completed in: {(step6_time - step2_time)/60:.2f} minutes")
    exit(1)
step6_time = time.time()
print(f"⏱️  Step 6 (Pivoting) completed in: {(step6_time - step4_time)/60:.2f} minutes")
adj_close_col = adj_close_candidates[0]
low_price_col = low_price_candidates[0]
low_price_date_col = low_price_date_candidates[0] if low_price_date_candidates else None
market_cap_col = market_cap_candidates[0]

print(f"Using columns:")
print(f"  - Adjusted Close: {adj_close_col}")
print(f"  - Low Price: {low_price_col}")
print(f"  - Low Price Date: {low_price_date_col}")
print(f"  - Market Cap: {market_cap_col}")

# STEP 7: Filter to last trading day of each month
print("\nSTEP 7: Filtering to last trading day of each month...")

df_pandas_all = pivoted.to_pandas()
unique_months = df_pandas_all['Month_Year'].unique()
print(f"Processing {len(unique_months)} unique months...")

filtered_data = []

for month_year in unique_months:
    month_data = df_pandas_all[df_pandas_all['Month_Year'] == month_year]
    
    # Find the most common date in this month (likely the last trading day)
    try:
        last_trading_day = month_data['Date'].value_counts().index[0] if len(month_data) > 0 else None
    except:
        last_trading_day = None
    
    if last_trading_day is not None:
        month_filtered = month_data[month_data['Date'] == last_trading_day]
        filtered_data.append(month_filtered)
        print(f"  - {month_year}: {len(month_filtered)} companies on date {last_trading_day}")

if not filtered_data:
    print("ERROR: No filtered data found!")
    exit(1)

df_filtered = pl.from_pandas(pd.concat(filtered_data, ignore_index=True))
print(f"Total filtered rows: {df_filtered.height}")

# STEP 8: Clean data and remove invalid entries
print("\nSTEP 8: Cleaning data and removing invalid entries...")

df_clean_initial = df_filtered.filter(
    (pl.col(adj_close_col).is_not_null()) & (pl.col(adj_close_col) > 0) &
    (pl.col(low_price_col).is_not_null()) & (pl.col(low_price_col) > 0) &
    (pl.col(market_cap_col).is_not_null()) & (pl.col(market_cap_col) > 0)
).with_columns([
    pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').alias('Month_Year_Date')
]).sort(['Month_Year_Date', 'Source_Tab']).unique(
    subset=['Company Name', 'Month_Year', 'Source_Tab'], 
    keep='last'
)

print(f"Rows after cleaning: {df_clean_initial.height}")

# STEP 9: Calculate market cap 95th percentiles for filtering
print("\nSTEP 9: Calculating 95th percentile market cap thresholds...")

df_clean_pandas = df_clean_initial.to_pandas()
market_cap_percentiles_list = []

for (month_year, source_tab), group in df_clean_pandas.groupby(['Month_Year', 'Source_Tab']):
    market_cap_values = group[market_cap_col].tolist()
    
    # Excel PERCENTILE.INC equivalent calculation
    clean_values = []
    for v in market_cap_values:
        if v is not None and not pd.isna(v) and v > 0:
            clean_values.append(v)
    
    if clean_values:
        clean_values = sorted(clean_values)
        n = len(clean_values)
        k = 0.95  # 95th percentile
        
        if k == 0:
            percentile_95th = clean_values[0]
        elif k == 1:
            percentile_95th = clean_values[-1]
        else:
            rank = k * (n - 1) + 1
            rank_int = int(rank)
            rank_frac = rank - rank_int
            
            if rank_int >= n:
                percentile_95th = clean_values[-1]
            elif rank_int < 1:
                percentile_95th = clean_values[0]
            else:
                lower_val = clean_values[rank_int - 1]
                upper_val = clean_values[rank_int] if rank_int < n else clean_values[rank_int - 1]
                percentile_95th = lower_val + rank_frac * (upper_val - lower_val)
    else:
        percentile_95th = None
    
    market_cap_percentiles_list.append({
        'Month_Year': month_year,
        'Source_Tab': source_tab,
        'Market_Cap_95th_Percentile': percentile_95th
    })
    print(f"  - {month_year} ({source_tab}): {len(clean_values)} valid companies, 95th percentile = {f'{percentile_95th:.2e}' if percentile_95th is not None else 'N/A'}")
    #print(f"  - {month_year} ({source_tab}): {len(clean_values)} valid companies, 95th percentile = {percentile_95th:.2e if percentile_95th else 'N/A'}")
    
    # Debug info for March 2000
    if month_year == 'Mar 2000':
        print(f"    DEBUG - March 2000 details:")
        print(f"    Total companies: {len(group)}")
        print(f"    Valid market caps: {len(clean_values)}")
        if clean_values:
            print(f"    Market cap range: {min(clean_values):.2e} to {max(clean_values):.2e}")

market_cap_percentiles = pl.from_pandas(pd.DataFrame(market_cap_percentiles_list))

# Add after: market_cap_percentiles = pl.from_pandas(pd.DataFrame(market_cap_percentiles_list))
step9_time = time.time()
print(f"⏱️  Step 9 (Percentiles) completed in: {(step9_time - step6_time)/60:.2f} minutes")

# STEP 10: Filter companies by market cap (top 5% only)
print("\nSTEP 10: Filtering companies by market cap (top 5% only)...")

df_with_market_cap_filter = df_clean_initial.join(
    market_cap_percentiles, on=['Month_Year', 'Source_Tab'], how='left'
).filter(pl.col(market_cap_col) >= pl.col('Market_Cap_95th_Percentile'))

print(f"Companies after market cap filter: {df_with_market_cap_filter.height}")

# STEP 11: Calculate price ratios
print("\nSTEP 11: Calculating price ratios (current/low)...")

df_with_ratio = df_with_market_cap_filter.with_columns([
    (pl.col(adj_close_col) / pl.when(pl.col(low_price_col) != 0).then(pl.col(low_price_col)).otherwise(1)).alias('Ratio')
])

print("Ratio calculation completed")

# STEP 12: Process each time period for rankings
print("\nSTEP 12: Processing rankings for each time period...")

unique_periods = df_with_ratio.select(['Month_Year', 'Source_Tab', 'Month_Year_Date']).unique().sort(['Source_Tab', 'Month_Year_Date'])
print(f"Processing {unique_periods.height} unique periods...")

# Add after: print(f"Processing {unique_periods.height} unique periods...")
step12_time = time.time()
print(f"⏱️  Steps 1-12 (Polars territory) completed in: {(step12_time - start_time)/60:.2f} minutes")

top30_results = []
bottom30_results = []

for period_row in unique_periods.iter_rows():
    month_year, source_tab, month_year_date = period_row
    
    period_data = df_with_ratio.filter(
        (pl.col('Month_Year') == month_year) & (pl.col('Source_Tab') == source_tab)
    ).unique(subset=['Company Name'], keep='first')
    
    if period_data.height == 0:
        continue
    
    sorted_data = period_data.sort('Ratio', descending=False)
    total_companies = period_data.height
    
    print(f"  - {month_year} ({source_tab}): {total_companies} companies")
    
    # Calculate top/bottom 30% counts
    top_30_pct_count = max(1, int(total_companies * 0.30))
    bottom_30_pct_count = max(1, int(total_companies * 0.30))
    
   # Replace the existing odd/even handling code with:
    # Calculate top/bottom 30% counts
    # For odd numbers, add 1 before calculating 30%
    adjusted_count = total_companies + 1 if total_companies % 2 == 1 else total_companies
    top_30_pct_count = max(1, int(adjusted_count * 0.30))
    bottom_30_pct_count = max(1, int(adjusted_count * 0.30))
    
    # Ensure we don't exceed total companies
    top_30_pct_count = min(top_30_pct_count, total_companies)
    bottom_30_pct_count = min(bottom_30_pct_count, total_companies)
    
    # Get first 30% (lowest ratios due to ascending sort) - label as Bottom30%
    top_30_pct = sorted_data.head(top_30_pct_count).with_columns([
        pl.lit('Top30%').alias('Ranking_Category'),
        pl.int_range(1, top_30_pct_count + 1).alias('Rank')
    ])
    
    # Get last 30% (highest ratios due to ascending sort) - label as Top30%
    bottom_30_pct = sorted_data.tail(bottom_30_pct_count).with_columns([
        pl.lit('Bottom30%').alias('Ranking_Category'),
        pl.int_range(1, bottom_30_pct_count + 1).alias('Rank')
    ]) 
    
    top30_results.append(top_30_pct)
    bottom30_results.append(bottom_30_pct)
    
    print(f"    Top 30%: {top_30_pct.height} companies, Bottom 30%: {bottom_30_pct.height} companies")

if not top30_results:
    print("ERROR: No ranking results generated!")
    exit(1)

# STEP 13: Combine all results
print("\nSTEP 13: Combining all ranking results...")

final_results = [pl.concat(top30_results)]
if bottom30_results:
    final_results.append(pl.concat(bottom30_results))

rankings_df = pl.concat(final_results)
print(f"Total ranking results: {rankings_df.height}")

# STEP 14: Sort and prepare final data
print("\nSTEP 14: Sorting and preparing final data...")

df_sorted = rankings_df.sort(
    ['Source_Tab', 'Month_Year_Date', 'Ranking_Category', 'Rank'], 
    descending=[False, False, True, False]
)

df_pandas = df_sorted.to_pandas()

# Handle Date column - convert month/year to Excel serial if needed
if 'Date' not in df_pandas.columns or df_pandas['Date'].isna().all():
    print("Converting Month_Year to Excel serial dates...")
    def month_year_to_excel_serial(month_year):
        try:
            date_obj = datetime.strptime(month_year, '%b %Y')
            last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
            return int((date_obj.replace(day=last_day) - datetime(1899, 12, 30)).days)
        except:
            return None
    
    df_pandas['Date'] = df_pandas['Month_Year'].apply(month_year_to_excel_serial)

df_pandas['Date'] = df_pandas['Date'].fillna(0).astype(int)

# Handle low price date column
if low_price_date_col and low_price_date_col in df_pandas.columns:
    df_pandas[low_price_date_col] = df_pandas[low_price_date_col].fillna(0).astype(int)
    df_pandas = df_pandas.rename(columns={low_price_date_col: '365_days_Low_Price_Date'})
else:
    df_pandas['365_days_Low_Price_Date'] = 0

# STEP 15: Select final columns
print("\nSTEP 15: Selecting final columns...")

columns_to_include = ['Company Name', 'Date', adj_close_col, market_cap_col]

# Add total returns column if available
for col in df_pandas.columns:
    if any(pattern in col.lower() for pattern in ['total returns', '30 days avg. returns over a period']): #'total returns' in col.lower():
        columns_to_include.append(col)
        print(f"Found total returns column: {col}")
        break

# Add remaining required columns
columns_to_include.extend([
    low_price_col, 
    '365_days_Low_Price_Date', 
    'Month_Year', 
    'Source_Tab', 
    'Ratio', 
    'Ranking_Category', 
    'Rank'
])

if 'Market_Cap_95th_Percentile' in df_pandas.columns:
    columns_to_include.append('Market_Cap_95th_Percentile')

final_columns = [col for col in columns_to_include if col in df_pandas.columns]
df_final = df_pandas[final_columns].copy()

print(f"Final columns: {final_columns}")
print(f"Final data shape: {df_final.shape}")

# STEP 16: Export to Excel
print("\nSTEP 16: Exporting to Excel...")

with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # All rankings
    df_final.to_excel(writer, sheet_name='All_Rankings', index=False)
    print(f"  - All_Rankings: {len(df_final)} rows")
    
    # Top 30% only
    top30_data = df_final[df_final['Ranking_Category'] == 'Top30%']
    top30_data.to_excel(writer, sheet_name='Top30%_Rankings', index=False)
    print(f"  - Top30%_Rankings: {len(top30_data)} rows")
    
    # Bottom 30% only
    bottom30_data = df_final[df_final['Ranking_Category'] == 'Bottom30%']
    bottom30_data.to_excel(writer, sheet_name='Bottom30%_Rankings', index=False)
    print(f"  - Bottom30%_Rankings: {len(bottom30_data)} rows")

print(f"\n✅ SUCCESS: Results exported to {output_file}")
print(f"Total processing completed with {len(df_final)} total rows")

# STEP 17: Summary statistics
print("\nSTEP 17: Summary Statistics...")
print(f"Unique companies processed: {df_final['Company Name'].nunique()}")
print(f"Unique time periods: {df_final['Month_Year'].nunique()}")
print(f"Top 30% companies: {len(df_final[df_final['Ranking_Category'] == 'Top30%'])}")
print(f"Bottom 30% companies: {len(df_final[df_final['Ranking_Category'] == 'Bottom30%'])}")

# Show sample of final data
print(f"\nSample of final data:")
print(df_final.head())

# Add after: print(df_final.head())
step17_time = time.time()
print(f"⏱️  Steps 13-17 (Rankings) completed in: {(step17_time - step12_time)/60:.2f} minutes")
# REPLACE STEP 18 onwards with the following code:
# COMPLETELY REPLACE everything from Step 18 onwards with this code:

print("\nSTEP 18: Preparing data for group-based compounding calculation...")

# Use df_final from Step 17 as base (25582 rows) - this contains the filtered companies we want
base_data = df_final.copy()
print(f"Base data rows: {len(base_data)} (should be 25582)")

# Use COMPLETE data from Step 6 for returns lookup
complete_data = pivoted.to_pandas()  # Convert to pandas for easier manipulation
print(f"Complete data rows from Step 6: {len(complete_data)}")

# Identify the returns column in COMPLETE data
returns_col = None
for col in complete_data.columns:
    if any(pattern in col.lower() for pattern in ['total returns', '30 days avg. returns over a period']):
        returns_col = col
        print(f"Found returns column in complete data: {returns_col}")
        break

if returns_col is None:
    print("ERROR: No returns column found in complete data!")
    exit(1)

# Convert Month_Year to datetime for both datasets
base_data['Month_Year_Date'] = pd.to_datetime(base_data['Month_Year'], format='%b %Y')
complete_data['Month_Year_Date'] = pd.to_datetime(complete_data['Month_Year'], format='%b %Y')

# Check actual data range
print(f"Base data date range: {base_data['Month_Year_Date'].min()} to {base_data['Month_Year_Date'].max()}")
print(f"Complete data date range: {complete_data['Month_Year_Date'].min()} to {complete_data['Month_Year_Date'].max()}")

# For 6-month GM: if data goes to Jan 2025, we can calculate up to Jun 2024
# For 12-month GM: if data goes to Jan 2025, we can calculate up to Dec 2023
last_data_month = complete_data['Month_Year_Date'].max()
last_6m_month = pd.to_datetime('2024-06-01')  # Jun 2024
last_12m_month = pd.to_datetime('2023-12-01')  # Dec 2023

print(f"Last data month: {last_data_month}")
print(f"Last calculable month for 6M: {last_6m_month}")
print(f"Last calculable month for 12M: {last_12m_month}")

print("\nSTEP 19: Creating returns lookup from COMPLETE data for ranked companies...")

# Create returns matrix from COMPLETE data but only for companies that appear in df_final
ranked_companies = set(base_data['Company Name'].unique())
print(f"Unique companies in df_final: {len(ranked_companies)}")

# Filter complete data to only include ranked companies
complete_data_filtered = complete_data[complete_data['Company Name'].isin(ranked_companies)]
print(f"Complete data filtered to ranked companies: {len(complete_data_filtered)} rows")

# Create returns matrix from filtered complete data
complete_returns_matrix = complete_data_filtered.pivot_table(
    index='Month_Year_Date', 
    columns='Company Name', 
    values=returns_col, 
    aggfunc='first'
).sort_index()

print(f"Returns matrix shape: {complete_returns_matrix.shape}")
print(f"Date range: {complete_returns_matrix.index.min()} to {complete_returns_matrix.index.max()}")

print("\nSTEP 20: Calculating monthly group averages for future periods...")

# Create a dictionary to store monthly differences
monthly_group_averages = {}

# Get all unique months from ranking data (df_final)
unique_months = sorted(base_data['Month_Year_Date'].unique())

for current_month in unique_months:
    print(f"Processing {current_month.strftime('%b %Y')}")
    
    # Get Top30% and Bottom30% companies for this month from df_final
    current_month_data = base_data[base_data['Month_Year_Date'] == current_month]
    
    top30_companies = current_month_data[current_month_data['Ranking_Category'] == 'Top30%']['Company Name'].tolist()
    bottom30_companies = current_month_data[current_month_data['Ranking_Category'] == 'Bottom30%']['Company Name'].tolist()
    
    print(f"  Top30%: {len(top30_companies)} companies, Bottom30%: {len(bottom30_companies)} companies")
    
    # Find current month in returns matrix
    if current_month not in complete_returns_matrix.index:
        print(f"  WARNING: {current_month.strftime('%b %Y')} not found in returns matrix")
        continue
        
    current_idx = complete_returns_matrix.index.get_loc(current_month)
    
    # Skip next month, start from month after next
    start_idx = current_idx + 2
    
    # Store monthly differences for this starting month
    monthly_differences = []
    
    # Calculate for next 24 months (covers both 6M and 12M)
    for future_idx in range(start_idx, min(start_idx + 24, len(complete_returns_matrix.index))):
        future_month = complete_returns_matrix.index[future_idx]
        
        # Get the group averages for this future month from base_data (df_final)
        future_month_data = base_data[base_data['Month_Year_Date'] == future_month]
        
        if len(future_month_data) > 0:
            # Get returns column name
            returns_col_final = None
            for col in base_data.columns:
                if any(pattern in col.lower() for pattern in ['total returns', '30 days avg. returns over a period']):
                    returns_col_final = col
                    break
            
            if returns_col_final:
                # Calculate group averages for this future month
                top30_future_data = future_month_data[future_month_data['Ranking_Category'] == 'Top30%']
                bottom30_future_data = future_month_data[future_month_data['Ranking_Category'] == 'Bottom30%']
                
                top30_avg = top30_future_data[returns_col_final].mean() if len(top30_future_data) > 0 else 0
                bottom30_avg = bottom30_future_data[returns_col_final].mean() if len(bottom30_future_data) > 0 else 0
                
                # Handle NaN values
                top30_avg = 0 if pd.isna(top30_avg) else top30_avg
                bottom30_avg = 0 if pd.isna(bottom30_avg) else bottom30_avg
            else:
                top30_avg = 0
                bottom30_avg = 0
        else:
            top30_avg = 0
            bottom30_avg = 0
        
        # Calculate difference: Top30% - Bottom30%
        difference = top30_avg - bottom30_avg
        monthly_differences.append(difference)
        
        if future_idx - start_idx < 6:  # Show first 6 months for debugging
            print(f"    {future_month.strftime('%b %Y')}: Top30%={top30_avg:.9f}, Bottom30%={bottom30_avg:.9f}, Diff={difference:.9f}")
    
    # Store all monthly differences for this starting month
    monthly_group_averages[current_month] = monthly_differences

print(f"Monthly differences calculated for {len(monthly_group_averages)} months")

# STEP 21: Calculating 6-month group compounding returns
print("\nSTEP 21: Calculating 6-month group compounding returns...")

base_data['Group_Compounding_6M'] = 0.0
base_data['Periods_Used_6M'] = 0
base_data['Group_Average_6M'] = 0.0
base_data['Group_Difference_6M'] = 0.0

for idx, row in base_data.iterrows():
    current_month = row['Month_Year_Date']
    
    # Skip calculation if beyond Jun 2024 for 6M
    if current_month > last_6m_month:
        continue
    
    if current_month in monthly_group_averages:
        differences = monthly_group_averages[current_month][:6]  # First 6 differences
        
        if len(differences) >= 6:
            # Simple compounding: (1+r1)*(1+r2)*...*(1+r6) - 1
            compound_factor = 1.0
            valid_periods = 0
            
            for diff in differences:
                compound_factor *= (1 + diff)
                valid_periods += 1
            
            cumulative_return = compound_factor - 1
            
            base_data.at[idx, 'Group_Compounding_6M'] = cumulative_return
            base_data.at[idx, 'Periods_Used_6M'] = valid_periods

print("6-month group compounding calculation completed.")

# STEP 22: Filtering and exporting 6-month results
print("\nSTEP 22: Filtering and exporting 6-month results...")

# Create filtered dataset for 6M (remove data after June 2024)
base_data_6m_filtered = base_data[base_data['Month_Year_Date'] <= last_6m_month].copy()
print(f"Rows after June 2024 filter: {len(base_data_6m_filtered)}")

# Remove Month_Year_Date column for export
base_data_6m_filtered_export = base_data_6m_filtered.drop(columns=['Month_Year_Date']).copy()

# Export filtered 6M data
output_file_6m_filtered = 'compounding_return_6months_group_04082025_FIXED.xlsx'
base_data_6m_filtered_export.to_excel(output_file_6m_filtered, index=False)
print(f"Filtered 6-month group compounding results exported to {output_file_6m_filtered}")

# STEP 23: Calculating 12-month group compounding returns
print("\nSTEP 23: Calculating 12-month group compounding returns...")

# Remove 6M columns and add 12M columns
base_data = base_data.drop(columns=['Group_Compounding_6M', 'Periods_Used_6M'])

# Add new columns for 12M calculations
base_data['Group_Compounding_12M'] = 0.0
base_data['Periods_Used_12M'] = 0

for idx, row in base_data.iterrows():
    current_month = row['Month_Year_Date']
    
    # Skip calculation if beyond Dec 2023 for 12M
    if current_month > last_12m_month:
        continue
    
    if current_month in monthly_group_averages:
        differences = monthly_group_averages[current_month][:12]  # First 12 differences
        
        if len(differences) >= 12:
            # Simple compounding: (1+r1)*(1+r2)*...*(1+r12) - 1
            compound_factor = 1.0
            valid_periods = 0
            
            for diff in differences:
                compound_factor *= (1 + diff)
                valid_periods += 1
            
            cumulative_return = compound_factor - 1
            
            base_data.at[idx, 'Group_Compounding_12M'] = cumulative_return
            base_data.at[idx, 'Periods_Used_12M'] = valid_periods

print("12-month group compounding calculation completed.")

# STEP 24: Filtering and exporting 12-month results
print("\nSTEP 24: Filtering and exporting 12-month results...")

# Create filtered dataset for 12M (remove data after December 2023)  
base_data_12m_filtered = base_data[base_data['Month_Year_Date'] <= last_12m_month].copy()
print(f"Rows after December 2023 filter: {len(base_data_12m_filtered)}")

# Remove Month_Year_Date column for export
base_data_12m_filtered_export = base_data_12m_filtered.drop(columns=['Month_Year_Date']).copy()

# Export filtered 12M data
output_file_12m_filtered = 'compounding_return_12months_group_04082025_FIXED.xlsx'
base_data_12m_filtered_export.to_excel(output_file_12m_filtered, index=False)
print(f"Filtered 12-month group compounding results exported to {output_file_12m_filtered}")

print(f"\nFinal summary:")
print(f"Base data (Step 17): {len(df_final)} rows")
print(f"6M group compounding data: {len(base_data_6m_filtered_export)} rows")
print(f"12M group compounding data: {len(base_data_12m_filtered_export)} rows")

# Add timing
total_time = time.time()
print(f"\n⏱️  TOTAL EXECUTION TIME: {(total_time - start_time)/60:.2f} minutes")
print(f"   - Data processing (Steps 1-17): {(step17_time - start_time)/60:.2f} min")
print(f"   - Group compounding (Steps 18+): {(total_time - step17_time)/60:.2f} min")
