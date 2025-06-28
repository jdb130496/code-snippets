import polars as pl
import pandas as pd
from datetime import datetime

def analyze_problem_tabs(file_path):
    """Focus specifically on the 2010-2015 and 2020-2025 tabs to find the issue"""
    
    print("🔍 FOCUSED ANALYSIS OF PROBLEM TABS")
    print("=" * 60)
    
    problem_tabs = ['2010-2015', '2020-2025']
    working_tabs = ['2000-2005', '2005-2010', '2015-2020']  # These work fine
    
    tab_data = {}
    
    # Read all tabs for comparison
    for tab in problem_tabs + working_tabs:
        try:
            print(f"\n=== ANALYZING TAB: {tab} ===")
            df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
            
            # Clean column names
            cleaned_columns = [col.strip() for col in df.columns]
            df.columns = cleaned_columns
            
            print(f"Raw data shape: {df.shape}")
            print(f"Companies: {df.height}")
            
            # Check for required columns
            required_cols = ['Market Capitalisation', '365 days Low Price', 'Adjusted Closing Price']
            available_cols = df.columns
            
            print(f"\nColumn Analysis:")
            for req_col in required_cols:
                if req_col in available_cols:
                    print(f"  ✓ {req_col}: FOUND")
                else:
                    print(f"  ❌ {req_col}: MISSING")
                    # Look for similar columns
                    similar = [col for col in available_cols if any(word in col.lower() for word in req_col.lower().split())]
                    if similar:
                        print(f"    Similar columns: {similar[:3]}")
            
            # Store processed data
            df = df.with_columns(pl.lit(tab).alias('Source_Tab'))
            value_cols = [col for col in df.columns if col not in ['Company Name', 'Source_Tab']]
            
            melted = df.unpivot(
                index=['Company Name', 'Source_Tab'], 
                on=value_cols,
                variable_name='Column', 
                value_name='Value'
            )
            
            # Extract dates and metrics
            melted = melted.with_columns([
                pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
                pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
            ])
            
            melted = melted.filter(pl.col('Month_Year').is_not_null())
            
            # Pivot
            pivoted = melted.pivot(
                values='Value',
                index=['Company Name', 'Month_Year', 'Source_Tab'], 
                on='Metric'
            )
            
            # Convert dates
            pivoted = pivoted.with_columns([
                pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').dt.timestamp().cast(pl.Int64).floordiv(86400000000).add(25569).alias('Date')
            ])
            
            tab_data[tab] = pivoted
            print(f"Processed data shape: {pivoted.shape}")
            
        except Exception as e:
            print(f"ERROR processing {tab}: {e}")
            tab_data[tab] = None
    
    # Now analyze the filtering step in detail
    print("\n" + "=" * 60)
    print("🔍 DETAILED FILTERING ANALYSIS")
    print("=" * 60)
    
    for tab in problem_tabs + working_tabs:
        if tab_data[tab] is None:
            continue
            
        df = tab_data[tab]
        print(f"\n=== FILTERING ANALYSIS FOR {tab} ===")
        print(f"Starting rows: {df.height}")
        
        # Check each required column exists and has data
        required_cols = ['Market Capitalisation', '365 days Low Price', 'Adjusted Closing Price']
        
        for col in required_cols:
            if col not in df.columns:
                print(f"❌ CRITICAL: Column '{col}' not found!")
                print(f"   Available columns: {sorted(df.columns)}")
                continue
            
            # Analyze this column in detail
            total_rows = df.height
            not_null_rows = df.filter(pl.col(col).is_not_null()).height
            greater_than_zero = df.filter((pl.col(col).is_not_null()) & (pl.col(col) > 0)).height
            
            print(f"\n📊 Column: {col}")
            print(f"   Total rows: {total_rows}")
            print(f"   Not null: {not_null_rows} ({not_null_rows/total_rows*100:.1f}%)")
            print(f"   > 0: {greater_than_zero} ({greater_than_zero/total_rows*100:.1f}%)")
            
            # Show sample values
            sample_data = df.select([col]).limit(10)
            sample_values = sample_data.to_series().to_list()
            print(f"   Sample values: {sample_values}")
            
            # Check data types
            dtype = df.select(col).dtypes[0]
            print(f"   Data type: {dtype}")
            
            # Check for common issues
            if dtype == pl.Utf8:  # String type
                print(f"   ⚠️  WARNING: Column is string type, not numeric!")
                # Try to see what string values we have
                unique_strings = df.select(col).unique().limit(5).to_series().to_list()
                print(f"   Sample string values: {unique_strings}")
        
        # Now apply the actual filter and see what happens
        print(f"\n🔬 STEP-BY-STEP FILTERING:")
        
        step_df = df
        print(f"   Start: {step_df.height} rows")
        
        # Filter 1: Market Cap
        if 'Market Capitalisation' in step_df.columns:
            step_df = step_df.filter(
                (pl.col('Market Capitalisation').is_not_null()) &
                (pl.col('Market Capitalisation') > 0)
            )
            print(f"   After Market Cap filter: {step_df.height} rows")
        
        # Filter 2: Low Price  
        if '365 days Low Price' in step_df.columns:
            step_df = step_df.filter(
                (pl.col('365 days Low Price').is_not_null()) &
                (pl.col('365 days Low Price') > 0)
            )
            print(f"   After Low Price filter: {step_df.height} rows")
        
        # Filter 3: Adjusted Close
        if 'Adjusted Closing Price' in step_df.columns:
            step_df = step_df.filter(
                (pl.col('Adjusted Closing Price').is_not_null()) &
                (pl.col('Adjusted Closing Price') > 0)
            )
            print(f"   After Adjusted Close filter: {step_df.height} rows")
        
        if step_df.height == 0:
            print(f"   ❌ ALL DATA ELIMINATED for {tab}")
        else:
            print(f"   ✓ {step_df.height} rows survive filtering for {tab}")

