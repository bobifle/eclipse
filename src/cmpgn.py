#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import zipfile
import os
import itertools
import collections

from util import jenv, getLogger
from mtoken import Character

log = getLogger(__name__)

PSet = collections.namedtuple('PSet', ['name', 'props'])

class Campaign(object):
	def __init__(self, name):
		self.name = name
		self.psets = []
		self.zones = []
		self.tables = []

	@property
	def tokens(self): return itertools.chain(*(zone.tokens for zone in self.zones))

	@property
	def chars(self): return (tok for tok in self.tokens if isinstance(tok, Character) and tok.type == 'PC')

	@property
	def assets(self): 
		for elem in  itertools.chain(self.tokens, self.tables):	
			for k,v in elem.assets.iteritems(): yield k,v

	def __repr__(self): return 'Cmpgn<%s,%s prop_sets, %s tokens>' % (self.name, len(self.psets), len(list(self.tokens)))

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
			md5s = [] # record added assets
			for name, asset in self.assets:
				if asset.md5 in md5s: continue # dont zip the same file twice
				log.debug("adding asset %s: %s" % (name, asset))
				md5s.append(asset.md5)
				zipme.writestr('assets/%s' % asset.md5,
					jenv().get_template('md5.template').render(name=os.path.splitext(os.path.basename(asset.fp))[0], extension='png', md5=asset.md5))
				zipme.writestr('assets/%s.png' % asset.md5, asset.bytes.getvalue())

	def build(self, zones, psets, tables):
		"""Build a campaign given the tokens, properties all json data."""
		self.zones.extend(zones)
		self.psets.extend(psets)
		self.tables.extend(tables)
		self.zipme()

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

