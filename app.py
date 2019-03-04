import json

from flask import Flask, jsonify, request
from pymongo import MongoClient

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'genes_db'
app.config['MONGO_URI'] = 'mongodb://localhost:27017/db'

db = MongoClient('localhost', 27017).test_database


with open('relations.json') as f:
    data = json.loads(f.read())

genes = db.genes
for elem in data:
    genes.insert(elem)


@app.route('/gene', methods=['GET'])
def get_gene():
    name = request.args.get('gene', type=str)
    return jsonify({name: genes.find_one({"gen": name})['id']})


@app.route('/abstract', methods=['GET'])
def get_abstract():
    name = request.args.get('gene', type=str)
    return jsonify({name: genes.find_one({"gen": name})['abstract']})


@app.route('/matches', methods=['GET'])
def get_match():
    name = request.args.get('gene', type=str)
    return jsonify({name: genes.find_one({"gen": name})['match']})


if __name__ == '__main__':
    app.run(debug=True)
