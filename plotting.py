import matplotlib
import numpy as np
import osmnx as ox

_EPS = 1e-3


def show_map(graph):
  # Get speed attribute for plotting
  max_speed = 0.
  min_speed = float('inf')
  for u, v, data in graph.edges(data=True):
    max_speed = max(data['speed'], max_speed)
    min_speed = min(data['speed'], min_speed)
  plot_speed = (max_speed != min_speed)

  # Go through all edges in graph, append with corresponding color from map
  cmap = matplotlib.cm.get_cmap('RdYlGn' if plot_speed else 'Greys')
  lines = []
  route_colors = []
  for u, v, data in graph.edges(data=True):
    # if it has a geometry attribute (ie, a list of line segments)
    if 'geometry' in data:
      xs, ys = data['geometry'].xy
      lines.append(list(zip(xs, ys)))
    else:
      x1 = graph.node[u]['x']
      y1 = graph.node[u]['y']
      x2 = graph.node[v]['x']
      y2 = graph.node[v]['y']
      line = [(x1, y1), (x2, y2)]
      lines.append(line)
    speed_ratio = (data['speed'] - min_speed) / (max_speed - min_speed) if plot_speed else 1.
    route_colors.append(cmap(speed_ratio))

  # Plot road network.
  fig, ax = ox.plot_graph(graph, show=False, close=False)
  lc = matplotlib.collections.LineCollection(lines, colors=route_colors, linewidths=2, alpha=0.5, zorder=3)
  ax.add_collection(lc)
  # Colorbar.
  if plot_speed:
    cax = ax.imshow([[min_speed, max_speed]], vmin=min_speed, vmax=max_speed, visible=False, cmap=cmap)  # This won't show.
    min_km_speed = int(np.ceil(min_speed * 3.6))
    max_km_speed = int(np.floor(max_speed * 3.6))
    cbar = fig.colorbar(cax, ticks=[min_km_speed / 3.6, max_km_speed / 3.6])
    cbar.ax.set_yticklabels(['%d km/h' % min_km_speed, '%d km/h' % max_km_speed])
