import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import calendar

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
    df = df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    df = df.filter(pl.col('Month_Year').is_not_null())
    
    if df.height == 0:
        raise ValueError("No data with valid dates found")
    
    return df

def pivot_and_convert_dates(df):
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
    except Exception as e:
        raise
    
    # Convert Date column if it exists
    if 'Date' in pivoted.columns:
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
    
    # Convert other date columns
    date_columns = [col for col in pivoted.columns if '365 days low price date' in col.lower()]
    
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
    
    return pivoted

def filter_for_consistent_monthly_data(df):
    """
    Instead of filtering for month-end dates, we'll use one record per company per month.
    This ensures we don't lose entire months due to date filtering.
    """
    print(f"Before monthly data filtering: {df.height} rows")
    
    # Add a sortable date column for consistent selection
    df = df.with_columns([
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').alias('Month_Year_Date')
    ])
    
    # If we have a Date column, prefer records closer to month-end
    # Otherwise, just take one record per company per month
    if 'Date' in df.columns:
        def get_month_end_preference_score(date_serial, month_year_str):
            """Score how close a date is to month-end (higher = closer to month-end)"""
            if pd.isna(date_serial) or date_serial <= 0:
                return 0
            
            try:
                date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_serial))
                # Parse the month_year to get the target month
                target_date = datetime.strptime(month_year_str, '%b %Y')
                
                # Check if the date is in the correct month/year
                if date_obj.year == target_date.year and date_obj.month == target_date.month:
                    # Get the last day of the month
                    last_day = calendar.monthrange(date_obj.year, date_obj.month)[1]
                    # Score based on how close to month-end (max score = last_day)
                    return date_obj.day
                else:
                    return 0
            except:
                return 0
        
        # Convert to pandas for complex scoring
        df_pandas = df.to_pandas()
        df_pandas['month_end_score'] = df_pandas.apply(
            lambda row: get_month_end_preference_score(row['Date'], row['Month_Year']), 
            axis=1
        )
        
        # Convert back to polars
        df = pl.from_pandas(df_pandas)
        
        # For each company-month combination, keep the record with the highest month_end_score
        df_filtered = df.sort(['Company Name', 'Month_Year', 'month_end_score'], descending=[False, False, True])
        df_filtered = df_filtered.unique(subset=['Company Name', 'Month_Year'], keep='first')
        
        # Drop the temporary scoring column
        df_filtered = df_filtered.drop('month_end_score')
        
    else:
        # If no Date column, just take one record per company per month
        df_filtered = df.unique(subset=['Company Name', 'Month_Year'], keep='first')
    
    print(f"After monthly data filtering: {df_filtered.height} rows")
    print(f"Unique months retained: {df_filtered.select('Month_Year').unique().height}")
    
    return df_filtered

def calculate_ratios_and_rank(df):
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
    
    missing_types = [key for key, col in required_cols.items() if col not in df.columns]
    if missing_types:
        raise ValueError(f"Cannot find required columns for: {missing_types}")
    
    # Calculate ratio
    df_with_ratio = df.with_columns([
        (pl.col(required_cols['adj_close']).fill_null(0) / 
         pl.when(pl.col(required_cols['low_price']).fill_null(0) != 0)
         .then(pl.col(required_cols['low_price']).fill_null(0))
         .otherwise(1)).alias('Ratio')
    ])
    
    # Filter valid data
    df_clean = df_with_ratio.filter(
        (pl.col(required_cols['adj_close']).is_not_null()) &
        (pl.col(required_cols['adj_close']) > 0) &
        (pl.col(required_cols['low_price']).is_not_null()) &
        (pl.col(required_cols['low_price']) > 0)
    )
    
    # Sort by date and remove any remaining duplicates
    df_clean = df_clean.sort(['Month_Year_Date', 'Source_Tab']).unique(
        subset=['Company Name', 'Month_Year'], 
        keep='last'
    )
    
    print(f"Final clean data: {df_clean.height} rows")
    print(f"Unique months in final data: {df_clean.select('Month_Year').unique().height}")
    
    # Debug: Check for specific months
    test_months = ['Apr 2000', 'Sep 2000', 'Dec 2000', 'Jan 2005', 'Jan 2020']
    for month in test_months:
        count = df_clean.filter(pl.col('Month_Year') == month).height
        print(f"{month}: {count} companies")
    
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
        return pl.concat([all_top30, all_bottom30])
    else:
        return None

def export_results(df, output_file='ranking_results_fixed.xlsx'):
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
        if unique_months_final:
            print(f"Date range: {unique_months_final[0]} to {unique_months_final[-1]}")
        
    except Exception as e:
        print(f"Error exporting results: {e}")
        import traceback
        traceback.print_exc()

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        print("=== PROCESSING WITH FIXED MONTH FILTERING ===")
        
        print("\nStep 1: Processing Excel file...")
        combined_df = process_excel_file(file_path)
        
        print("\nStep 2: Extracting dates and metrics...")
        df_extracted = extract_dates_and_metrics(combined_df)
        
        print("\nStep 3: Pivoting and converting dates...")
        df_pivoted = pivot_and_convert_dates(df_extracted)
        
        print("\nStep 4: Filtering for consistent monthly data...")
        df_filtered = filter_for_consistent_monthly_data(df_pivoted)
        
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
