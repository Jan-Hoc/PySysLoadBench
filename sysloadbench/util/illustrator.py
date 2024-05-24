import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np
from pathlib import Path

class Illustrator:

	def illustrate_results(stats: dict, path: Path | str, benchmark_name: str | None=None, run_name: str | None=None) -> None:
		"""creates graphs for statistics of run

		Args:
			stats (dict): stats as returned by Run.run_statistics
			path (Path | str): where to save graphs
			benchmark_name (str | None, optional): name of benchmark. Defaults to None.
			run_name (str | None, optional): name of run. Defaults to None.
		"""
		path = Path(path)
		Illustrator.__time_graph(stats['time'], path, benchmark_name, run_name)
		Illustrator.__data_graph(stats['cpu'], 'CPU Statistics', path, benchmark_name, run_name)
		Illustrator.__data_graph(stats['ram'], 'RAM Statistics', path, benchmark_name, run_name)

	def __time_graph(time_stats: dict, path: Path, benchmark_name: str | None=None, run_name: str | None=None) -> None:
		"""creates a plot for the given time stats as returned by Run under the key 'time' and saves it

		Args:
			time_stats (dict): expected to be in the same format as returned in the dict by Run under the key 'time'
			path (Path): location to save plot
			benchmark_name (str | None, optional): Name of benchmark. Defaults to None.
			run_name (str | None, optional): Name of run. Defaults to None.
		"""
		plot_len = len(time_stats['raw'])
		x_axis = range(1, plot_len + 1)

		img_name = 'time.png'
		if run_name is not None:
			img_name = run_name + '_' + img_name
		if benchmark_name is not None:
			img_name = benchmark_name + '_' + img_name

		plt.clf()
		plt.figure(figsize=(8,5), dpi=100)
		ax = plt.gca()
		ax.xaxis.set_major_locator(MaxNLocator(integer=True))

		plt.title('Time Statistics')
		plt.xlabel('Round')
		plt.ylabel('Seconds')

		plt.plot(x_axis, time_stats['raw'], linestyle='-', label='Raw Times')
		plt.fill_between(x_axis, np.array(time_stats['raw']) - time_stats['total']['stddev'], np.array(time_stats['raw']) + time_stats['total']['stddev'], alpha=.4)
		plt.plot(x_axis, [time_stats['total'][25]] * plot_len, linestyle=':', label='25th Percentile', color='y')
		plt.plot(x_axis, [time_stats['total']['mean']] * plot_len, linestyle='--', label='Mean', color='m')
		plt.plot(x_axis, [time_stats['total'][75]] * plot_len, linestyle=':', label='75th Percentile', color='c')
		plt.plot(x_axis, [time_stats['total']['max']] * plot_len, linestyle='--', label='Maximum Value', color='r')
		plt.legend(loc='upper left', bbox_to_anchor=(1.03, 1))
		plt.tight_layout()
		plt.savefig(path / img_name)

	def __data_graph(stats: dict, graph_title: str, path: Path, benchmark_name: str | None=None, run_name: str | None=None) -> None:
		"""creates a plot for the given RAM and CPU stats as returned by Run under the keys 'cpu' or 'ram' and saves it
		Args:
			stats (dict): expected to be in the same format as returned in the dict by Run under the key 'cpu' or 'ram'
			graph_title (str): either 'CPU Statistics' or 'RAM Statistics'
			path (Path): location to save plot
			benchmark_name (str | None, optional): Name of benchmark. Defaults to None.
			run_name (str | None, optional): Name of run. Defaults to None.
		"""
		plot_len = len(stats) - 1
		x_axis = range(1, plot_len + 1)
		rounds = range(0, plot_len)
		factor = 1 if graph_title == 'CPU Statistics' else 1024.0**2

		img_name = 'cpu.png' if graph_title == 'CPU Statistics' else 'ram.png'
		if run_name is not None:
			img_name = run_name + '_' + img_name
		if benchmark_name is not None:
			img_name = benchmark_name + '_' + img_name

		plt.clf()
		plt.figure(figsize=(8,5), dpi=100)
		ax = plt.gca()
		ax.xaxis.set_major_locator(MaxNLocator(integer=True))

		plt.title(graph_title)
		plt.xlabel('Round')
		plt.ylabel('Percent' if graph_title == 'CPU Statistics' else 'Mebibytes')

		plt.plot(x_axis, [stats[i]['mean'] / factor for i in rounds], linestyle='-', label='Mean of Round', color = 'b')
		plt.fill_between(x_axis, np.array([stats[i]['mean'] / factor for i in rounds]) - stats['total']['stddev'] / factor, np.array([stats[i]['mean'] / factor for i in rounds]) + stats['total']['stddev'] / factor, alpha=.4)
		plt.plot(x_axis, [stats['total']['mean'] / factor] * plot_len, linestyle='--', label='Mean Overall', color = 'b')
		plt.plot(x_axis, [stats[i][25] / factor for i in rounds], linestyle='-', label='25th Percentile of Round', color='y')
		plt.plot(x_axis, [stats['total'][25] / factor] * plot_len, linestyle='--', label='25th Percentile Overall', color='y')
		plt.plot(x_axis, [stats[i][75] / factor for i in rounds], linestyle='-', label='75th Percentile of Round', color='c')
		plt.plot(x_axis, [stats['total'][75] / factor] * plot_len, linestyle='--', label='75th Percentile Overall', color='c')
		plt.plot(x_axis, [stats[i]['max'] / factor for i in rounds], linestyle='-', label='Maximum Value of Round', color='r')
		plt.plot(x_axis, [stats['total']['max'] / factor] * plot_len, linestyle='--', label='Maximum Value Overall', color='r')

		plt.legend(loc='upper left', bbox_to_anchor=(1.03, 1))
		plt.tight_layout()
		plt.savefig(path / img_name)