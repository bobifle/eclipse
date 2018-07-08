#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zipfile
import os
import difflib
import itertools
import glob
import jinja2
import json
import re

from util import jenv, Img, getLogger, guid

log = getLogger(__name__)

imglibs = [ 'imglib', ]

def validate(propname):
	for c in r':<>\!;,*$#':
		if c in propname:
			raise ValueError("Invalid property name '%s'" % propname)

class Token(object):
	sentinel = object()
	@classmethod
	def from_json(cls, dct):
		_type = dct.get("_type", None)
		if _type is not None:
			if _type.lower() != cls.__name__.lower():
				raise ValueError("Wrong json type (%s) passed to class %s" % (_type, cls.__name__))
			ret = cls()
			for k,v in dct.iteritems():
				validate(k)
				setattr(ret, k, v)
			return ret
		return dct

	def __init__(self):
		self._md5 = self.sentinel
		self._img = self.sentinel
		self._guid = self.sentinel
		self._content = self.sentinel
		self.macros = []
		self.layer = 'TOKEN'
		self.name = 'defaultName'
		self.size = 'medium'
		self.assets = {}
		self.hasSight = 'false'
		self.snapToGrid = "true"
		self.snapToScale = "true" # snap to the grid size
		self.x, self.y = 0,0
		self.notes =''

	def __repr__(self):
		return "%s<%s>"%(self.__class__.__name__, self.name)

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
		for prop in object.__getattribute__(self, "props"):
			if prop.name.lower() == attr.lower(): return prop

	@property
	def states(self): raise NotImplementedError

	@property
	def guid(self):
		if self._guid is self.sentinel:
			self._guid = guid()
		return self._guid

	@property
	def type(self): return 'PC'

	@property
	def prop_type(self): return 'PC'

	@property
	def width(self): return self.icon.x

	@property
	def height(self): return self.icon.y

	@property
	def gmNotes(self): return ''

	@property
	def content_xml(self):
		if self._content is self.sentinel:
			self._content = jenv().get_template('token_content.template').render(token=self).encode("utf-8")
		return self._content or ''

	@property
	def properties_xml(self):
		content = jenv().get_template('token_properties.template').render(token=self).encode("utf-8")
		return content or ''

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
			for asset in self.assets.values():
				zipme.writestr('assets/%s' % asset.md5, jenv().get_template('md5.template').render(name=asset.fp, extension='png', md5=asset.md5))
				# zip the img itself
				zipme.writestr('assets/%s.png' % asset.md5, asset.bytes.getvalue())
			# build thumbnails
			zipme.writestr('thumbnail', self.icon.thumbnail(50,50).getvalue())
			zipme.writestr('thumbnail_large', self.icon.thumbnail(500,500).getvalue())

	# used by the heuristic trying to find the appropriate image for a token
	@property
	def matchImg(self): return self.name

	@property
	def icon(self):
		img = self.assets.get("icon", None)
		# try to fetch an appropriate image from the imglib directory
		# using a stupid heuristic: the image / token.name match ratio
		if img is None:
			# compute the diff ratio for the given name compared to the token name
			ratio = lambda name: difflib.SequenceMatcher(None, name.lower(), self.matchImg.lower()).ratio()
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
				log.debug("%s: Best match from the img lib is %s(%s)" % (self.name, bfpath, bratio))
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
				fp = self.icon.fp.replace('.png', '_p.png')
				if os.path.exists(fp):
					portrait = Img(fp)
					self.assets['portrait'] = portrait
		return portrait

	@portrait.setter
	def portrait(self, fp):
		self.assets['portrait'] = Img(fp)

class IToken(Token):
	"""Image token"""
	def __init__(self, *args, **kwargs):
		Token.__init__(self, *args, **kwargs)
		self.snapToGrid = 'false'
		self.snapToScale = 'false'
		self.layer = 'BACKGROUND'
	@property
	def props(self): return []
	@property
	def states(self): return []
	@property
	def type(self): return 'Img'
	@property
	def prop_type(self): return 'Lib'


class Map(IToken): pass

class NPC(Token):
	@property
	def type(self): return 'NPC'
	@property
	def prop_type(self): return 'NPC'
	@property
	def states(self): return []
	@property
	def props(self):
		# XXX there's a glitch, npcs have a struture like skills = {'foo': 50, 'bar':40} whiel pcs have skills= [{'foo':50}, {'bar':40}]
		properties = [TProp(k,v) for k,v in itertools.chain(self.attributes.iteritems(), self.skills.iteritems())]
		properties.extend([TProp(attr, json.dumps(getattr(self, attr))) for attr in ['morph', 'ware', 'weapons']])
		return properties

class Character(Token):
	def __init__(self, *args, **kwargs):
		Token.__init__(self, *args, **kwargs)
		self.hasSight = 'true'
	def __repr__(self): return 'Char<%s, %s, %s>' % (self.name, self.type, self.icon.fp)

	@property
	def props(self):
		return [TProp(*next(attr.iteritems())) for attr in itertools.chain(self.attributes, self.pools, self.skills, [{"morph": self.morph}])]
	@property
	def states(self): return []

class Morph(Character):
	def __repr__(self): return 'Morph<%s, %s, %s>' % (self.name, self.type, self.icon.fp)
	@property
	def matchImg(self): return self.name
	@property
	def type(self): return 'Morph'
	@property
	def props(self): return [TProp(*next(attr.iteritems())) for attr in itertools.chain(self.attributes, self.pools, self.movements)]
	@property
	def prop_type(self): return 'MORPH'


class TProp(object):
	"""Token property"""
	def __init__(self, name, value):
		self.name = name
		self.value = value
		# change props in the form "Know: sports" in to "Know (sport)"
		# because MT does not support : in prop names
		match = re.search(r'(\w+): (.*)', self.name)
		if match is not None:
			self.name = u"%s | %s" % (match.group(1), match.group(2))
			log.debug("Unsupported property name %s, changing it to  %s" % (name, self.name))
		validate(self.name)
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

class LToken(Token):
	"""Library Token."""
	def __init__(self, name, macros, icon):
		Token.__init__(self)
		self.name = name
		self.macros = macros
		self.icon = icon
		self.size = 'huge'
		self.images = []
		self.props = []
	@property
	def states(self): return []
	@property
	def type(self): return 'Lib'

	def addImage(self, name, fp):
		if not os.path.exists(fp): raise ValueError('image %s does not exists')
		if name in self.assets: raise ValueError('Asset %s already exists')
		self.assets[name] = Img(fp)

	def assetId(self, name):
		return "asset://%s" % self.assets[name].md5

	@property
	def prop_type(self): return 'Lib'


