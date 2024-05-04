import multiprocessing as mp
import numpy as np
import psutil
import os

class Collector:
	""" collects benchmarking data for code executed in "with" blocks
	can be run in several "with" blocks, where every iteration in a "with" block is regarded as a run
	if data should be reset for different code to be benchmarked, create a new collector

	collection of data is started in seperate python process
	this allows fore more accurate cpu and ram data collection of actual workload

	Methods
    -------
    statistics(self):
        returns the CPU and RAM statistics in a tuple 
		the statistics themselves are in dicts containing the keys
		- max: maximum
		- mean: mean
		- stddev: standard deviation
		- x: x percentile for x in [25, 50, 75, 90, 95, 99]
	"""

	def __init__(self):
		self.__cpu_data = []
		self.__ram_data = []
		self.__running = mp.Value('b', False)
		self.__measuring_interval = 0.05

	def __enter__(self):
		self.__running.value = True
		self.__cpu_queue = mp.Queue()
		self.__ram_queue = mp.Queue()
		self.__measuring_process = mp.Process(target=self.__gather_data, args=(os.getpid(),))
		self.__measuring_process.start()

	def __exit__(self, exc_type, exc_value, exc_traceback):
		self.__running.value = False
		self.__measuring_process.join()

		# collect data from finished child process
		cpu_data = []
		ram_data = []

		while not self.__cpu_queue.empty():
			cpu_data.append(self.__cpu_queue.get())
		self.__cpu_queue = None
		self.__cpu_data.append(cpu_data)

		while not self.__ram_queue.empty():
			ram_data.append(self.__ram_queue.get())
		self.__ram_queue = None
		self.__ram_data.append(ram_data)

	def statistics(self) -> tuple:
		"""returns the CPU and RAM statistics in a tuple 
		the statistics themselves are in dicts containing the keys
		- max: maximum
		- mean: mean
		- stddev: standard deviation
		- x: x percentile for x in [25, 50, 75, 90, 95, 99]

		Returns:
			(dict, dict): tuple containing (cpu_stats, ram_stats), which are dicts with the above keys
		"""
		percentiles = [25, 50, 75, 90, 95, 99]

		cpu_stats = {}
		ram_stats = {}

		cpu_data = np.array([x for iteration in self.__cpu_data for x in iteration])
		cpu_stats['max'] = np.max(cpu_data)
		cpu_stats['mean'] = round(np.mean(cpu_data), 2)
		cpu_stats['stddev'] = round(np.std(cpu_data), 2)
		for p in percentiles:
			cpu_stats[str(p)] = round(np.percentile(cpu_data, p), 2)

		ram_data = np.array([x for iteration in self.__ram_data for x in iteration])
		ram_stats['max'] = np.max(ram_data)
		ram_stats['mean'] = round(np.mean(ram_data), 2)
		ram_stats['stddev'] = round(np.std(ram_data), 2)
		for p in percentiles:
			ram_stats[str(p)] = round(np.percentile(ram_data, p), 2)

		return (cpu_stats, ram_stats)

	def __gather_data(self, pid) -> None:
		# collect RAM and CPU data and pass to parent process
		process = psutil.Process(pid)
		while self.__running.value:
			self.__cpu_queue.put(process.cpu_percent(self.__measuring_interval))
			self.__ram_queue.put(process.memory_info().vms)

		self.__cpu_queue.close()
		self.__ram_queue.close()