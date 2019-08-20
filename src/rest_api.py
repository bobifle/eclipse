#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, abort, make_response, request, jsonify
import logging
import random
from eclipse import pcs
from data import content
log = logging.getLogger(__name__)

app = Flask(__name__)
uroot = '/api'

tokens = pcs()

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': 'Not Found'}), 404)

@app.errorhandler(400)
def bad_request(error):
	return make_response(jsonify({'error': 'Bad request', 'req' : 'json'}), 400)

@app.route('/')
def index():
	return "Hello World"

@app.route(uroot + '/<string:obj>', methods=['GET'])
def get_object(obj):
	if obj not in content: abort(404)

	return jsonify({obj: content[obj]})

############## Tokens ##################
def _get_token(token_id):
	return next((t for i, t in enumerate(tokens) if i == token_id), None)

@app.route(uroot + '/tokens', methods=['GET'])
def get_tokens():
	return jsonify({'tokens':[t.to_dict() for t in tokens]})

@app.route(uroot + '/tokens/<int:token_id>', methods=['GET'])
def get_token(token_id):
	token = _get_token(token_id)
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

############## Rolls ##################

def _roll(diff=None):
	r = random.randint(0, 99) ; sr = str(r)
	# any double digit is a crit
	crit = len(sr)>1 and len(set(sr)) == 1
	success, superior = None, None
	if diff is not None:
		# a sucess occurs when the roll is equal to or under the difficulty
		success = r <= diff
		# superior sucess when the roll is >= 33, 2 superior sucesses when the roll is >= 66
		if success:	superior = 2 if r >= 66 else (1 if r >= 33 else 0)
		# superior failure when the roll is < 66, 2 superior failures when the roll is < 33
		if not success:	superior = 2 if r < 33 else (1 if r < 66 else 0)
	return {'value': r, 'crit': crit, 'success': success, 'superior': superior, 'diff' : diff}

def _roll_contested(diff0, diff1):
	draw = True
	# roll until there's no draw
	while draw:
		r0 = _roll(diff0)
		r1 = _roll(diff1)
		draw = r0['success'] == r1['success'] and r0['value'] == r1['value']
	# however succeed and roll highest wins
	if r0['success'] == r1['success']: win0 = r0['value'] > r1['value']
	if r0['success'] != r1['success']: win0 = r0['success']
	return [{'winner': win0, 'roll' : r0}, {'winner': not win0, 'roll' : r1}]

@app.route(uroot + '/roll')
def roll(): return jsonify(_roll())

@app.route(uroot + '/roll/<int:diff>')
def roll_diff(diff): return jsonify(_roll(diff))

@app.route(uroot + '/roll/<int:diff0>/<int:diff1>')
def roll_contested(diff0, diff1): return jsonify(_roll_contested(diff0, diff1))

############## Attacks ##################
def _melee(attacker_id, defender_id):
	atok = _get_token(attacker_id)
	dtok = _get_token(defender_id)
	if atok is None or dtok is None: return None
	# attacker melee skill check
	ask = atok.skill_check.melee
	# defender picks up the highest check between melee and fray
	melee, fray  = dtok.skill_check.melee, dtok.skill_check.fray
	dsk = melee if melee['value'] > fray['value'] else fray
	# rolls against their respective skill check value
	aroll = _roll(ask['value'])
	droll = _roll(dsk['value'])
	hit = False
	if aroll['success']:
		# defender failed it's a hit
		if not droll['success'] : hit = True
		# defender succeeded, crits trump high rolls
		if droll['success']:
			if aroll['crit'] == droll['crit']: hit = aroll['value'] > droll['value']
			if aroll['crit'] != droll['crit']: hit = aroll['crit']
	result = {'attacker': {'token_id': attacker_id, "roll": aroll, 'skill_check': ask}, 'defender': {'token_id': defender_id, 'roll' : droll, 'skill_check': dsk}, 'hit': hit}

	return result

@app.route(uroot + '/melee/<int:attacker_id>/<int:defender_id>')
def melee(attacker_id, defender_id): return jsonify(_melee(attacker_id, defender_id))


if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	app.config['PROPAGATE_EXCEPTIONS'] = True
	app.run(debug=True)
