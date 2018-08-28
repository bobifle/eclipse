#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import jinja2
import re
from util import jenv, getLogger

log = getLogger(__name__)

cachedMacro = {}

class Macro(object):
	sentinel = object()

	def __init__(self, label, tmpl, group, colors, others=None):
		self.tmpl = tmpl
		self._template = self.sentinel
		self._label = label
		self.colors = colors
		self.cattr = ['cognition', 'intuition', 'reflex', 'savvy', 'somatics', 'willpower'] # XXX eclipse specific in lib
		self.group = group
		self.others = others if (others is not None) else {}
		self.allowPlayerEdits = 'false'
		self.autoExecute = 'true'
		self._command = self.sentinel

	def __str__(self): return '%s<%s,grp=%s>' % (self.__class__.__name__, self.label, self.group)
	def __repr__(self): return str(self)

	def to_dict(self): return dict(self.__dict__)

	@property
	def label(self): return self._label

	@property
	def color(self): return self.colors[1]

	@property
	def fontColor(self): return self.colors[0]

	@property
	def roll_options(self):
		# search roll options that looks like "[r:" or "[r,
		roptions= set([e.lower() for e in re.findall(r'\[\s*(\w)\s*[:,]', self.command)])
		log.debug("%s roll options: %s" % (self, roptions))
		return roptions

	@property
	def discardOutput(self):
		"""True if the macro output should be discarded when calling the macro as UDF."""
		# search for all roll options, if any is not the roll option h, do not discard the output
		discard = int(not bool(self.roll_options - set(['h'])))
		log.debug("%s discard output : %s" % (self, discard))
		return discard

	@property
	def template(self): raise NotImplementedError()

	@property
	def cachable(self): return False

	@property
	def command(self):
		if self.label in cachedMacro:
			log.debug("Using cached macro %s" % self)
			return cachedMacro[self.label]
		if self._command is self.sentinel:
			self._command = self.template.render(macro=self, **self.others).encode("utf-8")
			if self.cachable:
				cachedMacro[self.label] = self._command
				log.debug("Adding macro %s to the cache" % self)
			log.debug("%s:\n%s", self, self._command)
		return self._command

class TMacro(Macro):
	"""Template Macro"""
	@property
	def template(self):
		if self._template is self.sentinel:
			self._template = jenv().get_template(self.tmpl)
		return self._template
class SMacro(Macro):
	"""String Macro"""
	@property
	def template(self):
		if self._template is self.sentinel:
			self._template = jinja2.Template(self.tmpl)
		return self._template
	@property
	def cachable(self): return not (('{{' in self.tmpl) or '{%' in self.tmpl)

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

	@property
	def template(self): raise NotImplementedError()


