from clckwrkbdgr.utils import classfield
from . import entity

class Terrain(entity.Entity):
	_metainfo_key = 'Terrain'
	passable = classfield('_passable', True) # allow free movement.
	remembered = classfield('_remembered', None) # sprite for "remembered" state, where it is not seen directly, but was visited before. By default is the same as the main sprite.
	allow_diagonal = classfield('_allow_diagonal', True) # allows diagonal movement to and from this cell. Otherwise only orthogonal movement is allowed.
	dark = classfield('_dark', False) # if True, no light is present and it is not considered transparent if further than 1 cell from the center.
