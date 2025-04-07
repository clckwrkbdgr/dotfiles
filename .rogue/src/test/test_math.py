import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import textwrap
import clckwrkbdgr.math
from ..math import Point, Size, Rect, Matrix
from ..math import distance
from ..math import FieldOfView, in_line_of_sight

class TestMapAlgorithms(unittest.TestCase):
	def should_calculate_field_of_view(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            #     #
				#                  #
				#                  #
				####################
				""").replace('\n', ''))
		fov = FieldOfView(3)
		for p in fov.update(Point(11, 2), is_transparent=lambda p: matrix.valid(p) and matrix.cell(p) != '#'):
			if matrix.cell(p) == '#':
				matrix.set_cell(p, '%')
			else:
				matrix.set_cell(p, '.')
		self.assertTrue(fov.is_visible(11, 2))
		self.assertTrue(fov.is_visible(12, 2))
		self.assertTrue(fov.is_visible(12, 2))
		self.assertFalse(fov.is_visible(14, 3))
		self.assertTrue(fov.is_visible(14, 2))
		self.assertFalse(fov.is_visible(15, 2))
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				#########%%%%%######
				#        .....     #
				#       .......    #
				#        ....%     #
				#        .....     #
				#          .       #
				####################
				"""))
	def should_calculate_field_of_view_in_absolute_darkness(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            #     #
				#                  #
				#                  #
				####################
				""").replace('\n', ''))
		fov = FieldOfView(3)
		source = Point(11, 2)
		for p in fov.update(Point(11, 2), is_transparent=lambda p: max(abs(source.x - p.x), abs(source.y - p.y)) < 1):
			matrix.set_cell(p, '.')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				####################
				#         ...      #
				#         ...      #
				#         ...#     #
				#                  #
				#                  #
				####################
				"""))
	def should_check_direct_line_of_sight(self):
		matrix = Matrix(Size(20, 7), '.')
		matrix.data = list(textwrap.dedent("""\
				####################
				#                  #
				#                  #
				#            ###   #
				#            #     #
				#                  #
				####################
				""").replace('\n', ''))
		source = Point(11, 2)
		is_transparent=lambda p: matrix.valid(p) and matrix.cell(p) not in '#*'
		for p in matrix.size.iter_points():
			if in_line_of_sight(source, p, is_transparent):
				if matrix.cell(p) == '#':
					matrix.set_cell(p, '*')
				else:
					matrix.set_cell(p, '.')
		self.assertEqual(matrix.tostring(), textwrap.dedent("""\
				########*******#####
				*..................*
				*..................*
				*............*##   #
				*............*     #
				*.............     #
				####**********######
				"""))
