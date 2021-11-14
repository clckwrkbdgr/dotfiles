import os, sys
import six

def choice(items, prompt=None): # pragma: no cover -- TODO
	item_keys = {}
	menu = []
	for index, item in enumerate(items):
		if isinstance(item, six.string_types):
			item_keys[index] = item
			menu.append((index,))
		else:
			key, item = item
			item_keys[key] = item
			item_keys[index] = item
			menu.append((index, key))
	while True:
		for keys in menu:
			print('{0}: {1}'.format(','.join(map(str, keys)), item_keys[keys[0]]))
		value = six.moves.input((prompt or '?') + ' ')
		if not value:
			break
		if value in item_keys:
			return value
		try:
			if int(value) in item_keys:
				return value
		except:
			pass

	return None
