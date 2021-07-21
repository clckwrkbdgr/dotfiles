import unittest
unittest.defaultTestLoader.testMethodPrefix = 'should'
import clckwrkbdgr.math.graph

class TestGraph(unittest.TestCase):
	def should_add_node(self):
		graph = clckwrkbdgr.math.graph.Graph()
		graph.add_node('A')
		self.assertTrue(graph.has_node('A'))
		self.assertFalse(graph.has_node('B'))
		graph.add_node('B')
		self.assertTrue(graph.has_node('B'))
		with self.assertRaises(ValueError):
			graph.add_node('B')
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
