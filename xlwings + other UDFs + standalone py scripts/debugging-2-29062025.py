import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import calendar

def debug_month_counts(df, step_name):
    """Helper function to debug month counts at each step"""
    if 'Month_Year' in df.columns:
        if isinstance(df, pl.DataFrame):
            unique_months = df.select('Month_Year').unique().sort('Month_Year')
            months_list = unique_months.to_pandas()['Month_Year'].tolist()
        else:
            months_list = sorted(df['Month_Year'].unique())
        
        print(f"\n=== {step_name} ===")
        print(f"Total rows: {len(df) if isinstance(df, pd.DataFrame) else df.height}")
        print(f"Unique months: {len(months_list)}")
        
        # Check for specific months that were mentioned as missing
        test_months = ['Apr 2000', 'Sep 2000', 'Dec 2000', 'Mar 2001', 'Jun 2001', 'Sep 2001', 'Dec 2001']
        missing_months = []
        present_months = []
        
        for month in test_months:
            if month in months_list:
                present_months.append(month)
            else:
                missing_months.append(month)
        
        if present_months:
            print(f"Present test months: {present_months}")
        if missing_months:
            print(f"MISSING test months: {missing_months}")
            
        # Show first 20 months
        print(f"First 20 months: {months_list[:20]}")
    else:
        print(f"\n=== {step_name} ===")
        print(f"Total rows: {len(df) if isinstance(df, pd.DataFrame) else df.height}")
        print("No Month_Year column found")

def process_excel_file(file_path):
    excel_file = pd.ExcelFile(file_path)
    available_tabs = excel_file.sheet_names
    
    expected_tabs = ['2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2025']
    tabs_to_process = []
    
    for expected in expected_tabs:
        if expected in available_tabs:
            tabs_to_process.append(expected)
        else:
            similar = [tab for tab in available_tabs if expected.replace('-', '') in tab.replace('-', '')]
            if similar:
                tabs_to_process.append(similar[0])
    
    print(f"Processing tabs: {tabs_to_process}")
    
    all_tab_data = []
    
    for tab in tabs_to_process:
        try:
            print(f"\nProcessing tab: {tab}")
            tab_df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
            
            if tab_df.height == 0:
                print(f"  Tab {tab} is empty, skipping")
                continue
            
            print(f"  Tab {tab}: {tab_df.height} rows, {tab_df.width} columns")
            
            cleaned_columns = [col.strip() for col in tab_df.columns]
            tab_df.columns = cleaned_columns
            tab_df = tab_df.with_columns(pl.lit(tab).alias('Source_Tab'))
            
            value_cols = [col for col in tab_df.columns if col not in ['Company Name', 'Source_Tab']]
            print(f"  Value columns found: {len(value_cols)}")
            
            melted = tab_df.unpivot(
                index=['Company Name', 'Source_Tab'], 
                on=value_cols,
                variable_name='Column', 
                value_name='Value'
            )
            
            print(f"  After melting: {melted.height} rows")
            all_tab_data.append(melted)
            
        except Exception as e:
            print(f"Error processing tab {tab}: {e}")
            continue
    
    if not all_tab_data:
        raise ValueError("No data could be read from any tabs")
    
    combined_df = pl.concat(all_tab_data)
    print(f"\nCombined data: {combined_df.height} rows")
    return combined_df

def extract_dates_and_metrics(df):
    print(f"\nExtracting dates and metrics from {df.height} rows...")
    
    df = df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    # Debug: Check what patterns we're finding
    sample_columns = df.select('Column').unique().head(10).to_pandas()['Column'].tolist()
    print(f"Sample column patterns: {sample_columns}")
    
    before_filter = df.height
    df = df.filter(pl.col('Month_Year').is_not_null())
    after_filter = df.height
    
    print(f"Rows before date filter: {before_filter}")
    print(f"Rows after date filter: {after_filter}")
    print(f"Rows filtered out: {before_filter - after_filter}")
    
    if df.height == 0:
        raise ValueError("No data with valid dates found")
    
    debug_month_counts(df, "After extracting dates and metrics")
    return df

