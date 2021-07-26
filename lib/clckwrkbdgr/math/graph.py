import copy

class Graph(object):
	def __init__(self, directional=False):
		self._nodes = set()
		self._connections = dict()
		self._directional = directional
	def __copy__(self):
		new_object = Graph(directional=self._directional)
		new_object._nodes = copy.copy(self._nodes)
		new_object._connections = {key:copy.copy(value) for key, value in self._connections.items()}
		return new_object
	def all_nodes(self):
		return self._nodes
	def all_links(self):
		yielded = []
		for node_from in self._connections:
			for node_to in self._connections[node_from]:
				if not self._directional and (node_to, node_from) in yielded:
					continue
				yielded.append( (node_from, node_to) )
				yield (node_from, node_to)
	def add_nodes(self, nodes):
		nodes = set(nodes)
		exist = nodes & self._nodes
		if exist:
			raise ValueError("Nodes {0} already exist.".format(', '.join(map(str, exist))))
		self._nodes |= nodes
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

def get_clusters(graph):
	clusters = []
	for a, b in graph.all_links():
		new_clusters = [{a, b}]
		for cluster in clusters:
			for other in new_clusters:
				if cluster & other:
					other.update(cluster)
					break
			else:
				new_clusters.append(cluster)
		clusters = new_clusters
	for node in graph.all_nodes():
		if any(node in cluster for cluster in clusters):
			continue
		clusters.append({node})
	return clusters

def is_connected(graph):
	return len(get_clusters(graph)) == 1
