#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import os
import json
log = logging.getLogger(__name__)

def json_files():
	jfiles = {}
	for root, dirs, files in os.walk('data'):
		for f in (f for f in files if f.endswith('.json')):
			obj = os.path.splitext(f)[0].lower()
			if obj in jfiles: log.warning('duplicate json file %s' % obj)
			with open(os.path.join(root, f), 'r') as _file:
				jfiles[obj] = json.load(_file)
	return jfiles

content = json_files()

skills = content['skills']