def pivot_and_convert_dates(df):
    debug_month_counts(df, "Before pivoting")
    
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
        print(f"Pivoted data: {pivoted.height} rows, {pivoted.width} columns")
    except Exception as e:
        print(f"Pivot error: {e}")
        raise
    
    debug_month_counts(pivoted, "After pivoting")
    
    # Convert Date column if it exists
    if 'Date' in pivoted.columns:
        print("Converting Date column...")
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
            )
            .otherwise(pl.col('Date'))
            .alias('Date')
        ])
    else:
        print("No Date column found in pivoted data")
    
    # Convert other date columns
    date_columns = [col for col in pivoted.columns if '365 days low price date' in col.lower()]
    print(f"Found {len(date_columns)} additional date columns to convert")
    
    for date_col in date_columns:
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
            )
            .otherwise(pl.col(date_col))
            .alias(date_col)
        ])
    
    debug_month_counts(pivoted, "After date conversion")
    return pivoted

def filter_month_end_only(df):
    debug_month_counts(df, "Before month-end filtering")
    
    if 'Date' not in df.columns:
        print("No Date column found - returning data unchanged")
        return df
    
    def is_month_end_date(date_serial):
        if pd.isna(date_serial) or date_serial <= 0:
            return False
        
        try:
            date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_serial))
            last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
            return date_obj.day == last_day
        except Exception:
            return False
    
    # Convert to pandas for filtering
    df_pandas = df.to_pandas()
    
    print(f"Checking {len(df_pandas)} rows for month-end dates...")
    
    # Debug: Check some sample dates
    sample_dates = df_pandas['Date'].dropna().head(10)
    print("Sample dates (Excel serial):")
    for date_val in sample_dates:
        try:
            if date_val > 0:
                date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_val))
                is_month_end = is_month_end_date(date_val)
                print(f"  {date_val} -> {date_obj.strftime('%Y-%m-%d')} (Month-end: {is_month_end})")
        except:
            print(f"  {date_val} -> Invalid date")
    
    # Keep only month-end dates
    mask = df_pandas['Date'].apply(is_month_end_date)
    df_filtered = df_pandas[mask].copy()
    
    print(f"Rows before month-end filter: {len(df_pandas)}")
    print(f"Rows after month-end filter: {len(df_filtered)}")
    print(f"Rows filtered out: {len(df_pandas) - len(df_filtered)}")
    
    debug_month_counts(df_filtered, "After month-end filtering")
    
    return pl.from_pandas(df_filtered)

