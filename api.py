from flask import Flask, jsonify
from downloader import download_dataset, search_datasets
import json


"""
    My api, run on pythonAnywhere
"""


app = Flask(__name__)


@app.route('/', methods = ['GET'])
def home():   
    data = "hello this is my api"
    return jsonify({'data': data}) 

@app.route('/search/<string:name>', methods=['GET'])
def search(name):
    data = search_datasets(name=f'q={name}') 
    return jsonify({'data': data['data']}) 

@app.route('/download/<string:id>', methods=['GET'])
def download(id):
    data, geo = download_dataset(id=id)
    return jsonify({'data': data, 'geo': geo}) 

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5000)