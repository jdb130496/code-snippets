import xlwings as xw
import pandas as pd
import sqlite3
import re
from io import StringIO

@xw.func
def sql_enhanced(range_ref, sql_statement, use_chunking=False, chunk_size=50000):
    """
    Enhanced SQL function that handles both range addresses and Table references
    Usage: =sql_enhanced("A1:C978721", "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'")
    Usage: =sql_enhanced(Table1[#All], "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'")
    Usage with chunking: =sql_enhanced("A1:C978721", "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'", TRUE, 50000)
    
    Args:
        range_ref: Range address string OR Excel range/table reference
        sql_statement: SQL query string (same syntax as native =sql())
        use_chunking: Boolean, whether to force chunked processing
        chunk_size: Size of chunks for large datasets
    
    Returns: Query results (attempts native xlwings sql first, custom fallback)
    """
    try:
        wb = xw.Book.caller()
        sheet = wb.sheets.active
        
        # Handle different types of range references
        if isinstance(range_ref, str):
            # String address like "A1:C978721"
            range_obj = sheet.range(range_ref)
        else:
            # Already a range object or table reference - get its address first
            try:
                # If it's already a range object, use it directly
                if hasattr(range_ref, 'address'):
                    range_obj = sheet.range(range_ref.address)
                else:
                    # Try to convert the reference to a range
                    range_obj = sheet.range(range_ref)
            except:
                # Fallback: treat as direct data
                if hasattr(range_ref, '__iter__') and not isinstance(range_ref, str):
                    # It's already data, process directly
                    return sql_query_optimized_internal(range_ref, sql_statement)
                else:
                    raise ValueError(f"Unable to process range reference: {range_ref}")
        
        # Get the data from the range
        data_range = range_obj.value
        
        # Skip native xlwings sql for now since it doesn't handle table refs well
        # Go straight to our custom implementation
        if use_chunking or len(data_range) > 100000:  # Use chunking for large datasets
            return sql_query_chunked_internal(data_range, sql_statement, chunk_size=chunk_size)
        else:
            return sql_query_optimized_internal(data_range, sql_statement)
                
    except Exception as outer_error:
        return [["Error:", str(outer_error)]]

@xw.func 
def sql_table_fixed(table_reference, sql_statement, chunk_size=50000):
    """
    Fixed SQL function for Excel Tables - handles various table reference formats
    Usage: =sql_table_fixed("Table14", F2)
    Usage: =sql_table_fixed("Table14[#All]", F2)  -- also works
    
    Args:
        table_reference: Table name (e.g., "Table14") or reference ("Table14[#All]")
        sql_statement: SQL query string
        chunk_size: Chunk size for large tables
    
    Returns: Query results
    """
    try:
        wb = xw.Book.caller()
        sheet = wb.sheets.active
        
        # Clean up the table reference - extract just the table name
        if isinstance(table_reference, str):
            # Remove [#All] if present and clean up
            table_name = table_reference.replace("[#All]", "").replace("[#Headers]", "").strip()
        else:
            table_name = str(table_reference)
        
        # Try different approaches to get the table data
        table_range = None
        
        # Method 1: Try direct table reference on current sheet
        try:
            table_range = sheet.range(f"{table_name}[#All]")
        except:
            pass
        
        # Method 2: Search all sheets for the table
        if table_range is None:
            for ws in wb.sheets:
                try:
                    table_range = ws.range(f"{table_name}[#All]")
                    break
                except:
                    continue
        
        # Method 3: If still not found, try without [#All]
        if table_range is None:
            try:
                table_range = sheet.range(table_name)
            except:
                pass
        
        if table_range is None:
            return [["Error:", f"Could not find table '{table_name}'. Check table name and ensure it exists."]]
        
        # Get the data
        data_range = table_range.value
        
        # Validate we have data
        if not data_range or len(data_range) == 0:
            return [["Error:", "No data found in table"]]
        
        # Process the SQL query directly here
        try:
            # Convert to DataFrame
            df = pd.DataFrame(data_range[1:], columns=data_range[0])
            df = df.dropna(how='all')
            
            # Clean column names for SQLite compatibility
            original_columns = df.columns.tolist()
            clean_columns = []
            column_mapping = {}
            
            for col in original_columns:
                clean_col = re.sub(r'[^\w]', '_', str(col))
                clean_columns.append(clean_col)
                column_mapping[col] = clean_col
            
            df.columns = clean_columns
            
            # Update SQL statement to use clean column names
            updated_sql = sql_statement
            for original, clean in column_mapping.items():
                pattern = rf'\[{re.escape(original)}\]'
                updated_sql = re.sub(pattern, clean, updated_sql)
                pattern = rf'"{re.escape(original)}"'
                updated_sql = re.sub(pattern, clean, updated_sql)
            
            # Create SQLite connection and execute
            conn = sqlite3.connect(':memory:')
            df.to_sql("a", conn, index=False, if_exists='replace')
            result_df = pd.read_sql_query(updated_sql, conn)
            conn.close()
            
            if len(result_df) == 0:
                return [["No results found"]]
            
            # Restore original column names
            result_columns = result_df.columns.tolist()
            restored_columns = []
            
            for col in result_columns:
                original_col = col
                for orig, clean in column_mapping.items():
                    if clean == col:
                        original_col = orig
                        break
                restored_columns.append(original_col)
            
            result_df.columns = restored_columns
            
            # Return as array
            output = [result_df.columns.tolist()]
            output.extend(result_df.values.tolist())
            
            return output
            
        except Exception as sql_error:
            return [["SQL Error:", str(sql_error)]]
            
    except Exception as e:
        return [["Table Error:", f"Exception: {str(e)}"]]

