import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
from clckwrkbdgr.math import solve

class TestSolvers(unittest.TestCase):
	def should_solve_linear_system(self):
		self.assertEqual(solve.linear_system( * ( (1, 3, 17) + (5, -3, 4) ) ), (3.5, 4.5))
		self.assertIsNone(solve.linear_system( * ( (1, 2, 4) + (2, 4, 8) ) ))
		self.assertEqual(solve.linear_system( * ( (0, 2, 17) + (5, -3, 4) ) ), (5.9, 8.5))
		self.assertIsNone(solve.linear_system( * ( (0, 0, 0) + (0, 0, 0) ) ))
	def should_solve_simplex_method(self):
		self.assertEqual(solve.SimplexLinearProgram([100, 10, 1000], [
			[50, 20, 200, 5*1000],
			[1, 0, 0, 200],
			[0, 1, 0, 1000],
			[0, 0, 1, 2],
			]).solve(), [92, 0, 2])
		self.assertEqual(solve.SimplexLinearProgram([100, 10, 1000], [
			[50, 20, 200, 7.5*1000],
			[1, 0, 0, 100],
			[0, 1, 0, 100],
			[0, 0, 1, 1],
			]).solve(), [100, 100, 1])
