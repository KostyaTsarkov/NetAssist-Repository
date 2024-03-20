#request
import requests
import json

print('hello')
#url = 'http://127.0.0.1:5000/receive_json'
json_data = '{"name": "Bob", "age": 25}'

response = requests.post('http://127.0.0.1:5000/receive_json', data=json_data)

print(response.text)