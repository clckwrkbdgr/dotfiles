def wrap_lines(lines, width=80, sep=' ', ellipsis="...", force_ellipsis=False, rjust_ellipsis=False):
	""" Wraps given list of lines into a single line of specified width
	while they can fit. Parts are separated with sep string.
	If first line does not fit and part of it cannot be displayed,
	or there are other lines that that cannot be displayed, displays ellipsis string
	at the end (may squeeze line even more to fit into max width).
	If rjust_ellipsis=True, puts ellipsis at the rightest possible position,
	filling gaps with spaces. Otherwise sticks it to the text.

	Returns pair (<number of lines displayed>, <result full line>).
	If first line does not fully fit and some part of it cannot be displayed,
	first number in the pair will be negative and it's abs will be equal to
	amount of characters that are displayed.
	"""
	if not lines:
		return 0, None
	if not force_ellipsis and len(lines) == 1 and len(lines[0]) <= width:
		return 0, lines[0]
	result = lines[0]
	if len(result) + len(ellipsis) > width:
		result = result[:width-len(ellipsis)] + ellipsis
		return -(width - len(ellipsis)), result
	to_remove = 1
	while len(lines) > to_remove and len(result) + len(sep) + len(lines[to_remove]) + len(ellipsis) <= width:
		result += sep + lines[to_remove]
		to_remove += 1
	if not force_ellipsis and len(lines) == to_remove:
		to_remove = 0
	if to_remove:
		if rjust_ellipsis:
			result = result.ljust(width-len(ellipsis))
		result += ellipsis
	return to_remove, result
