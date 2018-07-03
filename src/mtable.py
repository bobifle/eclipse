#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import MutableSequence

from util import jenv, Img, getLogger

log = getLogger(__name__)

class Entry(object):
	def __init__(self, _min, _max, value, imfp):
		self.min = _min
		self.max = _max
		self.value = value
		self.img = Img(imfp)

class Table(MutableSequence):
	def __init__(self, name, imgfp):
		self.name = name
		self.entries = []
		self.img = Img(imgfp)
		self.roll = ''

	@property
	def assets(self): return {e.img.fp: e.img for e in self.entries}

	def render(self):
		return jenv().get_template('table_content.template').render(table=self)

	def __getitem__(self, k): return self.entries[k]
	def __setitem__(self, k, v): self.entries[k] = v
	def __delitem__(self, k): del self.entries[k]
	def __len__(self): return len(self.entries)
	def insert(self, k, v): return self.entries.insert(k,v)