def calculate_ratios_and_rank(df):
    debug_month_counts(df, "Before ratio calculation")
    
    # Find required columns
    required_cols = {}
    
    adj_close_candidates = [col for col in df.columns if 'adjusted closing price' in col.lower()]
    if adj_close_candidates:
        required_cols['adj_close'] = adj_close_candidates[0]
        print(f"Found adjusted closing price column: {required_cols['adj_close']}")
    
    low_price_candidates = []
    for col in df.columns:
        if '365 days low price' in col.lower() and 'date' not in col.lower():
            low_price_candidates.append(col)
    
    if low_price_candidates:
        required_cols['low_price'] = low_price_candidates[0]
        print(f"Found low price column: {required_cols['low_price']}")
    
    low_price_date_candidates = [col for col in df.columns if '365 days low price date' in col.lower()]
    if low_price_date_candidates:
        required_cols['low_price_date'] = low_price_date_candidates[0]
        print(f"Found low price date column: {required_cols['low_price_date']}")
    
    missing_types = [key for key, col in required_cols.items() if col is None]
    if missing_types:
        raise ValueError(f"Cannot find required columns for: {missing_types}")
    
    # Calculate ratio
    df_with_ratio = df.with_columns([
        (pl.col(required_cols['adj_close']).fill_null(0) / 
         pl.when(pl.col(required_cols['low_price']).fill_null(0) != 0)
         .then(pl.col(required_cols['low_price']).fill_null(0))
         .otherwise(1)).alias('Ratio')
    ])
    
    # Add sortable date column
    df_with_ratio = df_with_ratio.with_columns([
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').alias('Month_Year_Date')
    ])
    
    debug_month_counts(df_with_ratio, "After adding ratio and date columns")
    
    # Filter valid data
    before_filter = df_with_ratio.height
    df_clean = df_with_ratio.filter(
        (pl.col(required_cols['adj_close']).is_not_null()) &
        (pl.col(required_cols['adj_close']) > 0) &
        (pl.col(required_cols['low_price']).is_not_null()) &
        (pl.col(required_cols['low_price']) > 0)
    )
    after_filter = df_clean.height
    
    print(f"Rows before price filter: {before_filter}")
    print(f"Rows after price filter: {after_filter}")
    print(f"Rows filtered out: {before_filter - after_filter}")
    
    debug_month_counts(df_clean, "After filtering valid prices")
    
    # Sort and remove duplicates
    before_unique = df_clean.height
    df_clean = df_clean.sort(['Month_Year_Date', 'Source_Tab']).unique(
        subset=['Company Name', 'Month_Year'], 
        keep='last'
    )
    after_unique = df_clean.height
    
    print(f"Rows before unique filter: {before_unique}")
    print(f"Rows after unique filter: {after_unique}")
    print(f"Duplicate rows removed: {before_unique - after_unique}")
    
    debug_month_counts(df_clean, "After removing duplicates")
    
    # Debug specific months
    test_months = ['Apr 2000', 'Sep 2000', 'Dec 2000']
    for month in test_months:
        count = df_clean.filter(pl.col('Month_Year') == month).height
        if count > 0:
            print(f"✓ {month}: {count} companies")
        else:
            print(f"✗ {month}: 0 companies (MISSING)")
    
    unique_periods = df_clean.select(['Month_Year', 'Source_Tab', 'Month_Year_Date']).unique().sort(['Source_Tab', 'Month_Year_Date'])
    print(f"Total unique periods for ranking: {unique_periods.height}")
    
    top30_results = []
    bottom30_results = []
    
    for period_row in unique_periods.iter_rows():
        month_year, source_tab, month_year_date = period_row
        
        period_data = df_clean.filter(
            (pl.col('Month_Year') == month_year) & 
            (pl.col('Source_Tab') == source_tab)
        )
        
        if period_data.height == 0:
            continue
        
        # Top 30
        sorted_desc = period_data.sort('Ratio', descending=True)
        top30 = sorted_desc.head(30)
        
        # Bottom 30
        sorted_asc = period_data.sort('Ratio', descending=False)
        bottom30 = sorted_asc.head(30)
        
        top30 = top30.with_columns([
            pl.lit('Top30').alias('Ranking_Category'),
            pl.int_range(1, top30.height + 1).alias('Rank')
        ])
        
        bottom30 = bottom30.with_columns([
            pl.lit('Bottom30').alias('Ranking_Category'),
            pl.int_range(1, bottom30.height + 1).alias('Rank')
        ])
        
        top30_results.append(top30)
        bottom30_results.append(bottom30)
    
    if top30_results and bottom30_results:
        all_top30 = pl.concat(top30_results)
        all_bottom30 = pl.concat(bottom30_results)
        final_result = pl.concat([all_top30, all_bottom30])
        
        debug_month_counts(final_result, "Final ranking results")
        return final_result
    else:
        return None

