import xlwings as xw
import pandas as pd

@xw.func
def get_texas_summary(data_range):
    """
    Custom UDF to get Texas firm summary
    Usage in Excel: =get_texas_summary(A1:C978721)
    
    Returns: Array with Firm/Headquarters, MP/CEO, and Count
    """
    try:
        # Convert xlwings range to pandas DataFrame
        df = pd.DataFrame(data_range[1:], columns=data_range[0])  # First row as headers
        
        # Clean the data
        df = df.dropna(how='all')
        df['Firm / Headquarters'] = df['Firm / Headquarters'].astype(str)
        df['MP / CEO'] = df['MP / CEO'].astype(str)
        
        # Filter for Texas
        texas_mask = df['Firm / Headquarters'].str.contains('Texas', case=False, na=False)
        texas_data = df[texas_mask]
        
        if len(texas_data) == 0:
            return [["No Texas records found"]]
        
        # Group by and count
        result = texas_data.groupby(['Firm / Headquarters', 'MP / CEO']).size().reset_index(name='CNT')
        result = result.sort_values(['CNT', 'Firm / Headquarters'], ascending=[False, True])
        
        # Return as list of lists with headers
        output = [['Firm / Headquarters', 'MP / CEO', 'CNT']]
        output.extend(result.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

@xw.func
def get_state_summary(data_range, state_name):
    """
    Custom UDF to get any state firm summary
    Usage in Excel: =get_state_summary(A1:C978721, "California")
    
    Args:
        data_range: Excel range with firm data
        state_name: Name of state to filter
    
    Returns: Array with Firm/Headquarters, MP/CEO, and Count
    """
    try:
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        
        df = df.dropna(how='all')
        df['Firm / Headquarters'] = df['Firm / Headquarters'].astype(str)
        df['MP / CEO'] = df['MP / CEO'].astype(str)
        
        # Filter for specified state
        state_mask = df['Firm / Headquarters'].str.contains(state_name, case=False, na=False)
        state_data = df[state_mask]
        
        if len(state_data) == 0:
            return [[f"No records found for {state_name}"]]
        
        # Group by and count
        result = state_data.groupby(['Firm / Headquarters', 'MP / CEO']).size().reset_index(name='CNT')
        result = result.sort_values(['CNT', 'Firm / Headquarters'], ascending=[False, True])
        
        # Return as list with headers
        output = [['Firm / Headquarters', 'MP / CEO', 'CNT']]
        output.extend(result.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

@xw.func
def get_firm_count(data_range, firm_name, ceo_name):
    """
    Get count for specific firm and CEO combination
    Usage in Excel: =get_firm_count(A1:C978721, "ADKF PC / San Antonio, Texas", "Scott Kopecky")
    
    Returns: Count of occurrences
    """
    try:
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        
        df = df.dropna(how='all')
        df['Firm / Headquarters'] = df['Firm / Headquarters'].astype(str)
        df['MP / CEO'] = df['MP / CEO'].astype(str)
        
        # Count exact matches
        count = len(df[(df['Firm / Headquarters'] == firm_name) & (df['MP / CEO'] == ceo_name)])
        
        return count
        
    except Exception as e:
        return f"Error: {str(e)}"

@xw.func
def get_top_states(data_range, top_n=10):
    """
    Get top N states by firm count - dynamically extracted from data
    Usage in Excel: =get_top_states(A1:C978721, 5)
    
    Returns: Array with State names and counts
    """
    try:
        import re
        
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        
        df = df.dropna(how='all')
        df['Firm / Headquarters'] = df['Firm / Headquarters'].astype(str)
        
        # Extract state-like patterns from the data
        state_pattern = r'\b([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)\b'  # Matches capitalized words
        
        state_counts = {}
        
        for firm_name in df['Firm / Headquarters']:
            # Look for patterns like "City, State" or "/ State" 
            # Common patterns: "San Antonio, Texas" or "/ California"
            
            # Pattern 1: City, State
            city_state_match = re.search(r',\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)', firm_name)
            if city_state_match:
                state = city_state_match.group(1).strip()
                state_counts[state] = state_counts.get(state, 0) + 1
                continue
            
            # Pattern 2: / State
            slash_state_match = re.search(r'/\s*([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)', firm_name)
            if slash_state_match:
                state = slash_state_match.group(1).strip()
                # Filter out obvious non-states (common firm name parts)
                non_states = {'LLC', 'LLP', 'PC', 'Inc', 'Corp', 'Company', 'Partners', 'Group', 'Associates'}
                if state not in non_states:
                    state_counts[state] = state_counts.get(state, 0) + 1
        
        # Convert to list and sort by count
        state_list = [[state, count] for state, count in state_counts.items()]
        state_list.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N with headers
        output = [['State', 'Count']]
        output.extend(state_list[:top_n])
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

@xw.func
def count_texas_firms(data_range):
    """
    Simple count of Texas firms
    Usage in Excel: =count_texas_firms(A1:C978721)
    
    Returns: Number of Texas firms
    """
    try:
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        
        df = df.dropna(how='all')
        df['Firm / Headquarters'] = df['Firm / Headquarters'].astype(str)
        
        count = df['Firm / Headquarters'].str.contains('Texas', case=False, na=False).sum()
        
        return count
        
    except Exception as e:
        return f"Error: {str(e)}"

@xw.func
def get_unique_texas_combinations(data_range):
    """
    Get count of unique Texas firm-CEO combinations
    Usage in Excel: =get_unique_texas_combinations(A1:C978721)
    
    Returns: Number of unique combinations
    """
    try:
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        
        df = df.dropna(how='all')
        df['Firm / Headquarters'] = df['Firm / Headquarters'].astype(str)
        df['MP / CEO'] = df['MP / CEO'].astype(str)
        
        # Filter for Texas
        texas_mask = df['Firm / Headquarters'].str.contains('Texas', case=False, na=False)
        texas_data = df[texas_mask]
        
        # Count unique combinations
        unique_count = len(texas_data.groupby(['Firm / Headquarters', 'MP / CEO']))
        
        return unique_count
        
    except Exception as e:
        return f"Error: {str(e)}"
