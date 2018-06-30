#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2

from util import jenv

class Macro(object):

	def __init__(self, token, action, label, tmpl):
		self.tmpl = tmpl
		self._label = label
		self.token = token
		self.action = action
	
	def __str__(self): return '%s<%s,grp=%s>' % (self.__class__.__name__, self.label, self.group)
	def __repr__(self): return str(self)

	@property
	def command(self): return jenv().get_template(self.tmpl).render(macro=self)

	@property
	def label(self): return self._label

	@property
	def group(self): return 'unknown' 

	@property
	def color(self): return {'Health' : 'green', 'Action': 'black'}.get(self.group, 'black')

	@property
	def fontColor(self): return 'white'

class SheetMacro(Macro):
	def __init__(self, token):
		Macro.__init__(self, token, None, 'Sheet', 'token_sheet.template')
		self.cattr = ['cognition', 'intuition', 'reflex', 'savvy', 'somatics', 'willpower']

	@property
	def group(self): return 'Sheet'
	@property
	def color(self): return 'blue'
	@property
	def fontColor(self): return 'white'
