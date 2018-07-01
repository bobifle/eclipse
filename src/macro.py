#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2

from util import jenv

class Macro(object):

	def __init__(self, token, label, tmpl):
		self.tmpl = tmpl
		self._label = label
		self.token = token
		self.colors = ('black', 'white')
	
	def __str__(self): return '%s<%s,grp=%s>' % (self.__class__.__name__, self.label, self.group)
	def __repr__(self): return str(self)

	@property
	def command(self): return jenv().get_template(self.tmpl).render(macro=self)

	@property
	def label(self): return self._label

	@property
	def group(self): return 'unknown' 

	@property
	def color(self): return self.colors[1]

	@property
	def fontColor(self): return self.colors[0]

class CssMacro(Macro):
	def __init__(self, token, label, fp):
		Macro.__init__(self, token, label, '')
		self.fp = fp
	@property
	def command(self):
		with open(self.fp, 'r') as css:
			return css.read()
	@property
	def group(self): return 'css' 

class SheetMacro(Macro):
	def __init__(self, token):
		Macro.__init__(self, token, 'Sheet', 'token_sheet.template')
		self.cattr = ['cognition', 'intuition', 'reflex', 'savvy', 'somatics', 'willpower']
		self.colors = ('white', 'blue')
	@property
	def group(self): return 'Sheet'
