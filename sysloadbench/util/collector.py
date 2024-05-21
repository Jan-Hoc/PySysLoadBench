import multiprocessing as mp
import psutil
import os
import time
from .evaluator import Evaluator

class Collector:
	""" collects benchmarking data for code executed in "with" blocks
	can be run in several "with" blocks, where every iteration in a "with" block is regarded as a run
	if data should be reset for different code to be benchmarked, create a new collector

	collection of data is started in seperate python process
	this allows fore more accurate cpu and ram data collection of actual workload

	Methods
    -------
    statistics(self):
        returns the CPU and RAM statistics in a dict ('cpu' and 'ram' as keys, results rounded to two decimal points) 
		the statistics themselves are in dicts containing the keys
		- max: maximum
		- mean: mean
		- stddev: standard deviation
		- x: x'th percentile for x in [25, 50, 75, 90, 95, 99] (x as int)
	"""

	def __init__(self, pid: int | None=None):
		self.__cpu_data = []
		self.__ram_data = []
		if pid is None:
			self.__pid = os.getpid()
		else:
			self.__pid = pid
		self.__running = mp.Value('b', False)
		self.__measuring_interval = 0.05

	def __enter__(self, pid: int | None=None):
		self.__running.value = True
		self.__cpu_queue = mp.Queue()
		self.__ram_queue = mp.Queue()
		if pid is None:
			pid = self.__pid
		self.__measuring_process = mp.Process(target=self.__gather_data, args=(pid,))
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

		if len(cpu_data) == 0:
			cpu_data = [0]
		self.__cpu_data.append(cpu_data)

		while not self.__ram_queue.empty():
			ram_data.append(self.__ram_queue.get())
		self.__ram_queue = None

		if len(ram_data) == 0:
			ram_data = [0]
		self.__ram_data.append(ram_data)

	def statistics(self) -> dict:
		"""returns the CPU and RAM statistics in a tuple (rounded to two decimal points)
		the statistics themselves are in dicts containing the keys
		- max: maximum
		- mean: mean
		- stddev: standard deviation
		- x: x'th percentile for x in [25, 50, 75, 90, 95, 99] (x as int)

		Returns:
			dict: {'cpu', 'ram'}, where values are dicts with the above keys
		"""
		percentiles = [25, 50, 75, 90, 95, 99]

		cpu_stats = Evaluator.calculate_statistics(self.__cpu_data, percentiles, 2)

		ram_stats = Evaluator.calculate_statistics(self.__ram_data, percentiles, 2)

		return {'cpu': cpu_stats, 'ram': ram_stats}

	def __gather_data(self, pid) -> None:
		# collect RAM and CPU data and pass to parent process
		process = psutil.Process(pid)
		process_list = [process] + process.children(recursive=True)

		for p in process_list:
			try:
				p.cpu_percent()
			except (psutil.NoSuchProcess, psutil.AccessDenied):
				continue

		while self.__running.value:
			cpu_load = 0
			ram_load = 0
			process_list = [process] + process.children(recursive=True)

			for p in process_list:
				try:
					cpu_load += p.cpu_percent()
					ram_load += p.memory_info().vms
				except (psutil.NoSuchProcess, psutil.AccessDenied):
					if p == process:
						self.__running.value = False
					continue

			self.__cpu_queue.put(cpu_load)
			self.__ram_queue.put(ram_load)
			time.sleep(self.__measuring_interval)

		self.__cpu_queue.close()
		self.__ram_queue.close()