import xlwings as xw
import pandas as pd
import numpy as np
from datetime import datetime
import os
import threading
from typing import Optional, Dict, List, Any

# Global variables for caching
_processed_data: Optional[pd.DataFrame] = None
_last_file_path: Optional[str] = None
_processing_lock = threading.Lock()

class BSEDataProcessor:
    """Optimized BSE data processor that includes single data point companies."""
    
    def __init__(self):
        self.chunk_size = 50000
        self.required_columns = ['Company Name', 'Date', 'Open Price', 'High Price', 'Low Price', 'Close Price']
        self.optional_columns = ['Market Cap', 'Debt-Equity Ratio', 'Capitaline Code']
    
    def _parse_date_efficiently(self, date_series: pd.Series) -> pd.Series:
        """Efficient date parsing with multiple format attempts."""
        formats = ['%d/%m/%Y', '%Y-%m-%d', '%m/%d/%Y', '%d-%m-%Y']
        
        for fmt in formats:
            try:
                return pd.to_datetime(date_series, format=fmt, errors='coerce')
            except:
                continue
        
        return pd.to_datetime(date_series, errors='coerce')
    
    def _calculate_metrics(self, dates: np.ndarray, prices: np.ndarray) -> Dict[str, float]:
        """Calculate financial metrics efficiently with handling for single data points."""
        if len(dates) < 1 or len(prices) < 1:
            return {}
        
        # Remove invalid data
        valid_mask = (prices > 0) & (~np.isnan(prices))
        valid_count = np.sum(valid_mask)
        
        if valid_count < 1:
            return {}
        
        dates = dates[valid_mask]
        prices = prices[valid_mask]
        
        # Sort by date
        sort_idx = np.argsort(dates)
        dates = dates[sort_idx]
        prices = prices[sort_idx]
        
        # Handle single data point case
        if len(prices) == 1:
            return {
                'cagr': 0.0,
                'mean_price': round(prices[0], 4),
                'std_dev': 0.0,
                'cov': 0.0,
                'latest_price': round(prices[0], 4),
                'data_points': 1,
                'single_data_point': True
            }
        
        # Calculate CAGR (Quarterly basis) for multiple data points
        days_diff = (dates[-1] - dates[0]).astype('timedelta64[D]').astype(int) + 1
        years = days_diff / 365
        
        cagr = None
        if years > 0 and prices[0] > 0:
            quarters = years * 4
            if quarters > 0:
                cagr = ((prices[-1] / prices[0]) ** (1 / quarters) - 1) * 4 * 100
        
        # Handle edge case where start and end dates are the same
        if years == 0:
            if len(prices) > 1:
                cagr = ((prices[-1] / prices[0]) - 1) * 100
            else:
                cagr = 0.0
        
        # Calculate other statistics
        mean_price = np.mean(prices)
        std_dev = np.std(prices, ddof=1)
        cov = std_dev / mean_price if mean_price > 0 else 0.0
        
        return {
            'cagr': round(cagr, 6) if cagr is not None else 0.0,
            'mean_price': round(mean_price, 6),
            'std_dev': round(std_dev, 6),
            'cov': round(cov, 6),
            'latest_price': round(prices[-1], 4),
            'data_points': len(prices),
            'single_data_point': False
        }
    
    def process_file(self, file_path: str) -> Dict[str, Any]:
        """Process CSV file with optimized memory usage."""
        file_path = os.path.normpath(file_path)
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_size_gb = os.path.getsize(file_path) / (1024**3)
        
        # Adjust chunk size based on file size
        if file_size_gb > 2:
            chunk_size = 25000
        elif file_size_gb > 1:
            chunk_size = 40000
        else:
            chunk_size = self.chunk_size
        
        company_data = {}
        processed_chunks = 0
        
        try:
            csv_iterator = pd.read_csv(
                file_path,
                delimiter='\t',
                chunksize=chunk_size,
                low_memory=False,
                dtype={
                    'Company Name': 'string',
                    'Open Price': 'float32',
                    'High Price': 'float32',
                    'Low Price': 'float32',
                    'Close Price': 'float32',
                    'Market Cap': 'float32',
                    'Debt-Equity Ratio': 'float32'
                },
                usecols=lambda x: x in self.required_columns + self.optional_columns
            )
            
            for chunk in csv_iterator:
                processed_chunks += 1
                
                # Skip chunks missing required columns
                if not all(col in chunk.columns for col in self.required_columns):
                    continue
                
                # Calculate average price using vectorized operations
                price_cols = ['Open Price', 'High Price', 'Low Price', 'Close Price']
                chunk['Average_Price'] = chunk[price_cols].mean(axis=1)
                
                # Parse dates efficiently
                chunk['Date'] = self._parse_date_efficiently(chunk['Date'])
                
                # Clean data
                chunk = chunk.dropna(subset=['Date', 'Average_Price'])
                chunk = chunk[chunk['Average_Price'] > 0]
                
                # Group by Company and Date to handle multiple entries per day
                if len(chunk) > 0:
                    chunk = chunk.groupby(['Company Name', 'Date']).agg({
                        'Average_Price': 'mean',
                        'Market Cap': 'last',
                        'Debt-Equity Ratio': 'last',
                        'Capitaline Code': 'first'
                    }).reset_index()
                
                if chunk.empty:
                    continue
                
                # Process each company in the chunk
                for company_name, group in chunk.groupby('Company Name'):
                    if pd.isna(company_name) or company_name == '' or str(company_name).strip() == '':
                        continue
                    
                    company_name = str(company_name).strip()
                    
                    if company_name not in company_data:
                        company_data[company_name] = {
                            'dates': [],
                            'prices': [],
                            'market_caps': [],
                            'debt_equity': [],
                            'capitaline_code': None
                        }
                    
                    # Store data
                    company_data[company_name]['dates'].extend(group['Date'].values)
                    company_data[company_name]['prices'].extend(group['Average_Price'].values)
                    
                    # Handle optional columns
                    if 'Market Cap' in group.columns:
                        company_data[company_name]['market_caps'].extend(
                            group['Market Cap'].fillna(0).values
                        )
                    if 'Debt-Equity Ratio' in group.columns:
                        company_data[company_name]['debt_equity'].extend(
                            group['Debt-Equity Ratio'].fillna(0).values
                        )
                    if 'Capitaline Code' in group.columns and company_data[company_name]['capitaline_code'] is None:
                        codes = group['Capitaline Code'].dropna()
                        if not codes.empty:
                            company_data[company_name]['capitaline_code'] = codes.iloc[0]
        
        except Exception as e:
            raise
        
        return self._calculate_company_metrics(company_data)
    
    def _calculate_company_metrics(self, company_data: Dict) -> Dict[str, Any]:
        """Calculate metrics for all companies including single data point companies."""
        results = []
        single_data_point_companies = 0
        
        for company_name, data in company_data.items():
            # Skip only if no data at all
            if len(data['dates']) < 1:
                continue
            
            # Convert to numpy arrays
            dates = np.array(data['dates'])
            prices = np.array(data['prices'])
            
            # Calculate metrics (now handles single data points)
            metrics = self._calculate_metrics(dates, prices)
            if not metrics:
                continue
            
            # Track single data point companies
            if metrics.get('data_points', 0) == 1:
                single_data_point_companies += 1
            
            # Get latest values
            latest_market_cap = data['market_caps'][-1] if data['market_caps'] else 0
            latest_debt_equity = data['debt_equity'][-1] if data['debt_equity'] else 0
            
            # Create result
            result_row = {
                'Capitaline_Code': data['capitaline_code'] or '',
                'Company_Name': company_name,
                'Price_CAGR': metrics['cagr'],
                'Mean_Price': metrics['mean_price'],
                'Standard_Deviation': metrics['std_dev'],
                'COV': metrics['cov'],
                'Latest_Price': metrics['latest_price'],
                'Latest_Debt_Equity': round(latest_debt_equity, 2),
                'Latest_Market_Cap': round(latest_market_cap, 2),
                'Data_Points': metrics['data_points'],
                'Single_Data_Point': metrics.get('single_data_point', False)
            }
            
            results.append(result_row)
        
        return {
            'dataframe': pd.DataFrame(results),
            'total_companies': len(results),
            'processed_companies': len(company_data),
            'single_data_point_companies': single_data_point_companies
        }

