import collections
import csv
import hashlib
import logging
import os

import msgpack
import numpy as np
import osmnx as ox
import networkx as nx
import tqdm
import utm

import utils


_DEFAULT_SPEED = 50. / 3.6  # Default speed in [m/s].


TaxiData = collections.namedtuple('TaxiData', ['pickup_time', 'dropoff_time', 'pickup_xy', 'dropoff_xy'])


def load_map(location='Manhattan, New York, USA', cache_directory='/tmp', force_redownload=False):
  cached_filename = hashlib.md5(location).hexdigest() + '.graphml'
  try:
    if force_redownload:
      raise IOError('Forcing re-download of graph.')
    logging.info('Trying to load map from "%s"', os.path.join(cache_directory, cached_filename))
    graph = ox.load_graphml(cached_filename, folder=cache_directory)
  except IOError:
    logging.info('Downloading map from "%s"', location)
    graph = ox.graph_from_place(location, network_type='drive')
    # Keep the largest strongly connected component.
    logging.info('Finding largest component')
    graph = max(nx.strongly_connected_component_subgraphs(graph), key=len)
    graph = ox.project_graph(graph)
    logging.info('Saving map to "%s"', os.path.join(cache_directory, cached_filename))
    ox.save_graphml(graph, filename=cached_filename, folder=cache_directory)
  # Add dummy speed and length information.
  for u, v, key, data in graph.edges(data=True, keys=True):
    if 'time' not in data:
      time = data['length'] / _DEFAULT_SPEED
      data['time'] = time
      data['speed'] = _DEFAULT_SPEED
    else:
      data['time'] = float(data['time'])
      data['speed'] = float(data['speed'])
    graph.add_edge(u, v, **data)
  return graph


def build_shortest_paths(graph, cache_directory='/tmp', force_recompute=False):
  # Load shortest pre-computed path lengths.
  h = hashlib.md5(str(len(graph.nodes())) + str(len(graph.edges()))).hexdigest()
  route_lengths_filename = os.path.join(cache_directory, 'route_lengths_%s.pickle' % h)
  try:
    if force_recompute:
      raise IOError('Forcing re-computation of shortest paths.')
    logging.info('Trying to load shortest paths from "%s"', route_lengths_filename)
    with open(route_lengths_filename, 'rb') as fp:
      route_lengths = msgpack.unpackb(fp.read())
  except (IOError, EOFError):
    logging.info('Computing all shortest path lengths')
    route_lengths = dict(nx.shortest_path_length(graph, weight='time'))
    # We need to convert all defaultdict to dict before saving.
    for k, v in route_lengths.iteritems():
      route_lengths[k] = dict(v)
    logging.info('Saving shortest paths to "%s"', route_lengths_filename)
    with open(route_lengths_filename, 'wb') as fp:
      fp.write(msgpack.packb(route_lengths))
  return route_lengths


def load_taxi(filename, cache_directory='/tmp', force_recompute=False, max_rides=0):
  """
  Loads the yellow taxicab in a friendly format.

  Data needs to be downloaded in a CSV format from:
  http://www.nyc.gov/html/tlc/html/about/trip_record_data.shtml
  > wget https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2016-06.csv

  Note that the latest data does not have exact positioning information.
  """

  def from_latlon(latlong):
    x, y, _, _ = utm.from_latlon(*latlong)
    return np.array([x, y])

  cached_filename = hashlib.md5(filename).hexdigest() + '_{}.bin'.format(max_rides)
  cached_path = os.path.join(cache_directory, cached_filename)

  try:
    if force_recompute:
      raise IOError('Forcing re-computation of the taxi data.')
    logging.info('Trying to load preprocessed taxi data from "%s"', cached_path)
    with open(cached_path, 'rb') as fp:
      taxi_data = TaxiData(*msgpack.unpackb(fp.read()))
  except (IOError, EOFError):
    logging.info('Loading taxi data from "%s"', filename)
    pickup_xy = []
    dropoff_xy = []
    pickup_times = []
    dropoff_times = []
    count_rows = -1  # Remove header line.
    with open(filename, 'rb') as fp:
      for line in fp.xreadlines():
        count_rows += 1
    with open(filename, 'rb') as fp:
      reader = csv.reader(fp)
      header_row_index = dict((h, i) for i, h in enumerate(reader.next()))
      # Unfortunately, we have to read everything as the files are not in order.
      for row in tqdm.tqdm(reader, total=count_rows):
        pickup_lat_long = (float(row[header_row_index['pickup_latitude']]), float(row[header_row_index['pickup_longitude']]))
        dropoff_lat_long = (float(row[header_row_index['dropoff_latitude']]), float(row[header_row_index['dropoff_longitude']]))
        pickup_xy.append(from_latlon(pickup_lat_long).tolist())
        dropoff_xy.append(from_latlon(dropoff_lat_long).tolist())
        pickup_times.append(row[header_row_index['tpep_pickup_datetime']])
        dropoff_times.append(row[header_row_index['tpep_dropoff_datetime']])
    logging.info('Saving processed taxi data to "%s"', cached_path)
    pickup_times = np.array(pickup_times, dtype='datetime64').astype(np.uint64).tolist()
    dropoff_times = np.array(dropoff_times, dtype='datetime64').astype(np.uint64).tolist()
    max_rides = max_rides if max_rides else len(pickup_times)
    pickup_times, dropoff_times, pickup_xy, dropoff_xy = zip(*sorted(zip(pickup_times, dropoff_times, pickup_xy, dropoff_xy))[:max_rides])
    taxi_data = TaxiData(
        np.array(pickup_times, dtype='uint64').tolist(),
        np.array(dropoff_times, dtype='uint64').tolist(),
        np.array(pickup_xy).tolist(),
        np.array(dropoff_xy).tolist())
    with open(cached_path, 'wb') as fp:
      fp.write(msgpack.packb(taxi_data))
  return taxi_data


