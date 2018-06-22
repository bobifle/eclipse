#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import json
import io
import hashlib
import zipfile
import os
import logging
import difflib
import itertools
from PIL import Image
import glob

log = logging.getLogger()

data='''
{"name" : "Bob", "attributes": {"som":5, "ref": 1}}
'''

imglibs = [ 'imglib', ]

md5Template = '''<net.rptools.maptool.model.Asset>
  <id>
	<id>{{md5}}</id>
  </id>
  <name>{{name}}</name>
  <extension>{{extension}}</extension>
  <image/>
</net.rptools.maptool.model.Asset>'''

_jenv = None

def jenv():
	global _jenv
	if _jenv is None:
		_jenv = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
	return _jenv


class Campaign(object):

	@property
	def name(self): return 'dft'

	@property
	def content_xml(self):
		content = jenv().get_template('cmpgn_content.template').render(cmpgn=self)
		return content or ''

	@property
	def properties_xml(self):
		content = jenv().get_template('cmpgn_properties.template').render(cmpgn=self)
		return content or ''

	def zipme(self):
		"""Zip the token into a rptok file."""
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.cmpgn'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml.encode('utf-8'))
			zipme.writestr('properties.xml', self.properties_xml)


class Prop(object):
	def __init__(self, name, value):
		self.name = name
		self.value = value
	def __repr__(self): return '%s<%s,%s>' % (self.__class__.__name__, self.name, self.value)
	def render(self):
		return jinja2.Template('''      <entry>
	    <string>{{prop.name.lower()}}</string>
	    <net.rptools.CaseInsensitiveHashMap_-KeyValue>
	      <key>{{prop.name}}</key>
	      <value class="string">{{prop.value}}</value>
	      <outer-class reference="../../../.."/>
	    </net.rptools.CaseInsensitiveHashMap_-KeyValue>
	  </entry>''').render(prop=self)

class Token(object):
	sentinel = object()

	def __init__(self):
		self._md5 = self.sentinel
		self._img = self.sentinel
		self.name = 'defaultName'
		self.size = 'medium'

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
	def macros(self): raise NotImplementedError

	@property
	def props(self): raise NotImplementedError

	@property
	def states(self): raise NotImplementedError

	@property
	def guid(self):	return ''

	@property
	def content_xml(self):
		with open(os.path.join('src','content.template')) as template:
			t = jinja2.Template(template.read())
		content = t.render(token=self)
		return content or ''

	@property
	def properties_xml(self):
		with open(os.path.join('src', 'properties.template')) as template:
			 t = jinja2.Template(template.read())
			 return t.render()

	@property
	def md5(self):
		if self._md5 is self.sentinel: # cache this expensive property
			out = io.BytesIO()
			self.img.save(out, format='png')
			self._md5 = hashlib.md5(out.getvalue()).hexdigest()
		return self._md5

	def zipme(self):
		"""Zip the token into a rptok file."""
		if not os.path.exists('build'): os.makedirs('build')
		with zipfile.ZipFile(os.path.join('build', '%s.rptok'%self.name), 'w') as zipme:
			zipme.writestr('content.xml', self.content_xml.encode('utf-8'))
			zipme.writestr('properties.xml', self.properties_xml)
			log.debug('Token image md5 %s' % self.md5)
			# default image for the token, right now it's a brown bear
			# zip the xml file named with the md5 containing the asset properties
			zipme.writestr('assets/%s' % self.md5, jinja2.Template(md5Template).render(name=self.name, extension='png', md5=self.md5))
			# zip the img itself
			out = io.BytesIO() ; self.img.save(out, format='PNG')
			zipme.writestr('assets/%s.png' % self.md5, out.getvalue())
			# build thumbnails
			out = io.BytesIO()
			im = self.img.copy() ; im.thumbnail((50,50)) ; im.save(out, format='PNG')
			zipme.writestr('thumbnail', out.getvalue())
			out = io.BytesIO()
			im = self.img.copy() ; im.thumbnail((500,500)) ; im.save(out, format='PNG')
			zipme.writestr('thumbnail_large', out.getvalue())

	@property
	def img(self):
		# try to fetch an appropriate image from the imglib directory
		# using a stupid heuristic: the image / token.name match ratio
		if self._img is self.sentinel: # cache to property
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
				self._img = Image.open(bfpath, 'r')
			else:
				self._img = Image.open(os.path.join('imglib', 'dft.png'), 'r')
		return self._img

class Character(Token):
	"Eclipse Character"

	@classmethod
	def from_json(cls, dct):
		if "name" in dct and "attributes" in dct:
			ret = cls()
			for k,v in dct.iteritems(): setattr(ret, k, v)
			return ret
		return dct

	def __repr__(self): return 'Char<%s>' % self.name

	@property
	def props(self): return [Prop('som', self.attributes['som'])]

	@property
	def states(self): return []

	@property
	def macros(self): return []

if __name__== '__main__':
	logging.basicConfig(level=logging.INFO)
	x = json.loads(data, object_hook = Character.from_json)
	x.zipme()
	Campaign().zipme()
