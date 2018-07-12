#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import csv
import shutil

from mtoken import Character, Morph, LToken, NPC
from macro import CssMacro, TMacro, LibMacro, SMacro
from mtable import Table, Entry
from cmpgn import Campaign, CProp, PSet
from zone import Zone
from util import lName, getLogger, configureLogger, parse_args, fromCsv

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
{"name": "infection", "showOnSheet": true, "value": "{psi*10}"},
{"name": "morph", "showOnSheet": true, "value": "{morph}"}
]
'''
npc_props='''[
{"name": "aptitudes", "showOnSheet": "true", "value": "COG {cognition} | INT {intuition} | REF {reflex} | SAV {savvy} | SOM {somatics} | WIL {willpower}"},
{"name": "others", "showOnSheet": "true", "value": "WT {wound_th} | DR {DR} | DUR {durability} | TP {TP} | Armor {energy}/{kinetic}"}
]
'''

smacros = {
	"Rename":'''
[h: name=tbl("Names")]
[h: setName(name)]
<!-- reselect the token to update the selection window with the new name-->
[h: tids = getSelected()]
[h: selectTokens(tids)]
[h: abort(0)] <!-- silence de macro -->
''',
	"Resleeve":'''
<!-- Set the token image according to its morph value -->
[h:  img = ep.getMorphImg()]
[r,if (img!=""), code: {
	[h:setTokenImage(img)] is resleeving the morph [r: getProperty("Morph")] 
	};{
	cannot resleeve into [r: getProperty("Morph")], it s not found in the morph tablelist
	}
]
''',
	"getMorphImg":'''
