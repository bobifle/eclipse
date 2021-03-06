#!/usr/bin/env python
# -*- coding: utf-8 -*-
import zipfile
import os
import difflib
import itertools
import glob
import jinja2
import re
import collections

from util import jenv, Img, getLogger, guid
from data import content

skills = content['skills']

log = getLogger(__name__)

imglibs = [ 'imglib', ]

def validate(propname):
	for c in r':<>\!;,*$#':
		if c in propname:
			raise ValueError("Invalid property name '%s'" % propname)

class SK(object):
	"""Helper for performing skill check"""
	def __init__(self, tok):
		self.tok = tok
	def base_score(self, skill):
		# compute the base score of a skill check, see STEP 6 of char creation
		sk = skills[skill]
		base_score = getattr(self.tok, sk['aptitude'].lower()).value
		# for fray and perceive, the we use apt x 2
		if skill in ['fray', 'perceive']: base_score += base_score
		return base_score
	def __getattr__(self, name):
		name = name.lower()
		# defaulting, page 31
		base = self.base_score(name)
		# if the token has the skill add it to the base score
		bonus =  getattr(self.tok, name).value if hasattr(self.tok, name) else 0
		# TODO: support
		return {'skill' : name, 'value' : min(base+bonus, 80), 'base' : base, 'bonus': bonus, 'can_crit': bool(bonus)}

class Proxy(collections.MutableMapping):
	def __init__(self, owner, content):
		object.__setattr__(self, 'content', content)
		object.__setattr__(self, 'owner', owner)
	def __getattr__(self, name):
		if name in self.content: return self.content[name]
		raise AttributeError('%s has not property "%s"' % (self.owner.__class__.__name__, name))
	def __setattr__(self, name, v): self.content[name] = v
	def __repr__(self): return "<%s %s>" % (self.__class__.__name__, self.content)
	# Mutablemapping interface
	def __iter__(self): return iter(self.content)
	def __getitem__(self, k): return self.content[k]
	def __setitem__(self, k, v): self.content[k] = v
	def __delitem__(self, k): del self.content[k]
	def __len__(self): return len(self.content)

class PropProxy(Proxy):
	subcategories = ["aptitudes", "skills", "pools"]
	@property
	def subs(self):
		return  [getattr(self, cat) for cat in PropProxy.subcategories if cat in self.content]
	def __init__(self, owner, content):
		if not isinstance(content, collections.MutableMapping): raise TypeError("Expecting a dict, bad Property content %s" % content)
		Proxy.__init__(self, owner, content)
		for sub in self.subcategories:
			content = self.content.get(sub, None)
			if content is not None:
				object.__setattr__(self, "_%s"%sub, content)
				object.__setattr__(self, sub, Proxy(self, getattr(self, "_%s"%sub)))
	def __getattr__(self, name):
		try:
			return Proxy.__getattr__(self, name)
		except AttributeError:
			# when a property is not found, look into the available subcategories
			for sub in self.subs:
				if hasattr(sub, name): return getattr(sub, name)
			raise

	def __setattr__(self, name, v):
		sub = next(iter([sub for sub in self.subs if name in sub]), None)
		if name not in self.content and sub:
			setattr(sub, name, v)
		Proxy.__setattr__(self, name, v)
	@property
	def flatten(self):
		flat = {}
		flat.update(**{k:v for k,v in self.iteritems() if k not in PropProxy.subcategories})
		for sub in self.subs:
			flat.update(**{k:v for k,v in sub.iteritems()})
		return flat

