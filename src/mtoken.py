#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zipfile
import os
import uuid
import base64
import logging
import difflib
import itertools
import glob
import jinja2

from util import jenv, Img, getLogger

log = getLogger(__name__)

imglibs = [ 'imglib', ]

class Token(object):
	sentinel = object()

	def __init__(self):
		self._md5 = self.sentinel
		self._img = self.sentinel
		self._guid = self.sentinel
		self.name = 'defaultName'
		self.size = 'medium'
		self.assets = {}
		self.hasSight = 'false'
		self.snapToGrid = "true"
		self.snapToScale = "true" # snap to the grid size
		self.x, self.y = 0,0
		self.notes =''

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
	def width(self): return self.icon.x

	@property
	def height(self): return self.icon.y

	@property
	def gmNotes(self): return ''

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

class Map(IToken): pass

class Character(Token):
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

	def __repr__(self): return 'Char<%s, %s, %s>' % (self.name, self.type, self.icon.fp)

	@property
	def props(self): return [TProp(*next(attr.iteritems())) for attr in itertools.chain(self.attributes, self.pools, self.skills)]
	@property
	def states(self): return []
	@property
	def macros(self): return []
	@property
	def layer(self): return 'TOKEN'

class Morph(Character):
	@classmethod
	def from_json(cls, dct):
		ret = cls()
		for k,v in dct.iteritems():
			print k, v
			setattr(ret, k, v)
		return ret
	def __repr__(self): return 'Morph<%s, %s, %s>' % (self.name, self.type, self.icon.fp)
	@property
	def layer(self): return 'TOKEN'
	@property
	def matchImg(self): return self.name
	@property
	def type(self): return 'MORPH'
	@property
	def props(self): return [TProp(*next(attr.iteritems())) for attr in itertools.chain(self.attributes, self.pools, self.movements)]

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
