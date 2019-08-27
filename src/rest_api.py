#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, abort, make_response, request, jsonify
import logging
import random
from eclipse import pcs
import mtoken
from data import content
log = logging.getLogger('eclipse' if __name__ == '__main__' else __name__)

app = Flask(__name__)
#host = '192.168.200.7'
host = 'localhost'
port = 5123
uroot = '/api'

tokens = {tok.key: tok for tok in pcs()}
print tokens

@app.errorhandler(404)
def not_found(error):
	return make_response(jsonify({'error': str(error)}), 404)

@app.errorhandler(400)
def bad_request(error):
	return make_response(jsonify({'error': str(error), 'req' : 'json'}), 400)

@app.route('/')
def index(): return "Hello World"

@app.route(uroot + '/<string:obj>', methods=['GET'])
def get_object(obj):
	if obj not in content: abort(404)
	return jsonify({obj: content[obj]})

############## Tokens ##################
def _get_token(token_id):
	return next((t for i, t in enumerate(tokens.values()) if i == token_id), None)

@app.route(uroot + '/tokens', methods=['GET'])
def get_tokens():
	return jsonify({'tokens':[t.to_dict() for t in tokens.values()]})

@app.route(uroot + '/tokens/<int:token_id>', methods=['GET'])
def get_token(token_id):
	token = _get_token(token_id)
	if token is None: abort(404)
	return jsonify({'token': token.to_dict()})

@app.route(uroot + '/token', methods = ['POST'])
def create_token():
	j = request.json
	if not j: abort(400, "expecting json data")
	if '_type' not in j: abort(400, 'The token msut have a type')
	cls = getattr(mtoken, j['_type'], None)
	if cls is None: abort(400, 'Type of Token "%s" unknown' % j['_type'])
	token = cls.from_json(j)
	if token.key not in tokens:
		log.debug("Adding a new token %s" % token)
		tokens[token.key] = token
	else:
		log.debug("Updating existing token %s" % token)
		tokens[token.key].update(token)

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

@app.route(uroot + '/roll/<int:diff0>/<int:diff1>.html')
def roll_contested_html(diff0, diff1): return '<p>This is a p</p><p>Anoter <b>bold</b> p </p>'

############## SKill checks ##################
def _skill_check(token_id, skill):
	try:
		return getattr(_get_token(token_id).skill_check, skill)
	except Exception, e:
		abort(400, str(e))

@app.route(uroot + '/token/<int:token_id>/skill_check/<string:skill>')
def skill_check(token_id, skill): return jsonify(_skill_check(token_id, skill))

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
	app.run(debug=True, host=host, port=port)
