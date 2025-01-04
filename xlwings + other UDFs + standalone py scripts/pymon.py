import xlwings as xw
from pythonmonkey import runtime

# Initialize PyMonkey JavaScript runtime
js_runtime = runtime.Runtime()

@xw.func
def js_test_function():
    # Basic JavaScript code: Pre-increment test
    js_code = """
    var x = 5;
    ++x;
    """

    # Execute the JavaScript code and get the result
    result = js_runtime.eval(js_code)
    
    # Return the result back to Excel
    return result

