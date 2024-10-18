import xlwings as xw
import execjs

@xw.func
def compare_pre_increment(values):
    # Check if the input is a list of lists or a flat list
    if isinstance(values[0], list):
        # Flatten the list of lists into a single list
        flat_values = [item for sublist in values for item in sublist]
    else:
        # Use the flat list directly
        flat_values = values

    # JavaScript code for pre-increment
    js_code = """
    function preIncrement(values) {
        return values.map(function(value) {
            var originalValue = value;
            value++;
            return [originalValue, value];
        });
    }
    """
    
    # Use execjs to run the JavaScript code
    ctx = execjs.compile(js_code)
    js_result = ctx.call("preIncrement", flat_values)

    # Python pre-increment
    def pre_increment_py(values):
        return [value + 1 for value in values]

    py_result = pre_increment_py(flat_values)

    # Prepare output with headings
    output = [["preincrement-JS-Original", "preincrement-JS-Incremented", "preincrement-PY"]]

    # Append results side by side (JS original, JS incremented, PY incremented)
    for (js_orig, js_inc), py_val in zip(js_result, py_result):
        output.append([js_orig, js_inc, py_val])

    return output
import xlwings as xw
import execjs

@xw.func
def compare_non_strict_equivalent(values1, values2):
    # Function to replace None values with 'null' and ensure everything is a list of lists
    def replace_none_with_null(values):
        if isinstance(values, (int, float)):  # Single value, not a list
            return [['null' if values is None else values]]
        elif isinstance(values, list) and not isinstance(values[0], list):  # Single row
            return [['null' if val is None else val for val in values]]
        else:  # List of rows
            return [[('null' if val is None else val) for val in row] for row in values]

    # Replace None values with 'null' in both input arrays
    values1 = replace_none_with_null(values1)
    values2 = replace_none_with_null(values2)

    # JavaScript function to check non-strict equality
    js_code = """
    function CompareNonStrict(values1, values2) {
        return values1.map((row, i) => 
            row.map((value, j) => {
                return value == values2[i][j];
            })
        );
    }
    """

    # Use execjs to compile and run the JavaScript function
    ctx = execjs.compile(js_code)

    # Apply JavaScript non-strict equality check
    try:
        js_result = ctx.call("CompareNonStrict", values1, values2)
    except Exception as e:
        js_result = [[str(e)] * len(values1[0])] * len(values1)

    # Python equality check (loose)
    def py_equal(values1, values2):
        # Python loose comparison (None should be treated as 'null' for loose equality)
        return [[val1 == val2 for val1, val2 in zip(row1, row2)] for row1, row2 in zip(values1, values2)]

    try:
        py_result = py_equal(values1, values2)
    except Exception as e:
        py_result = [[str(e)] * len(values1[0])] * len(values1)

    # Prepare output with headings
    output = [["JS-Non-Strict-Eq.(==)", "PY-Equal(==)"]]

    # Append results side by side (JS non-strict equality and Python equality)
    for js_row, py_row in zip(js_result, py_result):
        for js_val, py_val in zip(js_row, py_row):
            output.append([js_val, py_val])

    return output

