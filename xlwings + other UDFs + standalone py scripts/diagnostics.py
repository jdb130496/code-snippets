import polars as pl
import pandas as pd
from datetime import datetime

def process_excel_file_debug(file_path):
    """Process Excel file with detailed debugging for missing companies"""
    
    print("=== STEP 1: READING EXCEL FILE WITH DEBUG INFO ===")
    try:
        excel_file = pd.ExcelFile(file_path)
        available_tabs = excel_file.sheet_names
        print(f"Available tabs: {available_tabs}")
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        raise
    
    # Focus on tabs that might contain 2000 data
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
    
    print(f"Tabs to process: {tabs_to_process}")
    
    all_tab_data = []
    softrak_found_in_tabs = []
    
    for tab in tabs_to_process:
        print(f"\nProcessing tab: {tab}")
        
        try:
            # Read raw data first
            raw_df = pd.read_excel(file_path, sheet_name=tab)
            print(f"  Raw shape: {raw_df.shape}")
            
            # Check for Softrak in this tab BEFORE any processing
            softrak_matches = raw_df[raw_df.iloc[:, 0].astype(str).str.contains('Softrak', case=False, na=False)]
            if len(softrak_matches) > 0:
                print(f"  *** FOUND SOFTRAK in tab {tab} ***")
                print(f"  Softrak entries: {len(softrak_matches)}")
                print(f"  Company names: {softrak_matches.iloc[:, 0].tolist()}")
                softrak_found_in_tabs.append(tab)
                
                # Show sample of columns for this tab
                print(f"  Sample columns: {raw_df.columns[:10].tolist()}")
                
                # Look for Jan 2000 data specifically
                jan_2000_cols = [col for col in raw_df.columns if 'Jan 2000' in str(col)]
                if jan_2000_cols:
                    print(f"  Jan 2000 columns found: {jan_2000_cols}")
                    for softrak_idx in softrak_matches.index:
                        print(f"    Softrak row {softrak_idx}:")
                        for col in jan_2000_cols[:3]:  # Show first 3 Jan 2000 columns
                            value = raw_df.loc[softrak_idx, col]
                            print(f"      {col}: {value}")
            
            # Convert to Polars and continue processing
            tab_df = pl.from_pandas(raw_df)
            
            if tab_df.height == 0:
                continue
            
            # Clean column names
            cleaned_columns = [col.strip() for col in tab_df.columns]
            tab_df.columns = cleaned_columns
            tab_df = tab_df.with_columns(pl.lit(tab).alias('Source_Tab'))
            
            # Unpivot
            value_cols = [col for col in tab_df.columns if col not in ['Company Name', 'Source_Tab']]
            melted = tab_df.unpivot(
                index=['Company Name', 'Source_Tab'], 
                on=value_cols,
                variable_name='Column', 
                value_name='Value'
            )
            
            all_tab_data.append(melted)
            
        except Exception as e:
            print(f"  ERROR processing tab {tab}: {e}")
            continue
    
    print(f"\nSoftrak found in tabs: {softrak_found_in_tabs}")
    
    if not all_tab_data:
        raise ValueError("No data could be read from any tabs")
    
    combined_df = pl.concat(all_tab_data)
    print(f"Combined data shape: {combined_df.shape}")
    
    return combined_df, softrak_found_in_tabs

