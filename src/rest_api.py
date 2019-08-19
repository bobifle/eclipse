#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, abort, make_response, request, jsonify
import logging
import os
import json
from eclipse import pcs
log = logging.getLogger(__name__)

app = Flask(__name__)
uroot = '/api/v1.0'

tokens = pcs()

def json_files():
	jfiles = {}
	for root, dirs, files in os.walk('Data'):
		for f in (f for f in files if f.endswith('.json')):
			obj = os.path.splitext(f)[0].lower()
			if obj in jfiles: log.warning('duplicate json file %s' % obj)
			with open(os.path.join(root, f), 'r') as _file:
				print obj, _file
				jfiles[obj] = json.load(_file) 
	return jfiles

jcontent = json_files()

@app.route('/')
def index():
	return "Hello World"

@app.route(uroot + '/<string:obj>', methods=['GET'])
def get_object(obj):
	if obj not in jcontent: abort(404)
	
	return jsonify({obj: jcontent[obj]})

@app.route(uroot + '/tokens', methods=['GET'])
def get_tokens():
	return jsonify({'tokens':[t.to_dict() for t in tokens]})

@app.route(uroot + '/tokens/<int:token_id>', methods=['GET'])
def get_token(token_id):
	token = next((t for i, t in enumerate(tokens) if i == token_id), None)
	if token is None: abort(404)
	return jsonify({'token': token.to_dict()})

@app.route(uroot + '/tokens', methods = ['POST'])
def create_token():
	if not request.json:
		abort(400)
	token = {
		'id' : max((t['id'] for t in tokens)) + 1,
		'name' : request.json['name'],
	}
	tokens.append(token)
	return jsonify({'token': token.to_dict()}), 201

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not Found'}), 404)

@app.errorhandler(400)
def bad_request(error):
	return make_response(jsonify({'error': 'Bad request', 'req' : 'json'}), 400)

if __name__ == '__main__':
	logging.basicConfig()
	app.run(debug=True)
