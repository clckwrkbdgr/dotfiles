from ..utils import Enum

class Action(Enum):
	""" NONE
	EXIT
	SUICIDE
	WALK_TO
	AUTOEXPLORE
	GOD_TOGGLE_VISION
	GOD_TOGGLE_NOCLIP
	DESCEND
	MOVE
	WAIT
	"""

class UI(object):
	def __enter__(self): # pragma: no cover
		return self
	def __exit__(self, *targs): # pragma: no cover
		pass
	def redraw(self, game): # pragma: no cover
		raise NotImplementedError()
	def user_interrupted(self): # pragma: no cover
		raise NotImplementedError()
	def user_action(self, game): # pragma: no cover
		raise NotImplementedError()

def auto_ui(): # pragma: no cover -- TODO need to have more than one variant.
	from . import curses
	return curses.Curses