def track_softrak_through_pipeline(df, company_name="Softrak Technology Exports Ltd."):
    """Track Softrak through each step of the data pipeline"""
    
    print(f"\n=== TRACKING {company_name} THROUGH PIPELINE ===")
    
    # Step 1: Check in raw combined data
    print("STEP 1: Raw combined data")
    softrak_raw = df.filter(pl.col("Company Name").str.contains("Softrak"))
    print(f"  Softrak entries in raw data: {len(softrak_raw)}")
    if len(softrak_raw) > 0:
        print("  Sample entries:")
        print(softrak_raw.head(3).select(["Company Name", "Source_Tab", "Column", "Value"]))
        
        # Check for exact name match
        exact_match = df.filter(pl.col("Company Name") == company_name)
        print(f"  Exact name matches: {len(exact_match)}")
        
        # Check for Jan 2000 data specifically
        jan_data = softrak_raw.filter(pl.col("Column").str.contains("Jan 2000"))
        print(f"  Jan 2000 entries: {len(jan_data)}")
        if len(jan_data) > 0:
            print("  Jan 2000 sample:")
            print(jan_data.head(5).select(["Company Name", "Column", "Value"]))
    
    # Step 2: After date extraction
    print("\nSTEP 2: After date extraction")
    df_with_dates = df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ]).filter(pl.col('Month_Year').is_not_null())
    
    softrak_dates = df_with_dates.filter(pl.col("Company Name").str.contains("Softrak"))
    print(f"  Softrak entries after date extraction: {len(softrak_dates)}")
    if len(softrak_dates) > 0:
        jan_2000_softrak = softrak_dates.filter(pl.col("Month_Year") == "Jan 2000")
        print(f"  Jan 2000 Softrak entries: {len(jan_2000_softrak)}")
        if len(jan_2000_softrak) > 0:
            print("  Jan 2000 Softrak data:")
            print(jan_2000_softrak.select(["Company Name", "Month_Year", "Metric", "Value"]))
    
    # Step 3: After pivoting
    print("\nSTEP 3: After pivoting")
    try:
        pivoted = df_with_dates.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
        
        softrak_pivoted = pivoted.filter(pl.col("Company Name").str.contains("Softrak"))
        print(f"  Softrak entries after pivot: {len(softrak_pivoted)}")
        
        if len(softrak_pivoted) > 0:
            jan_2000_pivoted = softrak_pivoted.filter(pl.col("Month_Year") == "Jan 2000")
            print(f"  Jan 2000 Softrak entries after pivot: {len(jan_2000_pivoted)}")
            
            if len(jan_2000_pivoted) > 0:
                print("  Available columns for Softrak:")
                print(f"    {pivoted.columns}")
                
                # Show the actual data
                print("  Jan 2000 Softrak pivoted data:")
                print(jan_2000_pivoted)
                
        return pivoted, softrak_pivoted
        
    except Exception as e:
        print(f"  Error during pivot: {e}")
        return None, None

