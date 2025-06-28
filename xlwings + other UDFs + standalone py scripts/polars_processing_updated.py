
import polars as pl
import pandas as pd
import numpy as np
import datetime

def clean_and_parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        return None

def is_end_of_month(date):
    next_month = date.replace(day=28) + datetime.timedelta(days=4)
    last_day_of_month = next_month - datetime.timedelta(days=next_month.day)
    return date.day == last_day_of_month.day

def process_excel_file(file_path):
    # Read the Excel file
    excel_data = pd.ExcelFile(file_path, engine='openpyxl')
    
    all_data = []
    
    for sheet_name in excel_data.sheet_names:
        # Read each sheet into a DataFrame
        pandas_df = pd.read_excel(file_path, sheet_name=sheet_name, engine='openpyxl')
        
        # Clean and parse dates
        for col in pandas_df.columns:
            if pandas_df[col].dtype == 'object':
                pandas_df[col] = pandas_df[col].astype(str).replace('nan', '').replace('NaT', '').replace('None', '')
                pandas_df[col] = pandas_df[col].apply(clean_and_parse_date)
        
        # Validate end-of-month dates
        for col in pandas_df.columns:
            if pandas_df[col].dtype == 'datetime64[ns]':
                invalid_dates = pandas_df[~pandas_df[col].apply(is_end_of_month)]
                if not invalid_dates.empty:
                    print(f"Warning: Non-end-of-month dates found in sheet '{sheet_name}', column '{col}'")
        
        # Convert DataFrame to Polars DataFrame
        pl_df = pl.from_pandas(pandas_df)
        
        # Append to all_data list
        all_data.append(pl_df)
    
    # Concatenate all data
    final_data = pl.concat(all_data)
    
    # Calculate ratio
    final_data = final_data.with_columns(
        (pl.col("Low_Price_365_Days") / pl.col("Adjusted_Closing_Price")).alias("Price_Ratio")
    )
    
    # Filter companies below 5th percentile based on market capitalization
    market_cap_percentile = final_data.select(
        pl.col("Market_Capitalisation").quantile(0.05)
    ).to_numpy()[0][0]
    
    filtered_data = final_data.filter(
        pl.col("Market_Capitalisation") < market_cap_percentile
    )
    
    # Select top 30 and bottom 30 companies based on Price_Ratio
    top_30 = filtered_data.sort("Price_Ratio", reverse=True).head(30)
    bottom_30 = filtered_data.sort("Price_Ratio").head(30)
    
    final_selection = pl.concat([top_30, bottom_30])
    
    # Calculate Market Cap Percentile
    final_selection = final_selection.with_columns(
        (pl.col("Market_Capitalisation").rank("ordinal") / pl.len() * 100).alias("Market_Cap_Percentile")
    )
    
    # Prepare final summary
    final_summary = final_selection.select([
        "Company_Name",
        "Date",
        "Market_Capitalisation",
        "Total_Returns",
        "Low_Price_365_Days_Date",
        "Low_Price_365_Days",
        "Adjusted_Closing_Price",
        "Price_Ratio",
        "Market_Cap_Percentile"
    ])
    
    # Save to Excel
    final_summary.write_excel("prowess_final_summary_fixed.xlsx")

process_excel_file("prowess_data.xlsx")
