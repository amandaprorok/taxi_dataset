import heapq

import networkx as nx
import numpy as np
from scipy.spatial import cKDTree


class NearestNeighborSearcher(object):

  def __init__(self, graph):
    points = []
    indices = []
    for k, v in graph.node.iteritems():
      points.append([v['x'], v['y']])
      indices.append(k)
    self.indices = np.array(indices)
    self.kdtree = cKDTree(points, 10)

  def search(self, xy):
    if isinstance(xy, np.ndarray) and xy.shape == 1:
      single_point = True
      xy = [xy]
    else:
      single_point = False
    distances, indices = self.kdtree.query(xy)
    if single_point:
      return self.indices[indices[0]], distances[0]
    return self.indices[indices], distances

  def search_radius(self, xy, dist=1.):
    return self.kdtree.query_ball_point(xy, r=dist)

  def search_k(self, xy, k=1):
    return self.kdtree.query(xy, k=k)


def normalize_graph(graph, route_lengths):
  """Makes indices contiguous."""
  mapping = {}
  for i, node in enumerate(graph.nodes()):
    mapping[node] = i
  graph = nx.relabel_nodes(graph, mapping=mapping)
  # Update route lengths.
  assert len(mapping) == len(route_lengths)
  new_route_lengths = np.empty((len(mapping), len(mapping)), dtype=np.float32)
  for u, lengths in route_lengths.iteritems():
    assert len(lengths) == len(mapping)
    for v, l in lengths.iteritems():
      new_route_lengths[mapping[u], mapping[v]] = route_lengths[u][v]
  return graph, new_route_lengths, NearestNeighborSearcher(graph)


# Simple priority queue.
class PriorityQueue:

  def __init__(self):
    self._queue = []

  def push(self, item, priority=None):
    heapq.heappush(self._queue, (item if priority is None else priority, item))

  def pop(self):
    return heapq.heappop(self._queue)[-1]

  def peek(self):
    return self._queue[0][-1]

  def __len__(self):
    return len(self._queue)