<!-- Return the morph image-->
[h: end = table("Morphs", 5000)]
[h: index = 1]
[h: morphName = getProperty("Morph")]
[h: found = 0]
[h: name = ""]
[h,while (name != end && found==0),code : {
	[h: name = table("Morphs", index)]
	[h,if (name==morphName), code: {[h:macro.return=tableImage("Morphs", index)][h:found=1]};{}]
	[h: index = index+1]
}
]
''',
}



def morphs():
	"""Fetch morphs from the csvFile"""
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
			# attach a sleeve macro
			m.macros.append(TMacro("Sleeve", 'msleeve.template', 'Sleeve', ('white', 'blue')))
			_morphs.append(m)
	return _morphs

def eclipseTable():
	t = Table('Eclipse', 'imglib/ep_logo.png')
	for i, (name,img) in enumerate([('stub', 'imglib/dft.png'), ('csheet', 'imglib/csheet.png')]):
		t.append(Entry(i, i, name, img))
	return t

def skills():
	return json.dumps([dict(name=skill,apt=apt)for skill, apt in [
		("persuade", "savvy"),
		("deceive", "savvy"),
		("fray", "reflex"),
		("free_fall", "somatics"),
		("interface", "cognition"),
		]])

def traits(): return fromCsv('data/data_traits.csv')

def factions(): return fromCsv('data/data_factions.csv')

def pcs():
	with open('data/pcs.json', 'r') as jfile:
		chars = json.load(jfile, object_hook = Character.from_json)
	# assign to each player character their macro
	for tok in chars:
		tok.macros.append(SMacro("Sheet", '[macro("Sheet@Lib:ep"): "page=Ego; name=[r:getName()]"]', 'Sheet', ('white', 'blue')))
		tok.macros.append(SMacro("Resleeve", '[macro("Resleeve@Lib:ep"): ""]', 'Sheet', ('white', 'blue')))
	return chars

def npcs():
	with open('data/npcs.json', 'r') as jfile:
		npc_list = json.load(jfile, object_hook = NPC.from_json)
	for tok in npc_list:
		tok.macros.append(SMacro("Rename", smacros['Rename'], 'Sheet', ('white', 'blue')))
		tok.macros.append(SMacro("Resleeve", smacros['Resleeve'], 'Sheet', ('white', 'blue')))
	return npc_list

def libMacros():
	macros = []
	macros.extend([
		CssMacro('ep_css', 'css/ep.css', 'css', ('black', 'white')),
		TMacro("Sheet", 'sheet.template', 'Sheet', ('white', 'blue')),
		TMacro("EgoSheet", 'egoSheet.template', 'Sheet', ('white', 'blue')),
		TMacro("MorphSheet", 'morphSheet.template', 'Sheet', ('white', 'blue')),
		TMacro("Skills", 'skills.template', 'func', ('white', 'black')),
		TMacro("LibInfo", 'libInfo.template', 'func', ('white', 'black')),
		TMacro("Morphs", 'morphs.template', 'func', ('white', 'black')),
		SMacro("getMorphImg", smacros['getMorphImg'], 'func', ('white', 'black')),
	])
	# functions
	macros.extend([
		SMacro("isMorph", '''[h: macro.return="false"][h:ptype=getPropertyType()][h,if (pType=="MORPH"): macro.return="true"]''', 'func', ('white', 'black'))
	])
	macros.extend([ LibMacro(trait['name'],'Traits', ('white','red'), trait) for trait in traits()])
	macros.extend([ LibMacro(faction['name'],'Factions', ('white','blue'), faction) for faction in factions()])
	macros.extend([ LibMacro(sl['name'],'Sleights', ('white','blue'), sl) for sl in fromCsv('data/data_sleights.csv')])
	# keep this one last, very important, as it is function of previous added macros
	macros.append(TMacro("onCampaignLoad", 'onCampaignLoad.template', 'func', ('white', 'black'), {'functions': ['isMorph', 'getMorphImg']}))
	return macros

# build the list of lib tokens
def libTokens():
	libs = [LToken('Lib:ep', libMacros(), 'imglib/ep_logo.png')]
	# the gear lib
	emacros = []
	for (group, fp ,colors) in [
			('Gear', 'data/data_gear.csv', ('white', 'green')),
			]:
		emacros.extend([LibMacro(item['name'], group, colors, item) for item in fromCsv(fp)])
	libs.append(LToken('Lib:gear', emacros, 'imglib/icons/backpack.png'))
	emacros = []
	for (group, fp ,colors) in [
			('Melee Weapons', 'data/data_melee_weapons.csv', ('white', 'red')),
			('Ranged Weapons', 'data/data_ranged_weapons.csv', ('white', 'red')),
			]:
		emacros.extend([LibMacro(item['name'], group, colors, item) for item in fromCsv(fp)])
	libs.append(LToken('Lib:weap', emacros, 'imglib/icons/ammo-box.png'))
	emacros = []
	for (group, fp ,colors) in [
			('Armors', 'data/data_armor.csv', ('white', 'blue')),
			]:
		emacros.extend([LibMacro(item['name'], group, colors, item) for item in fromCsv(fp)])
	libs.append(LToken('Lib:weap', emacros, 'imglib/icons/space-suit.png'))
	return libs

def propertySets():
	sets = [PSet('Lib', [])] # the Lib property set is empty for now
	# Build the PC property type # XXX rebuilding pcs just for the first element :-/
	sets.append(PSet('PC',
		[CProp.fromTProp(p) for p in pcs()[0].props] + [CProp(p) for p in json.loads(pc_props)]
		))
	sets.append(PSet('MORPH',
		[CProp.fromTProp(p) for p in morphs()[0].props] + [CProp(p) for p in json.loads(morph_props)]
		))
	sets.append(PSet('NPC',
		[CProp.fromTProp(p) for p in npcs()[0].props] +[CProp(p) for p in json.loads(npc_props)]
		))
	return sets

def nameTable():
	t = Table('Names', 'imglib/ep_logo.png')
	with open('data/names.json', 'r') as jfile:
		for i, name in enumerate(json.load(jfile)["male"]):
			t.append(Entry(i, i, name, None))
	return t

def morphTable():
	t = Table('Morphs', 'imglib/ep_logo.png')
	for i, m in enumerate(morphs()):
		if m.icon: t.append(Entry(i, i, m.name, m.icon.fp))
	return t


def main():
	options, _ = parse_args()
	configureLogger(options.verbose)
	if options.clean:
		log.warning("cleaning the build directory")
		shutil.rmtree('build')
	zone = Zone('Library')
	zone.build(pcs()+npcs()+morphs()+libTokens())
	ecp = Campaign('eclipse')
	dmScreen = Zone('DM Screen')
	ecp.build([zone, dmScreen], propertySets(), [eclipseTable(), nameTable(), morphTable()])
	log.warning('Done building %s with a total of %s macros, %s assets' % (ecp, len(list(ecp.macros)), len(list(ecp.assets))))
	return ecp

if __name__== '__main__':
	cp = main()
