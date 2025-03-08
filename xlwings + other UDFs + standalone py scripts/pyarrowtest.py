import xlwings as xw
import pyarrow as pa
import pyarrow.compute as pc
import pandas as pd
from datetime import datetime

@xw.func
def test_data_processing():
    """Test function to debug data processing with sample data"""
    try:
        # Create sample data
        data = {
            'Date': ['1/1/2023', '2/15/2023', '3/30/2023', None, '12/31/2023'],
            'Memo': ['Test memo\\with\\backslash', None, 'None', '  Extra spaces  ', 'Normal memo'],
            'Amount': ['$1,234.56', '($789.01)', '$0.00', None, '$5,432.10'],
            'Qty': ['1', '2', None, '4', '5'],
            'Other': ['Test\\string', None, 'None', '  Spaces  ', 'Normal']
        }

        # Convert to PyArrow Table
        table = pa.Table.from_pydict(data)
        print("\nOriginal PyArrow Table:")
        print(table)

        # Debug Memo processing
        print("\n=== Memo Processing ===")
        memo_col = table.column('Memo')
        print("Original Memo:", memo_col.to_pylist())

        memo_filled = pc.fill_null(memo_col, '')
        print("After fill_null:", memo_filled.to_pylist())

        memo_string = pc.cast(memo_filled, pa.string())
        print("After cast to string:", memo_string.to_pylist())

        memo_no_none = pc.replace_substring(memo_string, 'None', '')
        print("After replacing 'None':", memo_no_none.to_pylist())

        memo_no_backslash = pc.replace_substring(memo_no_none, '\\', ' ')
        print("After replacing backslash:", memo_no_backslash.to_pylist())

        # Debug Date processing
        print("\n=== Date Processing ===")
        date_col = table.column('Date')
        print("Original Date:", date_col.to_pylist())

        try:
            date_timestamp = pc.strptime(date_col, format='%m/%d/%Y', unit='s')
            print("After strptime:", date_timestamp.to_pylist())
            
            excel_epoch = datetime(1899, 12, 30).timestamp()
            date_excel = pc.divide(pc.subtract(date_timestamp, excel_epoch), 86400)
            print("After Excel conversion:", date_excel.to_pylist())
        except Exception as e:
            print(f"Date conversion error: {e}")

        # Debug Amount processing
        print("\n=== Amount Processing ===")
        amount_col = table.column('Amount')
        print("Original Amount:", amount_col.to_pylist())

        amount_filled = pc.fill_null(amount_col, '$0.00')
        print("After fill_null:", amount_filled.to_pylist())

        amount_string = pc.cast(amount_filled, pa.string())
        print("After cast to string:", amount_string.to_pylist())

        amount_no_dollar = pc.replace_substring(amount_string, '$', '')
        print("After removing $:", amount_no_dollar.to_pylist())

        amount_no_comma = pc.replace_substring(amount_no_dollar, ',', '')
        print("After removing commas:", amount_no_comma.to_pylist())

        # Compare with pandas approach
        print("\n=== Pandas Comparison ===")
        df = pd.DataFrame(data)
        
        # Pandas Memo processing
        df['Memo'] = (df['Memo']
                    .fillna('')
                    .astype(str)
                    .replace('None', '')
                    .str.replace('\\', ' ', regex=False)
                    .str.strip())
        print("Pandas Memo result:", df['Memo'].tolist())

        # Pandas Amount processing
        df['Amount'] = (df['Amount']
                    .fillna('$0.00')
                    .astype(str)
                    .str.replace('$', '', regex=False)
                    .str.replace(',', '', regex=False)
                    .str.replace('(', '-', regex=False)
                    .str.replace(')', '', regex=False)
                    .str.strip())
        print("Pandas Amount result:", df['Amount'].tolist())

        # Final comparison
        print("\n=== Final Comparison ===")
        print("PyArrow Memo:", memo_no_backslash.to_pylist())
        print("Pandas Memo:", df['Memo'].tolist())
        
        # Return something to Excel
        return [["Debug output in UDF Server console"]]

    except Exception as e:
        print(f"Error in test_data_processing: {e}")
        return [["Error: " + str(e)]]

@xw.func
def test_backslash_handling():
    """Test backslash handling with real data example"""
    try:
        # Real data example - exactly as it appears in Excel cell
        test_memo = r"remake peice 1  10mm Opti-White+Temp. \ .060 Clear PVB \ 10mm   66 3/ 4  113 1/ 4  53.84  SF  23.01  1238.73  1238.73  16142(R)  Opti-White+Temp."
        
        # Create test data
        data = {
            'Memo': [test_memo, None, 'Normal text', '  Spaces  ', r'Test\string']
        }

        print("\n=== Original String ===")
        print(test_memo)
        
        # PyArrow approach
        print("\n=== PyArrow Processing ===")
        table = pa.Table.from_pydict(data)
        memo_col = table.column('Memo')
        print("Original:", memo_col.to_pylist())
        
        try:
            # Try different PyArrow approaches
            print("\nTrying different PyArrow replacements:")
            
            # Approach 1: Basic replacement
            result1 = pc.replace_substring(memo_col, '\\', ' ')
            print("Basic replace_substring:", result1.to_pylist())
            
            # Approach 2: Using regex
            result2 = pc.replace_substring_regex(memo_col, r'\\', ' ')
            print("replace_substring_regex:", result2.to_pylist())
            
        except Exception as e:
            print(f"PyArrow error: {e}")

        # Pandas approach
        print("\n=== Pandas Processing ===")
        df = pd.DataFrame(data)
        
        # Show intermediate steps
        print("1. Original:", df['Memo'].tolist())
        
        df['Memo'] = df['Memo'].fillna('')
        print("2. After fillna:", df['Memo'].tolist())
        
        df['Memo'] = df['Memo'].astype(str)
        print("3. After astype(str):", df['Memo'].tolist())
        
        df['Memo'] = df['Memo'].replace('None', '')
        print("4. After replace None:", df['Memo'].tolist())
        
        # Try both regex=True and regex=False for comparison
        df_copy = df.copy()
        
        # With regex=False
        df['Memo'] = df['Memo'].str.replace('\\', ' ', regex=False)
        print("5a. After replace backslash (regex=False):", df['Memo'].tolist())
        
        # With regex=True
        df_copy['Memo'] = df_copy['Memo'].str.replace(r'\\', ' ', regex=True)
        print("5b. After replace backslash (regex=True):", df_copy['Memo'].tolist())
        
        df['Memo'] = df['Memo'].str.replace(r'\s+', ' ', regex=True)
        print("6. After normalize spaces:", df['Memo'].tolist())
        
        df['Memo'] = df['Memo'].str.strip()
        print("7. Final result:", df['Memo'].tolist())

        return [["Check UDF Server console for debug output"]]

    except Exception as e:
        print(f"Error in test: {e}")
        return [["Error: " + str(e)]]

