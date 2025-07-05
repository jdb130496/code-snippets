import polars as pl
import pandas as pd
from datetime import datetime

def process_excel_file(file_path):
    """Process Excel file by stacking all tabs first, then applying business logic"""
    
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
    
    all_tab_data = []
    
    for tab in tabs_to_process:
        try:
            tab_df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
            
            if tab_df.height == 0:
                continue
            
            cleaned_columns = [col.strip() for col in tab_df.columns]
            tab_df.columns = cleaned_columns
            tab_df = tab_df.with_columns(pl.lit(tab).alias('Source_Tab'))
            
            value_cols = [col for col in tab_df.columns if col not in ['Company Name', 'Source_Tab']]
            
            melted = tab_df.unpivot(
                index=['Company Name', 'Source_Tab'], 
                on=value_cols,
                variable_name='Column', 
                value_name='Value'
            )
            
            all_tab_data.append(melted)
            
        except Exception as e:
            continue
    
    if not all_tab_data:
        raise ValueError("No data could be read from any tabs")
    
    combined_df = pl.concat(all_tab_data)
    return combined_df

def extract_dates_and_metrics(df):
    """Extract month/year and metric from column headers, handling Date columns specially"""
    
    # FIXED: Handle Date columns properly
    df = df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    df = df.filter(pl.col('Month_Year').is_not_null())
    
    if df.height == 0:
        raise ValueError("No data with valid dates found")
    
    return df

def standardize_metric_names(df):
    """Standardize metric names across different tabs"""
    # Handle the column order difference in 2015-2020 tab
    return df

def pivot_and_convert_dates(df):
    """Pivot data and handle date conversion properly"""
    
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
    except Exception as e:
        raise
    
    # FIXED: Convert the actual Date column (from "Jan 2000 Date" etc.)
    if 'Date' in pivoted.columns:
        print("Processing Date column (actual dates from Excel)...")
        
        pivoted = pivoted.with_columns([
            pl.when(pl.col('Date').is_not_null())
            .then(
                # Check if it's a very large number (likely timestamp)
                pl.when(pl.col('Date').cast(pl.Float64) > 1e15)
                .then(
                    # Convert nanosecond timestamp to Excel serial date
                    (pl.col('Date').cast(pl.Float64) / 86400000000000).cast(pl.Int64) + 25569
                )
                .when(pl.col('Date').cast(pl.Float64) > 1e12)
                .then(
                    # Convert millisecond timestamp to Excel serial date
                    (pl.col('Date').cast(pl.Float64) / 86400000).cast(pl.Int64) + 25569
                )
                .when(pl.col('Date').cast(pl.Float64) > 1e9)
                .then(
                    # Convert second timestamp to Excel serial date
                    (pl.col('Date').cast(pl.Float64) / 86400).cast(pl.Int64) + 25569
                )
                .when((pl.col('Date').cast(pl.Float64) >= 1) & (pl.col('Date').cast(pl.Float64) <= 100000))
                .then(
                    # Keep as Excel serial date (rounded to integer)
                    pl.col('Date').cast(pl.Int64)
                )
                .otherwise(
                    # For any other numeric value, try to interpret as Excel serial
                    pl.col('Date').cast(pl.Int64)
                )
            )
            .otherwise(pl.col('Date'))
            .alias('Date')
        ])
    
    # Find all 365 days low price date columns
    date_columns = [col for col in pivoted.columns if '365 days low price date' in col.lower()]
    
    if date_columns:
        print(f"Found {len(date_columns)} 365 days low price date columns to process...")
        
        for date_col in date_columns:
            print(f"Processing date column: {date_col}")
            
            # Convert date values to proper Excel serial format
            pivoted = pivoted.with_columns([
                pl.when(pl.col(date_col).is_not_null())
                .then(
                    # Check if it's a very large number (likely nanosecond timestamp)
                    pl.when(pl.col(date_col).cast(pl.Float64) > 1e15)
                    .then(
                        # Convert nanosecond timestamp to Excel serial date
                        (pl.col(date_col).cast(pl.Float64) / 86400000000000).cast(pl.Int64) + 25569
                    )
                    .when(pl.col(date_col).cast(pl.Float64) > 1e12)
                    .then(
                        # Convert millisecond timestamp to Excel serial date
                        (pl.col(date_col).cast(pl.Float64) / 86400000).cast(pl.Int64) + 25569
                    )
                    .when(pl.col(date_col).cast(pl.Float64) > 1e9)
                    .then(
                        # Convert second timestamp to Excel serial date
                        (pl.col(date_col).cast(pl.Float64) / 86400).cast(pl.Int64) + 25569
                    )
                    .when((pl.col(date_col).cast(pl.Float64) >= 1) & (pl.col(date_col).cast(pl.Float64) <= 100000))
                    .then(
                        # Keep as Excel serial date (rounded to integer)
                        pl.col(date_col).cast(pl.Int64)
                    )
                    .otherwise(
                        # For any other numeric value, try to interpret as Excel serial
                        pl.col(date_col).cast(pl.Int64)
                    )
                )
                .otherwise(pl.col(date_col))
                .alias(date_col)
            ])
    
    return pivoted

