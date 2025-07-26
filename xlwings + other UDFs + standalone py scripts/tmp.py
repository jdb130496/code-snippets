import polars as pl
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import re

def clean_and_parse_date(date_value, output_format='dd/mm/yyyy'):
    """Clean and parse various date formats - returns formatted string only"""
    if date_value is None or date_value == '' or str(date_value).strip() == '':
        return None
    
    # Convert to string if not already
    date_str = str(date_value).strip()
    
    # Skip if it's 'nan' or similar
    if date_str.lower() in ['nan', 'none', 'nat']:
        return None
    
    # Handle Excel serial number dates (numbers > 25000 are likely Excel dates)
    try:
        float_val = float(date_str)
        if float_val > 25000:  # Excel dates start from 1900, so this is likely a date
            # Convert Excel serial number to datetime
            # Excel epoch is 1900-01-01, but Excel incorrectly treats 1900 as leap year
            from datetime import datetime, timedelta
            excel_epoch = datetime(1899, 12, 30)  # Adjusted for Excel's leap year bug
            parsed_date = excel_epoch + timedelta(days=float_val)
            
            if output_format == 'dd/mm/yyyy':
                return parsed_date.strftime('%d/%m/%Y')
            else:
                return parsed_date.strftime('%Y-%m-%d')
        elif '.' in date_str and len(date_str) < 10 and float_val < 100:  # Likely a ratio, not a date
            return None
    except:
        pass
    
    # Handle timestamp format
    if '00:00:00' in date_str:
        date_str = date_str.split(' ')[0]
    
    # Try different date formats - prioritize dd-mm-yyyy and dd/mm/yyyy
    date_formats = [
        '%d-%m-%Y',    # dd-mm-yyyy (your Excel format)
        '%d/%m/%Y',    # dd/mm/yyyy
        '%Y-%m-%d',    # yyyy-mm-dd
        '%m/%d/%Y',    # mm/dd/yyyy
        '%Y/%m/%d'     # yyyy/mm/dd
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            if output_format == 'dd/mm/yyyy':
                return parsed_date.strftime('%d/%m/%Y')
            else:
                return parsed_date.strftime('%Y-%m-%d')
        except:
            continue
    
    return None

def clean_and_parse_date_for_sorting(date_value):
    """Parse date and return datetime object for sorting"""
    if date_value is None or date_value == '' or str(date_value).strip() == '':
        return None
    
    # Convert to string if not already
    date_str = str(date_value).strip()
    
    # Skip if it's 'nan' or similar
    if date_str.lower() in ['nan', 'none', 'nat']:
        return None
    
    # Handle Excel serial number dates
    try:
        float_val = float(date_str)
        if float_val > 25000:
            from datetime import datetime, timedelta
            excel_epoch = datetime(1899, 12, 30)
            return excel_epoch + timedelta(days=float_val)
        elif '.' in date_str and len(date_str) < 10 and float_val < 100:
            return None
    except:
        pass
    
    # Handle timestamp format
    if '00:00:00' in date_str:
        date_str = date_str.split(' ')[0]
    
    # Try different date formats - prioritize dd-mm-yyyy
    date_formats = [
        '%d-%m-%Y',    # dd-mm-yyyy (your Excel format)
        '%d/%m/%Y',    # dd/mm/yyyy
        '%Y-%m-%d',    # yyyy-mm-dd
        '%m/%d/%Y',    # mm/dd/yyyy
        '%Y/%m/%d'     # yyyy/mm/dd
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def is_numeric_column(series_data, threshold=0.7):
    """Check if a column contains mostly numeric data"""
    non_null_data = [x for x in series_data if x is not None and str(x).strip() != '']
    if len(non_null_data) == 0:
        return False
    
    numeric_count = 0
    for value in non_null_data:
        try:
            float(str(value))
            numeric_count += 1
        except:
            pass
    
    return (numeric_count / len(non_null_data)) >= threshold

def is_date_column(series_data, threshold=0.5):
    """Check if a column contains mostly date-like data"""
    non_null_data = [x for x in series_data if x is not None and str(x).strip() != '']
    if len(non_null_data) == 0:
        return False
    
    date_count = 0
    # Updated patterns to include dd-mm-yyyy format
    date_patterns = [
        r'\d{1,2}-\d{1,2}-\d{4}',  # DD-MM-YYYY or MM-DD-YYYY
        r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
        r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY or DD/MM/YYYY
    ]
    
    for value in non_null_data:
        value_str = str(value)
        for pattern in date_patterns:
            if re.search(pattern, value_str):
                date_count += 1
                break
        # Also check for Excel serial numbers that might be dates
        try:
            float_val = float(value_str)
            if float_val > 25000:  # Likely Excel date
                date_count += 1
        except:
            pass
    
    return (date_count / len(non_null_data)) >= threshold

def detect_column_structure_improved(df, company_col):
    """Detect the column structure more reliably with better debugging"""
    columns = [col for col in df.columns if col != company_col]
    
    print(f"Analyzing {len(columns)} columns for structure...")
    print(f"All columns: {columns[:20]}...")  # Show first 20 columns
    
    # Check if we need to look at the first row for actual headers
    first_row = df.head(1).to_pandas().iloc[0].tolist()
    print(f"First row values: {first_row[:10]}...")
    
    # Check if the first row contains the actual column headers
    potential_headers = []
    for i, val in enumerate(first_row[1:], 1):  # Skip company column
        if val and str(val).strip() and str(val) != 'nan':
            potential_headers.append((i, str(val).strip()))
    
    print(f"Potential headers from first row: {potential_headers[:10]}...")
    
    # Try to detect monthly patterns in the first row
    monthly_groups = {}
    # Updated regex to handle various date formats including dd-mm-yyyy
    date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})'
    
    for col_idx, header_val in potential_headers:
        match = re.search(date_pattern, header_val)
        if match:
            month_date = match.group(1)
            if month_date not in monthly_groups:
                monthly_groups[month_date] = []
            monthly_groups[month_date].append({
                'col_idx': col_idx,
                'col_name': columns[col_idx-1],
                'header_text': header_val
            })
    
    print(f"Found {len(monthly_groups)} monthly groups from headers")
    
    # If no monthly groups found from headers, fall back to original pattern-based detection
    if not monthly_groups:
        print("No monthly groups found in headers, trying original pattern detection...")
        return detect_column_structure_fallback(df, company_col)
    
    # Process each monthly group
    processed_groups = []
    for month_date, cols in sorted(monthly_groups.items()):
        print(f"Processing month: {month_date} with {len(cols)} columns")
        
        group_info = {
            'month_date': month_date,
            'date_col': None,
            'adj_price_col': None,
            'market_cap_col': None,
            'returns_col': None,
            'low_price_col': None,
            'low_date_col': None
        }
        
        # Match columns based on header text
        for col_info in cols:
            header_text = col_info['header_text'].lower()
            col_name = col_info['col_name']
            
            if 'date' in header_text and '365' not in header_text and 'low' not in header_text:
                group_info['date_col'] = col_name
            elif 'adjusted closing price' in header_text or 'closing price' in header_text:
                group_info['adj_price_col'] = col_name
            elif 'market capitalisation' in header_text or 'market cap' in header_text:
                group_info['market_cap_col'] = col_name
            elif 'total returns' in header_text or 'returns' in header_text:
                group_info['returns_col'] = col_name
            elif '365 days low price date' in header_text or ('low price date' in header_text and '365' in header_text):
                group_info['low_date_col'] = col_name
            elif '365 days low price' in header_text or ('low price' in header_text and '365' in header_text):
                group_info['low_price_col'] = col_name
        
        # Print what we found for this group
        print(f"  Group {month_date} mapping:")
        for key, val in group_info.items():
            if key != 'month_date':
                print(f"    {key}: {val}")
        
        # Only add if we have the essential columns
        if all([group_info['date_col'], group_info['adj_price_col'], 
                group_info['market_cap_col'], group_info['low_price_col']]):
            processed_groups.append(group_info)
            print(f"  ✓ Valid group for {month_date}")
        else:
            print(f"  ✗ Incomplete group for {month_date}")
    
    print(f"Successfully processed {len(processed_groups)} monthly groups")
    return processed_groups

