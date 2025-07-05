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
    """Extract month/year and metric from column headers"""
    
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
    
    metric_mapping = {
        '365 days First Closing': '365 days Low Price',
        '365 days First Closing Date': '365 days Low Price Date',
    }
    
    df = df.with_columns([
        pl.col('Metric').map_elements(
            lambda x: metric_mapping.get(x, x), 
            return_dtype=pl.Utf8
        ).alias('Metric')
    ])
    
    return df

def pivot_and_convert_dates(df):
    """Pivot data and convert dates to Excel serial format"""
    
    try:
        pivoted = df.pivot(
            values='Value',
            index=['Company Name', 'Month_Year', 'Source_Tab'], 
            on='Metric'
        )
    except Exception as e:
        raise
    
    pivoted = pivoted.with_columns([
        pl.col('Month_Year').str.strptime(pl.Date, '%b %Y').dt.timestamp().cast(pl.Int64).floordiv(86400000000).add(25569).alias('Date')
    ])
    
    return pivoted

def analyze_jan_2000_ties(df):
    """Detailed analysis of Jan 2000 data focusing on tie-breaking"""
    
    print("=== TIE-BREAKING ANALYSIS FOR JAN 2000 ===")
    
    # Find required columns
    required_cols = {
        'market_cap': None,
        'low_price': None,
        'adj_close': None
    }
    
    market_cap_candidates = [col for col in df.columns if 'market' in col.lower() and 'cap' in col.lower()]
    if market_cap_candidates:
        required_cols['market_cap'] = market_cap_candidates[0]
    
    low_price_candidates = [col for col in df.columns if '365 days low price' in col.lower()]
    if low_price_candidates:
        required_cols['low_price'] = low_price_candidates[0]
    
    adj_close_candidates = [col for col in df.columns if 'adjusted closing price' in col.lower()]
    if adj_close_candidates:
        required_cols['adj_close'] = adj_close_candidates[0]
    
    missing_types = [key for key, col in required_cols.items() if col is None]
    if missing_types:
        raise ValueError(f"Cannot find required columns for: {missing_types}")
    
    # Filter for Jan 2000 data
    jan_2000_date = 36526  # Excel serial for Jan 2000
    jan_data = df.filter(pl.col('Date') == jan_2000_date)
    
    if jan_data.height == 0:
        print("No Jan 2000 data found")
        return
    
    print(f"Total companies in Jan 2000: {jan_data.height}")
    
    # Calculate ratio
    jan_data = jan_data.with_columns([
        (pl.col(required_cols['low_price']).fill_null(0) / 
         pl.when(pl.col(required_cols['adj_close']).fill_null(0) != 0)
         .then(pl.col(required_cols['adj_close']).fill_null(0))
         .otherwise(1)).alias('Ratio')
    ])
    
    # Filter out invalid data
    jan_clean = jan_data.filter(
        (pl.col(required_cols['market_cap']).is_not_null()) &
        (pl.col(required_cols['market_cap']) > 0) &
        (pl.col(required_cols['low_price']).is_not_null()) &
        (pl.col(required_cols['low_price']) > 0) &
        (pl.col(required_cols['adj_close']).is_not_null()) &
        (pl.col(required_cols['adj_close']) > 0)
    )
    
    print(f"Valid companies after filtering: {jan_clean.height}")
    
    # Calculate 5th percentile
    market_cap_5th_percentile = jan_clean.select(
        pl.col(required_cols['market_cap']).quantile(0.05)
    ).item(0, 0)
    
    print(f"Market Cap 5th percentile: {market_cap_5th_percentile}")
    
    # Filter to small cap companies
    small_cap = jan_clean.filter(
        pl.col(required_cols['market_cap']) < market_cap_5th_percentile
    )
    
    print(f"Small cap companies (below 5th percentile): {small_cap.height}")
    
    # Add original row index for stable sorting analysis
    small_cap = small_cap.with_row_index("original_order")
    
    # Analyze ties in ratios
    ratio_counts = small_cap.group_by('Ratio').len().sort('len', descending=True)
    ties = ratio_counts.filter(pl.col('len') > 1)
    
    print(f"\nRatio tie analysis:")
    print(f"Unique ratios: {ratio_counts.height}")
    print(f"Tied ratios (>1 company): {ties.height}")
    
    if ties.height > 0:
        print("\nTop tied ratios:")
        print(ties.head(10))
        
        # Show companies with tied ratios
        for i in range(min(3, ties.height)):
            tied_ratio = ties.row(i)[0]
            tied_companies = small_cap.filter(pl.col('Ratio') == tied_ratio)
            print(f"\nCompanies with ratio {tied_ratio}:")
            companies_info = tied_companies.select([
                'Company Name', 
                'Ratio', 
                required_cols['market_cap'],
                'original_order'
            ]).sort('original_order')
            print(companies_info)
    
    # Test different sorting strategies
    print("\n=== TESTING DIFFERENT SORTING STRATEGIES ===")
    
    # Strategy 1: Sort by ratio only (current approach)
    sorted_by_ratio_only = small_cap.sort('Ratio')
    bottom30_strategy1 = sorted_by_ratio_only.head(30)
    
    # Strategy 2: Sort by ratio, then by company name (alphabetical tie-breaking)
    sorted_by_ratio_name = small_cap.sort(['Ratio', 'Company Name'])
    bottom30_strategy2 = sorted_by_ratio_name.head(30)
    
    # Strategy 3: Sort by ratio, then by market cap (financial tie-breaking)
    sorted_by_ratio_mcap = small_cap.sort(['Ratio', required_cols['market_cap']])
    bottom30_strategy3 = sorted_by_ratio_mcap.head(30)
    
    # Strategy 4: Sort by ratio, then by original order (stable sort)
    sorted_by_ratio_order = small_cap.sort(['Ratio', 'original_order'])
    bottom30_strategy4 = sorted_by_ratio_order.head(30)
    
    # Strategy 5: Reverse original order for ties (Excel might do this)
    sorted_by_ratio_reverse = small_cap.sort(['Ratio', 'original_order'], descending=[False, True])
    bottom30_strategy5 = sorted_by_ratio_reverse.head(30)
    
    print("Bottom 30 companies using different tie-breaking strategies:")
    
    strategies = [
        ("Strategy 1 (Ratio only)", bottom30_strategy1),
        ("Strategy 2 (Ratio + Name)", bottom30_strategy2),
        ("Strategy 3 (Ratio + Market Cap)", bottom30_strategy3),
        ("Strategy 4 (Ratio + Original Order)", bottom30_strategy4),
        ("Strategy 5 (Ratio + Reverse Order)", bottom30_strategy5),
    ]
    
    for strategy_name, strategy_result in strategies:
        print(f"\n{strategy_name}:")
        companies = strategy_result.select(['Company Name', 'Ratio']).to_pandas()
        for idx, row in companies.iterrows():
            print(f"  {idx+1:2d}. {row['Company Name']}: {row['Ratio']:.10f}")
    
    # Compare strategies
    print("\n=== STRATEGY COMPARISON ===")
    base_companies = set(bottom30_strategy1.select('Company Name').to_series())
    
    for strategy_name, strategy_result in strategies[1:]:
        strategy_companies = set(strategy_result.select('Company Name').to_series())
        differences = base_companies.symmetric_difference(strategy_companies)
        print(f"{strategy_name}: {len(differences)} differences from Strategy 1")
        if differences and len(differences) <= 10:
            print(f"  Different companies: {list(differences)}")
    
    # Precision analysis
    print("\n=== PRECISION ANALYSIS ===")
    ratios = small_cap.select('Ratio').to_series()
    
    # Round to different precision levels
    precision_levels = [6, 8, 10, 12, 15]
    for precision in precision_levels:
        rounded_ratios = [round(r, precision) for r in ratios]
        unique_rounded = len(set(rounded_ratios))
        print(f"Precision {precision} decimal places: {unique_rounded} unique ratios")
    
    return small_cap

def main():
    file_path = "2000-2025-new.xlsx"
    
    try:
        combined_df = process_excel_file(file_path)
        df_extracted = extract_dates_and_metrics(combined_df)
        df_standardized = standardize_metric_names(df_extracted)
        df_pivoted = pivot_and_convert_dates(df_standardized)
        
        # Focus on Jan 2000 tie analysis
        jan_data = analyze_jan_2000_ties(df_pivoted)
        
        print("\n=== RECOMMENDATIONS ===")
        print("1. Check if Excel is using a different tie-breaking strategy")
        print("2. Verify if precision differences affect the results")
        print("3. Consider the original data order in your Excel file")
        print("4. Test with one of the alternative sorting strategies above")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
