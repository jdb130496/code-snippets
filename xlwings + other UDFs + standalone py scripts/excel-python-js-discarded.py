import xlwings as xw
import pythonmonkey as pm
@xw.func
def compare_pre_increment(values):
    # Flatten the list of lists into a single list
    flat_values = values
    #if isinstance(values, (int, float)):
    #    flat_values = [[values]]
    #elif isinstance(values, list) and not isinstance(values[0], list):
    #    flat_values = [[v] for v in values]
    #flat_values = [item for sublist in values for item in sublist]
    # Define JavaScript pre-increment code
    js_code = """
    function preIncrement(values) {
        return values.map(value => {
            let originalValue = value;
            ++value;  // Increment first
            return [originalValue, value];  // Return both original and incremented values
        });
    }
    preIncrement
    """
    # Evaluate the JavaScript function
    pre_increment_js = pm.eval(js_code)
    # Handle Python pre-increment simulation
    def pre_increment_py(values):
        return [value + 1 for value in values]
    # Prepare output with headings
    output = [["preincrement-JS-Original", "preincrement-JS-Incremented", "preincrement-PY"]]
    # Apply JavaScript pre-increment by calling the JavaScript function
    try:
        js_result = pm.eval(f"preIncrement([{', '.join(map(str, flat_values))}])")
    except Exception as e:
        js_result = [[str(e), str(e)]] * len(flat_values)
    # Convert JavaScript results and handle floats with .0
    js_original = [int(val[0]) if isinstance(val[0], float) and val[0].is_integer() else val[0] for val in js_result]
    js_incremented = [int(val[1]) if isinstance(val[1], float) and val[1].is_integer() else val[1] for val in js_result]
    # Apply Python pre-increment
    try:
        py_result = pre_increment_py(flat_values)
    except Exception as e:
        py_result = [str(e)] * len(flat_values)
    # Append results side by side
    for js_orig, js_inc, py_val in zip(js_original, js_incremented, py_result):
        output.append([js_orig, js_inc, py_val])
    return output

import xlwings as xw
import pythonmonkey as pm

@xw.func
def compare_non_strict_equivalent(values1, values2):
    # Function to replace None values with 'null' and ensure everything is a list of lists
    print(values1)
    print(values2)
    x = values1
    y = values2
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

    # Debug: Write to a file instead of printing
    #with open("debug_output.txt", "w") as f:
    #    f.write(f"values1 after replacement: {values1}\n")
    #    f.write(f"values2 after replacement: {values2}\n")

    # JavaScript function to check non-strict equality
    js_code = """
    function CompareNonStrict(values1, values2) {
        return values1.map((row, i) => 
            row.map((value, j) => {
                return value == values2[i][j];
            })
        );
    }
    CompareNonStrict
    """

    # Evaluate the JavaScript function
    pre_increment_js = pm.eval(js_code)

    # Prepare output with headings
    output = [["JS-Non-Strict-Eq.(==)", "PY-Equal(==)"]]

    # Apply JavaScript non-strict equality check
    try:
        js_result = pm.eval(f"CompareNonStrict({values1}, {values2})")
    except Exception as e:
        js_result = [[str(e)] * len(values1[0])] * len(values1)

    # Python equality check (loose)
    def py_equal(values1, values2):
        # Python loose comparison (None should be treated as an empty string for loose equality)
        return [[val1 == val2 for val1, val2 in zip(row1, row2)] for row1, row2 in zip(values1, values2)]

    try:
        py_result = py_equal(values1, values2)
    except Exception as e:
        py_result = [[str(e)] * len(values1[0])] * len(values1)

    # Append results side by side
    for js_row, py_row in zip(js_result, py_result):
        for js_val, py_val in zip(js_row, py_row):
            output.append([js_val, py_val])

    return output

