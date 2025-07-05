import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import calendar

def process_excel_complete(file_path="2000-2025-new.xlsx", output_file='ranking_results.xlsx'):
    def get_last_trading_day(year, month):
        manual_dates = {
            (2001, 11): 29, (2002, 3): 28, (2009, 4): 29, (2011, 8): 30,
            (2013, 3): 28, (2014, 8): 28, (2016, 10): 30, (2018, 3): 28,
            (2020, 11): 27, (2022, 8): 30, (2024, 3): 28
        }
        if (year, month) in manual_dates:
            return datetime(year, month, manual_dates[(year, month)])
        last_day = calendar.monthrange(year, month)[1]
        last_date = datetime(year, month, last_day)
        while last_date.weekday() >= 5:
            last_date -= timedelta(days=1)
        return last_date
    
    def is_trading_day(date_serial):
        if pd.isna(date_serial) or date_serial <= 0:
            return False
        try:
            date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_serial))
            last_trading_day = get_last_trading_day(date_obj.year, date_obj.month)
            return date_obj.date() == last_trading_day.date()
        except:
            return False
    
    def days_from_trading_day(date_serial, target_month_year):
        try:
            date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_serial))
            target_date = datetime.strptime(target_month_year, '%b %Y')
            last_trading_day = get_last_trading_day(target_date.year, target_date.month)
            return abs((date_obj.date() - last_trading_day.date()).days)
        except:
            return 999
    
    excel_file = pd.ExcelFile(file_path)
    expected_tabs = ['2000-2005', '2005-2010', '2010-2015', '2015-2020', '2020-2025']
    tabs_to_process = []
    
    for expected in expected_tabs:
        if expected in excel_file.sheet_names:
            tabs_to_process.append(expected)
        else:
            similar = [tab for tab in excel_file.sheet_names if expected.replace('-', '') in tab.replace('-', '')]
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
            melted = tab_df.unpivot(index=['Company Name', 'Source_Tab'], on=value_cols, variable_name='Column', value_name='Value')
            all_tab_data.append(melted)
        except:
            continue
    
    if not all_tab_data:
        raise ValueError("No data found")
    
    combined_df = pl.concat(all_tab_data)
    
    df = combined_df.with_columns([
        pl.col('Column').str.extract(r'^(\w{3} \d{4})').alias('Month_Year'),
        pl.col('Column').str.replace(r'^\w{3} \d{4} ', '').alias('Metric')
    ]).filter(pl.col('Month_Year').is_not_null())
    
    pivoted = df.pivot(values='Value', index=['Company Name', 'Month_Year', 'Source_Tab'], on='Metric')
    
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
            ).otherwise(pl.col('Date')).alias('Date')
        ])
    
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
            ).otherwise(pl.col(date_col)).alias(date_col)
        ])
    
    if 'Date' not in pivoted.columns:
        return None
    
    df_pandas = pivoted.to_pandas()
    
    mask = df_pandas['Date'].apply(is_trading_day)
    df_filtered = df_pandas[mask].copy()
    
    if len(df_filtered) < len(df_pandas) * 0.1:
        def get_closest_to_trading_day(group):
            month_year = group['Month_Year'].iloc[0]
            group['days_from_trading_day'] = group['Date'].apply(lambda x: days_from_trading_day(x, month_year))
            return group.loc[group['days_from_trading_day'].idxmin()]
        
        df_filtered = df_pandas.groupby('Month_Year').apply(get_closest_to_trading_day).reset_index(drop=True)
        if 'days_from_trading_day' in df_filtered.columns:
            df_filtered = df_filtered.drop('days_from_trading_day', axis=1)
    
    df_filtered = pl.from_pandas(df_filtered)
    
    adj_close_candidates = [col for col in df_filtered.columns if 'adjusted closing price' in col.lower()]
    low_price_candidates = [col for col in df_filtered.columns if '365 days low price' in col.lower() and 'date' not in col.lower()]
    low_price_date_candidates = [col for col in df_filtered.columns if '365 days low price date' in col.lower()]
    
    if not adj_close_candidates or not low_price_candidates:
        return None
    
    adj_close_col = adj_close_candidates[0]
    low_price_col = low_price_candidates[0]
    low_price_date_col = low_price_date_candidates[0] if low_price_date_candidates else None
    
    df_with_ratio = df_filtered.with_columns([
        (pl.col(adj_close_col).fill_null(0) / 
         pl.when(pl.col(low_price_col).fill_null(0) != 0)
         .then(pl.col(low_price_col).fill_null(0))
         .otherwise(1)).alias('Ratio'),
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').alias('Month_Year_Date')
    ])
    
    df_clean = df_with_ratio.filter(
        (pl.col(adj_close_col).is_not_null()) &
        (pl.col(adj_close_col) > 0) &
        (pl.col(low_price_col).is_not_null()) &
        (pl.col(low_price_col) > 0)
    ).sort(['Month_Year_Date', 'Source_Tab']).unique(subset=['Company Name', 'Month_Year'], keep='last')
    
    unique_periods = df_clean.select(['Month_Year', 'Source_Tab', 'Month_Year_Date']).unique().sort(['Source_Tab', 'Month_Year_Date'])
    
    top30_results = []
    bottom30_results = []
    
    for period_row in unique_periods.iter_rows():
        month_year, source_tab, month_year_date = period_row
        period_data = df_clean.filter((pl.col('Month_Year') == month_year) & (pl.col('Source_Tab') == source_tab))
        
        if period_data.height == 0:
            continue
        
        sorted_desc = period_data.sort('Ratio', descending=True)
        top30 = sorted_desc.head(30).with_columns([
            pl.lit('Top30').alias('Ranking_Category'),
            pl.int_range(1, min(30, sorted_desc.height) + 1).alias('Rank')
        ])
        
        sorted_asc = period_data.sort('Ratio', descending=False)
        bottom30 = sorted_asc.head(30).with_columns([
            pl.lit('Bottom30').alias('Ranking_Category'),
            pl.int_range(1, min(30, sorted_asc.height) + 1).alias('Rank')
        ])
        
        top30_results.append(top30)
        bottom30_results.append(bottom30)
    
    if not top30_results or not bottom30_results:
        return None
    
    rankings_df = pl.concat([pl.concat(top30_results), pl.concat(bottom30_results)])
    df_sorted = rankings_df.sort(['Source_Tab', 'Month_Year_Date', 'Ranking_Category', 'Rank'], descending=[False, False, True, False])
    df_pandas = df_sorted.to_pandas()
    
    def excel_serial_to_date(serial):
        if pd.isna(serial) or serial <= 0:
            return ""
        try:
            date_obj = datetime(1899, 12, 30) + timedelta(days=int(serial))
            return date_obj.strftime('%d/%m/%Y')
        except:
            return str(serial)
    
    if 'Date' in df_pandas.columns:
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
    
    if low_price_date_col:
        df_pandas['365_days_Low_Price_Date_Formatted'] = df_pandas[low_price_date_col].apply(excel_serial_to_date)
    else:
        df_pandas['365_days_Low_Price_Date_Formatted'] = ""
    
    columns_to_include = ['Company Name', 'Date_Formatted', adj_close_col]
    
    for col in df_pandas.columns:
        if 'market capitalisation' in col.lower():
            columns_to_include.append(col)
            break
    
    for col in df_pandas.columns:
        if 'total returns' in col.lower():
            columns_to_include.append(col)
            break
    
    columns_to_include.extend([low_price_col, '365_days_Low_Price_Date_Formatted', 'Month_Year', 'Source_Tab', 'Ratio', 'Ranking_Category', 'Rank'])
    
    final_columns = [col for col in columns_to_include if col in df_pandas.columns]
    df_final = df_pandas[final_columns].copy()
    df_final = df_final.rename(columns={'Date_Formatted': 'Date', '365_days_Low_Price_Date_Formatted': '365_days_Low_Price_Date'})
    
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        df_final.to_excel(writer, sheet_name='All_Rankings', index=False)
        df_final[df_final['Ranking_Category'] == 'Top30'].to_excel(writer, sheet_name='Top30_Rankings', index=False)
        df_final[df_final['Ranking_Category'] == 'Bottom30'].to_excel(writer, sheet_name='Bottom30_Rankings', index=False)
    
    return f"Results exported to: {output_file} with {len(df_final)} total rows"

if __name__ == "__main__":
    try:
        result = process_excel_complete()
        print(result)
    except Exception as e:
        print(f"Error: {e}")
