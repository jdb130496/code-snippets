import pythonmonkey as pm
import sys
import json

def pre_increment(values):
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
    output_pre_increment = [['preincrement-JS-Original', 'preincrement-JS-Incremented', 'preincrement-PY']]
    for (js_orig, js_inc), py_val in zip(js_result_pre_increment, py_result):
        output_pre_increment.append([js_orig, js_inc, py_val])

    return output_pre_increment

if __name__ == "__main__":
    values = json.loads(sys.argv[1])
    result = pre_increment(values)
    print(json.dumps(result))

