#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import optparse

from mtoken import Map, Character, Morph
from cmpgn import Campaign, CProp
from util import lName, getLogger, configureLogger, parse_args

log = getLogger(lName)

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
		{"flex": 2},
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

morphs = [
'''{	"_type" : "Morph",
	"name": "arachnoid",
	"category": "synthmorph",
	"attributes": [
		{"durability":55},
		{"wound_th": 11},
		{"death_rating": 110}
		],
	"pools": [
		{"insight":1},
		{"moxie":0},
		{"vigor":4},
		{"flex": 2}
		],
	"movements": [
		{"hopper":[4,16]},
		{"thurst_vector":[8,40]},
		{"walker":[4,24]},
		{"wheeled":[8,40]}
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
	# eclipse characters will use their morph name to try finding the proper portrait in the imglib
	@property
	def matchImg(self): return self.morph

def main():
	options, args = parse_args()
	configureLogger(options.verbose)
	chars = [json.loads(tok, object_hook = ECharacter.from_json) for tok in tokens]
	_morphs = [json.loads(tok, object_hook = Morph.from_json) for tok in morphs]
	cp = Campaign('eclipse')
	cp.build(chars+_morphs, campaign_props)
	return cp

if __name__== '__main__':
	cp = main()
