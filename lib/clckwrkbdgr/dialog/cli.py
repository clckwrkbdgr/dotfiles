import os, sys
import six
from . import _base

def choice(items, prompt=None): # pragma: no cover -- TODO
	items = _base.make_choices(items)
	item_keys = _base.get_choices_map(items)

	menu = []
	for item in items:
		if item.key:
			menu.append((item.index, item.key))
		else:
			menu.append((item.index,))

	while True:
		for keys in menu:
			print('{0}: {1}'.format(','.join(map(str, keys)), item_keys[keys[0]]))
		key = six.moves.input((prompt or '?') + ' ')
		if not key:
			break
		result = _base.find_choice_in_map(item_keys, key)
		if result:
			return result
	return None
