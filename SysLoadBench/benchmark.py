from collector import Collector
from evaluator import Evaluator
from typing import Callable
import time
import gc
from prettytable import PrettyTable

class DuplicateBenchmark(Exception):
	pass

class BenchmarkNotFound(Exception):
	pass

class Benchmark:
	""" class to run benchmarks and collect results

	Methods
	-------
	benchmark(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, **kwargs):
		runs benchmarks for function benchmark. Calls setup function once in beginning and prerun before every run of benchmark.
		Runs warmup_rounds rounds for warmup, which are not measured and then measures for rounds rounds
		Prints results to terminal
		passes kwargs to benchmark, setup and prerun
		benchmark name must be unique, else raises DuplicateBenchmark exception

	statistics(self, name: str):
		returns result of benchmark name
		results are tuple (cpu, ram, time) with entries in format as Evaluator.calculate_statistics
		if benchmark with that name wasn't run yet, raises BenchmarkNotFound exception
	"""
	def __init__(self):
		self.__results = {}

	def run_benchmark(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, **kwargs) -> None:
		"""runs benchmarks for given function benchmark

		Args:
			name (str): name of benchmark, must be unique
			benchmark (Callable): function to benchmark
			setup (Callable | None, optional): setup function which is called once in beginning. Defaults to None.
			prerun (Callable | None, optional): setup function which is run once before every run of benchmark. Defaults to None.
			rounds (int, optional): Amount of times benchmark should be called to measure for statistic. Defaults to 1.
			warmup_rounds (int, optional): amount of untracked warmup rounds for benchmark. Defaults to 0.

		Raises:
			DuplicateBenchmark: if benchmark with name was already called
		"""
		if name in self.__results:
			raise DuplicateBenchmark(f'Benchmark named {name} already exists. Choose a unique name')

		print(f'Starting Benchmark {name}')
		kwargs = kwargs['kwargs']
		collector = Collector()

		# run setup
		if setup is not None:
			setup(**kwargs)
		
		# run warm up rounds
		for _ in range(warmup_rounds):
			if prerun is not None:
				prerun(**kwargs)
			benchmark(**kwargs)  

		# run actual benchmark
		times = [None] * rounds
		for i in range(rounds):
			if prerun is not None:
				prerun(**kwargs)
			gc.collect()
			gc.disable()
			with collector:
				start = time.process_time()
				benchmark(**kwargs)
				times[i] = time.process_time() - start
			gc.enable()

		collector_stats = collector.statistics()
		time_stats = Evaluator.calculate_statistics(times, [25, 50, 75, 90, 95, 99], 4)
		self.__results[name] = (*collector_stats, time_stats)
		self.__print_results(name)

	def statistics(self, name: str) -> tuple:
		"""return statistics for benchmark name

		Args:
			name (str): name of existing benchmark

		Raises:
			BenchmarkNotFound: is raised if no benchmark with name name was run yet

		Returns:
			tuple: tuple (cpu, ram, time) of results of benchmark in same format as returned by Evaluator.calculate_statistics
		"""
		if name not in self.__results:
			raise BenchmarkNotFound(f'Results of benchmark {name} not found')
		return self.__results[name]

	def __print_results(self, name: str) -> None:
		if name not in self.__results:
			raise BenchmarkNotFound(f'Results of benchmark {name} not found')

		t = PrettyTable(['System Component', 'Max.', 'Mean', 'Std. Dev.', '25th perc.', '50th perc.', '75th perc.', '90th perc.', '95th perc.', '99th perc.'])
		t.add_row(['CPU (%)', *self.__results[name][0].values()])
		t.add_row(['RAM (Bytes)', *self.__results[name][1].values()])
		t.add_row(['Time (Seconds)', *self.__results[name][2].values()])
		print(t)