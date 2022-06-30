from clckwrkbdgr import unittest
import textwrap, copy
from clckwrkbdgr.math import Point
import clckwrkbdgr.math.graph
from clckwrkbdgr.math.graph import get_clusters, is_connected, grid_from_matrix

class TestGraph(unittest.TestCase):
	def should_clone_graph(self):
		original = clckwrkbdgr.math.graph.Graph(directional=True)
		original.add_nodes(['A', 'B', 'C'])
		original.connect('A', 'B')
		original.connect('B', 'C')
		original.connect('C', 'A')

		clone = copy.copy(original)
		self.assertTrue(clone.has_node('A'))
		self.assertTrue(clone.has_node('B'))
		self.assertTrue(clone.has_node('C'))
		self.assertTrue(clone.has_connection('A', 'B'))
		self.assertFalse(clone.has_connection('A', 'C'))

		clone.remove_node('A')
		self.assertFalse(clone.has_node('A'))
		self.assertTrue(original.has_node('A'))
		self.assertTrue(original.has_connection('A', 'B'))
		self.assertTrue(original.has_connection('C', 'A'))
	def should_convert_graph_to_graphviz_representation(self):
		graph = clckwrkbdgr.math.graph.Graph(directional=True)
		graph.add_nodes(['A', 'B', 'C'])
		graph.connect('A', 'B')
		graph.connect('B', 'C')
		graph.connect('C', 'A')
		expected = textwrap.dedent("""\
				graph {
				  node A
				  node B
				  node C
				  A -> B
				  B -> C
				  C -> A
				}
				""")
		self.assertEqual(graph.to_dot(), expected)
	def should_add_node(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		self.assertTrue(graph.has_node('A'))
		self.assertFalse(graph.has_node('B'))
		graph.add_node('B')
		self.assertTrue(graph.has_node('B'))
		with self.assertRaises(ValueError):
			graph.add_node('B')
	def should_add_multiple_nodes(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_nodes(['A', 'B', 'C', 'A'])
		self.assertTrue(graph.has_node('A'))
		self.assertTrue(graph.has_node('B'))
		self.assertTrue(graph.has_node('C'))
		with self.assertRaises(ValueError):
			graph.add_nodes(['D', 'B'])
		self.assertFalse(graph.has_node('D'))
	def should_remove_node(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.connect('A', 'B')
		graph.connect('A', 'C')
		graph.connect('B', 'C')
		with self.assertRaises(ValueError):
			graph.remove_node('X')
		graph.remove_node('A')
		self.assertFalse(graph.has_node('A'))
		self.assertFalse(graph.has_connection('A', 'B'))
		self.assertFalse(graph.has_connection('A', 'C'))
		self.assertTrue(graph.has_connection('B', 'C'))
	def should_get_all_nodes(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		self.assertEqual(graph.all_nodes(), {'A', 'B', 'C'})
	def should_connect_nodes(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.add_node('D')
		with self.assertRaises(ValueError):
			graph.connect('A', 'X')
		with self.assertRaises(ValueError):
			graph.connect('X', 'A')
		graph.connect('A', 'B')
		with self.assertRaises(ValueError):
			graph.connect('A', 'B')
		with self.assertRaises(ValueError):
			graph.connect('B', 'A')
		graph.connect('B', 'C')
		self.assertEqual(graph.all_connections('B'), {'A', 'C'})
		self.assertEqual(graph.all_connections('D'), set())
		self.assertTrue(graph.has_connection('A', 'B'))
		self.assertTrue(graph.has_connection('B', 'A'))
		self.assertTrue(graph.has_connection('B', 'C'))
		self.assertFalse(graph.has_connection('A', 'C'))
		self.assertFalse(graph.has_connection('D', 'A'))
		self.assertFalse(graph.has_connection('A', 'D'))
	def should_connect_nodes_in_directional_graph(self):
		graph = clckwrkbdgr.math.graph.Graph(directional=True)
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.add_node('D')
		with self.assertRaises(ValueError):
			graph.connect('A', 'X')
		with self.assertRaises(ValueError):
			graph.connect('X', 'A')
		graph.connect('A', 'B')
		graph.connect('B', 'C')
		with self.assertRaises(ValueError):
			graph.connect('B', 'C')
		graph.connect('C', 'B')
		self.assertEqual(graph.all_connections('A'), {'B'})
		self.assertEqual(graph.all_connections('B'), {'C'})
		self.assertEqual(graph.all_connections('B', with_incoming=True), {'C', 'A'})
		self.assertEqual(graph.all_connections('D'), set())
		self.assertTrue(graph.has_connection('A', 'B'))
		self.assertFalse(graph.has_connection('B', 'A'))
		self.assertTrue(graph.has_connection('B', 'C'))
		self.assertTrue(graph.has_connection('C', 'B'))
		self.assertFalse(graph.has_connection('A', 'C'))
		self.assertFalse(graph.has_connection('D', 'A'))
		self.assertFalse(graph.has_connection('A', 'D'))
	def should_disconnect_nodes(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.add_node('D')
		graph.connect('A', 'B')
		graph.connect('A', 'C')
		graph.connect('B', 'C')
		with self.assertRaises(ValueError):
			graph.disconnect('A', 'X')
		with self.assertRaises(ValueError):
			graph.disconnect('X', 'A')
		with self.assertRaises(ValueError):
			graph.disconnect('A', 'D')
		with self.assertRaises(ValueError):
			graph.disconnect('D', 'A')
		graph.disconnect('A', 'B')
		graph.disconnect('C', 'B')
		self.assertFalse(graph.has_connection('A', 'B'))
		self.assertFalse(graph.has_connection('B', 'A'))
		self.assertTrue(graph.has_connection('A', 'C'))
	def should_disconnect_nodes_in_directional_graph(self):
		graph = clckwrkbdgr.math.graph.Graph(directional=True)
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.add_node('D')
		graph.connect('A', 'B')
		graph.connect('C', 'A')
		graph.connect('C', 'B')
		graph.connect('B', 'C')
		with self.assertRaises(ValueError):
			graph.disconnect('A', 'X')
		with self.assertRaises(ValueError):
			graph.disconnect('X', 'A')
		with self.assertRaises(ValueError):
			graph.disconnect('A', 'D')
		with self.assertRaises(ValueError):
			graph.disconnect('D', 'A')
		with self.assertRaises(ValueError):
			graph.disconnect('B', 'A')
		graph.disconnect('A', 'B')
		graph.disconnect('C', 'B')
		graph.disconnect('B', 'C')
		self.assertFalse(graph.has_connection('A', 'B'))
		self.assertFalse(graph.has_connection('B', 'A'))
		self.assertFalse(graph.has_connection('B', 'C'))
		self.assertFalse(graph.has_connection('C', 'B'))
		self.assertTrue(graph.has_connection('C', 'A'))
	def should_get_all_links(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.add_node('D')
		graph.connect('A', 'B')
		graph.connect('A', 'C')
		graph.connect('B', 'C')
		self.assertEqual(set(tuple(sorted(link)) for link in graph.all_links()), {
			('A', 'B'),
			('A', 'C'),
			('B', 'C'),
			})
	def should_get_all_links_in_directional_graph(self):
		graph = clckwrkbdgr.math.graph.Graph(directional=True)
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		graph.add_node('D')
		graph.connect('A', 'B')
		graph.connect('C', 'A')
		graph.connect('C', 'B')
		graph.connect('B', 'C')
		self.assertEqual(set(graph.all_links()), {
			('A', 'B'),
			('C', 'A'),
			('C', 'B'),
			('B', 'C'),
			})

class TestAlgorithms(unittest.TestCase):
	def should_get_all_clusters(self):
		graph = clckwrkbdgr.math.graph.Graph(directional=True)
		graph.add_node('A')
		graph.add_node('B')
		self.assertCountEqual(get_clusters(graph), [{'A'}, {'B'}])

		graph.add_node('C')
		self.assertCountEqual(get_clusters(graph), [{'A'}, {'B'}, {'C'}])

		graph.connect('A', 'B')
		self.assertCountEqual(get_clusters(graph), [{'A', 'B'}, {'C'}])

		graph.connect('C', 'A')
		self.assertCountEqual(get_clusters(graph), [{'A', 'B', 'C'}])

		graph.connect('B', 'C')
		self.assertCountEqual(get_clusters(graph), [{'A', 'B', 'C'}])

		graph.add_node('D')
		self.assertCountEqual(get_clusters(graph), [{'A', 'B', 'C'}, {'D'}])

		graph.add_node('E')
		graph.connect('D', 'E')
		self.assertCountEqual(get_clusters(graph), [{'A', 'B', 'C'}, {'D', 'E'}])
	def should_detect_fully_connected_graph(self):
		graph = clckwrkbdgr.math.graph.Graph(directional=True)
		graph.add_node('A')
		graph.add_node('B')
		graph.add_node('C')
		self.assertFalse(is_connected(graph))

		graph.connect('A', 'B')
		self.assertFalse(is_connected(graph))

		graph.connect('C', 'A')
		self.assertTrue(is_connected(graph))

		graph.connect('B', 'C')
		self.assertTrue(is_connected(graph))

		graph.add_node('D')
		self.assertFalse(is_connected(graph))
	def should_create_graph_from_matrix(self):
		m = clckwrkbdgr.math.Matrix.fromstring("ABC\nDEF\n123")
		grid = grid_from_matrix(m)
		self.assertEqual(set(grid.all_nodes()), set(m.keys()))
		self.assertTrue(grid.has_connection(Point(0, 0), Point(0, 1)))
		self.assertTrue(grid.has_connection(Point(0, 0), Point(1, 0)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(1, 1)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(0, 2)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(2, 0)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(2, 2)))

		grid = grid_from_matrix(m, with_diagonal=True)
		self.assertEqual(set(grid.all_nodes()), set(m.keys()))
		self.assertTrue(grid.has_connection(Point(0, 0), Point(0, 1)))
		self.assertTrue(grid.has_connection(Point(0, 0), Point(1, 0)))
		self.assertTrue(grid.has_connection(Point(0, 0), Point(1, 1)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(0, 2)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(2, 0)))
		self.assertFalse(grid.has_connection(Point(0, 0), Point(2, 2)))
