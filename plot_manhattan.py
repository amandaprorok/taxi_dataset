import argparse
import logging
import matplotlib.pylab as plt

import data
import plotting


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Shows Manhattan.')
  parser.add_argument('--taxi_filename', action='store', default=None, help='If set, shows the estimated average taxi speed.')
  parser.add_argument('--log', action='store', default=None, help='Level of logging, e.g.: "info".')
  args = parser.parse_args()

  if args.log:
    numeric_level = getattr(logging, args.log.upper(), None)
    logging.basicConfig(level=numeric_level)

  graph = data.load_map()
  if args.taxi_filename:
    taxi_data = data.load_taxi(args.taxi_filename)
    data.update_edge_speed(graph, taxi_data)

  plotting.show_map(graph)
  plt.show()
