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

def prettify_number(number, base=1000, decimals=2, powers=None):
	powers = powers or ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y']
	while abs(number) >= base and len(powers) > 1:
		powers = powers[1:]
		number /= float(base)
	integer = int(round(number, 1))
	result = str(integer)
	remainder = number - integer
	decimal_str = ''
	while decimals > 0:
		decimals -= 1
		remainder *= 10
		top = int(round(remainder, 1))
		remainder -= top
		decimal_str += str(top)
	decimal_str = decimal_str.rstrip('0')
	if decimal_str.strip('0'):
		result += '.' + decimal_str
	return result + powers[0]

def to_roman(number):
	""" Converts integer number to roman. """
	mille, number = divmod(number, 1000)
	centum, number = divmod(number, 100)
	decem, unus = divmod(number, 10)
	result = 'M' * mille
	for value, value_repr, mid_repr, next_repr in [
			(centum, 'C', 'D', 'M'),
			(decem, 'X', 'L', 'C'),
			(unus, 'I', 'V', 'X'),
			]:
		if value < 4:
			result += value_repr * value
		elif value == 4:
			result += value_repr + mid_repr
		elif value < 9:
			result += mid_repr + value_repr * (value - 5)
		else:
			result += value_repr + next_repr
	return result

def from_roman(roman_string):
	""" Converts roman number to integer. """
	NUMBERS = {
				'I' : 1,
				'V' : 5,
				'X' : 10,
				'L' : 50,
				'C' : 100,
				'D' : 500,
				'M' : 1000,
				}
	result = 0
	prev_value = 0
	for c in roman_string.upper():
		value = NUMBERS[c]
		if prev_value > 0 and prev_value < value:
			result -= prev_value * 2
		result += value
		prev_value = value
	return result

def to_braille(text):
	def _convert(code):
		bin_code = bin(code)[2:].zfill(6)[::-1]
		return [[int(bin_code[j + i * 3]) for i in range(2)] for j in range(3)]

	LETTERS_NUMBERS = list(map(_convert,
										[1, 3, 9, 25, 17, 11, 27, 19, 10, 26,
										5, 7, 13, 29, 21, 15, 31, 23, 14, 30,
										37, 39, 62, 45, 61, 53, 47, 63, 55, 46, 26]))
	CAPITAL_FORMAT = _convert(32)
	NUMBER_FORMAT = _convert(60)
	PUNCTUATION = {",": _convert(2), "-": _convert(18), "?": _convert(38),
						"!": _convert(22), ".": _convert(50), "_": _convert(36)}
	WHITESPACE = _convert(0)

	MAX_SYMBOLS = 10
	DIGITS = dict(zip('1234567890', range(10)))
	LETTERS = dict(zip('abcdefghijklmnopqrstuvwxyz', range(26)))

	result = []
	for c in text:
		if c in DIGITS:
			result.append(NUMBER_FORMAT)
			result.append(LETTERS_NUMBERS[DIGITS[c]])
		elif c.lower() in LETTERS:
			if c.isupper():
				result.append(CAPITAL_FORMAT)
			result.append(LETTERS_NUMBERS[LETTERS[c.lower()]])
		elif c in PUNCTUATION:
			result.append(PUNCTUATION[c])
		elif c == ' ':
			result.append(WHITESPACE)
		else: # pragma: no cover
			raise ValueError("Unknown char: {0}".format(c))

	rows = [[]]
	for c in result:
		rows[-1].append(c)
		if len(rows[-1]) >= MAX_SYMBOLS:
			rows.append([])
	if len(rows) > 1 and len(rows[-1]) < MAX_SYMBOLS:
		if rows[-1]:
			rows[-1] += [WHITESPACE for i in range(MAX_SYMBOLS - len(rows[-1]))]
		else:
			rows = rows[:-1]

	dots = []
	for row in rows:
		if dots:
			dots.append([0 for i in range(len(dots[0]))])
		row_dots = [[], [], []]
		for c in row:
			if row_dots[0]:
				row_dots[0] += [0]
				row_dots[1] += [0]
				row_dots[2] += [0]
			row_dots[0].extend(c[0])
			row_dots[1].extend(c[1])
			row_dots[2].extend(c[2])
		dots.extend(row_dots)
	return tuple(tuple(row) for row in dots)
