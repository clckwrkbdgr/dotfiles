from clckwrkbdgr.collections import DocstringEnum as Enum

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
	GRAB
	CONSUME
	DROP
	WIELD
	UNWIELD
	AUTOSTOP
	"""

class UI(object):
	""" Base interface for UI.
	Should be used as a context manager:
	>>> with UI():
	>>>    ...
	"""
	def __enter__(self): # pragma: no cover
		""" Should perform initialization of UI engine. """
		return self
	def __exit__(self, *targs): # pragma: no cover
		""" Should perform finalization of UI engine. """
		pass
	def redraw(self): # pragma: no cover
		""" Should update current display with changes (or redraw completely). """
		raise NotImplementedError()
	def user_action(self): # pragma: no cover
		""" Accepts user interaction from actual interface.

		Should return tuple (Action, <action payload (depends on action)>).
		"""
		raise NotImplementedError()

def auto_ui(): # pragma: no cover -- TODO need to have more than one variant.
	""" Auto-guesses available implementation for the current platform. """
	from . import curses
	return curses.Curses