def calculate_ratios_and_rank(df):
    """Calculate ratios and rank companies using Month_Year (original approach)"""
    
    print("=== CALCULATING RATIOS AND RANKING ===")
    
    # Find required columns
    required_cols = {
        'adj_close': None,
        'low_price': None,
        'low_price_date': None
    }
    
    # Look for adjusted closing price column
    adj_close_candidates = [col for col in df.columns if 'adjusted closing price' in col.lower()]
    if adj_close_candidates:
        required_cols['adj_close'] = adj_close_candidates[0]
    
    # Look for 365 days low price column
    low_price_candidates = []
    for col in df.columns:
        if '365 days low price' in col.lower() and 'date' not in col.lower():
            low_price_candidates.append(col)
    
    if low_price_candidates:
        required_cols['low_price'] = low_price_candidates[0]
    
    # Look for 365 days low price date column
    low_price_date_candidates = [col for col in df.columns if '365 days low price date' in col.lower()]
    if low_price_date_candidates:
        required_cols['low_price_date'] = low_price_date_candidates[0]
    
    missing_types = [key for key, col in required_cols.items() if col is None]
    if missing_types:
        print("Available columns:")
        for col in sorted(df.columns):
            print(f"  - {col}")
        raise ValueError(f"Cannot find required columns for: {missing_types}")
    
    print(f"Using columns:")
    print(f"  - Adjusted Close: '{required_cols['adj_close']}'")
    print(f"  - 365 Days Low Price: '{required_cols['low_price']}'")
    print(f"  - 365 Days Low Price Date: '{required_cols['low_price_date']}'")
    
    # Calculate ratio: current month's price / 365 days low
    df_with_ratio = df.with_columns([
        (pl.col(required_cols['adj_close']).fill_null(0) / 
         pl.when(pl.col(required_cols['low_price']).fill_null(0) != 0)
         .then(pl.col(required_cols['low_price']).fill_null(0))
         .otherwise(1)).alias('Ratio')
    ])
    
    # Add proper date sorting column - convert Month_Year to sortable format
    df_with_ratio = df_with_ratio.with_columns([
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').alias('Month_Year_Date')
    ])
    
    # Filter out invalid data
    df_clean = df_with_ratio.filter(
        (pl.col(required_cols['adj_close']).is_not_null()) &
        (pl.col(required_cols['adj_close']) > 0) &
        (pl.col(required_cols['low_price']).is_not_null()) &
        (pl.col(required_cols['low_price']) > 0)
    )
    
    print(f"Valid companies after filtering: {df_clean.height}")
    
    # Group by Month_Year and Source_Tab - but sort chronologically
    unique_periods = df_clean.select(['Month_Year', 'Source_Tab', 'Month_Year_Date']).unique().sort(['Source_Tab', 'Month_Year_Date'])
    print(f"Processing {unique_periods.height} unique month-year periods")
    
    top30_results = []
    bottom30_results = []
    
    for period_row in unique_periods.iter_rows():
        month_year, source_tab, month_year_date = period_row
        
        # Filter data for this specific month-year and source tab
        period_data = df_clean.filter(
            (pl.col('Month_Year') == month_year) & 
            (pl.col('Source_Tab') == source_tab)
        )
        
        if period_data.height == 0:
            continue
        
        # Sort by ratio in descending order for top 30
        sorted_desc = period_data.sort('Ratio', descending=True)
        top30 = sorted_desc.head(30)
        
        # Sort by ratio in ascending order for bottom 30
        sorted_asc = period_data.sort('Ratio', descending=False)
        bottom30 = sorted_asc.head(30)
        
        # Add ranking information
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
        
        # Log progress
        top_ratio = top30.select('Ratio').max().item(0, 0) if top30.height > 0 else 0
        bottom_ratio = bottom30.select('Ratio').min().item(0, 0) if bottom30.height > 0 else 0
        print(f"Processed {source_tab} - {month_year}: {period_data.height} companies, Top ratio: {top_ratio:.6f}, Bottom ratio: {bottom_ratio:.6f}")
    
    # Combine all results
    if top30_results and bottom30_results:
        all_top30 = pl.concat(top30_results)
        all_bottom30 = pl.concat(bottom30_results)
        all_rankings = pl.concat([all_top30, all_bottom30])
        
        print(f"\nTotal rankings generated:")
        print(f"Top 30 entries: {all_top30.height}")
        print(f"Bottom 30 entries: {all_bottom30.height}")
        print(f"Total entries: {all_rankings.height}")
        
        return all_rankings
    else:
        print("No ranking results generated")
        return None

