import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
try:
	from cStringIO import StringIO
except: # pragma: no cover
	from io import StringIO
from clckwrkbdgr.math import Point
from .. import monsters
from ..engine import items
from clckwrkbdgr.pcg import RNG
import clckwrkbdgr.serialize.stream as savefile
from ..defs import Version
from . import mock_dungeon
from ..engine import actors
