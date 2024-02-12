import contextlib
from ..fs import SerializedEntity

@contextlib.contextmanager
def stored_entity(path, name, default_constructor):
	savefile = SerializedEntity(path, 0, entity_name=name, unlink=False, readable=True)
	savefile.load()
	if savefile.entity:
		entity = savefile.entity
	else:
		entity = default_constructor()
		savefile.reset(entity)
	yield entity
	savefile.save()
