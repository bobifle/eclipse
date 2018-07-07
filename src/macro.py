#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import jinja2
from util import jenv

class Macro(object):

	def __init__(self, label, tmpl, group, colors, others=None):
		self.tmpl = tmpl
		self._label = label
		self.colors = colors
		self.cattr = ['cognition', 'intuition', 'reflex', 'savvy', 'somatics', 'willpower'] # XXX eclipse specific in lib
		self.group = group
		self.others = others if (others is not None) else {}
		self.allowPlayerEdits = 'false'
		self.autoExecute = 'true'

	def __str__(self): return '%s<%s,grp=%s>' % (self.__class__.__name__, self.label, self.group)
	def __repr__(self): return str(self)

	@property
	def label(self): return self._label

	@property
	def color(self): return self.colors[1]

	@property
	def fontColor(self): return self.colors[0]

class TMacro(Macro):
	"""Template Macro"""
	@property
	def command(self):
		return jenv().get_template(self.tmpl).render(macro=self, **self.others).encode("utf-8")

class SMacro(Macro):
	"""Template Macro"""
	@property
	def command(self):
		#XXX no env available !
		return jinja2.Template(self.tmpl).render(macro=self, **self.others).encode("utf-8")

class LibMacro(TMacro):
	def __init__(self, label, group, colors, data):
		TMacro.__init__(self, label, 'libmacro.template', group, colors)
		self._data = data
	@property
	def data(self): return ((json.dumps(k), json.dumps(v)) for k,v in self._data.iteritems())

class CssMacro(Macro):
	def __init__(self, label, fp, group, colors):
		Macro.__init__(self, label, '', group, colors)
		self.fp = fp
	@property
	def command(self):
		with open(self.fp, 'r') as css:
			return css.read()

