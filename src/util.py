#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import io
import hashlib
import optparse
from PIL import Image
try:
	import coloredlogs # optional
except ImportError: pass
import logging

# the jinja environment
_jenv = None

# Name of the main logger
lName = 'mtools'
# the main logger
mLog = logging.getLogger(lName)
def getLogger(name): return logging.getLogger(lName+'.'+name)
# the util sublogger
log = getLogger(__name__)

def configureLogger(verbose):
	"""Configure the loggers, do not call twice."""
	coloredlogs.DEFAULT_FIELD_STYLES['levelname'] = {'color': 'white'}
	try:
		#coloredlogs.install(level=logging.INFO-verbose*10, fmt='%(name)s %(levelname)8s %(message)s', logger=mLog)
		coloredlogs.install(level=logging.INFO-verbose*10, fmt='%(name)s %(levelname)8s %(message)s', logger=mLog)
	except NameError:
		logging.getLogger(lName.setLevel(level=logging.INFO-verbose*10))

def parse_args():
	parser = optparse.OptionParser()
	parser.add_option('-v', '--verbose', dest='verbose', action='count', default=0,
			help='increase the logging level')
	return parser.parse_args()

def jenv():
	"""Return a jinja environment."""
	global _jenv
	if _jenv is None:
		_jenv = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))
	return _jenv

class Img(object):
	"""A PIL.Image higher layer for MT assets."""
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
