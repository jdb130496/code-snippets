from flask import Flask, jsonify
app = Flask(__name__)
@app.route('/')
def home():
    return jsonify(message="Server is running!")
@app.route('/my_function', methods=['POST'])
def my_function():
    data = request.json
    result = data['value'] * 2
    return jsonify(result=result)
if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5460)

