import os, sys, subprocess
try:
	import tkinter
except: # pragma: no cover
	tkinter = None
import six
import clckwrkbdgr.pkg
from . import _base

def message(text): # pragma: no cover -- TODO
	root = tkinter.Tk()
	tkinter.Label(root, text=text).pack()
	tkinter.Button(text='Ok', command=root.destroy).pack()
	root.attributes('-topmost', True)
	root.mainloop()
	return True

def choice(items, prompt=None): # pragma: no cover -- TODO
	if clckwrkbdgr.pkg.is_app_installed('zenity'):
		actual = zenity_choice
	else:
		actual = tkinter_choice
	return actual(items, prompt=prompt)

def tkinter_choice(items, prompt=None): # pragma: no cover -- TODO
	items = _base.make_choices(items)
	item_keys = _base.get_choices_map(items)
	root = tkinter.Tk()
	tkinter.Label(root, text=prompt).pack()
	key = tkinter.StringVar()
	for item in items:
		tkinter.Radiobutton(root, text=item.text, variable=key, value=item.key or str(item.index)).pack(anchor='w')
	key.set(None)
	tkinter.Button(text='Ok', command=root.destroy).pack()
	root.attributes('-topmost', True)
	root.mainloop()
	if not key.get():
		return None
	result = _base.find_choice_in_map(item_keys, key.get())
	return result

def zenity_choice(items, prompt=None): # pragma: no cover -- TODO
	items = _base.make_choices(items)
	item_keys = _base.get_choices_map(items)

	menu = []
	for item in items:
		if item.key:
			menu.extend((item.key, item.text))
		else:
			menu.extend((item.index, item.text))

	zenity = subprocess.Popen(['zenity', '--list', '--text', str(prompt or ''), '--column', 'key', '--column', 'value', '--print-column', '1', '--hide-column', '1', '--hide-header'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
	choice, _ = zenity.communicate('\n'.join(map(str, menu)).encode('utf-8', 'replace'))
	zenity.wait()

	if not choice:
		return None
	key = choice.decode('utf-8', 'replace').rstrip('\n')
	result = _base.find_choice_in_map(item_keys, key)
	return result
