import polars as pl
import pandas as pd
from datetime import datetime

def track_data_by_tab(df, step_name):
    """Track data counts by source tab at each processing step"""
    print(f"\n--- {step_name} ---")
    if 'Source_Tab' in df.columns:
        tab_counts = df.group_by('Source_Tab').len().sort('Source_Tab')
        print(tab_counts)
        
        # Specifically check for our missing tabs
        missing_tabs = ['2010-2015', '2020-2025']
        for tab in missing_tabs:
            count = df.filter(pl.col('Source_Tab') == tab).height
            if count == 0:
                print(f"⚠️  {tab}: 0 rows (DATA LOST)")
            else:
                print(f"✓ {tab}: {count} rows")
    else:
        print(f"Total rows: {df.height}")
    return df

def process_excel_file_with_tracking(file_path):
    """Original process_excel_file but with detailed tracking"""
    
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
        if expected in available_tabs:
            tabs_to_process.append(expected)
        else:
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
        print(f"\nProcessing tab: {tab}")
        
        try:
            tab_df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
            print(f"  Raw data shape: {tab_df.shape}")
            
            if tab_df.height == 0:
                print(f"  Warning: Tab {tab} is empty")
                continue
            
            # Clean column names
            cleaned_columns = [col.strip() for col in tab_df.columns]
            tab_df.columns = cleaned_columns
            
            # Add source tab identifier
            tab_df = tab_df.with_columns(pl.lit(tab).alias('Source_Tab'))
            
            # Get all columns except Company Name
            value_cols = [col for col in tab_df.columns if col not in ['Company Name', 'Source_Tab']]
            print(f"  Value columns count: {len(value_cols)}")
            
            # Sample some column names to check format
            sample_cols = value_cols[:5]
            print(f"  Sample columns: {sample_cols}")
            
            # Check for date pattern
            date_cols = [col for col in value_cols if any(month in col for month in ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])]
            print(f"  Date-like columns: {len(date_cols)}")
            
            # Melt/unpivot the data
            melted = tab_df.unpivot(
                index=['Company Name', 'Source_Tab'], 
                on=value_cols,
                variable_name='Column', 
                value_name='Value'
            )
            print(f"  After unpivot shape: {melted.shape}")
            
            # Check for non-null values
            non_null_count = melted.filter(pl.col('Value').is_not_null()).height
            print(f"  Non-null values: {non_null_count}")
            
            all_tab_data.append(melted)
            print(f"  ✓ Successfully processed tab: {tab}")
            
        except Exception as e:
            print(f"  ERROR processing tab {tab}: {e}")
            continue
    
    if not all_tab_data:
        raise ValueError("No data could be read from any tabs")
    
    # Stack all tabs vertically
    print(f"\nCombining {len(all_tab_data)} tabs...")
    combined_df = pl.concat(all_tab_data)
    
    # Track data after combining
    combined_df = track_data_by_tab(combined_df, "AFTER COMBINING TABS")
    
    return combined_df

def extract_dates_and_metrics_with_tracking(df):
    """Extract dates with detailed tracking of what gets filtered out"""
    
    print("\n=== STEP 2: EXTRACTING DATES AND METRICS ===")
    
    # Show sample columns before processing
    print("Sample column values before extraction:")
    sample_columns = df.select('Column').unique().limit(10)
    for col in sample_columns.to_series().to_list():
        print(f"  '{col}'")
    
    # Track data before extraction
    df = track_data_by_tab(df, "BEFORE DATE EXTRACTION")
    
    # Extract month/year and metric from column headers
    df = df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    # Check what failed extraction by tab
    print("\nChecking failed extractions by tab:")
    failed_by_tab = df.filter(pl.col('Month_Year').is_null()).group_by('Source_Tab').agg([
        pl.count().alias('Failed_Count'),
        pl.col('Column').unique().alias('Sample_Failed_Columns')
    ])
    
    if failed_by_tab.height > 0:
        print("Failed extractions by tab:")
        print(failed_by_tab)
        
        # Show specific failed columns for our target tabs
        for tab in ['2010-2015', '2020-2025']:
            tab_failures = df.filter(
                (pl.col('Source_Tab') == tab) & 
                (pl.col('Month_Year').is_null())
            ).select('Column').unique().limit(5)
            
            if tab_failures.height > 0:
                print(f"\nFailed columns in {tab}:")
                for col in tab_failures.to_series().to_list():
                    print(f"  '{col}'")
    
    # Filter out rows where date extraction failed
    df = df.filter(pl.col('Month_Year').is_not_null())
    
    # Track data after filtering
    df = track_data_by_tab(df, "AFTER DATE EXTRACTION")
    
    if df.height == 0:
        raise ValueError("No data with valid dates found")
    
    return df

