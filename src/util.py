#!/usr/bin/env python
# -*- coding: utf-8 -*-
import jinja2
import io
import os
import hashlib
import optparse
import base64
import uuid
import csv
import codecs
import cStringIO
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
def getLogger(name):
	return logging.getLogger(lName+'.'+name if lName != name else lName)
# the util sublogger
log = getLogger(__name__)

def configureLogger(verbose):
	"""Configure the loggers, do not call twice."""
	formatter = logging.Formatter('%(name)s : %(levelname)s : %(message)s')
	# logging to the stream, use the colored version if available
	try:
		coloredlogs.DEFAULT_FIELD_STYLES['levelname'] = {'color': 'white'}
		coloredlogs.install(level=logging.DEBUG, fmt='%(name)s %(levelname)8s %(message)s', logger=mLog)
		mLog.handlers[-1].setLevel(logging.WARNING-verbose*10)
	except NameError:
		ch = logging.StreamHandler()
		ch.setLevel(logging.WARNING-verbose*10)
		ch.setFormatter(formatter)
		mLog.addHandler(ch)

	mLog.setLevel(logging.DEBUG) # don't filter anythig let the handlers to the filtering
	fh = logging.FileHandler(os.path.join('build', mLog.name+'.log'), mode="w") # mode w will erase previous logs
	fh.setLevel(logging.DEBUG)
	# create formatter and add it to the handlers
	fh.setFormatter(formatter)
	mLog.addHandler(fh)

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

	def __repr__(self): return "Img<%s,%s>" % (os.path.basename(self.fp), self.md5)

	@property
	def md5(self): return self._md5

	def thumbnail(self, x,y):
		thumb = io.BytesIO()
		img = Image.open(self.fp)
		img.thumbnail((x,y))
		img.save(thumb, format='png')
		return thumb

def guid():
	"""Return a serialized GUID, it's an uuid4 encoded in base64."""
	return base64.b64encode(uuid.uuid4().bytes)

class UTF8Recoder(object):
	"""
	Iterator that reads an encoded stream and reencodes the input to UTF-8
	"""
	def __init__(self, f, encoding):
		self.reader = codecs.getreader(encoding)(f)

	def __iter__(self): return self

	def next(self):
		return self.reader.next().encode("utf-8")

class UnicodeReader(object):
	"""
	A CSV reader which will iterate over lines in the CSV file "f",
	which is encoded in the given encoding.
	"""

	def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
		f = UTF8Recoder(f, encoding)
		self.reader = csv.DictReader(f, dialect=dialect, **kwds)

	def next(self):
		row = self.reader.next()
		return {unicode(k, "utf-8"):unicode(v, "utf-8") for k,v in row.iteritems()}

	def __iter__(self): return self
