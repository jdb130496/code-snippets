# Define the input array for pre-increment
values_pre_increment = [123, 456, 789.678, 101112]

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
from javascript import require
js = require('vm')
ctx_pre_increment = js.runInNewContext(js_code_pre_increment)
js_result_pre_increment = ctx_pre_increment.preIncrement(values_pre_increment)

# Python pre-increment
def pre_increment_py(values):
    return [value + 1 for value in values]

py_result_pre_increment = pre_increment_py(values_pre_increment)

# Print results for pre-increment
print("Pre-increment results:")
print("JS Result:", js_result_pre_increment)
print("PY Result:", py_result_pre_increment)