# Initialize processor
processor = BSEDataProcessor()

@xw.func
def process_csv_file(file_path: str) -> str:
    """Process the large CSV file and cache the results"""
    global _processed_data, _last_file_path
    
    if not file_path:
        return "Error: Please provide file_path argument"
    
    file_path = os.path.normpath(file_path)
    
    with _processing_lock:
        try:
            # Check if already processed
            if _processed_data is not None and _last_file_path == file_path:
                single_point_count = (_processed_data['Data_Points'] == 1).sum()
                return f"Data already loaded ({len(_processed_data)} companies, {single_point_count} single data point)"
            
            # Process the file
            result = processor.process_file(file_path)
            _processed_data = result['dataframe']
            _last_file_path = file_path
            
            single_point_count = result.get('single_data_point_companies', 0)
            return f"Success: {result['total_companies']} companies ({single_point_count} single data point)"
            
        except Exception as e:
            return f"Error: {str(e)}"

@xw.func
def get_single_data_point_companies(file_path: str) -> List[List]:
    """Get list of companies with single data points"""
    global _processed_data, _last_file_path
    
    if not file_path:
        return [["Error: Please provide file_path argument"]]
    
    file_path = os.path.normpath(file_path)
    
    if _processed_data is None or _last_file_path != file_path:
        process_result = process_csv_file(file_path)
        if process_result.startswith("Error"):
            return [[process_result]]
    
    try:
        single_point_companies = _processed_data[_processed_data['Data_Points'] == 1].copy()
        
        if single_point_companies.empty:
            return [["No companies with single data point found"]]
        
        result = [["Company Name", "Latest Price", "Market Cap", "Debt-Equity Ratio"]]
        
        for _, row in single_point_companies.iterrows():
            result.append([
                row['Company_Name'],
                row['Latest_Price'],
                row['Latest_Market_Cap'],
                row['Latest_Debt_Equity']
            ])
        
        return result
    
    except Exception as e:
        return [[f"Error: {str(e)}"]]

