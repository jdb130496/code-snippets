import xlwings as xw

@xw.func
@xw.arg('text_range', ndim=2)
@xw.arg('delimiter', ndim=1)
def text_split_range(text_range, delimiter):
    """
    Custom UDF to split a range of cells into a list of lists based on a delimiter.
    :param text_range: Excel range (2D array) containing text.
    :param delimiter: The delimiter character or substring.
    :return: List of lists containing substrings.
    """
    try:
        result = []
        max_len = 0
        for row in text_range:
            row_result = []
            for cell in row:
                if cell is not None:
                    substrings = cell.split(delimiter[0])
                    row_result.extend(substrings)
                    max_len = max(max_len, len(substrings))
                else:
                    row_result.append(None)
            result.append(row_result)

        # Fill in missing values with an empty string
        for row in result:
            if len(row) < max_len:
                row.extend([""] * (max_len - len(row)))

        return result
    except AttributeError:
        return None  # Handle cases where input is not valid

