#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import json
import io
import hashlib
import zipfile
import os
import sys
import uuid
import base64
try:
	import coloredlogs # optional
except ImportError: pass
import logging
import difflib
import itertools
from PIL import Image
import glob

log = logging.getLogger()

tokens='''
{	"_type" : "Character", 
	"name" : "Amal",
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
		]

}
'''

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

imglibs = [ 'imglib', ]

_jenv = None

def jenv():
	global _jenv
	if _jenv is None:
		_jenv = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
	return _jenv

class Campaign(object):
	def __init__(self, name):
		self.name = name
		self.props = []
		self.tokens = []

	def __repr__(self): return 'Cmpgn<%s>' % self.name

	def setProps(self, token):
		"""Set campaign properties using the given token as reference"""
		self.props = []
		for prop in token.props:
			self.props.append(CProp.fromTProp(prop))

	@property
	def content_xml(self):
		content = jenv().get_template('cmpgn_content.template').render(cmpgn=self)
		return content or ''

	@property
	def properties_xml(self):
		content = jenv().get_template('cmpgn_properties.template').render(cmpgn=self)
		return content or ''

	def zipme(self):
		"""Zip the Campaing into a cmpgn file."""
		log.info("Zipping %s" % self)
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.cmpgn'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml.encode('utf-8'))
			zipme.writestr('properties.xml', self.properties_xml)
			for token in self.tokens:
				for name, asset in token.assets.iteritems():
					zipme.writestr('assets/%s' % asset.md5, jenv().get_template('md5.template').render(name=name, extension='png', md5=asset.md5))
					zipme.writestr('assets/%s.png' % asset.md5, asset.bytes.getvalue())

class CProp(object):
	"""Campaign property."""
	def __init__(self, name, showOnSheet, defaultValue):
		self.name=name
		self._showOnSheet = showOnSheet
		self.defaultValue = defaultValue
	@classmethod
	def fromTProp(cls, token_prop):
		return cls(token_prop.name, False, '')
	def __repr__(self): return '%s<%s>' % (self.__class__.__name__, self.name)
	@property
	def shortname(self): return ''
	@property
	def showOnSheet(self): return "true" if self._showOnSheet else 'false'
	@showOnSheet.setter
	def showOnSheet(self, v): self._showOnSheet = v
	def render(self):
		return jinja2.Template('''            <net.rptools.maptool.model.TokenProperty>
              <name>{{prop.name}}</name>
	      {% if prop.shortname %}
	      <shortName>{{prop.shortname}}</shortName>}
	      {% endif -%}
              <highPriority>{{prop.showOnSheet}}</highPriority>
              <ownerOnly>false</ownerOnly>
              <gmOnly>false</gmOnly>
              <defaultValue>{{prop.defaultValue}}</defaultValue>
            </net.rptools.maptool.model.TokenProperty>''').render(prop=self)

class ECampaign(Campaign):
	"""Eclipse Phase campaign."""
	def setProps(self, token):
		Campaign.setProps(self, token)
		for prop in json.loads(campaign_props):
			self.props.append(CProp(prop['name'], prop['showOnSheet'], prop['value']))

class TProp(object):
	"""Token property"""
	def __init__(self, name, value):
		self.name = name
		self.value = value
	def __repr__(self): return '%s<%s,%s>' % (self.__class__.__name__, self.shortname, self.value)

	@property
	def shortname(self): return self.name[:3].upper()

	def render(self):
		return jinja2.Template('''      <entry>
	    <string>{{prop.name.lower()}}</string>
	    <net.rptools.CaseInsensitiveHashMap_-KeyValue>
	      <key>{{prop.name}}</key>
	      <value class="string">{{prop.value}}</value>
	      <outer-class reference="../../../.."/>
	    </net.rptools.CaseInsensitiveHashMap_-KeyValue>
	  </entry>''').render(prop=self)

class Img(object):
	def __init__(self, fp):
		self.bytes = io.BytesIO()
		self.fp = fp
		with Image.open(fp) as img:
			self.x, self.y = img.size
			img.save(self.bytes, format='png')
		self._md5 = hashlib.md5(self.bytes.getvalue()).hexdigest()
	@property
	def md5(self): return self._md5

	def thumbnail(self, x,y):
		thumb = io.BytesIO()
		with Image.open(self.fp, 'r') as img:
			img.thumbnail((x,y))
			img.save(thumb, format='png')
		return thumb

