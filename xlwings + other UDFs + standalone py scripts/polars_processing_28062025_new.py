import polars as pl
import pandas as pd
from datetime import datetime

def process_excel_file(file_path):
    """Process Excel file by stacking all tabs first, then applying business logic"""
    
    # First, let's check what tabs actually exist in the file
    print("=== STEP 1: CHECKING AVAILABLE TABS ===")
    try:
        excel_file = pd.ExcelFile(file_path)
        available_tabs = excel_file.sheet_names
        print(f"Available tabs in Excel file: {available_tabs}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise
    
    # Define expected tabs and find matches
    expected_tabs = ['2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2025']
    tabs_to_process = []
    
    for expected in expected_tabs:
        # Try exact match first
        if expected in available_tabs:
            tabs_to_process.append(expected)
        else:
            # Try to find similar names
            similar = [tab for tab in available_tabs if expected.replace('-', '') in tab.replace('-', '')]
            if similar:
                print(f"Found similar tab for {expected}: {similar[0]}")
                tabs_to_process.append(similar[0])
            else:
                print(f"Warning: Could not find tab for {expected}")
    
    print(f"Tabs to process: {tabs_to_process}")
    
    all_tab_data = []
    
    print("\n=== STEP 1: READING AND STACKING ALL TABS ===")
    
    for tab in tabs_to_process:
        print(f"Processing tab: {tab}")
        
        # Read each tab
        try:
            tab_df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
            print(f"  Raw data shape: {tab_df.shape}")
            
            if tab_df.height == 0:
                print(f"  Warning: Tab {tab} is empty")
                continue
            
            # Clean column names by removing leading/trailing spaces
            cleaned_columns = [col.strip() for col in tab_df.columns]
            tab_df.columns = cleaned_columns
            
            # Add source tab identifier
            tab_df = tab_df.with_columns(pl.lit(tab).alias('Source_Tab'))
            
            # Get all columns except Company Name
            value_cols = [col for col in tab_df.columns if col not in ['Company Name', 'Source_Tab']]
            print(f"  Value columns count: {len(value_cols)}")
            print(f"  Sample columns: {value_cols[:5]}")
            
            # Melt/unpivot the data
            melted = tab_df.unpivot(
                index=['Company Name', 'Source_Tab'], 
                on=value_cols,
                variable_name='Column', 
                value_name='Value'
            )
            print(f"  After unpivot shape: {melted.shape}")
            
            all_tab_data.append(melted)
            print(f"  Successfully processed tab: {tab}")
            
        except Exception as e:
            print(f"  ERROR processing tab {tab}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    if not all_tab_data:
        raise ValueError("No data could be read from any tabs")
    
    # Stack all tabs vertically
    print(f"\nCombining {len(all_tab_data)} tabs...")
    combined_df = pl.concat(all_tab_data)
    print(f"Combined raw data shape: {combined_df.shape}")
    
    # Show which tabs contributed data
    tab_summary = combined_df.group_by('Source_Tab').len().sort('Source_Tab')
    print("Data by source tab:")
    print(tab_summary)
    
    return combined_df

def extract_dates_and_metrics(df):
    """Extract month/year and metric from column headers"""
    
    print("\n=== STEP 2: EXTRACTING DATES AND METRICS ===")
    
    # Extract month/year and metric from column headers
    df = df.with_columns([
        # Extract the first two parts as date (e.g., "Jan 2000")
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        # Extract everything after the date as metric
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    # Filter out rows where date extraction failed
    df = df.filter(pl.col('Month_Year').is_not_null())
    print(f"After date extraction: {df.shape}")
    
    if df.height == 0:
        raise ValueError("No data with valid dates found")
    
    # Show unique dates and metrics for verification
    unique_dates = df.select('Month_Year').unique().sort('Month_Year')
    unique_metrics = df.select('Metric').unique().sort('Metric')
    
    print(f"Unique dates ({unique_dates.height}): {unique_dates.head(3).to_series().to_list()} ... {unique_dates.tail(3).to_series().to_list()}")
    print(f"Unique metrics ({unique_metrics.height}): {unique_metrics.to_series().to_list()}")
    
    return df

def standardize_metric_names(df):
    """Standardize metric names across different tabs"""
    
    print("\n=== STEP 2.5: STANDARDIZING METRIC NAMES ===")
    
    # Create mapping for standardizing metric names
    metric_mapping = {
        '365 days First Closing': '365 days Low Price',  # Map First Closing to Low Price for consistency
        '365 days First Closing Date': '365 days Low Price Date',
        # Add other mappings as needed
    }
    
    # Apply the mapping
    df = df.with_columns([
        pl.col('Metric').map_elements(
            lambda x: metric_mapping.get(x, x), 
            return_dtype=pl.Utf8
        ).alias('Metric')
    ])
    
    # Show the mapping that was applied
    print("Applied metric name mappings:")
    for old, new in metric_mapping.items():
        count = df.filter(pl.col('Metric') == new).height
        if count > 0:
            print(f"  {old} -> {new} ({count} records)")
    
    # Show final unique metrics
    unique_metrics = df.select('Metric').unique().sort('Metric')
    print(f"Final unique metrics ({unique_metrics.height}): {unique_metrics.to_series().to_list()}")
    
    return df

def pivot_and_convert_dates(df):
    """Pivot data and convert dates to Excel serial format"""
    
    print("\n=== STEP 3: PIVOTING DATA ===")
    
    # Pivot efficiently using Polars
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
        print(f"After pivot shape: {pivoted.shape}")
        
        # Show available metrics
        metric_cols = [col for col in pivoted.columns if col not in ['Company Name', 'Month_Year', 'Source_Tab']]
        print(f"Available metrics: {metric_cols}")
        
    except Exception as e:
        print(f"ERROR during pivot: {e}")
        raise
    
    print("\n=== STEP 4: CONVERTING DATES ===")
    
    # Convert Month_Year to proper date and Excel serial number
    pivoted = pivoted.with_columns([
        # Parse the date string to actual date, then convert to Excel serial
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').dt.timestamp().cast(pl.Int64).floordiv(86400000000).add(25569).alias('Date')
    ])
    
    # Show date range
    min_date = pivoted.select('Date').min().item()
    max_date = pivoted.select('Date').max().item()
    print(f"Date range: {min_date} to {max_date} (Excel serial)")
    
    # Convert back to readable dates for verification
    try:
        min_readable = datetime(1900, 1, 1) + pd.Timedelta(days=min_date - 2)
        max_readable = datetime(1900, 1, 1) + pd.Timedelta(days=max_date - 2)
        print(f"Date range (readable): {min_readable.strftime('%Y-%m-%d')} to {max_readable.strftime('%Y-%m-%d')}")
    except:
        pass
    
    return pivoted

def apply_business_logic(df):
    """Apply the same business logic as original script with flexible column handling"""
    
    print("\n=== STEP 5: APPLYING BUSINESS LOGIC ===")
    
    # Check available columns
    print(f"Available columns: {df.columns}")
    
    # Check which required columns we have - be flexible about naming
    required_cols = {
        'market_cap': None,
        'low_price': None,
        'adj_close': None
    }
    
    # Find market cap column
    market_cap_candidates = [col for col in df.columns if 'market' in col.lower() and 'cap' in col.lower()]
    if market_cap_candidates:
        required_cols['market_cap'] = market_cap_candidates[0]
        print(f"Found market cap column: {required_cols['market_cap']}")
    
    # Find low price column
    low_price_candidates = [col for col in df.columns if '365 days low price' in col.lower()]
    if low_price_candidates:
        required_cols['low_price'] = low_price_candidates[0]
        print(f"Found low price column: {required_cols['low_price']}")
    
    # Find adjusted closing price column
    adj_close_candidates = [col for col in df.columns if 'adjusted closing price' in col.lower()]
    if adj_close_candidates:
        required_cols['adj_close'] = adj_close_candidates[0]
        print(f"Found adjusted close column: {required_cols['adj_close']}")
    
    # Check if we have all required columns
    missing_types = [key for key, col in required_cols.items() if col is None]
    if missing_types:
        print(f"Missing column types: {missing_types}")
        print("Available columns:")
        for col in df.columns:
            print(f"  - {col}")
        raise ValueError(f"Cannot find required columns for: {missing_types}")
    
    print("Calculating ratios and filtering data...")
    
    # Calculate the ratio using the found column names
    df = df.with_columns([
        (pl.col(required_cols['low_price']).fill_null(0) / 
         pl.when(pl.col(required_cols['adj_close']).fill_null(0) != 0)
         .then(pl.col(required_cols['adj_close']).fill_null(0))
         .otherwise(1)).alias('Ratio')
    ])
    
    # Filter out invalid data using the found column names
    df = df.filter(
        (pl.col(required_cols['market_cap']).is_not_null()) &
        (pl.col(required_cols['market_cap']) > 0) &
        (pl.col(required_cols['low_price']).is_not_null()) &
        (pl.col(required_cols['low_price']) > 0) &
        (pl.col(required_cols['adj_close']).is_not_null()) &
        (pl.col(required_cols['adj_close']) > 0)
    )
    
    print(f"After filtering: {df.shape}")
    
    if df.height == 0:
        raise ValueError("No valid data after filtering")
    
    # Calculate market cap percentiles
    print("Calculating percentiles...")
    df = df.with_columns([
        ((pl.col(required_cols['market_cap']).rank() / df.height) * 100).alias('Market_Cap_Percentile')
    ])
    
    # Filter to bottom 5th percentile
    df_filtered = df.filter(pl.col('Market_Cap_Percentile') <= 5)
    print(f"Companies in bottom 5th percentile: {df_filtered.height}")
    
    if df_filtered.height == 0:
        raise ValueError("No companies in bottom 5th percentile")
    
    # Store the actual column names for later use
    df_filtered = df_filtered.with_columns([
        pl.lit(required_cols['market_cap']).alias('_market_cap_col'),
        pl.lit(required_cols['low_price']).alias('_low_price_col'),  
        pl.lit(required_cols['adj_close']).alias('_adj_close_col')
    ])
    
    return df_filtered

def get_top_bottom_30(df):
    """Process each date group to get top/bottom 30"""
    
    print("\n=== STEP 6: GETTING TOP/BOTTOM 30 FOR EACH DATE ===")
    
    result_list = []
    
    # Get unique dates and process each
    unique_dates = df.select('Date').unique().sort('Date')
    print(f"Processing {unique_dates.height} unique dates...")
    
    for i in range(unique_dates.height):
        date_val = unique_dates.row(i)[0]
        
        # Get companies for this date
        group = df.filter(pl.col('Date') == date_val)
        
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
        raise ValueError("No results generated")
    
    print("Combining final results...")
    final_df = pl.concat(result_list)
    
    return final_df

def prepare_final_output(df):
    """Prepare final output with proper column handling"""
    
    print("\n=== STEP 7: PREPARING FINAL OUTPUT ===")
    
    # Get the actual column names that were used
    market_cap_col = df.select('_market_cap_col').item(0, 0) if '_market_cap_col' in df.columns else 'Market Capitalisation'
    low_price_col = df.select('_low_price_col').item(0, 0) if '_low_price_col' in df.columns else '365 days Low Price'
    adj_close_col = df.select('_adj_close_col').item(0, 0) if '_adj_close_col' in df.columns else 'Adjusted Closing Price'
    
    print(f"Using columns:")
    print(f"  Market Cap: {market_cap_col}")
    print(f"  Low Price: {low_price_col}")
    print(f"  Adj Close: {adj_close_col}")
    
    # Find date columns (excluding our main Date column)
    date_columns = [col for col in df.columns if 'Date' in col and col != 'Date' and not col.startswith('_')]
    print(f"Found date columns to process: {date_columns}")
    
    # Filter out unwanted date columns
    wanted_date_columns = []
    for date_col in date_columns:
        # Skip columns we don't want in output
        if 'first_closing_date' in date_col.lower():
            print(f"  Skipping unwanted column: {date_col}")
            continue
        wanted_date_columns.append(date_col)
    
    print(f"Date columns to include: {wanted_date_columns}")
    
    # Create a working copy of the dataframe
    working_df = df.clone()
    
    # Process each wanted date column
    for date_col in wanted_date_columns:
        try:
            print(f"Processing date column: {date_col}")
            
            # Convert the problematic column to a safe integer format
            safe_name = date_col.replace(' ', '_').replace('(', '').replace(')', '')
            
            # Handle the conversion step by step
            working_df = working_df.with_columns([
                pl.when(pl.col(date_col).is_null())
                .then(0)
                .when(pl.col(date_col).is_nan())
                .then(0)
                .when(pl.col(date_col) > 1e15)  # Very large numbers (likely nanoseconds)
                .then((pl.col(date_col) / 1e9 / 86400 + 25569).round())
                .when(pl.col(date_col) > 2958465)  # Excel max date
                .then(0)
                .when(pl.col(date_col) < 1)  # Excel min date  
                .then(0)
                .otherwise(pl.col(date_col).fill_null(0).round())
                .alias(safe_name + '_temp')
            ])
            
            # Now safely cast to int32 with bounds checking
            working_df = working_df.with_columns([
                pl.when(pl.col(safe_name + '_temp') > 2147483647)  # Int32 max
                .then(0)
                .when(pl.col(safe_name + '_temp') < -2147483648)  # Int32 min
                .then(0)
                .otherwise(pl.col(safe_name + '_temp'))
                .cast(pl.Int32)
                .alias(safe_name)
            ])
            
            # Drop the temporary column
            working_df = working_df.drop(safe_name + '_temp')
            
            print(f"  Successfully processed {date_col} -> {safe_name}")
            
        except Exception as e:
            print(f"  Error processing {date_col}: {e}")
            # If conversion fails completely, just set to 0
            safe_name = date_col.replace(' ', '_').replace('(', '').replace(')', '')
            working_df = working_df.with_columns([pl.lit(0).cast(pl.Int32).alias(safe_name)])
            print(f"  Set {date_col} to constant 0")
    
    # Now prepare final output columns using the processed dataframe
    output_cols = [
        pl.col('Company Name'),
        pl.col('Month_Year'),
        pl.col('Date').cast(pl.Int32),
        pl.col(market_cap_col).fill_null(0).alias('Market_Capitalization'),
        pl.col(adj_close_col).fill_null(0).alias('Adj_Close_Price'),
        pl.col(low_price_col).fill_null(0).alias('Low_Price'),
        pl.col('Ratio'),
        pl.col('Market_Cap_Percentile').round(2).alias('Percentile'),
        pl.col('Top_Bottom_30'),
        pl.col('Source_Tab')  # Keep track of which tab data came from
    ]
    
    # Add optional columns if available
    if 'Total Returns (%)' in working_df.columns:
        output_cols.insert(-2, pl.col('Total Returns (%)').fill_null(0).alias('Total_Returns'))
    
    # Add only the wanted processed date columns
    for date_col in wanted_date_columns:
        safe_name = date_col.replace(' ', '_').replace('(', '').replace(')', '')
        if safe_name in working_df.columns:
            output_cols.insert(-1, pl.col(safe_name))
            print(f"  Added to output: {safe_name}")
    
    # Create final output
    print("Creating final output...")
    try:
        output = working_df.select(output_cols)
        print(f"Output created successfully: {output.shape}")
        
        # Try to sort
        output = output.sort(['Date', 'Top_Bottom_30', 'Company Name'], descending=[False, True, False])
        print(f"Sorted successfully")
        
    except Exception as e:
        print(f"Error creating/sorting output: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    # Show summary by source tab
    print("\nSummary by source tab:")
    try:
        summary = output.group_by("Source_Tab").len().sort("Source_Tab")
        print(summary)
    except Exception as e:
        print(f"Could not create summary: {e}")
    
    # Show final column names
    print(f"\nFinal columns: {output.columns}")
    
    return output

def main():
    file_path = "2000-2025-new.xlsx"  # Your file name
    
    try:
        # Step 1: Process Excel file (stack all tabs)
        combined_df = process_excel_file(file_path)
        
        # Step 2: Extract dates and metrics
        df_extracted = extract_dates_and_metrics(combined_df)
        
        # Step 2.5: Standardize metric names across tabs
        df_standardized = standardize_metric_names(df_extracted)
        
        # Step 3: Pivot and convert dates
        df_pivoted = pivot_and_convert_dates(df_standardized)
        
        # Step 4: Apply business logic (filtering, percentiles)
        df_filtered = apply_business_logic(df_pivoted)
        
        # Step 5: Get top/bottom 30 for each date
        df_top_bottom = get_top_bottom_30(df_filtered)
        
        # Step 6: Prepare final output
        final_output = prepare_final_output(df_top_bottom)
        
        if final_output is None:
            raise ValueError("Failed to create final output")
        
        # Step 7: Save results
        print(f"\n=== FINAL RESULTS ===")
        print(f"Final output shape: {final_output.shape}")
        
        # Show final date range
        final_min_date = final_output.select('Date').min().item()
        final_max_date = final_output.select('Date').max().item()
        try:
            final_min_readable = datetime(1900, 1, 1) + pd.Timedelta(days=final_min_date - 2)
            final_max_readable = datetime(1900, 1, 1) + pd.Timedelta(days=final_max_date - 2)
            print(f"Final date range: {final_min_readable.strftime('%Y-%m-%d')} to {final_max_readable.strftime('%Y-%m-%d')}")
        except:
            print(f"Final date range: {final_min_date} to {final_max_date}")
        
        # Save to CSV (avoids Excel row limit)
        csv_output = "processed_output_stacked_fixed.csv"
        final_output.write_csv(csv_output)
        print(f"Output written to {csv_output}")
        
        # Also save a smaller Excel version for convenience (first 1M rows)
        if final_output.height <= 1000000:
            try:
                final_pandas = final_output.to_pandas()
                excel_output = "processed_output_stacked_fixed.xlsx"
                final_pandas.to_excel(excel_output, index=False, engine='openpyxl')
                print(f"Excel output written to {excel_output}")
            except Exception as e:
                print(f"Could not create Excel file: {e}")
        else:
            print(f"Dataset too large for Excel ({final_output.height} rows). Use CSV file.")
        
        # Show sample of final data
        print("\nSample of final data:")
        print(final_output.head(5))
        
        # Show summary statistics
        print("\nSummary by tab and category:")
        summary_stats = final_output.group_by(['Source_Tab', 'Top_Bottom_30']).len().sort(['Source_Tab', 'Top_Bottom_30'])
        print(summary_stats)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
