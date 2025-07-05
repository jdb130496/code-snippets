import polars as pl
import pandas as pd
from datetime import datetime, timedelta
import calendar

def get_last_trading_day_of_month(year, month):
    """
    Get the last trading day (weekday) of a given month.
    If month-end is Saturday/Sunday, returns the previous Friday.
    """
    # Get the last day of the month
    last_day = calendar.monthrange(year, month)[1]
    last_date = datetime(year, month, last_day)
    
    # If it's Saturday (5) or Sunday (6), go back to Friday
    while last_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
        last_date -= timedelta(days=1)
    
    return last_date

def is_month_end_trading_date(date_serial):
    """
    Check if a date serial number represents the last trading day of its month.
    Considers weekends - if month-end is Sat/Sun, accepts the previous Friday.
    """
    if pd.isna(date_serial) or date_serial <= 0:
        return False
    
    try:
        # Convert Excel serial date to datetime
        date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_serial))
        
        # Get the last trading day of that month
        last_trading_day = get_last_trading_day_of_month(date_obj.year, date_obj.month)
        
        # Check if current date equals last trading day of month
        return date_obj.date() == last_trading_day.date()
        
    except Exception:
        return False

def filter_month_end_trading_days(df):
    """
    Keep only rows where the Date is the last trading day of that month.
    This accounts for weekends - if month-end is Sat/Sun, keeps Friday's data.
    """
    if 'Date' not in df.columns:
        print("No 'Date' column found - returning original dataframe")
        return df
    
    # Convert to pandas for easier date handling
    df_pandas = df.to_pandas()
    
    print(f"\n=== MONTH-END TRADING DAY FILTERING ===")
    print(f"Before filtering: {len(df_pandas)} total rows")
    
    # Group by Month_Year to see what we have
    if 'Month_Year' in df_pandas.columns:
        month_summary = df_pandas.groupby('Month_Year').agg({
            'Date': ['count', lambda x: sum(df_pandas.loc[x.index, 'Date'].apply(is_month_end_trading_date))]
        }).round(2)
        month_summary.columns = ['Total_Rows', 'Trading_Day_Rows']
        print("\nMonth-wise breakdown (first 10):")
        for month, row in month_summary.head(10).iterrows():
            print(f"  {month}: {row['Total_Rows']} total, {row['Trading_Day_Rows']} trading day")
    
    # Apply month-end trading day filter
    mask = df_pandas['Date'].apply(is_month_end_trading_date)
    df_filtered = df_pandas[mask].copy()
    
    print(f"\nAfter filtering: {len(df_filtered)} rows kept")
    print(f"Removed: {len(df_pandas) - len(df_filtered)} rows with non-trading-day dates")
    
    # Show which months remain and their actual dates
    if 'Month_Year' in df_filtered.columns and len(df_filtered) > 0:
        remaining_months = sorted(df_filtered['Month_Year'].unique())
        print(f"\nMonths remaining after filter: {len(remaining_months)}")
        print("Sample months with their trading day dates:")
        
        for month in remaining_months[:10]:  # Show first 10
            month_data = df_filtered[df_filtered['Month_Year'] == month]
            if len(month_data) > 0:
                date_val = month_data['Date'].iloc[0]
                try:
                    date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_val))
                    weekday_name = date_obj.strftime('%A')
                    print(f"  {month}: {date_obj.strftime('%d/%m/%Y')} ({weekday_name})")
                except:
                    print(f"  {month}: Error converting date")
        
        # Check for specific months you're concerned about
        test_months = ['Apr 2000', 'Jan 2000', 'Jan 2005', 'Jan 2020']
        print(f"\nSpecific month check:")
        for month in test_months:
            count = len(df_filtered[df_filtered['Month_Year'] == month])
            if count > 0:
                # Show the actual date kept
                month_data = df_filtered[df_filtered['Month_Year'] == month]
                date_val = month_data['Date'].iloc[0]
                try:
                    date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_val))
                    weekday_name = date_obj.strftime('%A')
                    print(f"  {month}: {count} companies - {date_obj.strftime('%d/%m/%Y')} ({weekday_name}) ✓")
                except:
                    print(f"  {month}: {count} companies ✓")
            else:
                print(f"  {month}: 0 companies ✗ (LOST)")
    
    # Convert back to polars
    return pl.from_pandas(df_filtered)

# Alternative flexible approach that finds the closest trading day to month-end
def filter_closest_to_month_end_trading_day(df):
    """
    For each Month_Year, keep the date closest to the last trading day of that month.
    This is more flexible and handles cases where exact trading day data doesn't exist.
    """
    if 'Date' not in df.columns:
        print("No 'Date' column found - returning original dataframe")
        return df
    
    def days_from_month_end_trading_day(date_serial, target_month_year):
        """Calculate how many days away from the last trading day this date is"""
        try:
            date_obj = datetime(1899, 12, 30) + timedelta(days=int(date_serial))
            
            # Parse the target month/year to get the right month
            target_date = datetime.strptime(target_month_year, '%b %Y')
            last_trading_day = get_last_trading_day_of_month(target_date.year, target_date.month)
            
            return abs((date_obj.date() - last_trading_day.date()).days)
        except:
            return 999  # Large number for invalid dates
    
    # Convert to pandas for easier processing
    df_pandas = df.to_pandas()
    
    print(f"\n=== FLEXIBLE TRADING DAY FILTERING ===")
    print(f"Before filtering: {len(df_pandas)} total rows")
    
    # For each Month_Year, find the date closest to the last trading day
    def get_closest_to_trading_day(group):
        month_year = group['Month_Year'].iloc[0]
        group['days_from_trading_day'] = group['Date'].apply(
            lambda x: days_from_month_end_trading_day(x, month_year)
        )
        return group.loc[group['days_from_trading_day'].idxmin()]
    
    df_filtered = df_pandas.groupby('Month_Year').apply(get_closest_to_trading_day).reset_index(drop=True)
    
    print(f"After filtering: {len(df_filtered)} rows kept")
    print(f"Kept closest to trading day for each month")
    
    # Show sample results
    print(f"\nSample results (first 10):")
    for _, row in df_filtered.head(10).iterrows():
        try:
            date_obj = datetime(1899, 12, 30) + timedelta(days=int(row['Date']))
            weekday_name = date_obj.strftime('%A')
            
            # Calculate what the ideal trading day would be
            target_date = datetime.strptime(row['Month_Year'], '%b %Y')
            ideal_trading_day = get_last_trading_day_of_month(target_date.year, target_date.month)
            
            is_exact = date_obj.date() == ideal_trading_day.date()
            print(f"  {row['Month_Year']}: {date_obj.strftime('%d/%m/%Y')} ({weekday_name}) {'✓' if is_exact else '(closest)'}")
        except:
            print(f"  {row['Month_Year']}: Error converting date")
    
    # Clean up temporary column if it exists
    if 'days_from_trading_day' in df_filtered.columns:
        df_filtered = df_filtered.drop('days_from_trading_day', axis=1)
    
    return pl.from_pandas(df_filtered)


# Example usage in your main function:
"""
Replace your current filter_month_end_only() call with either:

# Option 1: Strict - only keep exact last trading days
df_filtered = filter_month_end_trading_days(df_pivoted)

# Option 2: Flexible - keep closest to last trading day (RECOMMENDED)
df_filtered = filter_closest_to_month_end_trading_day(df_pivoted)
"""