def export_results(df, output_file='ranking_results_debug.xlsx'):
    if df is None:
        print("No data to export")
        return
    
    try:
        df_sorted = df.sort([
            'Source_Tab',
            'Month_Year_Date',
            'Ranking_Category',  
            'Rank'
        ], descending=[False, False, True, False])
        
        df_pandas = df_sorted.to_pandas()
        
        # Find required columns
        required_cols = {}
        for col in df_pandas.columns:
            if 'adjusted closing price' in col.lower():
                required_cols['adj_close'] = col
            elif '365 days low price' in col.lower() and 'date' not in col.lower():
                required_cols['low_price'] = col
            elif '365 days low price date' in col.lower():
                required_cols['low_price_date'] = col
        
        # Format Date column
        if 'Date' in df_pandas.columns:
            def excel_serial_to_date(serial):
                if pd.isna(serial) or serial <= 0:
                    return ""
                try:
                    date_obj = datetime(1899, 12, 30) + timedelta(days=int(serial))
                    return date_obj.strftime('%d/%m/%Y')
                except:
                    return str(serial)
            
            df_pandas['Date_Formatted'] = df_pandas['Date'].apply(excel_serial_to_date)
        else:
            def month_year_to_last_day(month_year):
                try:
                    date_obj = datetime.strptime(month_year, '%b %Y')
                    last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
                    return date_obj.replace(day=last_day).strftime('%d/%m/%Y')
                except:
                    return month_year
            
            df_pandas['Date_Formatted'] = df_pandas['Month_Year'].apply(month_year_to_last_day)
        
        # Format 365 days low price date
        if 'low_price_date' in required_cols:
            def excel_serial_to_date(serial):
                if pd.isna(serial) or serial <= 0:
                    return ""
                try:
                    date_obj = datetime(1899, 12, 30) + timedelta(days=int(serial))
                    return date_obj.strftime('%d/%m/%Y')
                except:
                    return str(serial)
            
            df_pandas['365_days_Low_Price_Date_Formatted'] = df_pandas[required_cols['low_price_date']].apply(excel_serial_to_date)
        else:
            df_pandas['365_days_Low_Price_Date_Formatted'] = ""
        
        # Select final columns
        columns_to_include = ['Company Name', 'Date_Formatted']
        
        if 'adj_close' in required_cols:
            columns_to_include.append(required_cols['adj_close'])
        
        for col in df_pandas.columns:
            if 'market capitalisation' in col.lower():
                columns_to_include.append(col)
                break
        
        for col in df_pandas.columns:
            if 'total returns' in col.lower():
                columns_to_include.append(col)
                break
        
        if 'low_price' in required_cols:
            columns_to_include.append(required_cols['low_price'])
        
        columns_to_include.extend([
            '365_days_Low_Price_Date_Formatted',
            'Month_Year', 
            'Source_Tab',
            'Ratio',
            'Ranking_Category',
            'Rank'
        ])
        
        final_columns = [col for col in columns_to_include if col in df_pandas.columns]
        df_final = df_pandas[final_columns].copy()
        
        df_final = df_final.rename(columns={
            'Date_Formatted': 'Date',
            '365_days_Low_Price_Date_Formatted': '365_days_Low_Price_Date'
        })
        
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            df_final.to_excel(writer, sheet_name='All_Rankings', index=False)
            
            top30_df = df_final[df_final['Ranking_Category'] == 'Top30'].copy()
            top30_df.to_excel(writer, sheet_name='Top30_Rankings', index=False)
            
            bottom30_df = df_final[df_final['Ranking_Category'] == 'Bottom30'].copy()
            bottom30_df.to_excel(writer, sheet_name='Bottom30_Rankings', index=False)
        
        print(f"Results exported to {output_file}")
        
        # Final summary
        unique_months_final = sorted(df_final['Month_Year'].unique())
        print(f"\nFINAL SUMMARY:")
        print(f"Total records in output: {len(df_final)}")
        print(f"Unique months in output: {len(unique_months_final)}")
        print(f"Date range: {unique_months_final[0] if unique_months_final else 'None'} to {unique_months_final[-1] if unique_months_final else 'None'}")
        
    except Exception as e:
        print(f"Error exporting results: {e}")
        import traceback
        traceback.print_exc()

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        print("=== DEBUGGING SCRIPT TO FIND MISSING MONTHS ===")
        
        print("\nStep 1: Processing Excel file...")
        combined_df = process_excel_file(file_path)
        
        print("\nStep 2: Extracting dates and metrics...")
        df_extracted = extract_dates_and_metrics(combined_df)
        
        print("\nStep 3: Pivoting and converting dates...")
        df_pivoted = pivot_and_convert_dates(df_extracted)
        
        print("\nStep 4: Filtering month-end dates...")
        df_filtered = filter_month_end_only(df_pivoted)
        
        print("\nStep 5: Calculating ratios and rankings...")
        rankings_df = calculate_ratios_and_rank(df_filtered)
        
        if rankings_df is not None:
            print("\nStep 6: Exporting results...")
            export_results(rankings_df)
            print("\nProcessing completed successfully!")
        else:
            print("No rankings data generated.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
