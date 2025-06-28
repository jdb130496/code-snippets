import polars as pl
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re

def clean_and_parse_date(date_value, output_format='dd/mm/yyyy'):
    """Clean and parse various date formats including dd-mm-yyyy"""
    if date_value is None or date_value == '' or str(date_value).strip() == '':
        return None
    
    # Handle datetime objects directly from Excel
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y') if output_format == 'dd/mm/yyyy' else date_value.strftime('%Y-%m-%d')
    
    # Handle pandas Timestamp objects
    if hasattr(date_value, 'to_pydatetime'):
        dt = date_value.to_pydatetime()
        return dt.strftime('%d/%m/%Y') if output_format == 'dd/mm/yyyy' else dt.strftime('%Y-%m-%d')
    
    date_str = str(date_value).strip()
    
    if date_str.lower() in ['nan', 'none', 'nat']:
        return None
    
    # Handle Excel serial number dates
    try:
        float_val = float(date_str)
        if float_val > 25000:
            excel_epoch = datetime(1899, 12, 30)
            parsed_date = excel_epoch + timedelta(days=float_val)
            return parsed_date.strftime('%d/%m/%Y') if output_format == 'dd/mm/yyyy' else parsed_date.strftime('%Y-%m-%d')
        elif '.' in date_str and len(date_str) < 10 and float_val < 100:
            return None
    except:
        pass
    
    # Handle timestamp format
    if '00:00:00' in date_str:
        date_str = date_str.split(' ')[0]
    
    # Try different date formats - prioritize dd-mm-yyyy
    date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt)
            return parsed_date.strftime('%d/%m/%Y') if output_format == 'dd/mm/yyyy' else parsed_date.strftime('%Y-%m-%d')
        except:
            continue
    
    return None

def clean_and_parse_date_for_sorting(date_value):
    """Parse date and return datetime object for sorting"""
    if date_value is None or date_value == '' or str(date_value).strip() == '':
        return None
    
    # Handle datetime objects directly from Excel
    if isinstance(date_value, datetime):
        return date_value
    
    # Handle pandas Timestamp objects
    if hasattr(date_value, 'to_pydatetime'):
        return date_value.to_pydatetime()
    
    date_str = str(date_value).strip()
    
    if date_str.lower() in ['nan', 'none', 'nat']:
        return None
    
    # Handle Excel serial number dates
    try:
        float_val = float(date_str)
        if float_val > 25000:
            excel_epoch = datetime(1899, 12, 30)
            return excel_epoch + timedelta(days=float_val)
        elif '.' in date_str and len(date_str) < 10 and float_val < 100:
            return None
    except:
        pass
    
    if '00:00:00' in date_str:
        date_str = date_str.split(' ')[0]
    
    date_formats = ['%d-%m-%Y', '%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%Y/%m/%d']
    
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    
    return None

def detect_monthly_columns(df, company_col):
    """Detect monthly columns by looking for date patterns in column names"""
    columns = [col for col in df.columns if col != company_col]
    
    print(f"Analyzing {len(columns)} columns for monthly structure...")
    
    # Pattern to match monthly columns like "Jan 2000 Date", "Jan 2000 365 days Low Price Date"
    month_pattern = r'([A-Za-z]{3}\s+\d{4})'
    
    monthly_groups = {}
    
    for col in columns:
        match = re.search(month_pattern, col)
        if match:
            month_year = match.group(1)
            if month_year not in monthly_groups:
                monthly_groups[month_year] = {}
            
            col_lower = col.lower()
            if 'date' in col_lower and '365' not in col_lower:
                monthly_groups[month_year]['date_col'] = col
            elif '365 days low price date' in col_lower:
                monthly_groups[month_year]['low_date_col'] = col
            elif 'adjusted closing price' in col_lower or 'closing price' in col_lower:
                monthly_groups[month_year]['adj_price_col'] = col
            elif 'market capitalisation' in col_lower:
                monthly_groups[month_year]['market_cap_col'] = col
            elif 'total returns' in col_lower:
                monthly_groups[month_year]['returns_col'] = col
            elif '365 days low price' in col_lower:
                monthly_groups[month_year]['low_price_col'] = col
    
    # Filter complete groups
    complete_groups = []
    for month_year, cols in monthly_groups.items():
        if all(key in cols for key in ['date_col', 'adj_price_col', 'market_cap_col', 'low_price_col']):
            complete_groups.append({
                'month_year': month_year,
                **cols
            })
    
    print(f"Found {len(complete_groups)} complete monthly groups")
    return complete_groups