def update_edge_speed(graph, taxi_data,
                      nearest_neighbor_searcher=None,
                      cache_directory='/tmp',
                      force_recompute=False,
                      min_ride_count=10,
                      ignore_location_greater_than=300.,
                      ignore_rides_longer_than=20):
  h = hashlib.md5(str(len(graph.nodes())) + str(len(graph.edges()))).hexdigest()
  edge_times_filename = os.path.join(cache_directory, 'edge_times_%s.pickle' % h)
  try:
    if force_recompute:
      raise IOError('Forcing re-computation of edge speed.')
    logging.info('Trying to load edge times from "%s"', edge_times_filename)
    with open(edge_times_filename, 'rb') as fp:
      edge_times = msgpack.unpackb(fp.read())
  except IOError:
    if nearest_neighbor_searcher is None:
      nearest_neighbor_searcher = utils.NearestNeighborSearcher(graph)
    logging.info('Computing all routes to calculate edge time')
    routes = nx.shortest_path(graph, weight='length')
    logging.info('Computing edge statistics')
    edge_times = collections.defaultdict(lambda: collections.defaultdict(lambda: []))
    for start_time, end_time, u, v in tqdm.tqdm(zip(taxi_data.pickup_time, taxi_data.dropoff_time,
                                                    taxi_data.pickup_xy, taxi_data.dropoff_xy)):
      if end_time - start_time < ignore_rides_longer_than:
        continue
      # Assume taxi took shortest route.
      u_node, du = nearest_neighbor_searcher.search(u)
      if du > ignore_location_greater_than:
        continue
      v_node, dv = nearest_neighbor_searcher.search(v)
      if dv > ignore_location_greater_than:
        continue
      route = routes[u_node][v_node]
      # Get route length.
      length = 0.
      for a, b in zip(route[:-1], route[1:]):
        length += min([data for data in graph.edge[a][b].values()], key=lambda x: x['length'])['length']
      # Assume vehicle drove at a constant speed.
      speed = length / float(end_time - start_time)
      for a, b in zip(route[:-1], route[1:]):
        length = min([data for data in graph.edge[a][b].values()], key=lambda x: x['length'])['length']
        edge_times[a][b].append(length / speed)
    # Take median time (thus removing outliers).
    edge_times = dict(edge_times)
    for u, neighbors in edge_times.iteritems():
      to_delete = []
      for v, times in neighbors.iteritems():
        if len(times) >= min_ride_count:
          edge_times[u][v] = np.median(times)
        else:
          to_delete.append(v)
      for v in to_delete:
        del neighbors[v]
      edge_times[u] = dict(neighbors)
    with open(edge_times_filename, 'wb') as fp:
      fp.write(msgpack.packb(edge_times))
  # Clip outliers (due to wrongly reported road lengths).
  all_speeds = []
  all_lengths = []
  for u, v, key, data in graph.edges(data=True, keys=True):
    if u in edge_times and v in edge_times[u]:
      all_speeds.append(data['length'] / edge_times[u][v])
      all_lengths.append(data['length'])
  all_speeds = np.array(all_speeds)
  all_lengths = np.array(all_lengths)
  mean_speed = np.mean(all_speeds)
  std_speed = np.std(all_speeds)
  logging.info('Average speed: %.2f +- %.2f km/h', mean_speed * 3.6, std_speed * 3.6)
  # Add a time attribute to edges.
  for u, v, key, data in graph.edges(data=True, keys=True):
    if u in edge_times and v in edge_times[u]:
      speed = np.clip(data['length'] / edge_times[u][v], mean_speed - 2. * std_speed, mean_speed + 2. * std_speed)
    else:
      speed = mean_speed
    data['time'] = data['length'] / speed
    data['speed'] = speed
    graph.add_edge(u, v, **data)
