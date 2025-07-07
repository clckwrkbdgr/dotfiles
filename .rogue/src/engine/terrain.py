from clckwrkbdgr.utils import classfield

class Terrain(object):
	sprite = classfield('_sprite', ' ')
	name = classfield('_name', 'void')
	passable = classfield('_passable', True) # allow free movement.
	remembered = classfield('_remembered', None) # sprite for "remembered" state, where it is not seen directly, but was visited before.
	allow_diagonal = classfield('_allow_diagonal', True) # allows diagonal movement to and from this cell. Otherwise only orthogonal movement is allowed.
	dark = classfield('_dark', False) # if True, no light is present and it is not considered transparent if further than 1 cell from the center.