@xw.func
def get_company_list(file_path: str) -> List[str]:
    """Get list of all company names"""
    global _processed_data, _last_file_path
    
    if not file_path:
        return ["Error: Please provide file_path argument"]
    
    file_path = os.path.normpath(file_path)
    
    if _processed_data is None or _last_file_path != file_path:
        process_result = process_csv_file(file_path)
        if process_result.startswith("Error"):
            return [process_result]
    
    return sorted(_processed_data['Company_Name'].tolist())

@xw.func
def get_company_data(file_path: str, company_name: str, metric: str = "all"):
    """Get specific data for a company"""
    global _processed_data, _last_file_path
    
    if not file_path:
        return "Error: Please provide file_path argument"
    
    file_path = os.path.normpath(file_path)
    
    if _processed_data is None or _last_file_path != file_path:
        process_result = process_csv_file(file_path)
        if process_result.startswith("Error"):
            return process_result
    
    company_data = _processed_data[_processed_data['Company_Name'].str.contains(company_name, case=False, na=False)]
    
    if company_data.empty:
        return f"Error: Company '{company_name}' not found"
    
    row = company_data.iloc[0]
    
    metric_map = {
        "CAGR": "Price_CAGR",
        "COV": "COV", 
        "MEAN_PRICE": "Mean_Price",
        "LATEST_PRICE": "Latest_Price",
        "LATEST_DEBT_EQUITY": "Latest_Debt_Equity",
        "LATEST_MARKET_CAP": "Latest_Market_Cap",
        "DATA_POINTS": "Data_Points"
    }
    
    if metric.lower() == "all":
        result = [
            row['Price_CAGR'],
            row['COV'],
            row['Mean_Price'],
            row['Latest_Price'],
            row['Latest_Debt_Equity'],
            row['Latest_Market_Cap'],
            row['Data_Points']
        ]
        
        if row['Data_Points'] == 1:
            result.append("Single data point")
        
        return result
    elif metric.upper() in metric_map:
        value = row[metric_map[metric.upper()]]
        if row['Data_Points'] == 1 and metric.upper() in ['CAGR', 'COV']:
            return f"{value} (Single data point)"
        return value
    else:
        return f"Error: Unknown metric '{metric}'"

