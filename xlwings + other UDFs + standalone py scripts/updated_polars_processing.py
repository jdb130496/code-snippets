
import polars as pl
import pandas as pd
import datetime

def clean_and_parse_date(date_str):
    try:
        return datetime.datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        return None

def is_end_of_month(date):
    next_month = date.replace(day=28) + datetime.timedelta(days=4)
    return next_month.day == 1

def process_excel_file(file_path):
    excel_data = pd.ExcelFile(file_path)
    all_data = []

    for sheet_name in excel_data.sheet_names:
        pandas_df = excel_data.parse(sheet_name)
        pandas_df.columns = pandas_df.columns.str.strip().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')

        for col in pandas_df.columns:
            pandas_df[col] = pandas_df[col].astype(str).replace('nan', '').replace('NaT', '').replace('None', '')
            if 'date' in col.lower():
                pandas_df[col] = pandas_df[col].apply(clean_and_parse_date)
                invalid_dates = pandas_df[col].apply(lambda x: x is not None and not is_end_of_month(x))
                if invalid_dates.any():
                    print(f"Warning: Non-end-of-month dates found in sheet '{sheet_name}', column '{col}'")

        pl_df = pl.from_pandas(pandas_df)
        all_data.append(pl_df)

    combined_df = pl.concat(all_data)

    combined_df = combined_df.with_columns([
        (pl.col("Low_Price") / pl.col("Adjusted_Closing_Price")).alias("Price_Ratio")
    ])

    market_cap_percentile = combined_df.select([
        pl.col("Market_Capitalisation").rank("ordinal").alias("Market_Cap_Rank"),
        pl.col("Market_Capitalisation")
    ])
    market_cap_percentile = market_cap_percentile.with_columns([
        (pl.col("Market_Cap_Rank") / pl.count() * 100).alias("Market_Cap_Percentile")
    ])

    combined_df = combined_df.join(market_cap_percentile, on="Market_Capitalisation")

    filtered_df = combined_df.filter(pl.col("Market_Cap_Percentile") <= 5)

    top_30 = filtered_df.sort("Price_Ratio").head(30)
    bottom_30 = filtered_df.sort("Price_Ratio", reverse=True).head(30)

    final_df = pl.concat([top_30, bottom_30])

    final_df = final_df.select([
        pl.col("Company_Name"),
        pl.col("Date"),
        pl.col("Market_Capitalisation"),
        pl.col("Total_Returns"),
        pl.col("Low_Price_Date"),
        pl.col("Low_Price"),
        pl.col("Adjusted_Closing_Price"),
        pl.col("Price_Ratio"),
        pl.col("Market_Cap_Percentile")
    ])

    final_df.write_csv("processed_data.csv")
