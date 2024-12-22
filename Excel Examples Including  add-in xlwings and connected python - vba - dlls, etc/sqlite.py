import xlwings as xw
import pandas as pd
import sqlite3
from decimal import Decimal

@xw.func
def sql_query_direct(query, *data_ranges):
    """
    Execute a SQL query on multiple Excel data ranges and return the results.
    Data ranges will be in the format 'A6:K2000'.

    Parameters:
        query (str): SQL query string to execute.
        *data_ranges (str): Excel ranges (e.g., "A6:K2000", "M6:W2000").

    Returns:
        list: Query results as a list of lists (for Excel output).
    """
    # Initialize an in-memory SQLite database
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    # Read data from each range and load into pandas DataFrame
    dataframes = []

    # Loop over each data range
    for idx, data_range in enumerate(data_ranges):
        # Get the sheet and range from xlwings
        sheet = xw.Book.caller().sheets.active
        # Get the data from the Excel range (excluding headers)
        data = sheet.range(data_range).value
        
        if not data:
            continue
        
        # First row is headers, so we separate it
        headers = data[0]
        rows = data[1:]  # Remaining rows after header

        # Convert to a pandas DataFrame
        df = pd.DataFrame(rows, columns=headers)

        # Create a table for this DataFrame in SQLite
        table_name = f"a{idx + 1}"  # Dynamic table names: a1, a2, etc.
        df.to_sql(table_name, conn, if_exists='replace', index=False)

    # Execute the provided SQL query
    query_results = pd.read_sql_query(query, conn)

    # Convert the query results to a list of lists (including headers) to return to Excel
    result_list = [list(query_results.columns)] + query_results.values.tolist()

    # Close the SQLite connection
    conn.close()

    # Return the query results as a list of lists
    return result_list

