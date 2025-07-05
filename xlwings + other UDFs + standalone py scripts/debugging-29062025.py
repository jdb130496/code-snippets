def extract_dates_and_metrics(df):
    """Extract month/year and metric from column headers, handling Date columns specially"""
    
    # First, identify which columns are actual Date columns vs other metrics
    date_columns = []
    other_columns = []
    
    for col in df.columns:
        if col in ['Company Name', 'Source_Tab']:
            continue
        # Check if this is a Date column (e.g., "Jan 2000 Date")
        if col.endswith(' Date') and not col.endswith('Low Price Date'):
            date_columns.append(col)
        else:
            other_columns.append(col)
    
    print(f"Found {len(date_columns)} Date columns and {len(other_columns)} other metric columns")
    
    # Process Date columns - extract the month/year and keep the date values
    date_data = []
    for date_col in date_columns:
        # Extract month/year from column name (e.g., "Jan 2000 Date" -> "Jan 2000")
        month_year = date_col.replace(' Date', '')
        
        # Create records for each company with their actual date
        temp_df = df.select(['Company Name', 'Source_Tab', date_col]).rename({date_col: 'Date_Value'})
        temp_df = temp_df.with_columns([
            pl.lit(month_year).alias('Month_Year'),
            pl.lit('Date').alias('Metric')
        ])
        temp_df = temp_df.rename({'Date_Value': 'Value'})
        date_data.append(temp_df)
    
    # Process other metric columns normally
    other_data = []
    for col in other_columns:
        month_year_match = None
        metric_name = None
        
        # Extract month/year pattern from column name
        import re
        match = re.match(r'^(\w{3} \d{4}) (.+)$', col)
        if match:
            month_year_match = match.group(1)
            metric_name = match.group(2)
        
        if month_year_match and metric_name:
            temp_df = df.select(['Company Name', 'Source_Tab', col]).rename({col: 'Value'})
            temp_df = temp_df.with_columns([
                pl.lit(month_year_match).alias('Month_Year'),
                pl.lit(metric_name).alias('Metric')
            ])
            other_data.append(temp_df)
    
    # Combine all data
    all_data = []
    if date_data:
        all_data.extend(date_data)
    if other_data:
        all_data.extend(other_data)
    
    if not all_data:
        raise ValueError("No data with valid dates found")
    
    combined_df = pl.concat(all_data)
    
    # Filter out rows where Month_Year is null
    combined_df = combined_df.filter(pl.col('Month_Year').is_not_null())
    
    if combined_df.height == 0:
        raise ValueError("No data with valid dates found")
    
    return combined_df

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
    
    # Convert the Date column (actual dates) to proper format
    if 'Date' in pivoted.columns:
        print("Processing Date column...")
        
        # Convert date values to proper format
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
    
    # Handle 365 days low price date columns
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

def export_results(df, output_file='ranking_results_fixed.xlsx'):
    """Export results to Excel file using actual Date column values"""
    
    if df is None:
        print("No data to export")
        return
    
    try:
        print(f"Starting export process for {df.height:,} rows...")
        
        # Sort by Source_Tab, Month_Year_Date (chronological), Ranking_Category, and Rank
        print("Sorting data...")
        df_sorted = df.sort([
            'Source_Tab',
            'Month_Year_Date',
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
        
        # Use the actual Date column from the data
        print("Using actual Date column from the data...")
        
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
            
            # Convert the Date column to readable format
            print("Converting Date column to readable format...")
            df_pandas['Date_Formatted'] = df_pandas['Date'].apply(excel_serial_to_date)
        else:
            print("WARNING: No Date column found in data")
            # Fallback to Month_Year
            def month_year_to_date(month_year):
                try:
                    from datetime import datetime
                    date_obj = datetime.strptime(month_year, '%b %Y')
                    return date_obj.strftime('%d/%m/%Y')
                except:
                    return month_year
            
            df_pandas['Date_Formatted'] = df_pandas['Month_Year'].apply(month_year_to_date)
        
        # Convert 365 days low price date column to readable format
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
            
            df_pandas['365_days_Low_Price_Date_Formatted'] = df_pandas[required_cols['low_price_date']].apply(excel_serial_to_date)
        else:
            df_pandas['365_days_Low_Price_Date_Formatted'] = ""
        
        # Create the final output structure
        final_df = df_pandas[[
            'Company Name',
            'Date_Formatted',  # Use the actual Date column
            required_cols.get('adj_close', 'Adjusted_Closing_Price') if 'adj_close' in required_cols else 'Month_Year',
            required_cols.get('low_price', '365_days_Low_Price') if 'low_price' in required_cols else 'Month_Year',
            '365_days_Low_Price_Date_Formatted',
            'Month_Year',
            'Source_Tab',
            'Ratio',
            'Ranking_Category',
            'Rank'
        ]].copy()
        
        # Rename columns for clarity
        final_df = final_df.rename(columns={
            'Date_Formatted': 'Date'
        })
        
        print("Creating Excel file...")
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            
            print("Writing main data...")
            final_df.to_excel(writer, sheet_name='All_Rankings', index=False)
            
            print("Writing Top 30 data...")
            top30_df = final_df[final_df['Ranking_Category'] == 'Top30'].copy()
            top30_df.to_excel(writer, sheet_name='Top30_Rankings', index=False)
            
            print("Writing Bottom 30 data...")
            bottom30_df = final_df[final_df['Ranking_Category'] == 'Bottom30'].copy()
            bottom30_df.to_excel(writer, sheet_name='Bottom30_Rankings', index=False)
        
        print(f"Results exported to {output_file}")
        print(f"Export completed successfully!")
        
        # Show sample of the output
        print("\n=== SAMPLE OUTPUT WITH ACTUAL DATES ===")
        sample_df = final_df[['Company Name', 'Date', 'Month_Year']].head(10)
        print(sample_df)
        
    except Exception as e:
        print(f"Error exporting results: {e}")
        import traceback
        traceback.print_exc()
