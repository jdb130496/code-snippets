import pythonmonkey as pm

def js_compare_pre_increment_pm(values):
    # Check if the input is a list of lists or a flat list
    if isinstance(values[0], list):
        # Flatten the list of lists into a single list
        flat_values = [item if item is not None else 'null' for sublist in values for item in sublist]
    else:
        # Use the flat list directly
        flat_values = [item if item is not None else 'null' for item in values]

    # JavaScript code for pre-increment
    js_code_pre_increment = """
    function preIncrement(values) {
        return values.map(function(value) {
            if (value === 'null') {
                return ['null', 'null'];
            }
            var originalValue = parseFloat(value);
            value = originalValue + 1;
            return [originalValue, value];
        });
    }
    preIncrement
    """
    
    # Use pythonmonkey to run the JavaScript code
    pre_increment = pm.eval(js_code_pre_increment)
    js_result_pre_increment = pre_increment(flat_values)

    # Python pre-increment
    def pre_increment_py(values):
        return [float(value) + 1 if value != 'null' else 'null' for value in values]

    py_result = pre_increment_py(flat_values)

    # Prepare output with headings
    output = [["preincrement-JS-Original", "preincrement-JS-Incremented", "preincrement-PY"]]

    # Append results side by side (JS original, JS incremented, PY incremented)
    for (js_orig, js_inc), py_val in zip(js_result_pre_increment, py_result):
        output.append([js_orig, js_inc, py_val])

    return output

def js_compare_non_strict_equ_pm(values):
    # Check if the input is a list of lists
    if not isinstance(values[0], list):
        return "Input must be a list of lists"

    # Break down the input into two arrays
    Ar1 = [row[0] for row in values]
    Ar2 = [row[1] for row in values]

    # Function to replace None values with 'null'
    def replace_none_with_null(values):
        return ['null' if val is None else val for val in values]

    # Replace None values with 'null' in both arrays
    Ar1 = replace_none_with_null(Ar1)
    Ar2 = replace_none_with_null(Ar2)

    # JavaScript code for non-strict equality check
    js_code_non_strict = """
    function CompareNonStrict(values1, values2) {
        return values1.map((value, i) => {
            if (value === 'null' || values2[i] === 'null') {
                return value === values2[i];
            }
            return value == values2[i];
        });
    }
    CompareNonStrict
    """

    # Use pythonmonkey to run the JavaScript code
    compare_non_strict = pm.eval(js_code_non_strict)
    js_result_non_strict = compare_non_strict(Ar1, Ar2)

    # Python equality check (loose)
    def py_equal(values1, values2):
        # Python loose comparison (None should be treated as 'null' for loose equality)
        return [val1 == val2 for val1, val2 in zip(values1, values2)]

    py_result_non_strict = py_equal(Ar1, Ar2)

    # Prepare output with headings
    output = [["JS-Non-Strict-Eq.(==)", "PY-Equal(==)"]]

    # Append results side by side (Value1, Value2, JS non-strict equality, Python equality)
    for js_res, py_res in zip(js_result_non_strict, py_result_non_strict):
        output.append([js_res, py_res])

    return output

# Example usage
if __name__ == "__main__":
    # Example data for pre-increment function
    values_pre_increment = [123, 456, 789.678, 101112]
    
    result_pre_increment = js_compare_pre_increment_pm(values_pre_increment)
    
    print("Pre Increment Results:")
    for row in result_pre_increment:
        print(row)

    # Example data for non-strict equality function
    values_non_strict_equ = [[123, 123], [456, '456'], [None, None], [789.678, 789.678], ['101112', 101112]]
    
    result_non_strict_equ = js_compare_non_strict_equ_pm(values_non_strict_equ)
    
    print("\nNon-Strict Equality Results:")
    for row in result_non_strict_equ:
        print(row)