def detect_column_structure_fallback(df, company_col):
    """Fallback method using the original approach with pattern matching"""
    columns = [col for col in df.columns if col != company_col]
    
    print(f"Using fallback detection for {len(columns)} columns...")
    
    # Sample data from first 20 rows for analysis
    sample_size = min(20, df.height)
    
    column_types = []
    for col in columns:
        sample_data = df.select(pl.col(col).head(sample_size)).to_series().to_list()
        
        if is_date_column(sample_data):
            column_types.append('date')
        elif is_numeric_column(sample_data):
            column_types.append('numeric')
        else:
            column_types.append('text')
    
    print(f"Detected column types: {list(zip(columns[:10], column_types[:10]))}...")
    
    # Find repeating patterns
    monthly_groups = []
    i = 0
    
    while i < len(column_types):
        # Look for date column as start of group
        if column_types[i] == 'date':
            group_start = i
            # Check if we have at least 5 more columns after this
            if i + 5 < len(column_types):
                # Expected pattern: date, price, market_cap, returns, low_price, low_date
                expected_pattern = ['date', 'numeric', 'numeric', 'numeric', 'numeric']
                actual_pattern = column_types[i:i+5]
                
                # Allow some flexibility in the pattern
                pattern_match = sum(1 for a, e in zip(actual_pattern, expected_pattern) if a == e) >= 3
                
                if pattern_match:
                    monthly_groups.append({
                        'start_idx': group_start,
                        'date_col': columns[i],
                        'adj_price_col': columns[i+1],
                        'market_cap_col': columns[i+2], 
                        'returns_col': columns[i+3],
                        'low_price_col': columns[i+4],
                        'low_date_col': columns[i+5] if i+5 < len(columns) else None
                    })
                    i += 6  # Move to next potential group
                    continue
        i += 1
    
    print(f"Detected {len(monthly_groups)} monthly data groups using fallback method")
    return monthly_groups

