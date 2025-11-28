#!/usr/bin/env python
import os, sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'lib'))
import rogue
rogue.cli(['--gui'])
""" Without following line PyDroid will not start it as GUI for some insane reason:
from kivy
"""
