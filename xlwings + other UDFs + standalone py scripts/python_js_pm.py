import xlwings as xw
import pythonmonkey as pm

@xw.func
def js_compare_pre_increment_pm(values):
    if isinstance(values[0], list):
        flat_values = [item if item is not None else 'null' for sublist in values for item in sublist]
    else:
        flat_values = [item if item is not None else 'null' for item in values]

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
    pre_increment = pm.eval(js_code_pre_increment)
    js_result_pre_increment = pre_increment(flat_values)

    def pre_increment_py(values):
        return [float(value) + 1 if value != 'null' else 'null' for value in values]
    py_result = pre_increment_py(flat_values)

    output = [["preincrement-JS-Original", "preincrement-JS-Incremented", "preincrement-PY"]]
    for (js_orig, js_inc), py_val in zip(js_result_pre_increment, py_result):
        output.append([js_orig, js_inc, py_val])
    return output

@xw.func
def js_compare_non_strict_equ_pm(values):
    if not isinstance(values[0], list):
        return "Input must be a list of lists"
    
    Ar1 = [row[0] for row in values]
    Ar2 = [row[1] for row in values]

    def replace_none_with_null(values):
        return ['null' if val is None else val for val in values]
    
    Ar1 = replace_none_with_null(Ar1)
    Ar2 = replace_none_with_null(Ar2)

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
    compare_non_strict = pm.eval(js_code_non_strict)
    js_result_non_strict = compare_non_strict(Ar1, Ar2)

    def py_equal(values1, values2):
        return [val1 == val2 for val1, val2 in zip(values1, values2)]
    py_result_non_strict = py_equal(Ar1, Ar2)

    output = [["JS-Non-Strict-Eq.(==)", "PY-Equal(==)"]]
    for js_res, py_res in zip(js_result_non_strict, py_result_non_strict):
        output.append([js_res, py_res])
    return output

@xw.func
def js_compare_strict_equivalent_pm(values):
    if not isinstance(values[0], list):
        return "Input must be a list of lists"
    
    Ar1 = [row[0] for row in values]
    Ar2 = [row[1] for row in values]

    def replace_none_with_null(values):
        return ['null' if val is None else val for val in values]
    
    Ar1 = replace_none_with_null(Ar1)
    Ar2 = replace_none_with_null(Ar2)

    js_code_strict = """
    function CompareStrict(values1, values2) {
        return values1.map((value, i) => {
            if (value === 'null' || values2[i] === 'null') {
                return value === values2[i];
            }
            return value === values2[i];
        });
    }
    CompareStrict
    """
    compare_strict = pm.eval(js_code_strict)
    js_result_strict = compare_strict(Ar1, Ar2)

    def py_equal(values1, values2):
        return [val1 == val2 for val1, val2 in zip(values1, values2)]
    py_result_non_strict = py_equal(Ar1, Ar2)

    output = [["JS-Strict-Eq.(===)", "PY-Equal(==)"]]
    for js_res, py_res in zip(js_result_strict, py_result_non_strict):
        output.append([js_res, py_res])
    return output
