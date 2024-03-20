from flask import Flask, request
import json

app = Flask(__name__)

@app.route('/receive_json', methods=['POST'])
def receive_json():
    json_data = request.data
    data = json.loads(json_data)

    print(json_data)
    # Обращаемся к полученным данным
    name = data['name']
    age = data['age']

    return f"Полученное имя: {name}\nПолученный возраст: {age}"

if __name__ == '__main__':
    app.run()