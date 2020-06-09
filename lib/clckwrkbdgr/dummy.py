""" Dummy module to substitute missing dependencies, e.g.:
>>> try:
...    import termcolor
... except ImportError:
...    import dummy as termcolor

Now some functionality of missing modules can be used in form of dummy functions,
i.e. it will make no real effect.
E.g. `termcolor.colored` will return text without any alterations.

See sections below for the list of supported modules.
"""

# termcolor

def colored(s, *args, **kwargs):
	return s