class Token(object):
	sentinel = object()

	def __init__(self):
		self._md5 = self.sentinel
		self._img = self.sentinel
		self._guid = self.sentinel
		self.name = 'defaultName'
		self.size = 'medium'
		self.assets = {}
		self.snapToGrid = "true"
		self.snapToScale = "true" # snap to the grid size
		self.x, self.y = 0,0

	# XXX system dependant ?
	@property
	def size_guid(self):
		# XXX may depend on the maptool version
		return {
			'tiny':       'fwABAc5lFSoDAAAAKgABAA==',
			'small':      'fwABAc5lFSoEAAAAKgABAA==',
			'medium':     'fwABAc9lFSoFAAAAKgABAQ==',
			'large':      'fwABAdBlFSoGAAAAKgABAA==',
			'huge':       'fwABAdBlFSoHAAAAKgABAA==',
			'gargantuan': 'fwABAdFlFSoIAAAAKgABAQ==',
		}[self.size.lower()]
	
	def __getattr__(self, attr):
		for prop in self.props:
			if prop.name.lower() == attr.lower(): return prop

	@property
	def macros(self): raise NotImplementedError

	@property
	def props(self): raise NotImplementedError

	@property
	def states(self): raise NotImplementedError

	@property
	def guid(self):	
		if self._guid is self.sentinel:
			self._guid = base64.b64encode(uuid.uuid4().bytes)
		return self._guid

	@property
	def type(self): return 'PC'

	@property
	def prop_type(self): return 'Eclipse'

	@property
	def width(self): 
		return self.icon.x

	@property
	def height(self):
		return self.icon.y

	@property
	def content_xml(self):
		content = jenv().get_template('token_content.template').render(token=self)
		return content or ''

	@property
	def properties_xml(self):
		content = jenv().get_template('token_properties.template').render(token=self)
		return content or ''

	@property
	def layer(self): raise NotImplementedError

	def render(self): return self.content_xml

	def zipme(self):
		"""Zip the token into a rptok file."""
		log.info("Zipping %s" % self)
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.rptok'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml.encode('utf-8'))
			zipme.writestr('properties.xml', self.properties_xml)
			# default image for the token, right now it's a brown bear
			# zip the xml file named with the md5 containing the asset properties
			zipme.writestr('assets/%s' % self.icon.md5, jenv().get_template('md5.template').render(name=self.name, extension='png', md5=self.icon.md5))
			# zip the img itself
			zipme.writestr('assets/%s.png' % self.icon.md5, self.icon.bytes.getvalue())
			# build thumbnails
			zipme.writestr('thumbnail', self.icon.thumbnail(50,50).getvalue())
			zipme.writestr('thumbnail_large', self.icon.thumbnail(500,500).getvalue())

	@property
	def icon(self):
		img = self.assets.get("icon", None)
		# try to fetch an appropriate image from the imglib directory
		# using a stupid heuristic: the image / token.name match ratio
		if img is None:
			# compute the diff ratio for the given name compared to the token name
			ratio = lambda name: difflib.SequenceMatcher(None, name.lower(), self.name.lower()).ratio()
			# morph "/abc/def/anyfile.png" into "anyfile"
			short_name = lambda full_path: os.path.splitext(os.path.basename(full_path))[0]
			# list of all img files
			files = itertools.chain(*(glob.glob(os.path.join(os.path.expanduser(imglib), '*.png')) for imglib in imglibs))
			bratio=0
			if files:
				# generate the diff ratios
				ratios = ((f, ratio(short_name(f))) for f in files)
				# pickup the best match, it's a tuple (fpath, ratio)
				bfpath, bratio = max(itertools.chain(ratios, [('', 0)]), key = lambda i: i[1])
				log.debug("Best match from the img lib is %s(%s)" % (bfpath, bratio))
			if bratio > 0.8:
				self.assets['icon'] = Img(bfpath)
			else:
				self.assets['icon'] = Img(os.path.join('imglib', 'dft.png'))
		return self.assets.get('icon', None)
	@icon.setter
	def icon(self, fp): self.assets['icon'] = Img(fp)

	@property
	def portrait(self): 
		portrait = self.assets.get('portrait', None)
		if portrait is None:
			if self.icon:
				fp = self.icon.filename.replace('.png', '_p.png')
				if os.path.exists(fp):
					self.assests['portrait'] = Img(fp)
			
		return self.assets.get('portrait', None)

	@portrait.setter
	def portrait(self, fp): 
		self.assets['portrait'] = Img(fp)

class Character(Token):
	"Eclipse Character"
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

class IToken(Token):
	def __init__(self, *args, **kwargs):
		Token.__init__(self, *args, **kwargs)
		self.snapToGrid = 'false'
		self.snapToScale = 'false'
	@property
	def props(self): return []
	@property
	def states(self): return []
	@property
	def macros(self): return []
	@property
	def layer(self): return 'BACKGROUND'
	@property
	def type(self): return 'NPC'

if __name__== '__main__':
	# initialize the colored logs if the module is installed
	if hasattr(sys.modules[__name__], "coloredlogs") :
		coloredlogs.install(fmt='%(name)s %(levelname)8s %(message)s')
	logging.basicConfig(level=logging.INFO)
	amal = json.loads(tokens, object_hook = Character.from_json)
	amal.assets['icon'] = Img('imglib/arachnoid.png')
	amal.assets['portrait'] = Img('imglib/arachnoid_p.png')
	amal.zipme()
	cmpgn = ECampaign('dft')
	cmpgn.setProps(amal)
	main_scene = IToken()
	main_scene.name = 'main_scene'
	cmpgn.tokens.append(main_scene)
	cmpgn.tokens.append(amal)
	cmpgn.zipme()