@xw.func
def sql_simple(data_range, sql_statement):
    """
    Simplified SQL function that works directly with data ranges (no table refs)
    Usage: =sql_simple(A1:C978721, "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'")
    
    This is the most reliable version - pass the actual range, not table references
    """
    try:
        # Handle case where data_range might be a single cell with the SQL
        if isinstance(data_range, str):
            return [["Error:", "First parameter should be data range, second should be SQL"]]
            
        return sql_query_optimized_internal(data_range, sql_statement)
        
    except Exception as e:
        return [["Simple Error:", str(e)]]
    """
    Direct SQL processing without trying native first
    Usage: =sql_direct(A1:C978721, "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'")
    
    This is equivalent to native =sql() but with better memory management
    """
    return sql_query_optimized_internal(data_range, sql_statement)

@xw.func
def sql_chunked(data_range, sql_statement, chunk_size=50000):
    """
    SQL processing with explicit chunking for very large datasets
    Usage: =sql_chunked(A1:C978721, "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'", 50000)
    """
    return sql_query_chunked_internal(data_range, sql_statement, chunk_size)

def sql_query_chunked_internal(data_range, sql_statement, table_name="a", chunk_size=50000):
    """
    Internal chunked SQL processing
    """
    try:
        # Get headers
        headers = data_range[0]
        data_rows = data_range[1:]
        
        # Create in-memory SQLite database
        conn = sqlite3.connect(':memory:')
        
        # Process data in chunks
        total_rows = len(data_rows)
        
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk_data = data_rows[start_idx:end_idx]
            
            # Create DataFrame for this chunk
            chunk_df = pd.DataFrame(chunk_data, columns=headers)
            chunk_df = chunk_df.dropna(how='all')
            
            # Clean column names
            original_columns = chunk_df.columns.tolist()
            clean_columns = [re.sub(r'[^\w]', '_', str(col)) for col in original_columns]
            column_mapping = dict(zip(original_columns, clean_columns))
            chunk_df.columns = clean_columns
            
            # Append to SQLite table
            if_exists = 'replace' if start_idx == 0 else 'append'
            chunk_df.to_sql(table_name, conn, index=False, if_exists=if_exists)
        
        # Update SQL statement for clean column names
        updated_sql = sql_statement
        for original, clean in column_mapping.items():
            pattern = rf'\[{re.escape(original)}\]'
            updated_sql = re.sub(pattern, clean, updated_sql)
            pattern = rf'"{re.escape(original)}"'
            updated_sql = re.sub(pattern, clean, updated_sql)
        
        # Execute the SQL query
        result_df = pd.read_sql_query(updated_sql, conn)
        conn.close()
        
        if len(result_df) == 0:
            return [["No results found"]]
        
        # Restore original column names in results
        result_columns = result_df.columns.tolist()
        restored_columns = []
        
        for col in result_columns:
            original_col = col
            for orig, clean in column_mapping.items():
                if clean == col:
                    original_col = orig
                    break
            restored_columns.append(original_col)
        
        result_df.columns = restored_columns
        
        # Return as array
        output = [result_df.columns.tolist()]
        output.extend(result_df.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Chunked Error:", str(e)]]
    """
    Internal function for SQL processing (same logic as before)
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        df = df.dropna(how='all')
        
        # Clean column names for SQLite compatibility
        original_columns = df.columns.tolist()
        clean_columns = []
        column_mapping = {}
        
        for col in original_columns:
            clean_col = re.sub(r'[^\w]', '_', str(col))
            clean_columns.append(clean_col)
            column_mapping[col] = clean_col
        
        df.columns = clean_columns
        
        # Update SQL statement to use clean column names
        updated_sql = sql_statement
        for original, clean in column_mapping.items():
            pattern = rf'\[{re.escape(original)}\]'
            updated_sql = re.sub(pattern, clean, updated_sql)
            pattern = rf'"{re.escape(original)}"'
            updated_sql = re.sub(pattern, clean, updated_sql)
        
        # Create SQLite connection and execute
        conn = sqlite3.connect(':memory:')
        df.to_sql(table_name, conn, index=False, if_exists='replace')
        result_df = pd.read_sql_query(updated_sql, conn)
        conn.close()
        
        if len(result_df) == 0:
            return [["No results found"]]
        
        # Restore original column names
        result_columns = result_df.columns.tolist()
        restored_columns = []
        
        for col in result_columns:
            original_col = col
            for orig, clean in column_mapping.items():
                if clean == col:
                    original_col = orig
                    break
            restored_columns.append(original_col)
        
        result_df.columns = restored_columns
        
        # Return as array
        output = [result_df.columns.tolist()]
        output.extend(result_df.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

@xw.func
def sql_query(data_range, sql_statement, table_name="a"):
    """
    Custom UDF to execute SQL on Excel data using SQLite
    Usage in Excel: =sql_query(A1:C978721, "SELECT * FROM a WHERE column LIKE '%Texas%'", "a")
    
    Args:
        data_range: Excel range with data (first row should be headers)
        sql_statement: SQL query string (use table_name as table reference)
        table_name: Name to use for the table in SQL (default: "a")
    
    Returns: Query results as array
    """
    try:
        # Convert xlwings range to pandas DataFrame
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        
        # Clean the data
        df = df.dropna(how='all')
        
        # Create in-memory SQLite database
        conn = sqlite3.connect(':memory:')
        
        # Write DataFrame to SQLite with specified table name
        df.to_sql(table_name, conn, index=False, if_exists='replace')
        
        # Execute the SQL query
        result_df = pd.read_sql_query(sql_statement, conn)
        
        # Close connection
        conn.close()
        
        if len(result_df) == 0:
            return [["No results found"]]
        
        # Convert result to list of lists with headers
        output = [result_df.columns.tolist()]
        output.extend(result_df.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

@xw.func
def sql_query_chunked(data_range, sql_statement, table_name="a", chunk_size=50000):
    """
    Custom UDF to execute SQL on large Excel data using chunked processing
    Usage in Excel: =sql_query_chunked(A1:C978721, "SELECT * FROM a WHERE column LIKE '%Texas%'", "a", 50000)
    
    Args:
        data_range: Excel range with data
        sql_statement: SQL query string
        table_name: Name to use for the table in SQL
        chunk_size: Number of rows to process at once
    
    Returns: Query results as array
    """
    try:
        # Get headers
        headers = data_range[0]
        data_rows = data_range[1:]
        
        # Create in-memory SQLite database
        conn = sqlite3.connect(':memory:')
        
        # Process data in chunks to manage memory
        total_rows = len(data_rows)
        
        for start_idx in range(0, total_rows, chunk_size):
            end_idx = min(start_idx + chunk_size, total_rows)
            chunk_data = data_rows[start_idx:end_idx]
            
            # Create DataFrame for this chunk
            chunk_df = pd.DataFrame(chunk_data, columns=headers)
            chunk_df = chunk_df.dropna(how='all')
            
            # Append to SQLite table
            if_exists = 'replace' if start_idx == 0 else 'append'
            chunk_df.to_sql(table_name, conn, index=False, if_exists=if_exists)
        
        # Execute the SQL query
        result_df = pd.read_sql_query(sql_statement, conn)
        
        # Close connection
        conn.close()
        
        if len(result_df) == 0:
            return [["No results found"]]
        
        # Convert result to list of lists with headers
        output = [result_df.columns.tolist()]
        output.extend(result_df.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

@xw.func
def sql_query_optimized(data_range, sql_statement, table_name="a"):
    """
    Optimized SQL UDF with better error handling and data type inference
    Usage in Excel: =sql_query_optimized(A1:C978721, "SELECT * FROM a WHERE [Firm / Headquarters] LIKE '%Texas%'")
    
    Note: Column names with spaces should be wrapped in square brackets in SQL
    """
    try:
        # Convert to DataFrame
        df = pd.DataFrame(data_range[1:], columns=data_range[0])
        df = df.dropna(how='all')
        
        # Clean column names for SQLite compatibility and create mapping
        original_columns = df.columns.tolist()
        clean_columns = []
        column_mapping = {}
        
        for col in original_columns:
            # Replace problematic characters in column names
            clean_col = re.sub(r'[^\w]', '_', str(col))
            clean_columns.append(clean_col)
            column_mapping[col] = clean_col
        
        df.columns = clean_columns
        
        # Update SQL statement to use clean column names if needed
        updated_sql = sql_statement
        for original, clean in column_mapping.items():
            # Replace bracketed column names: [Original Name] -> clean_name
            pattern = rf'\[{re.escape(original)}\]'
            updated_sql = re.sub(pattern, clean, updated_sql)
            
            # Replace quoted column names: "Original Name" -> clean_name
            pattern = rf'"{re.escape(original)}"'
            updated_sql = re.sub(pattern, clean, updated_sql)
        
        # Create SQLite connection
        conn = sqlite3.connect(':memory:')
        
        # Load data with appropriate data types
        df.to_sql(table_name, conn, index=False, if_exists='replace')
        
        # Execute query
        result_df = pd.read_sql_query(updated_sql, conn)
        conn.close()
        
        if len(result_df) == 0:
            return [["No results found"]]
        
        # Restore original column names in results if they match
        result_columns = result_df.columns.tolist()
        restored_columns = []
        
        for col in result_columns:
            # Find original column name
            original_col = col
            for orig, clean in column_mapping.items():
                if clean == col:
                    original_col = orig
                    break
            restored_columns.append(original_col)
        
        result_df.columns = restored_columns
        
        # Return as array
        output = [result_df.columns.tolist()]
        output.extend(result_df.values.tolist())
        
        return output
        
    except Exception as e:
        return [["Error:", str(e)]]

# Additional utility functions for common operations
@xw.func
def sql_count(data_range, where_clause="", table_name="a"):
    """
    Quick count with optional WHERE clause
    Usage: =sql_count(A1:C978721, "column LIKE '%Texas%'")
    """
    sql = f"SELECT COUNT(*) as count FROM {table_name}"
    if where_clause:
        sql += f" WHERE {where_clause}"
    
    result = sql_query_optimized(data_range, sql, table_name)
    
    if len(result) > 1:
        return result[1][0]  # Return just the count value
    return 0

@xw.func
def sql_distinct_count(data_range, column_name, where_clause="", table_name="a"):
    """
    Count distinct values in a column
    Usage: =sql_distinct_count(A1:C978721, "Firm / Headquarters", "column LIKE '%Texas%'")
    """
    clean_column = re.sub(r'[^\w]', '_', column_name)
    sql = f"SELECT COUNT(DISTINCT {clean_column}) as distinct_count FROM {table_name}"
    if where_clause:
        # Clean the where clause column names too
        clean_where = where_clause
        clean_where = re.sub(r'\b' + re.escape(column_name) + r'\b', clean_column, clean_where)
        sql += f" WHERE {clean_where}"
    
    result = sql_query_optimized(data_range, sql, table_name)
    
    if len(result) > 1:
        return result[1][0]
    return 0
