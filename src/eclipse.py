#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import csv

from mtoken import Character, Morph, LToken, TProp
from macro import SheetMacro, CssMacro, Macro
from mtable import Table, Entry
from cmpgn import Campaign, CProp, PSet
from zone import Zone
from util import lName, getLogger, configureLogger, parse_args

log = getLogger(lName)

morph_props='''[
{"name": "pools", "showOnSheet": true, "value": "Ins {insight} | Mox {moxie} |Vig {vigor} | Flex {flex}"}
]
'''
pc_props='''[
{"name": "aptitudes", "showOnSheet": true, "value": "COG {cognition} | INT {intuition} | REF {reflex} | SAV {savvy} | SOM {somatics} | WIL {willpower}"},
{"name": "pools", "showOnSheet": true, "value": "Ins {insight} | Mox {moxie} |Vig {vigor} | Flex {flex}"},
{"name": "initiative", "showOnSheet": true, "value": "{(reflex + intuition)/5}"},
{"name": "lucidity", "showOnSheet": true, "value": "{willpower*2}"},
{"name": "insanity", "showOnSheet": true, "value": "{lucidity*2}"},
{"name": "trauma", "showOnSheet": true, "value": "{lucidity/5}"},
{"name": "infection", "showOnSheet": true, "value": "{psi*10}"}
]
'''

def getMorphs():
	_morphs= []
	with open('data/data_morphs.csv', 'r') as csvfile:
		reader = csv.DictReader(csvfile)
		for row in reader:
			m = Morph()
			m.name = row['name']
			m.notes = row['desc']
			m.category = row['type']
			m.attributes = [
				{'wound_th': int(row['WT'])},
				{'durability': int(row['Durability'])},
			]
			m.pools = []
			firstEd2Second = lambda attrList: int(sum((int(row[attr]) for attr in attrList))/2.5)
			m.pools = [
				{'insight': firstEd2Second(['COG', 'INT'])},
				{'moxie': firstEd2Second(['SAV', 'WIL'])},
				{'vigor': firstEd2Second(['REF', 'SOM'])},
				{'flex': int(row['CP'])/20},
			]
			m.movements=[{"walker":[4,24]}]
			_morphs.append(m)
	return _morphs

def eclipseTable():
	t = Table('Eclipse', 'imglib/ep_logo.png')
	for i, (name,img) in enumerate([('stub', 'imglib/dft.png'), ('csheet', 'imglib/csheet.png')]):
		t.append(Entry(i, i, name, img))
	return t

def libMacros(ep):
	return [
		CssMacro(ep, 'ep_css', 'css/ep.css', 'css', ('black', 'white')),
		Macro(ep, "Sheet", 'sheet.template', 'Sheet', ('white', 'blue')),
		Macro(ep, "MainSheet", 'mainSheet.template', 'Sheet', ('white', 'blue')),
		Macro(ep, "MorphSheet", 'morphSheet.template', 'Sheet', ('white', 'blue')),
		Macro(ep, "Skills", 'skills.template', 'Skills', ('white', 'black')),
		Macro(ep, "onCampaignLoad", 'onCampaignLoad.template', 'Misc', ('white', 'black')),
	]

def skills():
	return json.dumps([dict(name=skill,apt=apt)for skill, apt in [
		("persuade", "savvy"),
		("deceive", "savvy"),
		("fray", "reflex"),
		("free_fall", "somatics"),
		]])

def main():
	options, args = parse_args()
	configureLogger(options.verbose)
	with open('data/pcs.json', 'r') as jfile:
		chars = json.load(jfile, object_hook = Character.from_json)
	for tok in chars: tok.macros = [SheetMacro(tok)]
	_morphs = getMorphs()
	ep = LToken('Lib:ep', []); ep.macros = libMacros(ep)
	ep.props = [TProp('skills', skills())]
	zone = Zone('Library')
	zone.build(chars+_morphs+[ep])
	# Build the PC property type
	pc = PSet('PC', [CProp.fromTProp(p) for p in chars[0].props])
	pc.props.extend([CProp(p['name'], p['showOnSheet'], p['value']) for p in json.loads(pc_props)])
	# Build the Morph property type
	pmorph = PSet('MORPH', [CProp.fromTProp(p) for p in _morphs[0].props])
	pmorph.props.extend([CProp(p['name'], p['showOnSheet'], p['value']) for p in json.loads(morph_props)])
	plib = PSet('Lib', [CProp.fromTProp(p) for p in ep.props])
	# Build the Lib property type (empty)
	cp = Campaign('eclipse')
	cp.build([zone], [pc, pmorph, plib], [eclipseTable()])
	log.warning('Done building %s' % cp)
	return cp

if __name__== '__main__':
	cp = main()
