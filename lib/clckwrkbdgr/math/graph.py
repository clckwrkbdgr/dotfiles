class Graph(object):
	def __init__(self, directional=False):
		self._nodes = set()
		self._connections = dict()
		self._directional = directional
	def all_nodes(self):
		return self._nodes
	def add_node(self, node):
		if node in self._nodes:
			raise ValueError("Node {0} already exists.".format(node))
		self._nodes.add(node)
	def has_node(self, node):
		return node in self._nodes
	def remove_node(self, node):
		if node not in self._nodes:
			raise ValueError("Node {0} does not exist.".format(node))
		for link in self._connections:
			if node in self._connections[link]:
				self._connections[link].remove(node)
		if node in self._connections:
			del self._connections[node]
		self._nodes.remove(node)
	def connect(self, node, other):
		if node not in self._nodes:
			raise ValueError("Node {0} does not present in graph.".format(node))
		if other not in self._nodes:
			raise ValueError("Node {0} does not present in graph.".format(other))
		if node not in self._connections:
			self._connections[node] = set()
		if other in self._connections[node]:
			raise ValueError("Connection {0}->{1} already exists.".format(node, other))
		self._connections[node].add(other)
		if not self._directional:
			if other not in self._connections:
				self._connections[other] = set()
			self._connections[other].add(node)
	def has_connection(self, node, other):
		if self._directional:
			if node not in self._connections:
				return False
			if other not in self._connections[node]:
				return False
			return True
		else:
			return (node in self._connections and other in self._connections[node]) or (other in self._connections and node in self._connections[other])
	def all_connections(self, node, with_incoming=False):
		result = set()
		if node in self._connections:
			result |= self._connections[node]
		if self._directional and with_incoming:
			result |= set(other for other in self._connections if node in self._connections[other])
		return result
	def disconnect(self, node, other):
		if node not in self._nodes:
			raise ValueError("Node {0} does not present in graph.".format(node))
		if other not in self._nodes:
			raise ValueError("Node {0} does not present in graph.".format(other))
		if self._directional:
			if node not in self._connections:
				raise ValueError("Nodes are not connected {0}->{1}".format(node, other))
			if other not in self._connections[node]:
				raise ValueError("Nodes are not connected {0}->{1}".format(node, other))
			self._connections[node].remove(other)
		else:
			found = False
			if node in self._connections and other in self._connections[node]:
				found = True
				self._connections[node].remove(other)
			if other in self._connections and node in self._connections[other]:
				found = True
				self._connections[other].remove(node)
			if not found:
				raise ValueError("Nodes are not connected {0}<->{1}".format(node, other))
