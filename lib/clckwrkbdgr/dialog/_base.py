from collections import namedtuple
import six

Choice = namedtuple('Choice', 'index key text')

def make_choices(items):
	""" Converts list of given items to list of Choice objects.
	Item may be either string or tuple (key, text).
	Item text and keys should be all strings or str-able objects.
	"""
	result = []
	for index, item in enumerate(items):
		if isinstance(item, six.string_types):
			result.append(Choice(index, None, str(item)))
		else:
			key, item = item
			result.append(Choice(index, str(key), str(item)))
	return result

def get_choices_map(choices):
	""" Returns dict where every index and key are mapped to objects:
	map[index] = map[key] = Choice(...)
	"""
	result = {}
	for choice in choices:
		result[choice.index] = choice
		if choice.key:
			result[choice.key] = choice
	return result

def find_choice_in_map(choice_map, key):
	if key in choice_map:
		return choice_map[key]
	try:
		if int(key) in choice_map:
			return choice_map[int(key)]
	except:
		pass
	return None