@xw.func
def get_top_companies(file_path: str, metric: str = "CAGR", count: int = 10, include_single_point: bool = True) -> List[List]:
    """Get top companies by specified metric"""
    global _processed_data, _last_file_path
    
    if not file_path:
        return [["Error: Please provide file_path argument"]]
    
    file_path = os.path.normpath(file_path)
    
    if _processed_data is None or _last_file_path != file_path:
        process_result = process_csv_file(file_path)
        if process_result.startswith("Error"):
            return [[process_result]]
    
    metric_map = {
        "CAGR": "Price_CAGR",
        "COV": "COV",
        "MEAN_PRICE": "Mean_Price", 
        "LATEST_PRICE": "Latest_Price",
        "LATEST_MARKET_CAP": "Latest_Market_Cap"
    }
    
    if metric.upper() not in metric_map:
        return [[f"Error: Unknown metric '{metric}'"]]
    
    column_name = metric_map[metric.upper()]
    
    try:
        # Filter data based on single point preference
        if include_single_point:
            filtered_data = _processed_data.dropna(subset=[column_name])
        else:
            filtered_data = _processed_data[
                (_processed_data['Data_Points'] > 1) & 
                (_processed_data[column_name].notna())
            ]
        
        top_companies = filtered_data.nlargest(count, column_name)
        
        result = [["Company Name", metric.upper(), "Data Points"]]
        
        for _, row in top_companies.iterrows():
            result.append([
                row['Company_Name'], 
                row[column_name], 
                row['Data_Points']
            ])
        
        return result
    
    except Exception as e:
        return [[f"Error: {str(e)}"]]

@xw.func
def get_all_data_as_array(file_path: str) -> List[List]:
    """Get all processed data as a dynamic array for Excel"""
    global _processed_data, _last_file_path
    
    if not file_path:
        return [["Error: Please provide file_path argument"]]
    
    file_path = os.path.normpath(file_path)
    
    if _processed_data is None or _last_file_path != file_path:
        process_result = process_csv_file(file_path)
        if process_result.startswith("Error"):
            return [[process_result]]
    
    try:
        result = []
        
        # Add headers (exclude the Single_Data_Point column for cleaner output)
        headers = [col for col in _processed_data.columns if col != 'Single_Data_Point']
        result.append(headers)
        
        # Add data rows (limit to prevent Excel crashes)
        max_rows = min(len(_processed_data), 100000)
        for i in range(max_rows):
            row = _processed_data.iloc[i]
            data_row = []
            for col in headers:
                value = row[col]
                if pd.isna(value) or value is None:
                    data_row.append("")
                else:
                    data_row.append(value)
            result.append(data_row)
        
        if len(_processed_data) > max_rows:
            result.append([f"... and {len(_processed_data) - max_rows} more rows"])
        
        return result
    
    except Exception as e:
        return [[f"Error: {str(e)}"]]

@xw.func
def clear_cache() -> str:
    """Clear cached data"""
    global _processed_data, _last_file_path
    
    with _processing_lock:
        _processed_data = None
        _last_file_path = None
    
    return "Cache cleared"

@xw.func
def check_processing_status() -> str:
    """Check if processing is complete"""
    global _processed_data
    
    if _processed_data is None:
        return "No data loaded"
    else:
        single_count = (_processed_data['Data_Points'] == 1).sum()
        return f"Ready: {len(_processed_data)} companies ({single_count} single data point)"

if __name__ == "__main__":
    xw.serve()
