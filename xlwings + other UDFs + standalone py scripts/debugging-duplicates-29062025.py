import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import calendar

def process_excel_file(file_path):
    print(f"Processing Excel file: {file_path}")
    try:
        excel_file = pd.ExcelFile(file_path)
        available_tabs = excel_file.sheet_names
        print(f"Available tabs: {available_tabs}")
        
        expected_tabs = ['2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2025']
        tabs_to_process = []
        
        for expected in expected_tabs:
            if expected in available_tabs:
                tabs_to_process.append(expected)
            else:
                similar = [tab for tab in available_tabs if expected.replace('-', '') in tab.replace('-', '')]
                if similar:
                    tabs_to_process.append(similar[0])
        
        print(f"Tabs to process: {tabs_to_process}")
        
        all_tab_data = []
        
        for tab in tabs_to_process:
            try:
                print(f"Processing tab: {tab}")
                tab_df = pl.from_pandas(pd.read_excel(file_path, sheet_name=tab))
                
                if tab_df.height == 0:
                    print(f"  Tab {tab} is empty, skipping")
                    continue
                
                print(f"  Tab {tab} has {tab_df.height} rows")
                
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
                
                print(f"  Melted data has {melted.height} rows")
                all_tab_data.append(melted)
                
            except Exception as e:
                print(f"Error processing tab {tab}: {e}")
                continue
        
        if not all_tab_data:
            raise ValueError("No data could be read from any tabs")
        
        combined_df = pl.concat(all_tab_data)
        print(f"Combined data has {combined_df.height} rows")
        return combined_df
        
    except Exception as e:
        print(f"Error in process_excel_file: {e}")
        raise

def extract_dates_and_metrics(df):
    print("Extracting dates and metrics...")
    df = df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ])
    
    df = df.filter(pl.col('Month_Year').is_not_null())
    print(f"After date extraction: {df.height} rows")
    
    if df.height == 0:
        raise ValueError("No data with valid dates found")
    
    return df

def pivot_and_convert_dates(df):
    print("Pivoting data...")
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
        print(f"Pivoted data has {pivoted.height} rows")
    except Exception as e:
        print(f"Error in pivoting: {e}")
        raise
    
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
    
    return pivoted

def filter_month_end_only(df):
    print("Filtering month-end dates...")
    if 'Date' not in df.columns:
        print("No Date column found, returning original data")
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
    
    # Keep only month-end dates
    mask = df_pandas['Date'].apply(is_month_end_date)
    df_filtered = df_pandas[mask].copy()
    
    print(f"After month-end filtering: {len(df_filtered)} rows")
    
    # Convert back to polars
    return pl.from_pandas(df_filtered)

def debug_duplicates(df):
    """Debug function to identify why certain dates have duplicates"""
    
    print("\n" + "="*50)
    print("DEBUGGING DUPLICATE DATES")
    print("="*50)
    
    print(f"Total rows in filtered data: {df.height}")
    print(f"Columns: {df.columns}")
    
    # Check for duplicate Month_Year entries across tabs
    print("\nAnalyzing Month_Year + Company combinations across tabs...")
    
    month_year_counts = df.group_by(['Month_Year', 'Company Name']).agg([
        pl.col('Source_Tab').n_unique().alias('tab_count'),
        pl.col('Source_Tab').unique().alias('tabs'),
        pl.col('Date').n_unique().alias('date_count') if 'Date' in df.columns else pl.lit(0).alias('date_count'),
        pl.col('Date').unique().alias('dates') if 'Date' in df.columns else pl.lit([]).alias('dates')
    ])
    
    # Find entries that appear in multiple tabs
    duplicates = month_year_counts.filter(pl.col('tab_count') > 1)
    
    print(f"Found {duplicates.height} Month_Year + Company combinations appearing in multiple tabs")
    
    if duplicates.height > 0:
        print("\nFirst 20 duplicate combinations:")
        dup_df = duplicates.head(20).to_pandas()
        for idx, row in dup_df.iterrows():
            print(f"  {row['Month_Year']} - {row['Company Name']}")
            print(f"    Tabs: {row['tabs']}")
            if 'Date' in df.columns:
                print(f"    Dates: {row['dates']}")
            print(f"    Tab count: {row['tab_count']}")
            print()
    
    # Check specifically for Jan 2005 and Jan 2020
    target_months = ['Jan 2005', 'Jan 2020']
    
    for target_month in target_months:
        print(f"\n{'='*30}")
        print(f"DETAILED CHECK FOR {target_month}")
        print(f"{'='*30}")
        
        target_data = df.filter(pl.col('Month_Year') == target_month)
        
        if target_data.height > 0:
            print(f"Total rows for {target_month}: {target_data.height}")
            
            companies_by_tab = target_data.group_by('Source_Tab').agg([
                pl.col('Company Name').n_unique().alias('unique_companies'),
                pl.col('Company Name').count().alias('total_records'),
                pl.col('Date').n_unique().alias('unique_dates') if 'Date' in df.columns else pl.lit(0).alias('unique_dates'),
                pl.col('Date').unique().alias('dates') if 'Date' in df.columns else pl.lit([]).alias('dates')
            ])
            
            print(f"Data breakdown for {target_month}:")
            tab_df = companies_by_tab.to_pandas()
            for _, row in tab_df.iterrows():
                print(f"  Tab: {row['Source_Tab']}")
                print(f"    Unique companies: {row['unique_companies']}")
                print(f"    Total records: {row['total_records']}")
                if 'Date' in df.columns:
                    print(f"    Unique dates: {row['unique_dates']}")
                    print(f"    Dates: {row['dates']}")
                print()
            
            # Show some sample companies for this month
            sample_companies = target_data.select(['Company Name', 'Source_Tab', 'Date' if 'Date' in df.columns else pl.lit('No Date')]).head(10)
            print(f"Sample records for {target_month}:")
            sample_df = sample_companies.to_pandas()
            for _, row in sample_df.iterrows():
                print(f"  {row['Company Name']} - Tab: {row['Source_Tab']}" + 
                      (f" - Date: {row.get('Date', 'N/A')}" if 'Date' in df.columns else ""))
        else:
            print(f"No data found for {target_month}")
    
    return df

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        print("Starting debug analysis...")
        
        combined_df = process_excel_file(file_path)
        
        df_extracted = extract_dates_and_metrics(combined_df)
        
        df_pivoted = pivot_and_convert_dates(df_extracted)
        
        # Filter to keep only month-end dates
        df_filtered = filter_month_end_only(df_pivoted)
        
        # Run debug analysis
        debug_duplicates(df_filtered)
        
        print("\nDebug analysis completed!")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
