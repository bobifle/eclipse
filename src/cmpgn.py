#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import zipfile
import os
import json
import itertools

from util import jenv, getLogger
from mtoken import Character

log = getLogger(__name__)

class Campaign(object):
	def __init__(self, name):
		self.name = name
		self.props = []
		self.zones = []

	@property
	def tokens(self): return itertools.chain(*(zone.tokens for zone in self.zones))

	@property
	def chars(self): return (tok for tok in self.tokens if isinstance(tok, Character) and tok.type == 'PC')

	def __repr__(self): return 'Cmpgn<%s,%s props, %s tokens>' % (self.name, len(self.props), len(list(self.tokens)))

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
					zipme.writestr('assets/%s' % asset.md5,
							jenv().get_template('md5.template').render(name=os.path.splitext(os.path.basename(asset.fp))[0], extension='png', md5=asset.md5))
					zipme.writestr('assets/%s.png' % asset.md5, asset.bytes.getvalue())

	def build(self, zones, cprops):
		"""Build a campaign given the tokens, properties all json data."""
		self.zones.extend(zones)
		# use the first character properties, and add these as campaign properties as well
		self.props.extend([CProp.fromTProp(p) for p in next(self.chars).props])
		self.props.extend([CProp(p['name'], p['showOnSheet'], p['value']) for p in json.loads(cprops)])
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