class Token(object):
	sentinel = object()
	@classmethod
	def from_json(cls, dct):
		ret = cls()
		for k,v in dct.iteritems():
			validate(k)
			setattr(ret, k, v)
		return ret
	def from_maptool_json(cls, dct):
		_type = dct.get("_type", None)
		if _type is not None:
			if _type.lower() != cls.__name__.lower():
				raise ValueError("Wrong json type (%s) passed to class %s" % (_type, cls.__name__))
			ret = cls()
			ret.attributes, ret.pools, ret.skills = {}, {}, {}
			for k,v in dct.iteritems():
				validate(k)
				setattr(ret, k, v)
			return ret
		return dct

	def to_dict(self):
		d = dict(self.__dict__)
		# XXX uncaching _guid could bring problems ???
		for cache in ['_md5', '_img', '_content', '_guid']:
			d.pop(cache)
		d.pop('assets')
		d['macros'] = [m.to_dict() for m in d['macros']]
		return d

	def __init__(self):
		self._md5 = self.sentinel
		self._img = self.sentinel
		self._guid = self.sentinel
		self._content = self.sentinel
		self._props = {}
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

	@property
	def key(self): return self.name.lower()
	def __eq__(self, o): return self.key == o.key
	def __ne__(self, o): return not self == o
	def __hash__(self): return hash(self.key)

	def update(self, other):
		if self != other:
			log.error("Cannot update a token with a different token %s != %s" % (self, other))
			return
		for k in other.to_dict():  # iterate only over serializable/json attributes
			old = getattr(self, k)
			new = getattr(other, k)
			if new != old:
				log.debug("Updating property %s from %s to %s" % (k, getattr(self, k), new))
				setattr(self, k, new)

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

	@property
	def states(self): raise NotImplementedError

	@property
	def props(self): return PropProxy(self, self._props)

	@property
	def token_props(self): return [TProp(k,v) for k,v in self.props.flatten.iteritems()]

	@property
	def guid(self):
		if self._guid is self.sentinel:
			self._guid = guid()
		return self._guid

	@property
	def token_type(self): return 'PC'

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
			self._content = jenv().get_template('token_content.template').render(token=self)
		return self._content or ''

	@property
	def properties_xml(self):
		return jenv().get_template('token_properties.template').render(token=self) or u''

	@property
	def skill_check(self): return SK(self)

	def render(self): return self.content_xml

	def zipme(self):
		"""Zip the token into a rptok file."""
		log.info("Zipping %s" % self)
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.rptok'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml)
			zipme.writestr('properties.xml', self.properties_xml)
			# default image for the token, right now it's a brown bear
			# zip the xml file named with the md5 containing the asset properties
			for asset in self.assets.values():
				zipme.writestr('assets/%s' % asset.md5, jenv().get_template('md5.template').render(name=asset.fp, extension='png', md5=asset.md5))
				# zip the img itself
				zipme.writestr('assets/%s.png' % asset.md5, asset.bytes)
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
	def states(self): return []
	@property
	def token_type(self): return 'Img'
	@property
	def prop_type(self): return 'Lib'


class Map(IToken): pass

class NPC(Token):
	@property
	def token_type(self): return 'NPC'
	@property
	def prop_type(self): return 'NPC'
	@property
	def states(self): return []

class Character(Token):
	def __init__(self, *args, **kwargs):
		Token.__init__(self, *args, **kwargs)
		self.hasSight = 'true'
	def __repr__(self): return 'Char<%s, %s, %s>' % (self.name, self.token_type, self.icon.fp)
	@property
	def states(self): return []

class Morph(Character):
	def __repr__(self): return 'Morph<%s, %s, %s>' % (self.name, self.token_type, self.icon.fp)
	@property
	def matchImg(self): return self.name
	@property
	def token_type(self): return 'Morph'
	@property
	def prop_type(self): return 'MORPH'


class TProp(object):
	"""Token property"""
	# the template is the same for all instance, it's expensive to create
	# so a class attribute is a good option
	template = jinja2.Template('''      <entry>
	    <string>{{prop.name.lower()}}</string>
	    <net.rptools.CaseInsensitiveHashMap_-KeyValue>
	      <key>{{prop.name}}</key>
	      <value class="string">{{prop.value}}</value>
	      <outer-class reference="../../../.."/>
	    </net.rptools.CaseInsensitiveHashMap_-KeyValue>
	  </entry>''')
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
	def key(self): return self.name.lower(), self.value
	def __hash__(self) : return hash(self.key)
	def __eq__(self, other) : return self.key == other.key
	def __ne__(self, other) : return self.key != other.key

	@property
	def shortname(self): return self.name[:3].upper()

	def render(self):
		return self.template.render(prop=self)

class LToken(Token):
	"""Library Token."""
	def __init__(self, name, macros, icon):
		Token.__init__(self)
		self.name = name
		self.macros = macros
		self.icon = icon
		self.size = 'huge'
		self.images = []
	@property
	def states(self): return []
	@property
	def token_type(self): return 'Lib'

	def addImage(self, name, fp):
		if not os.path.exists(fp): raise ValueError('image %s does not exists')
		if name in self.assets: raise ValueError('Asset %s already exists')
		self.assets[name] = Img(fp)

	def assetId(self, name):
		return "asset://%s" % self.assets[name].md5

	@property
	def prop_type(self): return 'Lib'


