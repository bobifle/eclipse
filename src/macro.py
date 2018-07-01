#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2

from util import jenv

class Macro(object):

	def __init__(self, token, label, tmpl, group, colors):
		self.tmpl = tmpl
		self._label = label
		self.token = token
		self.colors = colors
		self.cattr = ['cognition', 'intuition', 'reflex', 'savvy', 'somatics', 'willpower'] # XXX eclipse specific in lib 
		self.group = group
	
	def __str__(self): return '%s<%s,grp=%s>' % (self.__class__.__name__, self.label, self.group)
	def __repr__(self): return str(self)

	@property
	def command(self): return jenv().get_template(self.tmpl).render(macro=self)

	@property
	def label(self): return self._label

	@property
	def color(self): return self.colors[1]

	@property
	def fontColor(self): return self.colors[0]

class CssMacro(Macro):
	def __init__(self, token, label, fp, group, colors):
		Macro.__init__(self, token, label, '', group, colors)
		self.fp = fp
	@property
	def command(self):
		with open(self.fp, 'r') as css:
			return css.read()

class SheetMacro(Macro):
	def __init__(self, token):
		Macro.__init__(self, token, 'Sheet', None, 'Sheet', ('white', 'blue'))
	@property
	def command(self): return '[macro("Sheet@Lib:ep"): "page=Main; name=%s"]' % self.token.name