def compare_column_structures(file_path):
    """Compare column structures between working and problem tabs"""
    
    print("\n" + "=" * 60)
    print("📋 COLUMN STRUCTURE COMPARISON")
    print("=" * 60)
    
    problem_tabs = ['2010-2015', '2020-2025']
    working_tabs = ['2000-2005', '2005-2010', '2015-2020']
    
    all_metrics = set()
    tab_metrics = {}
    
    for tab in problem_tabs + working_tabs:
        try:
            df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
            cleaned_columns = [col.strip() for col in df.columns]
            
            # Extract unique metrics from column names
            metrics = set()
            for col in cleaned_columns:
                if col != 'Company Name':
                    # Remove the date part to get the metric
                    metric = col
                    # Try to remove month/year pattern
                    import re
                    metric = re.sub(r'^\w{3} \d{4} ', '', metric)
                    metrics.add(metric)
            
            tab_metrics[tab] = metrics
            all_metrics.update(metrics)
            
            print(f"\n{tab}: {len(metrics)} unique metrics")
            
        except Exception as e:
            print(f"Error reading {tab}: {e}")
    
    # Find metrics that are missing from problem tabs
    print(f"\n📊 METRIC COMPARISON:")
    
    # Get metrics from working tabs
    working_metrics = set()
    for tab in working_tabs:
        if tab in tab_metrics:
            working_metrics.update(tab_metrics[tab])
    
    # Check what's missing from problem tabs
    for tab in problem_tabs:
        if tab not in tab_metrics:
            continue
            
        print(f"\n{tab}:")
        missing_metrics = working_metrics - tab_metrics[tab]
        extra_metrics = tab_metrics[tab] - working_metrics
        
        if missing_metrics:
            print(f"  Missing metrics: {sorted(list(missing_metrics))}")
        else:
            print(f"  ✓ Has all working tab metrics")
            
        if extra_metrics:
            print(f"  Extra metrics: {sorted(list(extra_metrics))}")

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        analyze_problem_tabs(file_path)
        compare_column_structures(file_path)
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
