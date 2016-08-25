#!/usr/bin/python

import os
import sys
from P4 import P4
from pprint import pprint 

p4 = P4()

p4.port = 'aplp4:2001'
p4.user = 'rakhee.k'
p4.client = 'rakhee.k_ws_escher'

try:
    p4.connect()
    p4_changes = p4.run(changes)
    p4.disconnect()
except P4Exception:
    for e in p4.errors:
        print e
pprint(p4_changes)
	