def export_results(df, output_file='ranking_results_fixed.xlsx'):
    """Export results to Excel file with proper structure using actual dates from Date column"""
    
    if df is None:
        print("No data to export")
        return
    
    try:
        print(f"Starting export process for {df.height:,} rows...")
        
        # Sort by Source_Tab, Month_Year_Date (chronological), Ranking_Category, and Rank
        print("Sorting data...")
        df_sorted = df.sort([
            'Source_Tab',
            'Month_Year_Date',  # Use the date column for proper chronological sorting
            'Ranking_Category',  
            'Rank'
        ], descending=[False, False, True, False])
        
        print("Converting to pandas...")
        df_pandas = df_sorted.to_pandas()
        
        # Find required columns for final output
        required_cols = {}
        for col in df_pandas.columns:
            if 'adjusted closing price' in col.lower():
                required_cols['adj_close'] = col
            elif '365 days low price' in col.lower() and 'date' not in col.lower():
                required_cols['low_price'] = col
            elif '365 days low price date' in col.lower():
                required_cols['low_price_date'] = col
        
        # FIXED: Use the actual Date column (from "Jan 2000 Date" etc.) instead of Month_Year
        print("Using actual Date column from the Excel data...")
        
        if 'Date' in df_pandas.columns:
            def excel_serial_to_date(serial):
                if pd.isna(serial) or serial <= 0:
                    return ""
                try:
                    import datetime
                    # Convert Excel serial number to actual date
                    date_obj = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(serial))
                    return date_obj.strftime('%d/%m/%Y')
                except:
                    return str(serial)
            
            # Use the actual Date column values
            print("Converting actual Date column to readable format...")
            df_pandas['Date_Formatted'] = df_pandas['Date'].apply(excel_serial_to_date)
        else:
            print("WARNING: No Date column found, falling back to Month_Year")
            # Fallback: if no Date column found, use Month_Year but warn user
            def month_year_to_first_day(month_year):
                """Convert 'Jan 2000' format to '01/01/2000' (first day of month as fallback)"""
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(month_year, '%b %Y')
                    return date_obj.strftime('%d/%m/%Y')
                except:
                    return month_year
            
            df_pandas['Date_Formatted'] = df_pandas['Month_Year'].apply(month_year_to_first_day)
        
        # Convert 365 days low price date column to readable format (separate from main Date)
        if 'low_price_date' in required_cols:
            def excel_serial_to_date(serial):
                if pd.isna(serial) or serial <= 0:
                    return ""
                try:
                    import datetime
                    date_obj = datetime.datetime(1899, 12, 30) + datetime.timedelta(days=int(serial))
                    return date_obj.strftime('%d/%m/%Y')
                except:
                    return str(serial)
            
            # Format the 365 days low price date (separate from main Date column)
            df_pandas['365_days_Low_Price_Date_Formatted'] = df_pandas[required_cols['low_price_date']].apply(excel_serial_to_date)
        else:
            df_pandas['365_days_Low_Price_Date_Formatted'] = ""
        
        # Create the final output structure matching the screenshot
        columns_to_include = ['Company Name', 'Date_Formatted']
        
        # Add other columns if they exist
        if 'adj_close' in required_cols:
            columns_to_include.append(required_cols['adj_close'])
        
        # Add Market_Capitalisation and Total_Returns if they exist
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
        
        # Select columns that actually exist
        final_columns = [col for col in columns_to_include if col in df_pandas.columns]
        df_final = df_pandas[final_columns].copy()
        
        # Rename for clarity
        df_final = df_final.rename(columns={
            'Date_Formatted': 'Date',
            '365_days_Low_Price_Date_Formatted': '365_days_Low_Price_Date'
        })
        
        print("Creating Excel file...")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            print("Writing main data...")
            df_final.to_excel(writer, sheet_name='All_Rankings', index=False)
            
            print("Writing Top 30 data...")
            top30_df = df_final[df_final['Ranking_Category'] == 'Top30'].copy()
            top30_df.to_excel(writer, sheet_name='Top30_Rankings', index=False)
            
            print("Writing Bottom 30 data...")
            bottom30_df = df_final[df_final['Ranking_Category'] == 'Bottom30'].copy()
            bottom30_df.to_excel(writer, sheet_name='Bottom30_Rankings', index=False)
            
            print("Creating summary...")
            try:
                summary_data = []
                for (source_tab, month_year, ranking_cat), group in df_final.groupby(
                    ['Source_Tab', 'Month_Year', 'Ranking_Category']
                ):
                    summary_data.append({
                        'Source_Tab': source_tab,
                        'Month_Year': month_year,
                        'Ranking_Category': ranking_cat,
                        'Count': len(group),
                        'Min_Ratio': group['Ratio'].min(),
                        'Max_Ratio': group['Ratio'].max(),
                        'Mean_Ratio': group['Ratio'].mean()
                    })
                
                summary_df = pd.DataFrame(summary_data)
                summary_df = summary_df.sort_values(['Source_Tab', 'Month_Year', 'Ranking_Category'])
                summary_df.to_excel(writer, sheet_name='Monthly_Summary', index=False)
                
            except Exception as summary_error:
                print(f"Warning: Could not create summary sheet: {summary_error}")
        
        print(f"Results exported to {output_file}")
        print(f"Export completed successfully!")
        
        # Show sample of the corrected output
        print("\n=== FIXED DATE COLUMNS SAMPLE ===")
        if 'Date' in df_final.columns:
            sample_df = df_final[['Company Name', 'Date', 'Month_Year']].head(10)
            print("Now using actual dates from Date column (not month-end derived from Month_Year):")
            print(sample_df)
        
    except Exception as e:
        print(f"Error exporting results: {e}")
        import traceback
        traceback.print_exc()

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        print("Processing Excel file...")
        combined_df = process_excel_file(file_path)
        print(f"Combined data shape: {combined_df.shape}")
        
        print("Extracting dates and metrics...")
        df_extracted = extract_dates_and_metrics(combined_df)
        print(f"After extraction: {df_extracted.shape}")
        
        print("Standardizing metric names...")
        df_standardized = standardize_metric_names(df_extracted)
        
        print("Pivoting data and handling dates...")
        df_pivoted = pivot_and_convert_dates(df_standardized)
        print(f"Pivoted data shape: {df_pivoted.shape}")
        
        print("Calculating ratios and ranking by Month_Year...")
        rankings_df = calculate_ratios_and_rank(df_pivoted)
        
        if rankings_df is not None:
            print("Exporting results...")
            export_results(rankings_df)
            
            # Display sample results
            print("\n=== SAMPLE RESULTS ===")
            print("Top 5 highest ratios overall:")
            top_sample = rankings_df.filter(pl.col('Ranking_Category') == 'Top30').sort('Ratio', descending=True).head(5)
            print(top_sample.select(['Company Name', 'Month_Year', 'Source_Tab', 'Ratio', 'Rank']))
            
            print("\nBottom 5 lowest ratios overall:")
            bottom_sample = rankings_df.filter(pl.col('Ranking_Category') == 'Bottom30').sort('Ratio').head(5)
            print(bottom_sample.select(['Company Name', 'Month_Year', 'Source_Tab', 'Ratio', 'Rank']))
        
        print("\n=== PROCESSING COMPLETE ===")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