def pivot_and_convert_dates_with_tracking(df):
    """Pivot with tracking"""
    
    df = track_data_by_tab(df, "BEFORE PIVOT")
    
    # Pivot efficiently using Polars
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
        print(f"After pivot shape: {pivoted.shape}")
        
    except Exception as e:
        print(f"ERROR during pivot: {e}")
        # Check if pivot fails for specific tabs
        for tab in ['2010-2015', '2020-2025']:
            tab_data = df.filter(pl.col('Source_Tab') == tab)
            if tab_data.height > 0:
                print(f"Tab {tab} data before pivot: {tab_data.height} rows")
                print(f"Unique metrics in {tab}: {tab_data.select('Metric').unique().height}")
        raise
    
    # Convert dates
    pivoted = pivoted.with_columns([
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').dt.timestamp().cast(pl.Int64).floordiv(86400000000).add(25569).alias('Date')
    ])
    
    pivoted = track_data_by_tab(pivoted, "AFTER PIVOT AND DATE CONVERSION")
    
    return pivoted

def apply_business_logic_with_tracking(df):
    """Apply business logic with tracking"""
    
    df = track_data_by_tab(df, "BEFORE BUSINESS LOGIC")
    
    # Check which required columns we have
    required_base_cols = ['Market Capitalisation', '365 days Low Price', 'Adjusted Closing Price']
    missing_cols = [col for col in required_base_cols if col not in df.columns]
    
    if missing_cols:
        print(f"Missing required columns: {missing_cols}")
        print("Available columns:")
        for col in df.columns:
            print(f"  '{col}'")
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Calculate the ratio
    df = df.with_columns([
        (pl.col('365 days Low Price').fill_null(0) / 
         pl.when(pl.col('Adjusted Closing Price').fill_null(0) != 0)
         .then(pl.col('Adjusted Closing Price').fill_null(0))
         .otherwise(1)).alias('Ratio')
    ])
    
    # Track before filtering
    print("\nBefore filtering invalid data:")
    for tab in ['2010-2015', '2020-2025']:
        tab_data = df.filter(pl.col('Source_Tab') == tab)
        if tab_data.height > 0:
            valid_market_cap = tab_data.filter(
                (pl.col('Market Capitalisation').is_not_null()) &
                (pl.col('Market Capitalisation') > 0)
            ).height
            print(f"{tab}: {tab_data.height} total, {valid_market_cap} with valid market cap")
    
    # Filter out invalid data
    df = df.filter(
        (pl.col('Market Capitalisation').is_not_null()) &
        (pl.col('Market Capitalisation') > 0) &
        (pl.col('365 days Low Price').is_not_null()) &
        (pl.col('365 days Low Price') > 0) &
        (pl.col('Adjusted Closing Price').is_not_null()) &
        (pl.col('Adjusted Closing Price') > 0)
    )
    
    df = track_data_by_tab(df, "AFTER FILTERING INVALID DATA")
    
    if df.height == 0:
        raise ValueError("No valid data after filtering")
    
    # Calculate market cap percentiles
    df = df.with_columns([
        ((pl.col('Market Capitalisation').rank() / df.height) * 100).alias('Market_Cap_Percentile')
    ])
    
    # Filter to bottom 5th percentile
    df_filtered = df.filter(pl.col('Market_Cap_Percentile') <= 5)
    
    df_filtered = track_data_by_tab(df_filtered, "AFTER PERCENTILE FILTERING (Bottom 5%)")
    
    return df_filtered

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        print("🔍 TRACKING DATA PROCESSING FOR MISSING TABS")
        print("=" * 60)
        
        # Step 1: Process Excel file
        combined_df = process_excel_file_with_tracking(file_path)
        
        # Step 2: Extract dates and metrics
        df_extracted = extract_dates_and_metrics_with_tracking(combined_df)
        
        # Step 3: Pivot and convert dates
        df_pivoted = pivot_and_convert_dates_with_tracking(df_extracted)
        
        # Step 4: Apply business logic
        df_filtered = apply_business_logic_with_tracking(df_pivoted)
        
        # Final summary
        print("\n" + "=" * 60)
        print("🎯 FINAL SUMMARY")
        print("=" * 60)
        
        final_summary = df_filtered.group_by('Source_Tab').len().sort('Source_Tab')
        print("Final data by tab:")
        print(final_summary)
        
        # Check specifically for our missing tabs
        for tab in ['2010-2015', '2020-2025']:
            count = df_filtered.filter(pl.col('Source_Tab') == tab).height
            if count == 0:
                print(f"❌ {tab}: NO DATA in final output")
            else:
                print(f"✅ {tab}: {count} rows in final output")
        
        # Save intermediate files for inspection
        print("\nSaving debug files...")
        combined_df.write_csv("debug_1_combined.csv")
        df_extracted.write_csv("debug_2_extracted.csv")
        df_pivoted.write_csv("debug_3_pivoted.csv")
        df_filtered.write_csv("debug_4_filtered.csv")
        
        print("Debug files saved:")
        print("  - debug_1_combined.csv")
        print("  - debug_2_extracted.csv") 
        print("  - debug_3_pivoted.csv")
        print("  - debug_4_filtered.csv")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
