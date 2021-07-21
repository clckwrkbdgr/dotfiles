import logging

def linear_system(a, b, c, d, e, f):
	""" Solves linear system given by coeffs:
	{ a x + b y = c
	{ d x + e y = f
	Returns (x, y) if there is a single solution, otherwise None.
	"""
	if a == 0:
		if b == 0:
				return None
		y, x = linear_system(b,a,c, e,d,f)
		return x, y
	if abs(e - d * b / a) < 1e-6:
		return None
	y = (f - d * c / a) / (e - d * b / a)
	x = c / a - b * y / a
	return x, y

class SimplexLinearProgram(object):
	""" Solves max linear programming problem.
	"""
	def __init__(self, fitness, constraints):
		""" Fitness is a list of coeffs of fitness functions: Ax + By + Cz + ... -> (A, B, C, ...)
		Number of fitness coeffs should be equal to the number of variables.

		Constraints is the list of coeffs in constraining inequalities:
		Px + Qy + Rz + ... <= S   -> (P, Q, R, ..., S)
		Number of coeffs should equal to the number of variables (use 0 for missing ones) + limiting value.
		"""
		self.fitness = fitness
		self.constraints = constraints
	@staticmethod
	def basis_line(index, size):
		return [0] * index + [1] + [0] * (size - 1 - index)
	def solve(self):
		""" Calculates and returns tuple of the max plan. """
		logging.debug("fitness", self.fitness)
		logging.debug("constraints", self.constraints)
		value_count = len(self.fitness)
		basis_size = len(self.constraints)
		table = [line[:-1] + self.basis_line(index, basis_size) for index, line in enumerate(self.constraints)]
		logging.debug("table", table)
		plan = [line[-1] for line in self.constraints]
		logging.debug("plan", plan)
		index = [-x for x in self.fitness] + [0] * basis_size
		logging.debug("index", index)
		safe = 1000
		mapping = list(range(value_count, value_count + basis_size))
		while safe and any(x < 0 for x in index):
			safe -= 1
			logging.debug("------ iteration -------")
			logging.debug("mapping", mapping)
			minimal_index = index.index(min(index))
			logging.debug("leader column", minimal_index)
			leaders = [(b/x if x else -1) for b,x in zip(plan, [line[minimal_index] for line in table])]
			logging.debug("leaders", leaders)
			leader_line = leaders.index(min(l for l in leaders if l > -1))
			logging.debug("leader line", leader_line)
			solver_element = table[leader_line][minimal_index]
			logging.debug("solver element", solver_element)
			new_plan = [x - (plan[leader_line] * line[minimal_index]) / solver_element for x, line in zip(plan, table)]
			new_plan[leader_line] = plan[leader_line] / solver_element
			logging.debug("new plan", new_plan)
			mapping[leader_line] = minimal_index
			logging.debug("new mapping", mapping)
			new_index = [x - (index[minimal_index] * t) / solver_element for x, t in zip(index, table[leader_line])]
			logging.debug("new index", new_index)
			new_table = [
						[
							x - (table[row_index][minimal_index] * table[leader_line][col_index]) / solver_element
							for col_index, x
							in enumerate(line)
							]
						for row_index, line
						in enumerate(table)
						]
			new_table[leader_line] = [x/solver_element for x in table[leader_line]]
			logging.debug("new table", new_table)
			plan = new_plan
			index = new_index
			table = new_table
		optimal = dict((i, value) for i, value in zip(mapping, plan) if i < value_count)
		logging.debug("optimal", optimal)
		values = [(optimal[pos] if pos in optimal else 0) for pos in range(value_count)]
		logging.debug("values", values)
		return values
