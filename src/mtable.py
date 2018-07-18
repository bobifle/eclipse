#!/usr/bin/env python
# -*- coding: utf-8 -*-
from collections import MutableSequence
import json

from util import jenv, Img, getLogger

log = getLogger(__name__)

class Entry(object):
	def __init__(self, _min, _max, value, imfp):
		self.min = _min
		self.max = _max
		self.value = value
		self.img = Img(imfp) if imfp else None

class Table(MutableSequence):
	def __init__(self, name, imgfp):
		self.name = name
		self.entries = []
		self.img = Img(imgfp)
		self.roll = ''
		self._emap = {}
		self.append(Entry(0,0,"{}", None)) # index 0 is a hash map to quickly access entries by values)

	@property
	def assets(self): return {e.img.fp: e.img for e in self.entries if e.img}

	def render(self):
		return jenv().get_template('table_content.template').render(table=self)

	def __getitem__(self, k): return self.entries[k]
	def __setitem__(self, k, v): self.entries[k] = v
	def __delitem__(self, k): del self.entries[k]
	def __len__(self): return len(self.entries)
	def insert(self, k, v): return self.entries.insert(k,v) # pylint: disable=W0221

	def buildIndex(self):
		self._emap = {}
		for i, entry in enumerate(self[1:]):
			if entry.value in self._emap: raise ValueError('%s already indexed, indexed tables cannot have multiple entries with the same value' %(entry.value))
			self._emap[entry.value] = i+1
		self[0].value = json.dumps(self._emap)


