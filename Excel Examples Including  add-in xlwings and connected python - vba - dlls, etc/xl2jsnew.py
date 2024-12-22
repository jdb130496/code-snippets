import xlwings as xw
from pythonmonkey import eval as js_eval

@xw.func
def test_pythonmonkey():
    # JavaScript code to test
    js_code = """
    function add(a, b) {
        return a + b;
    }
    add
    """
    
    # Use PythonMonkey to run the JavaScript code
    add = js_eval(js_code)
    
    # Test the JavaScript function
    result = add(2, 3)
    
    return result

# Run the UDF server
if __name__ == "__main__":
    xw.serve()
