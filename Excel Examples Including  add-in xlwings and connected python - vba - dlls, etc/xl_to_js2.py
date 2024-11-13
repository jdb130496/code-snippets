import xlwings as xw
from javascript import require

@xw.func
def js_compare_pre_increment(values):
    # Ensure values is always a list of lists
    if not isinstance(values, list):
        values = [[values]]
    elif not isinstance(values[0], list):
        values = [[v] for v in values]

    # Flatten the list of lists into a single list
    flat_values = [item if item is not None else 'null' for sublist in values for item in sublist]

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
    """
    
    # Use JSPyBridge to run the JavaScript code
    vm = require('vm')
    ctx = vm.createContext({})
    vm.runInContext(js_code_pre_increment, ctx)

    # Run the JavaScript function
    js_result_pre_increment = ctx.preIncrement(flat_values)

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

@xw.func
def js_compare_strict_equivalent(values):
    # Ensure values is always a list of lists
    if not isinstance(values, list):
        values = [[values]]
    elif not isinstance(values[0], list):
        values = [values]

    # Break down the input into two arrays
    Ar1 = [row[0] for row in values]
    Ar2 = [row[1] for row in values]

    # Function to replace None values with 'null'
    def replace_none_with_null(values):
        return ['null' if val is None else val for val in values]

    # Replace None values with 'null' in both arrays
    Ar1 = replace_none_with_null(Ar1)
    Ar2 = replace_none_with_null(Ar2)

    # JavaScript code for strict equality check
    js_code_strict = """
    function CompareStrict(values1, values2) {
        return values1.map((value, i) => {
            if (value === 'null' || values2[i] === 'null') {
                return value === values2[i];
            }
            return value === values2[i];
        });
    }
    """

    # Use JSPyBridge to run the JavaScript code
    vm = require('vm')

    # Create a new context and run the JavaScript code
    ctx = vm.createContext({})
    vm.runInContext(js_code_strict, ctx)

    # Run the JavaScript function
    js_result_strict = ctx.CompareStrict(Ar1, Ar2)

    # Python equality check (loose)
    def py_equal(values1, values2):
        return [val1 == val2 for val1, val2 in zip(values1, values2)]

    py_result_non_strict = py_equal(Ar1, Ar2)

    # Prepare output with headings
    output = [["JS-Strict-Eq.(===)", "PY-Equal(==)"]]

    # Append results side by side (JS strict equality, Python equality)
    for js_res, py_res in zip(js_result_strict, py_result_non_strict):
        output.append([js_res, py_res])

    return output

@xw.func
def js_compare_non_strict_equivalent(values):
    # Ensure values is always a list of lists
    if not isinstance(values, list):
        values = [[values]]
    elif not isinstance(values[0], list):
        values = [values]

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
                return value == values2[i];
            }
            return value == values2[i];
        });
    }
    """

    # Use JSPyBridge to run the JavaScript code
    vm = require('vm')

    # Create a new context and run the JavaScript code
    ctx = vm.createContext({})
    vm.runInContext(js_code_non_strict, ctx)

    # Run the JavaScript function
    js_result_non_strict = ctx.CompareNonStrict(Ar1, Ar2)

    # Python equality check (loose)
    def py_equal(values1, values2):
        return [val1 == val2 for val1, val2 in zip(values1, values2)]

    py_result_non_strict = py_equal(Ar1, Ar2)

    # Prepare output with headings
    output = [["JS-Non-Strict-Eq.(==)", "PY-Equal(==)"]]

    # Append results side by side (JS non-strict equality, Python equality)
    for js_res, py_res in zip(js_result_non_strict, py_result_non_strict):
        output.append([js_res, py_res])

    return output