def analyze_softrak_filtering(pivoted_df, softrak_data):
    """Analyze why Softrak might be filtered out"""
    
    if pivoted_df is None or len(softrak_data) == 0:
        print("\nNo pivoted data to analyze")
        return
    
    print(f"\n=== ANALYZING SOFTRAK FILTERING ===")
    
    # Find required columns
    market_cap_candidates = [col for col in pivoted_df.columns if 'market' in col.lower() and 'cap' in col.lower()]
    low_price_candidates = [col for col in pivoted_df.columns if '365 days low price' in col.lower()]
    adj_close_candidates = [col for col in pivoted_df.columns if 'adjusted closing price' in col.lower()]
    
    print(f"Market cap columns: {market_cap_candidates}")
    print(f"Low price columns: {low_price_candidates}")
    print(f"Adj close columns: {adj_close_candidates}")
    
    if not (market_cap_candidates and low_price_candidates and adj_close_candidates):
        print("Missing required columns for analysis")
        return
    
    market_cap_col = market_cap_candidates[0]
    low_price_col = low_price_candidates[0]
    adj_close_col = adj_close_candidates[0]
    
    # Focus on Jan 2000 data
    jan_2000_date = 36526  # Excel serial for Jan 2000
    pivoted_with_date = pivoted_df.with_columns([
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').dt.timestamp().cast(pl.Int64).floordiv(86400000000).add(25569).alias('Date')
    ])
    
    jan_data = pivoted_with_date.filter(pl.col('Date') == jan_2000_date)
    softrak_jan = jan_data.filter(pl.col("Company Name").str.contains("Softrak"))
    
    if len(softrak_jan) == 0:
        print("No Softrak data found for Jan 2000 after date conversion")
        return
    
    print(f"\nSoftrak Jan 2000 data found: {len(softrak_jan)}")
    
    # Check the values for Softrak
    for idx in range(len(softrak_jan)):
        row = softrak_jan.row(idx)
        company_name = row[0]  # Company Name is first column
        
        # Get column indices
        market_cap_idx = jan_data.columns.index(market_cap_col)
        low_price_idx = jan_data.columns.index(low_price_col)
        adj_close_idx = jan_data.columns.index(adj_close_col)
        
        market_cap = row[market_cap_idx]
        low_price = row[low_price_idx]
        adj_close = row[adj_close_idx]
        
        print(f"\nCompany: {company_name}")
        print(f"  Market Cap: {market_cap}")
        print(f"  Low Price: {low_price}")
        print(f"  Adj Close: {adj_close}")
        
        # Calculate ratio
        if adj_close and adj_close != 0:
            ratio = low_price / adj_close if low_price else 0
            print(f"  Calculated Ratio: {ratio}")
        else:
            print(f"  Cannot calculate ratio (adj_close is {adj_close})")
        
        # Check if it passes basic filters
        passes_not_null = market_cap is not None and low_price is not None and adj_close is not None
        passes_positive = (market_cap or 0) > 0 and (low_price or 0) > 0 and (adj_close or 0) > 0
        
        print(f"  Passes not-null filter: {passes_not_null}")
        print(f"  Passes positive filter: {passes_positive}")
    
    # Calculate 5th percentile for Jan 2000
    jan_clean = jan_data.filter(
        (pl.col(market_cap_col).is_not_null()) &
        (pl.col(market_cap_col) > 0) &
        (pl.col(low_price_col).is_not_null()) &
        (pl.col(low_price_col) > 0) &
        (pl.col(adj_close_col).is_not_null()) &
        (pl.col(adj_close_col) > 0)
    )
    
    print(f"\nJan 2000 clean companies: {len(jan_clean)}")
    
    if len(jan_clean) > 0:
        market_cap_5th = jan_clean.select(pl.col(market_cap_col).quantile(0.05)).item()
        print(f"5th percentile market cap: {market_cap_5th}")
        
        # Check if Softrak is below 5th percentile
        softrak_jan_clean = jan_clean.filter(pl.col("Company Name").str.contains("Softrak"))
        print(f"Softrak in clean data: {len(softrak_jan_clean)}")
        
        if len(softrak_jan_clean) > 0:
            softrak_market_cap = softrak_jan_clean.select(market_cap_col).item()
            print(f"Softrak market cap: {softrak_market_cap}")
            print(f"Is below 5th percentile: {softrak_market_cap < market_cap_5th}")
            
            if softrak_market_cap < market_cap_5th:
                # Softrak should be included - check final ranking
                small_cap = jan_clean.filter(pl.col(market_cap_col) < market_cap_5th)
                small_cap_with_ratio = small_cap.with_columns([
                    (pl.col(low_price_col) / pl.col(adj_close_col)).alias('Ratio')
                ])
                
                softrak_final = small_cap_with_ratio.filter(pl.col("Company Name").str.contains("Softrak"))
                if len(softrak_final) > 0:
                    softrak_ratio = softrak_final.select('Ratio').item()
                    print(f"Softrak final ratio: {softrak_ratio}")
                    
                    # Where would it rank?
                    sorted_small_cap = small_cap_with_ratio.sort('Ratio')
                    softrak_rank = None
                    for i in range(len(sorted_small_cap)):
                        if "Softrak" in sorted_small_cap.row(i)[0]:
                            softrak_rank = i + 1
                            break
                    
                    print(f"Softrak rank in sorted list: {softrak_rank}")
                    print(f"Should be in bottom 30: {softrak_rank <= 30}")
                    
                    # Show companies around Softrak's rank
                    if softrak_rank:
                        start_idx = max(0, softrak_rank - 5)
                        end_idx = min(len(sorted_small_cap), softrak_rank + 5)
                        print(f"\nCompanies around Softrak (rank {start_idx+1} to {end_idx}):")
                        around_softrak = sorted_small_cap.slice(start_idx, end_idx - start_idx)
                        for i, row in enumerate(around_softrak.rows()):
                            rank = start_idx + i + 1
                            company = row[0]
                            ratio = row[-1]  # Ratio is last column
                            marker = " <-- SOFTRAK" if "Softrak" in company else ""
                            print(f"  {rank:3d}. {company}: {ratio:.10f}{marker}")

def main():
    file_path = "2000-2025-new.xlsx"  # Update with your actual file path
    
    try:
        # Process with debugging
        combined_df, softrak_tabs = process_excel_file_debug(file_path)
        
        # Track Softrak through the pipeline
        pivoted_df, softrak_pivoted = track_softrak_through_pipeline(combined_df)
        
        # Analyze filtering issues
        analyze_softrak_filtering(pivoted_df, softrak_pivoted)
        
        print(f"\n=== SUMMARY ===")
        print(f"Softrak found in tabs: {softrak_tabs}")
        print(f"Check the detailed output above to identify why Softrak is missing from bottom 30")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
