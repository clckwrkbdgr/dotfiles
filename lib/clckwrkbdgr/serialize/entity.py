import os
import contextlib
try:
	from pathlib2 import Path
except ImportError: # pragma: no cover
	from pathlib import Path
try:
	import jsonpickle
except: # pragma: no cover
	jsonpickle = None

class SerializedEntity: # pragma: no cover -- TODO requires functional tests.
	def __init__(self, filename, current_version, entity_name='data', unlink=False, readable=False):
		self.filename = Path(filename)
		self.version = current_version
		self.entity_name = entity_name
		self.unlink = unlink
		self.readable = readable
		self.entity = None
	def load(self):
		if not self.filename.exists():
			return None
		data = self.filename.read_text()
		savedata = jsonpickle.decode(data, keys=True)
		if savedata['version'] > self.version:
			raise RuntimeError("Stored data version {0} is newer than currently supported {1}".format(savedata['version'], self.version))
		self.entity = savedata[self.entity_name]
		if self.unlink:
			os.unlink(str(self.filename))
		return self.entity
	def reset(self, new_value=None):
		self.entity = new_value
	def save(self, entity=None):
		if entity is None:
			entity = self.entity
		if entity is None:
			return
		savedata = {'version':self.version, self.entity_name:entity}
		if self.readable:
			data = jsonpickle.encode(savedata, indent=2, keys=True)
		else:
			data = jsonpickle.encode(savedata, keys=True)
		self.filename.write_bytes(data.encode('utf-8', 'replace'))
	def __enter__(self):
		self.load()
		return self
	def __exit__(self, *args, **kwargs):
		self.save()
	@classmethod
	@contextlib.contextmanager
	def store(cls, path, name, default_constructor):
		""" Context manager for serialized entity store in a file.
		Tries to load entity with given name from the specified path,
		otherwise creates new entity with provided callable default_constructor.
		On exit saves entity to the file.
		"""
		savefile = cls(path, 0, entity_name=name, unlink=False, readable=True)
		savefile.load()
		if savefile.entity:
			entity = savefile.entity
		else:
			entity = default_constructor()
			savefile.reset(entity)
		yield entity
		savefile.save()
