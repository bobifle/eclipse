#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import optparse
try:
	import coloredlogs # optional
except ImportError: pass
import logging

from token import Map, Character
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

class ECharacter(Character):
	@property
	def matchImg(self): return self.morph

if __name__== '__main__':
	# initialize the colored logs if the module is installed
	try:
		coloredlogs.install(fmt='%(name)s %(levelname)8s %(message)s')
	except NameError: pass
	parser = optparse.OptionParser()
	parser.add_option('-v', '--verbose', dest='verbose', action='count',
			help='increase the logging level')
	(options, args) = parser.parse_args()
	logging.basicConfig(level=logging.INFO-options.verbose*10)
	chars = [json.loads(tok, object_hook = ECharacter.from_json) for tok in tokens]
	for index, char in enumerate(chars):
		# set their icon
		# char.icon = 'imglib/%s.png'%char.morph
		# offset characters from 1 grid unit from each other
		char.x = (index+20)*50
		char.zipme()
	cp = Campaign('eclipse')
	# use the first character properties, and add these as campaign properties as well
	cp.props.extend([CProp.fromTProp(p) for p in chars[0].props])
	cp.props.extend([CProp(p['name'], p['showOnSheet'], p['value']) for p in json.loads(campaign_props)])
	main_scene = Map()
	main_scene.name = 'main_scene'
	cp.tokens.append(main_scene)
	cp.tokens.extend(chars)
	cp.zipme()
