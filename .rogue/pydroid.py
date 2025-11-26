#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
sys.path.append(os.path.join(os.path.dirname(__file__)))
import rogue
rogue.cli(['--gui'])
