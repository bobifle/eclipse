#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import io
import hashlib
import logging
from PIL import Image

log = logging.getLogger()

_jenv = None

def jenv():
	global _jenv
	if _jenv is None:
		_jenv = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
	return _jenv

class Img(object):
	def __init__(self, fp):
		self.bytes = io.BytesIO()
		self.fp = fp
		img = Image.open(fp)
		self.x, self.y = img.size
		img.save(self.bytes, format='png')
		self._md5 = hashlib.md5(self.bytes.getvalue()).hexdigest()
	@property
	def md5(self): return self._md5

	def thumbnail(self, x,y):
		thumb = io.BytesIO()
		img = Image.open(self.fp)
		img.thumbnail((x,y))
		img.save(thumb, format='png')
		return thumb
