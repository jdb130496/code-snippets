import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import re
import sys

def clean_and_parse_date(date_value, output_format='dd/mm/yyyy'):
    """Clean and parse various date formats including dd-mm-yyyy"""
    if pd.isna(date_value) or date_value == '' or str(date_value).strip() == '':
        return None
    
    # Handle datetime objects directly from Excel
    if isinstance(date_value, datetime):
        return date_value.strftime('%d/%m/%Y') if output_format == 'dd/mm/yyyy' else date_value.strftime('%Y-%m-%d')
    
    # Handle pandas Timestamp objects
    if isinstance(date_value, pd.Timestamp):
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
    if pd.isna(date_value) or date_value == '' or str(date_value).strip() == '':
        return None
    
    # Handle datetime objects directly from Excel
    if isinstance(date_value, datetime):
        return date_value
    
    # Handle pandas Timestamp objects
    if isinstance(date_value, pd.Timestamp):
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

def explore_excel_structure(excel_file_path, sheet_name):
    """Explore the Excel structure to find the correct header row"""
    print(f"\nExploring structure of sheet: {sheet_name}")
    
    # Try reading with different header rows
    for header_row in [0, 1, 2, 3]:
        try:
            print(f"\nTrying header_row={header_row}:")
            df = pd.read_excel(excel_file_path, sheet_name=sheet_name, header=header_row, nrows=5)
            print(f"Shape: {df.shape}")
            print("Column names:")
            for i, col in enumerate(df.columns[:10]):
                print(f"  {i+1}: '{col}'")
            if len(df.columns) > 10:
                print(f"  ... and {len(df.columns)-10} more columns")
            
            # Check if this looks like the right header
            date_like_cols = [col for col in df.columns if any(word in str(col).lower() for word in ['date', 'month', 'year', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'])]
            if date_like_cols:
                print(f"Found {len(date_like_cols)} date-like columns with header_row={header_row}")
                return header_row
                
        except Exception as e:
            print(f"Error with header_row={header_row}: {e}")
    
    return 0  # Default to first row

def detect_monthly_columns_new_format(df, company_col):
    """Detect monthly columns in the new format: 'Jan 2000 Date', 'Jan 2000 Adjusted', etc."""
    columns = [col for col in df.columns if col != company_col]
    
    print(f"Analyzing {len(columns)} columns for monthly structure...")
    
    # Debug: Print first 20 column names to understand the structure
    print("Sample column names:")
    for i, col in enumerate(columns[:20]):
        print(f"  {i+1}: '{col}'")
    
    if len(columns) > 20:
        print(f"  ... and {len(columns)-20} more columns")
    
    # Updated patterns to match the new format
    # Looking for patterns like "Jan 2000 Date", "Feb 2000 Adjusted", etc.
    month_pattern = r'([A-Za-z]{3}\s+\d{4})\s+(.+)'
    
    monthly_groups = {}
    
    for col in columns:
        col_str = str(col).strip()
        match = re.search(month_pattern, col_str)
        
        if match:
            month_year = match.group(1)  # e.g., "Jan 2000"
            col_type = match.group(2).lower()  # e.g., "date", "adjusted", etc.
            
            if month_year not in monthly_groups:
                monthly_groups[month_year] = {}
            
            # Map column types based on the actual names in your Excel
            if 'date' in col_type:
                if '365' in col_type or 'low' in col_type:
                    monthly_groups[month_year]['low_date_col'] = col
                else:
                    monthly_groups[month_year]['date_col'] = col
            elif 'adjusted' in col_type:
                monthly_groups[month_year]['adj_price_col'] = col
            elif 'market' in col_type:
                monthly_groups[month_year]['market_cap_col'] = col
            elif 'total' in col_type and 'ret' in col_type:
                monthly_groups[month_year]['returns_col'] = col
            elif '365' in col_type and ('da' in col_type or 'low' in col_type):
                if 'date' in col_type:
                    monthly_groups[month_year]['low_date_col'] = col
                else:
                    monthly_groups[month_year]['low_price_col'] = col
    
    print(f"Found monthly groups: {list(monthly_groups.keys())}")
    
    # Debug: Show what columns were found for each group
    for month_year, cols in monthly_groups.items():
        print(f"\n{month_year} columns:")
        for col_type, col_name in cols.items():
            print(f"  {col_type}: {col_name}")
    
    # Filter complete groups - make requirements more flexible
    complete_groups = []
    for month_year, cols in monthly_groups.items():
        # Check for required columns (adjust based on what's actually available)
        has_date = 'date_col' in cols
        has_price = 'adj_price_col' in cols
        has_market_cap = 'market_cap_col' in cols
        has_low_price = 'low_price_col' in cols
        
        if has_date and has_price and has_market_cap:
            group_data = {
                'month_year': month_year,
                'date_col': cols['date_col'],
                'adj_price_col': cols['adj_price_col'],
                'market_cap_col': cols['market_cap_col'],
                'returns_col': cols.get('returns_col', cols['adj_price_col']),  # Use adj_price if no returns
                'low_price_col': cols.get('low_price_col', cols['adj_price_col']),  # Use adj_price if no low_price
                'low_date_col': cols.get('low_date_col', cols['date_col'])  # Use date if no low_date
            }
            complete_groups.append(group_data)
            print(f"✓ Complete group: {month_year}")
        else:
            missing = []
            if not has_date: missing.append('date')
            if not has_price: missing.append('price')
            if not has_market_cap: missing.append('market_cap')
            print(f"✗ Incomplete group {month_year}, missing: {missing}")
    
    print(f"Found {len(complete_groups)} complete monthly groups")
    return complete_groups

def process_prowess_data_pandas(excel_file_path):
    """Process Prowess data using pandas with dd-mm-yyyy date format support"""
    
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
            print(f"\n{'='*50}")
            print(f"Processing sheet: {sheet_name}")
            print(f"{'='*50}")
            
            try:
                # First, explore the structure to find the right header row
                correct_header_row = explore_excel_structure(excel_file_path, sheet_name)
                
                # Read Excel sheet with the correct header row
                df = pd.read_excel(excel_file_path, sheet_name=sheet_name, header=correct_header_row)
                
                if df.empty or df.shape[0] < 2:
                    print(f"Skipping empty sheet: {sheet_name}")
                    continue
                
                print(f"Sheet shape with header_row={correct_header_row}: {df.shape}")
                
                # Clean company names
                company_col = df.columns[0]
                print(f"Company column: '{company_col}'")
                
                # Clean and filter company data
                df[company_col] = df[company_col].astype(str)
                df = df[
                    df[company_col].notna() & 
                    (df[company_col] != "") &
                    (df[company_col] != "Company Name") &
                    (df[company_col] != "nan") &
                    (~df[company_col].str.contains('Unnamed', na=False))
                ].copy()
                
                if df.empty:
                    print(f"No valid company data in {sheet_name}")
                    continue
                
                print(f"Companies after cleaning: {df.shape[0]}")
                
                # Detect monthly columns using the new format
                monthly_groups = detect_monthly_columns_new_format(df, company_col)
                
                if not monthly_groups:
                    print(f"No monthly groups found in {sheet_name}")
                    
                    # Show sample column names for debugging
                    print("\nSample column names for debugging:")
                    for i, col in enumerate(df.columns[:10]):
                        print(f"  {i}: '{col}'")
                    
                    continue
                
                # Process each monthly group
                monthly_data = []
                
                for group in monthly_groups:
                    print(f"\nProcessing {group['month_year']}")
                    
                    try:
                        # Select and rename columns
                        month_data = df[[
                            company_col,
                            group['date_col'],
                            group['adj_price_col'],
                            group['market_cap_col'],
                            group['returns_col'],
                            group['low_price_col'],
                            group['low_date_col']
                        ]].copy()
                        
                        month_data.columns = [
                            'Company_Name', 'Raw_Date', 'Raw_Adj_Price', 
                            'Raw_Market_Cap', 'Raw_Returns', 'Raw_Low_Price', 'Raw_Low_Date'
                        ]
                        
                        # Process dates
                        print("  Processing dates...")
                        month_data['Date'] = month_data['Raw_Date'].apply(
                            lambda x: clean_and_parse_date(x, 'dd/mm/yyyy')
                        )
                        month_data['Low_Price_Date_365'] = month_data['Raw_Low_Date'].apply(
                            lambda x: clean_and_parse_date(x, 'dd/mm/yyyy')
                        )
                        month_data['Date_Sort'] = month_data['Raw_Date'].apply(
                            lambda x: clean_and_parse_date_for_sorting(x)
                        )
                        
                        # Convert numeric columns
                        print("  Converting numeric columns...")
                        month_data['Adjusted_Closing_Price'] = pd.to_numeric(month_data['Raw_Adj_Price'], errors='coerce')
                        month_data['Market_Capitalisation'] = pd.to_numeric(month_data['Raw_Market_Cap'], errors='coerce')
                        month_data['Total_Returns'] = pd.to_numeric(month_data['Raw_Returns'], errors='coerce')
                        month_data['Low_Price_365'] = pd.to_numeric(month_data['Raw_Low_Price'], errors='coerce')
                        
                        # Add metadata columns
                        month_data['Source_Sheet'] = sheet_name
                        month_data['Monthly_Group'] = group['month_year']
                        
                        # Filter valid data
                        print("  Filtering valid data...")
                        valid_mask = (
                            month_data['Company_Name'].notna() &
                            month_data['Date'].notna() &
                            month_data['Adjusted_Closing_Price'].notna() &
                            month_data['Market_Capitalisation'].notna() &
                            (month_data['Adjusted_Closing_Price'] > 0)
                        )
                        
                        month_data = month_data[valid_mask].copy()
                        
                        if not month_data.empty:
                            # Calculate ratio (handle case where Low_Price_365 might be NaN)
                            month_data['Low_to_Adjusted_Ratio'] = np.where(
                                month_data['Low_Price_365'].notna() & (month_data['Low_Price_365'] > 0),
                                month_data['Low_Price_365'] / month_data['Adjusted_Closing_Price'],
                                np.nan
                            )
                            
                            # Select final columns
                            final_cols = [
                                "Company_Name", "Date", "Date_Sort", "Adjusted_Closing_Price", 
                                "Market_Capitalisation", "Total_Returns", "Low_Price_365", 
                                "Low_Price_Date_365", "Source_Sheet", "Monthly_Group",
                                "Low_to_Adjusted_Ratio"
                            ]
                            
                            month_data = month_data[final_cols]
                            
                            monthly_data.append(month_data)
                            print(f"  Added {len(month_data)} records for {group['month_year']}")
                        else:
                            print(f"  No valid records for {group['month_year']}")
                        
                    except Exception as e:
                        print(f"Error processing {group['month_year']}: {e}")
                        import traceback
                        traceback.print_exc()
                        continue
                
                if monthly_data:
                    sheet_data = pd.concat(monthly_data, ignore_index=True)
                    all_processed_data.append(sheet_data)
                    print(f"Total records from {sheet_name}: {len(sheet_data)}")
                
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        if not all_processed_data:
            raise ValueError("No data could be processed from any sheet")
        
        # Combine all data
        combined_data = pd.concat(all_processed_data, ignore_index=True)
        print(f"\nTotal combined records: {combined_data.shape}")
        
        # Find 5th percentile companies
        print("Calculating 5th percentile companies...")
        avg_market_cap = combined_data.groupby("Company_Name")["Market_Capitalisation"].mean().reset_index()
        avg_market_cap.columns = ["Company_Name", "Avg_Market_Cap"]
        
        percentile_5 = np.percentile(avg_market_cap["Avg_Market_Cap"], 5)
        print(f"5th percentile market cap threshold: {percentile_5:,.2f}")
        
        small_cap_companies = avg_market_cap[avg_market_cap["Avg_Market_Cap"] <= percentile_5]["Company_Name"]
        
        filtered_data = combined_data[combined_data["Company_Name"].isin(small_cap_companies)].copy()
        print(f"Records for small cap companies: {len(filtered_data)}")
        
        # Get top 30 and bottom 30 by ratio (only for companies with valid ratios)
        print("Selecting top and bottom companies by ratio...")
        valid_ratio_data = filtered_data[filtered_data["Low_to_Adjusted_Ratio"].notna()]
        
        if len(valid_ratio_data) == 0:
            print("No companies with valid ratios found!")
            return pd.DataFrame()
        
        avg_ratios = valid_ratio_data.groupby("Company_Name")["Low_to_Adjusted_Ratio"].mean().reset_index()
        avg_ratios.columns = ["Company_Name", "Avg_Ratio"]
        avg_ratios = avg_ratios.sort_values("Avg_Ratio")
        
        n_companies = min(30, len(avg_ratios) // 2)
        
        bottom_30 = avg_ratios.head(n_companies).copy()
        bottom_30["Group"] = "Bottom 30"
        
        top_30 = avg_ratios.tail(n_companies).copy()
        top_30["Group"] = "Top 30"
        
        selected_companies = pd.concat([bottom_30, top_30], ignore_index=True)
        
        # Create final summary
        print("Creating final summary...")
        final_data = filtered_data.merge(
            selected_companies[["Company_Name", "Group"]], 
            on="Company_Name", 
            how="inner"
        )
        
        final_summary = final_data[[
            "Company_Name", "Date", "Date_Sort", "Market_Capitalisation",
            "Total_Returns", "Low_Price_Date_365", "Low_Price_365",
            "Adjusted_Closing_Price", "Low_to_Adjusted_Ratio", "Group",
            "Source_Sheet", "Monthly_Group"
        ]].copy()
        
        final_summary.columns = [
            "Name_Of_Company", "Date", "Date_Sort", "Market_Capitalisation",
            "Total_Returns", "365_days_Low_Price_Date", "365_days_Low_Price",
            "Adjusted_Closing_Price", "Ratio_Low_to_Adjusted", "Group",
            "Source_Sheet", "Monthly_Group"
        ]
        
        # Sort data
        final_summary = final_summary.sort_values([
            "Source_Sheet", "Group", "Name_Of_Company", "Date_Sort"
        ], ascending=[True, False, True, True])
        
        # Remove sort column
        final_summary = final_summary.drop("Date_Sort", axis=1)
        
        print(f"Final summary shape: {final_summary.shape}")
        return final_summary
        
    except Exception as e:
        print(f"Error in processing: {e}")
        raise

# Usage
if __name__ == "__main__":
    excel_file = sys.argv[1] if len(sys.argv) > 1 else "2000-2025-new.xlsx"
    
    try:
        print(f"Processing file: {excel_file}")
        result = process_prowess_data_pandas(excel_file)
        
        print("\nPROCESSING COMPLETED SUCCESSFULLY!")
        print(f"Final dataset shape: {result.shape}")
        
        if not result.empty:
            print("\nFirst few rows:")
            print(result.head())
            
            # Save results
            output_file = "prowess_final_summary_pandas.xlsx"
            result.to_excel(output_file, index=False)
            print(f"\nResults saved to: {output_file}")
            
            # Show summary by group
            print("\nSummary by Group:")
            group_summary = result.groupby('Group').agg({
                'Name_Of_Company': ['count', 'nunique'],
                'Ratio_Low_to_Adjusted': 'mean'
            })
            group_summary.columns = ['Total_Records', 'Unique_Companies', 'Avg_Ratio']
            print(group_summary)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
