#!/usr/bin/env python2
import sys

import pyborg

borg = pyborg.pyborg()

# ##########################################
# change learning in pyborg.cfg
# ##########################################

for line in open(sys.argv[1], "r"):
    if line != '' and line != '\n':
        borg.learn(pyborg.filter_message(line, borg))

borg.save_all()
