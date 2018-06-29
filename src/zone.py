#!/usr/bin/env python
# -*- coding: utf-8 -*-

from mtoken import Map
from util import jenv, getLogger, guid

log = getLogger(__name__)

class Zone(object):
	sentinel = object()
	def __init__(self, name):
		self.name = name
		self.tokens = []
		self._guid = self.sentinel

	def __repr__(self): return '%s<%s, %s tokens>' % (self.__class__.__name__, self.name, len(self.tokens))

	@property
	def guid(self):
		if self._guid is self.sentinel: self._guid = guid()
		return self._guid

	@property
	def content_xml(self):
		content = jenv().get_template('zone_content.template').render(zone=self)
		return content or ''

	def render(self): return self.content_xml

	def build(self, tokens):
		"""Build a campaign given the tokens, properties all json data."""
		offsets = {"PC": (100,400), "Lib": (100,200), "Morph": (100,600)}
		for index, tok in enumerate(tokens):
			x,y = offsets[tok.type]
			line = index/20
			col = index%20
			tok.x = x + (col)*50
			tok.y = y + line*100
		main_scene = Map()
		main_scene.name = 'empty_pate_blue'
		main_scene.y = 0
		main_scene.x=0
		self.tokens.append(main_scene)
		self.tokens.extend(tokens)