def process_prowess_data_polars(excel_file_path):
    """
    Process Prowess data with improved date handling and column detection
    """
    
    print(f"Processing Excel file: {excel_file_path}")
    
    try:
        # Get sheet names
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_names = excel_file.sheet_names
        print(f"Available sheets: {sheet_names}")
        
        # Enhanced sheet filtering for new naming pattern
        # Skip Query1 sheet and process data sheets (including new naming pattern)
        data_sheets = []
        for sheet in sheet_names:
            sheet_lower = sheet.lower()
            # Skip Query1 and any other non-data sheets
            if 'query' not in sheet_lower and sheet.strip() != '':
                data_sheets.append(sheet)
        
        print(f"Data sheets to process: {data_sheets}")
        
        if not data_sheets:
            print("Warning: No data sheets found! Available sheets:", sheet_names)
            # If no sheets match our filter, process all except Query1
            data_sheets = [sheet for sheet in sheet_names if sheet != 'Query1']
            print(f"Fallback: Processing all non-Query1 sheets: {data_sheets}")
        
        all_processed_data = []
        
        for sheet_name in data_sheets:
            print(f"\nProcessing sheet: {sheet_name}")
            
            try:
                # Read the sheet with pandas first for better Excel handling
                # Don't convert everything to string - preserve numeric date values
                pandas_df = pd.read_excel(excel_file_path, sheet_name=sheet_name)
                
                # Check if the sheet is empty or has no meaningful data
                if pandas_df.empty or pandas_df.shape[0] < 2:
                    print(f"Skipping empty or too small sheet: {sheet_name}")
                    continue
                
                print(f"Original sheet shape: {pandas_df.shape}")
                print(f"Column names: {list(pandas_df.columns)[:10]}...")
                
                # Only convert non-numeric columns to string to preserve Excel date numbers
                for col in pandas_df.columns:
                    if pandas_df[col].dtype == 'object':
                        pandas_df[col] = pandas_df[col].astype(str).replace('nan', '').replace('NaT', '').replace('None', '')
                    # Keep numeric columns as-is (they might be Excel date serial numbers)
                
                # Convert to polars with mixed schema
                df = pl.from_pandas(pandas_df)
                print(f"Raw data shape: {df.shape}")
                
                if df.height == 0:
                    print(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                # Show first few column names for debugging
                print(f"First 10 columns in {sheet_name}: {df.columns[:10]}")
                
                # The first column should be Company Name
                company_col = df.columns[0]
                print(f"Company column: {company_col}")
                
                # Clean up company names and remove header rows
                df = df.with_columns(
                    pl.col(company_col).cast(pl.Utf8, strict=False).alias(company_col)
                )
                
                # Remove rows where company name is null, empty, or header-like
                df = df.filter(
                    pl.col(company_col).is_not_null() & 
                    (pl.col(company_col) != "") &
                    (pl.col(company_col) != "Company Name") &
                    (pl.col(company_col) != company_col) &
                    (~pl.col(company_col).str.contains("Company", literal=False).fill_null(False))
                )
                
                print(f"After filtering companies: {df.shape}")
                
                if df.height == 0:
                    print(f"No valid company data found in {sheet_name}")
                    continue
                
                # Detect column structure with improved method
                monthly_groups = detect_column_structure_improved(df, company_col)
                
                if not monthly_groups:
                    print(f"Could not detect column structure for {sheet_name}, skipping...")
                    # Show some debug info
                    print("Available columns:", df.columns[:20])
                    print("First few rows of data:", df.head(3))
                    continue
                
                # Process each monthly group
                monthly_data = []
                
                for i, group in enumerate(monthly_groups):
                    group_label = group.get('month_date', f'Group_{i+1}')
                    print(f"Processing monthly group {i+1} for {group_label}")
                    
                    try:
                        # Extract and clean the data
                        select_cols = [
                            pl.col(company_col).alias("Company_Name"),
                            pl.col(group['date_col']).alias("Raw_Date"),
                            pl.col(group['adj_price_col']).alias("Raw_Adj_Price"),
                            pl.col(group['market_cap_col']).alias("Raw_Market_Cap"),
                            pl.col(group['returns_col']).alias("Raw_Returns") if group['returns_col'] else pl.lit(None).alias("Raw_Returns"),
                            pl.col(group['low_price_col']).alias("Raw_Low_Price"),
                            pl.col(group['low_date_col']).alias("Raw_Low_Date") if group['low_date_col'] else pl.lit(None).alias("Raw_Low_Date")
                        ]
                        
                        month_data = df.select(select_cols)
                        
                        # Clean and convert data types with proper date handling
                        month_data = month_data.with_columns([
                            # Process dates - separate functions for display and sorting
                            pl.col("Raw_Date").map_elements(
                                lambda x: clean_and_parse_date(x, 'dd/mm/yyyy'), 
                                return_dtype=pl.Utf8
                            ).alias("Date"),
                            
                            pl.col("Raw_Date").map_elements(
                                lambda x: clean_and_parse_date_for_sorting(x), 
                                return_dtype=pl.Datetime
                            ).alias("Date_Sort"),
                            
                            pl.col("Raw_Low_Date").map_elements(
                                lambda x: clean_and_parse_date(x, 'dd/mm/yyyy'), 
                                return_dtype=pl.Utf8
                            ).alias("Low_Price_Date_365"),
                            
                            pl.col("Raw_Low_Date").map_elements(
                                lambda x: clean_and_parse_date_for_sorting(x), 
                                return_dtype=pl.Datetime
                            ).alias("Low_Date_Sort"),
                            
                            # Convert numeric columns with error handling
                            pl.col("Raw_Adj_Price").cast(pl.Float64, strict=False).alias("Adjusted_Closing_Price"),
                            pl.col("Raw_Market_Cap").cast(pl.Float64, strict=False).alias("Market_Capitalisation"),
                            pl.col("Raw_Returns").cast(pl.Float64, strict=False).alias("Total_Returns"),
                            pl.col("Raw_Low_Price").cast(pl.Float64, strict=False).alias("Low_Price_365"),
                            
                            # Add source info
                            pl.lit(sheet_name).alias("Source_Sheet"),
                            pl.lit(f"Group_{i+1}_{group_label}").alias("Monthly_Group")
                        ])
                        
                        # Remove temporary columns
                        month_data = month_data.select([
                            "Company_Name", "Date", "Date_Sort", "Adjusted_Closing_Price", "Market_Capitalisation",
                            "Total_Returns", "Low_Price_365", "Low_Price_Date_365", "Low_Date_Sort", 
                            "Source_Sheet", "Monthly_Group"
                        ])
                        
                        # Filter out rows with invalid data
                        month_data = month_data.filter(
                            pl.col("Company_Name").is_not_null() &
                            pl.col("Date").is_not_null() &
                            pl.col("Date_Sort").is_not_null() &  # Ensure we have sortable dates
                            pl.col("Adjusted_Closing_Price").is_not_null() &
                            pl.col("Market_Capitalisation").is_not_null() &
                            pl.col("Low_Price_365").is_not_null() &
                            (pl.col("Adjusted_Closing_Price") > 0) &  # Avoid division by zero
                            (pl.col("Market_Capitalisation") >= 0)
                        )
                        
                        if month_data.height > 0:
                            # Calculate the ratio: 365 days Low Price / Adjusted Closing Price
                            month_data = month_data.with_columns(
                                (pl.col("Low_Price_365") / pl.col("Adjusted_Closing_Price")).alias("Low_to_Adjusted_Ratio")
                            )
                            
                            monthly_data.append(month_data)
                            print(f"  Added {month_data.height} valid records for {group_label}")
                        else:
                            print(f"  No valid records found for {group_label}")
                            
                    except Exception as e:
                        print(f"Error processing monthly group {group_label}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                if monthly_data:
                    sheet_data = pl.concat(monthly_data)
                    all_processed_data.append(sheet_data)
                    print(f"Total records from {sheet_name}: {sheet_data.height}")
                else:
                    print(f"No monthly data could be processed from {sheet_name}")
                
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not all_processed_data:
            raise ValueError("No data could be processed from any sheet")
        
        # Combine all data
        combined_data = pl.concat(all_processed_data)
        print(f"\nTotal combined records: {combined_data.shape}")
        
        # Show data quality summary
        print("\nData Quality Summary:")
        print(f"Unique companies: {combined_data.select('Company_Name').n_unique()}")
        date_min = combined_data.select(pl.col('Date').min()).item()
        date_max = combined_data.select(pl.col('Date').max()).item()
        print(f"Date range: {date_min} to {date_max}")
        print(f"Records with valid ratios: {combined_data.filter(pl.col('Low_to_Adjusted_Ratio').is_not_null()).height}")
        
        # Step 2: Find companies below 5th percentile based on market capitalization
        print("\nStep 2: Finding companies below 5th percentile by market cap...")
        
        # Calculate average market cap per company across all months
        avg_market_cap = combined_data.group_by("Company_Name").agg(
            pl.col("Market_Capitalisation").mean().alias("Avg_Market_Cap")
        )
        
        # Calculate 5th percentile threshold
        percentile_5 = avg_market_cap.select(
            pl.col("Avg_Market_Cap").quantile(0.05).alias("percentile_5")
        ).item()
        
        print(f"5th percentile market cap threshold: {percentile_5:,.2f}")
        
        # Filter companies below 5th percentile
        small_cap_companies = avg_market_cap.filter(
            pl.col("Avg_Market_Cap") <= percentile_5
        ).select("Company_Name")
        
        print(f"Companies below 5th percentile: {small_cap_companies.height}")
        
        # Filter main data to only include these companies
        filtered_data = combined_data.join(small_cap_companies, on="Company_Name", how="inner")
        print(f"Records for small cap companies: {filtered_data.height}")
        
        # Step 3: Find top 30 and bottom 30 companies based on average ratio
        print("\nStep 3: Finding top 30 and bottom 30 companies by ratio...")
        
        # Calculate average ratio per company
        avg_ratios = filtered_data.group_by("Company_Name").agg(
            pl.col("Low_to_Adjusted_Ratio").mean().alias("Avg_Ratio")
        ).sort("Avg_Ratio")
        
        print(f"Companies with calculated ratios: {avg_ratios.height}")
        
        # Get bottom 30 and top 30
        n_companies = min(30, avg_ratios.height // 2)  # Adjust if we don't have enough companies
        
        bottom_30 = avg_ratios.head(n_companies).with_columns(pl.lit("Bottom 30").alias("Group"))
        top_30 = avg_ratios.tail(n_companies).with_columns(pl.lit("Top 30").alias("Group"))
        
        selected_companies = pl.concat([bottom_30, top_30])
        print(f"Selected companies: {selected_companies.height}")
        
        # Step 4: Create final summary
        print("\nStep 4: Creating final summary...")
        
        # Join with original data to get all details
        final_data = filtered_data.join(
            selected_companies.select(["Company_Name", "Group"]), 
            on="Company_Name", 
            how="inner"
        )
        
        # Add market cap percentile for each record
        final_data = final_data.with_columns(
            (pl.col("Market_Capitalisation").rank("ordinal") / pl.len() * 100).alias("Market_Cap_Percentile")
        )
        
        # Select and rename columns for final output (keep sort columns)
        final_summary = final_data.select([
            pl.col("Company_Name").alias("Name_Of_Company"),
            pl.col("Date"),
            pl.col("Date_Sort"),  # Keep for sorting
            pl.col("Market_Capitalisation"),
            pl.col("Total_Returns"),
            pl.col("Low_Price_Date_365").alias("365_days_Low_Price_Date"),
            pl.col("Low_Date_Sort"),  # Keep for potential sorting
            pl.col("Low_Price_365").alias("365_days_Low_Price"),
            pl.col("Adjusted_Closing_Price"),
            pl.col("Low_to_Adjusted_Ratio").alias("Ratio_Low_to_Adjusted"),
            pl.col("Market_Cap_Percentile").alias("Market_Cap_Percentile"),
            pl.col("Group"),
            pl.col("Source_Sheet"),
            pl.col("Monthly_Group")
        ])
        
        # Apply the required sorting: Source_Sheet (asc), Group (desc), Name_Of_Company (asc), Date (asc)
        # Use the datetime Date_Sort column for proper chronological sorting
        final_summary = final_summary.sort([
            "Source_Sheet",
            "Group", 
            "Name_Of_Company",
            "Date_Sort"
        ], descending=[False, True, False, False])
        
        # Remove the sort helper columns from final output
        final_summary = final_summary.drop(["Date_Sort", "Low_Date_Sort"])
        
        print(f"Final summary shape: {final_summary.shape}")
        return final_summary
        
    except Exception as e:
        print(f"Error in processing: {e}")
        import traceback
        traceback.print_exc()
        raise

# Usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        excel_file = sys.argv[1]
    else:
        excel_file = "2000-2025.xlsx"
    
    try:
        print(f"Processing file: {excel_file}")
        result = process_prowess_data_polars(excel_file)
        
        print("\n" + "="*50)
        print("PROCESSING COMPLETED SUCCESSFULLY!")
        print("="*50)
        
        print(f"\nFinal dataset shape: {result.shape}")
        print(f"Columns: {result.columns}")
        
        if result.height > 0:
            print("\nFirst few rows:")
            print(result.head())
            
            # Check date formats in output
            print("\nDate format samples:")
            date_samples = result.select(['Name_Of_Company', 'Date', '365_days_Low_Price_Date']).head(10)
            print(date_samples)
            
            # Save results
            output_file = "prowess_final_summary_fixed.xlsx"
            result.write_excel(output_file)
            print(f"\nResults saved to: {output_file}")
            
            # Show summary by group
            if 'Group' in result.columns:
                print("\nSummary by Group:")
                group_summary = result.group_by(['Group']).agg([
                    pl.len().alias('Total_Records'),
                    pl.col('Name_Of_Company').n_unique().alias('Unique_Companies'),
                    pl.col('Ratio_Low_to_Adjusted').mean().alias('Avg_Ratio')
                ])
                print(group_summary)
                
                print("\nTop 10 companies by ratio:")
                top_ratios = result.group_by('Name_Of_Company').agg(
                    pl.col('Ratio_Low_to_Adjusted').mean
