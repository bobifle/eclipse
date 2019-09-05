#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import json
import collections
log = logging.getLogger(__name__)

class Data(collections.MutableMapping):
	def __init__(self): self._content = {}
	@property
	def cname(self): return self.__class__.__name__ # class name
	def __repr__(self): return "%s<%s>" % (self.cname, ','.join(self._content.keys()))
	# mutableMapping impl
	def __getitem__(self, k) : return self._content[k]
	def __setitem__(self, k, v) : self._content[k] = v
	def __delitem__(self, k) : del self._content[k]
	def __iter__(self): return iter(self._content)
	def __len__(self): return len(self._content)
	# some python magic to write data.skills instead of data['skills']
	def __getattr__(self, name):
		if name in self: return self[name]
		raise AttributeError('%s has no attribute "%s"' % (self.cname, name))

content = Data()

def get_data():
	global content
	jfiles = {}
	for root, dirs, files in os.walk('data'):
		for f in (f for f in files if f.endswith('.json')):
			obj = os.path.splitext(f)[0].lower()
			if obj in jfiles: log.warning('duplicate json file %s' % obj)
			with open(os.path.join(root, f), 'r') as _file:
				content[obj] = json.load(_file)
	return content

content = get_data()

