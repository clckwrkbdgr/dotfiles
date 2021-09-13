import ranger.gui.colorscheme
from ranger.gui.color import *

class Dim(ranger.gui.colorscheme.ColorScheme):
	def use(self, context):
		fore, back, attr = white, default, normal
		if context.reset:
			return (fore, back, attr)
		if context.error or context.badinfo:
			return (black, red, bold)
		# TODO sync with dir_colors.
		# TODO refactor for file types.
		if context.marked:
			if context.selected:
				return (blue, yellow, attr)
			else:
				return (blue, back, attr)
		if context.directory:
			if context.link:
				if context.good:
					fore, attr = blue, bold
				elif context.bad:
					fore, attr = red, bold
				if context.selected:
					return (fore, yellow, attr)
				else:
					return (fore, back, attr)
			if context.selected:
				return (black, yellow, normal)
			else:
				return (yellow, back, bold)
		if context.executable:
			if context.selected:
				return (green, yellow, normal)
			else:
				return (green, back, bold)
		if context.link:
			if context.good:
				fore, attr = blue, normal
			elif context.bad:
				fore, attr = red, normal
			if context.selected:
				return (fore, yellow, attr)
			else:
				return (fore, back, attr)
		if context.fifo or context.socket or context.device:
			if context.selected:
				return (magenta, yellow, normal)
			else:
				return (magenta, back, normal)
		if context.file:
			if context.selected:
				return (black, yellow, normal)
			else:
				return (white, back, normal)
		return (fore, back, attr)