def process_prowess_data_polars(excel_file_path):
    """Process Prowess data with dd-mm-yyyy date format support"""
    
    print(f"Processing Excel file: {excel_file_path}")
    
    try:
        excel_file = pd.ExcelFile(excel_file_path)
        sheet_names = excel_file.sheet_names
        print(f"Available sheets: {sheet_names}")
        
        # Skip Query sheets
        data_sheets = [sheet for sheet in sheet_names if 'query' not in sheet.lower()]
        print(f"Data sheets to process: {data_sheets}")
        
        all_processed_data = []
        
        for sheet_name in data_sheets:
            print(f"\nProcessing sheet: {sheet_name}")
            
            try:
                # Read Excel sheet - convert all data to strings first to avoid serialization issues
                pandas_df = pd.read_excel(excel_file_path, sheet_name=sheet_name, dtype=str)
                
                if pandas_df.empty or pandas_df.shape[0] < 2:
                    print(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                print(f"Sheet shape: {pandas_df.shape}")
                
                # Convert to polars
                df = pl.from_pandas(pandas_df)
                
                # Clean company names
                company_col = df.columns[0]
                df = df.with_columns(pl.col(company_col).cast(pl.Utf8, strict=False))
                df = df.filter(
                    pl.col(company_col).is_not_null() & 
                    (pl.col(company_col) != "") &
                    (pl.col(company_col) != "Company Name")
                )
                
                if df.height == 0:
                    print(f"No valid company data in {sheet_name}")
                    continue
                
                # Detect monthly columns
                monthly_groups = detect_monthly_columns(df, company_col)
                
                if not monthly_groups:
                    print(f"No monthly groups found in {sheet_name}")
                    continue
                
                # Process each monthly group
                monthly_data = []
                
                for group in monthly_groups:
                    print(f"Processing {group['month_year']}")
                    
                    try:
                        # Select columns
                        select_cols = [
                            pl.col(company_col).alias("Company_Name"),
                            pl.col(group['date_col']).alias("Raw_Date"),
                            pl.col(group['adj_price_col']).alias("Raw_Adj_Price"),
                            pl.col(group['market_cap_col']).alias("Raw_Market_Cap"),
                            pl.col(group.get('returns_col', group['adj_price_col'])).alias("Raw_Returns"),
                            pl.col(group['low_price_col']).alias("Raw_Low_Price"),
                            pl.col(group.get('low_date_col', group['date_col'])).alias("Raw_Low_Date")
                        ]
                        
                        month_data = df.select(select_cols)
                        
                        # Clean and convert data using apply instead of map_elements for better compatibility
                        # First convert to pandas for date processing, then back to polars
                        month_pandas = month_data.to_pandas()
                        
                        # Process dates
                        month_pandas['Date'] = month_pandas['Raw_Date'].apply(
                            lambda x: clean_and_parse_date(x, 'dd/mm/yyyy')
                        )
                        month_pandas['Low_Price_Date_365'] = month_pandas['Raw_Low_Date'].apply(
                            lambda x: clean_and_parse_date(x, 'dd/mm/yyyy')
                        )
                        month_pandas['Date_Sort'] = month_pandas['Raw_Date'].apply(
                            lambda x: clean_and_parse_date_for_sorting(x)
                        )
                        
                        # Convert numeric columns
                        month_pandas['Adjusted_Closing_Price'] = pd.to_numeric(month_pandas['Raw_Adj_Price'], errors='coerce')
                        month_pandas['Market_Capitalisation'] = pd.to_numeric(month_pandas['Raw_Market_Cap'], errors='coerce')
                        month_pandas['Total_Returns'] = pd.to_numeric(month_pandas['Raw_Returns'], errors='coerce')
                        month_pandas['Low_Price_365'] = pd.to_numeric(month_pandas['Raw_Low_Price'], errors='coerce')
                        
                        # Add metadata columns
                        month_pandas['Source_Sheet'] = sheet_name
                        month_pandas['Monthly_Group'] = group['month_year']
                        
                        # Convert back to polars
                        month_data = pl.from_pandas(month_pandas)
                        
                        # Select final columns
                        month_data = month_data.select([
                            "Company_Name", "Date", "Date_Sort", "Adjusted_Closing_Price", 
                            "Market_Capitalisation", "Total_Returns", "Low_Price_365", 
                            "Low_Price_Date_365", "Source_Sheet", "Monthly_Group"
                        ])
                        
                        # Filter valid data
                        month_data = month_data.filter(
                            pl.col("Company_Name").is_not_null() &
                            pl.col("Date").is_not_null() &
                            pl.col("Adjusted_Closing_Price").is_not_null() &
                            pl.col("Market_Capitalisation").is_not_null() &
                            pl.col("Low_Price_365").is_not_null() &
                            (pl.col("Adjusted_Closing_Price") > 0)
                        )
                        
                        if month_data.height > 0:
                            # Calculate ratio
                            month_data = month_data.with_columns(
                                (pl.col("Low_Price_365") / pl.col("Adjusted_Closing_Price")).alias("Low_to_Adjusted_Ratio")
                            )
                            
                            monthly_data.append(month_data)
                            print(f"  Added {month_data.height} records for {group['month_year']}")
                        
                    except Exception as e:
                        print(f"Error processing {group['month_year']}: {e}")
                        continue
                
                if monthly_data:
                    sheet_data = pl.concat(monthly_data)
                    all_processed_data.append(sheet_data)
                    print(f"Total records from {sheet_name}: {sheet_data.height}")
                
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {e}")
                continue
        
        if not all_processed_data:
            raise ValueError("No data could be processed from any sheet")
        
        # Combine all data
        combined_data = pl.concat(all_processed_data)
        print(f"\nTotal combined records: {combined_data.shape}")
        
        # Find 5th percentile companies
        avg_market_cap = combined_data.group_by("Company_Name").agg(
            pl.col("Market_Capitalisation").mean().alias("Avg_Market_Cap")
        )
        
        percentile_5 = avg_market_cap.select(
            pl.col("Avg_Market_Cap").quantile(0.05)
        ).item()
        
        print(f"5th percentile market cap threshold: {percentile_5:,.2f}")
        
        small_cap_companies = avg_market_cap.filter(
            pl.col("Avg_Market_Cap") <= percentile_5
        ).select("Company_Name")
        
        filtered_data = combined_data.join(small_cap_companies, on="Company_Name", how="inner")
        print(f"Records for small cap companies: {filtered_data.height}")
        
        # Get top 30 and bottom 30 by ratio
        avg_ratios = filtered_data.group_by("Company_Name").agg(
            pl.col("Low_to_Adjusted_Ratio").mean().alias("Avg_Ratio")
        ).sort("Avg_Ratio")
        
        n_companies = min(30, avg_ratios.height // 2)
        
        bottom_30 = avg_ratios.head(n_companies).with_columns(pl.lit("Bottom 30").alias("Group"))
        top_30 = avg_ratios.tail(n_companies).with_columns(pl.lit("Top 30").alias("Group"))
        
        selected_companies = pl.concat([bottom_30, top_30])
        
        # Create final summary
        final_data = filtered_data.join(
            selected_companies.select(["Company_Name", "Group"]), 
            on="Company_Name", 
            how="inner"
        )
        
        final_summary = final_data.select([
            pl.col("Company_Name").alias("Name_Of_Company"),
            pl.col("Date"),
            pl.col("Date_Sort"),
            pl.col("Market_Capitalisation"),
            pl.col("Total_Returns"),
            pl.col("Low_Price_Date_365").alias("365_days_Low_Price_Date"),
            pl.col("Low_Price_365").alias("365_days_Low_Price"),
            pl.col("Adjusted_Closing_Price"),
            pl.col("Low_to_Adjusted_Ratio").alias("Ratio_Low_to_Adjusted"),
            pl.col("Group"),
            pl.col("Source_Sheet"),
            pl.col("Monthly_Group")
        ])
        
        # Sort data
        final_summary = final_summary.sort([
            "Source_Sheet",
            "Group", 
            "Name_Of_Company",
            "Date_Sort"
        ], descending=[False, True, False, False])
        
        # Remove sort column
        final_summary = final_summary.drop("Date_Sort")
        
        print(f"Final summary shape: {final_summary.shape}")
        return final_summary
        
    except Exception as e:
        print(f"Error in processing: {e}")
        raise

# Usage
if __name__ == "__main__":
    import sys
    
    excel_file = sys.argv[1] if len(sys.argv) > 1 else "2000-2025-new.xlsx"
    
    try:
        print(f"Processing file: {excel_file}")
        result = process_prowess_data_polars(excel_file)
        
        print("\nPROCESSING COMPLETED SUCCESSFULLY!")
        print(f"Final dataset shape: {result.shape}")
        
        if result.height > 0:
            print("\nFirst few rows:")
            print(result.head())
            
            # Save results
            output_file = "prowess_final_summary_fixed.xlsx"
            result.write_excel(output_file)
            print(f"\nResults saved to: {output_file}")
            
            # Show summary by group
            print("\nSummary by Group:")
            group_summary = result.group_by(['Group']).agg([
                pl.len().alias('Total_Records'),
                pl.col('Name_Of_Company').n_unique().alias('Unique_Companies'),
                pl.col('Ratio_Low_to_Adjusted').mean().alias('Avg_Ratio')
            ])
            print(group_summary)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
