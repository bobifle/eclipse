#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
try:
	import coloredlogs # optional
except ImportError: pass
import logging
import itertools

from token import Token, IToken, TProp
from cmpgn import Campaign, CProp

log = logging.getLogger()

tokens=[

'''{	"_type" : "Character",
	"name" : "Chi",
	"morph": "sylph",
	"attributes": [
		{"somatics":10},
		{"reflex": 15},
		{"savvy": 20},
		{"intuition": 15},
		{"cognition": 20},
		{"willpower" : 20}
		],
	"pools": [
		{"insight":1},
		{"moxie":3},
		{"vigor":1},
		{"flex": 1},
		{"ego_flex": 1}
		],
	"skills": [
		{"melee":0},
		{"psi":0}
		],
	"notes": "A native Martian, you were assigned male at birth in pre-Fall Noctis to a family of industrialists part of the Martian hyperelite.<p>You're socially perceptive, with a gift for ingratiating yourself to potential contacts. Everyone needs a psychologist even if they don't know it.</p>"
}
''',
'''{	"_type" : "Character",
	"name" : "Njal",
	"morph": "wirehead",
	"attributes": [
		{"somatics":15},
		{"reflex": 20},
		{"savvy": 10},
		{"intuition": 15},
		{"cognition": 20},
		{"willpower" : 15}
		],
	"pools": [
		{"insight":4},
		{"moxie":0},
		{"vigor":2},
		{"flex": 1},
		{"ego_flex": 1}
		],
	"skills": [
		{"melee":0},
		{"psi":0}
		],
	"notes": ""
}
''',
'''{	"_type" : "Character",
	"name" : "Amal",
	"morph": "arachnoid",
	"attributes": [
		{"somatics":15},
		{"reflex": 20},
		{"savvy": 15},
		{"intuition": 20},
		{"cognition": 15},
		{"willpower" : 15}
		],
	"pools": [
		{"insight":1},
		{"moxie":0},
		{"vigor":4},
		{"flex": 1},
		{"ego_flex": 1}
		],
	"skills": [
		{"melee":55},
		{"psi":0}
		],
	"notes": ""
}
''',
]

campaign_props='''[
{"name": "aptitudes", "showOnSheet": true, "value": "COG {cognition} | INT {intuition} | REF {reflex} | SAV {savvy} | SOM {somatics} | WIL {willpower}"},
{"name": "pools", "showOnSheet": true, "value": "Ins {insight} | Mox {moxie} |Vig {vigor} | Flex {flex}"},
{"name": "initiative", "showOnSheet": true, "value": "{(reflex + intuition)/5}"},
{"name": "lucidity", "showOnSheet": true, "value": "{willpower*2}"},
{"name": "insanity", "showOnSheet": true, "value": "{lucidity*2}"},
{"name": "trauma", "showOnSheet": true, "value": "{lucidity/5}"},
{"name": "infection", "showOnSheet": true, "value": "{psi*10}"}
]
'''

class ECampaign(Campaign):
	"""Eclipse Phase campaign."""
	def setProps(self, token):
		Campaign.setProps(self, token)
		for prop in json.loads(campaign_props):
			self.props.append(CProp(prop['name'], prop['showOnSheet'], prop['value']))

class Character(Token):
	"Eclipse Character"
	def __init__(self, *args, **kwargs):
		Token.__init__(self, *args, **kwargs)
		self.hasSight = 'true'
	@classmethod
	def from_json(cls, dct):
		_type = dct.get("_type", None)
		if _type is not None and _type.lower() == "character":
			ret = cls()
			for k,v in dct.iteritems(): setattr(ret, k, v)
			return ret
		return dct

	def __repr__(self): return 'Char<%s>' % self.name

	@property
	def props(self): return [TProp(*next(attr.iteritems())) for attr in itertools.chain(self.attributes, self.pools, self.skills)]
	@property
	def states(self): return []
	@property
	def macros(self): return []
	@property
	def layer(self): return 'TOKEN'

if __name__== '__main__':
	# initialize the colored logs if the module is installed
	try:
		coloredlogs.install(fmt='%(name)s %(levelname)8s %(message)s')
	except NameError: pass
	logging.basicConfig(level=logging.INFO)
	chars = [json.loads(tok, object_hook = Character.from_json) for tok in tokens]
	for index, char in enumerate(chars):
		# set their icon
		char.icon = 'imglib/%s.png'%char.morph
		# offset characters from 1 grid unit from each other
		char.x = (index+20)*50
		char.zipme()
	cmpgn = ECampaign('dft')
	cmpgn.setProps(chars[0])
	main_scene = IToken()
	main_scene.name = 'main_scene'
	cmpgn.tokens.append(main_scene)
	cmpgn.tokens.extend(chars)
	cmpgn.zipme()
