#!/usr/bin/python

import time
from telnetlib import Telnet

t = Telnet()
t.open("192.168.59.103", 8649)

data = t.read_all()

t.close()

print data
