from .util.collector import Collector
from .util.evaluator import Evaluator
from typing import Callable
from copy import deepcopy
import time
import gc
from prettytable import PrettyTable

class DuplicateRun(Exception):
	pass

class RunNotFound(Exception):
	pass

class Run:
	""" class to run benchmark runs and collect results

	Methods
	-------
	benchmark_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=False, **kwargs):
		runs benchmarks for function benchmark. Calls setup function once in beginning and prerun before every round of run.
		runs warmup_rounds rounds for warmup, which are not measured and then measures for rounds rounds
		prints results to terminal
		passes kwargs to benchmark, setup and prerun
		run name must be unique, else raises DuplicateRun exception

	run_statistics(self, name: str):
		returns result of run name
		results are dict {'cpu', 'ram', 'time'} with entries in format as Evaluator.calculate_statistics
			key 'time' only has entry 'total', and additional key 'raw' to see raw times over the different runs
		if benchmark run with that name wasn't run yet, raises RunNotFound exception
	"""
	def __init__(self):
		self.__results = {}

	def benchmark_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=False, **kwargs) -> None:
		"""runs benchmarks for given function benchmark

		Args:
			name (str): name of run, must be unique
			benchmark (Callable): function to benchmark
			setup (Callable | None, optional): setup function which is called once in beginning. Defaults to None.
			prerun (Callable | None, optional): setup function which is run once before every round of run. Defaults to None.
			rounds (int, optional): Amount of times benchmark should be called to measure for statistic. Defaults to 1.
			warmup_rounds (int, optional): amount of untracked warmup rounds for benchmark. Defaults to 0.
			gc_active(bool, optional): enable or disable garbage collection during benchmark. 
				Activating gives more "real world" results, while deactivating gives more reproducable results

		Raises:
			DuplicateRun: if benchmark with name was already called
		"""

		if name in self.__results:
			raise DuplicateRun(f'Run named {name} already exists. Choose a unique name')

		print(f'Starting Run {name}')

		collector = Collector()

		# run setup		
		kwargs = kwargs['kwargs']
		if setup is not None:
			setup(**kwargs)
		
		# run warm up rounds
		for _ in range(warmup_rounds):
			if prerun is not None:
				prerun(**kwargs)
			benchmark(**kwargs)  

		# benchmark actual run
		times = [None] * rounds
		for i in range(rounds):
			if prerun is not None:
				prerun(**kwargs)

			# do garbage collection before every run for consistency
			gc.collect()
			# disable garbage collection if set to do so
			if not gc_active:
				gc.disable()

			with collector:
				start = time.process_time()
				benchmark(**kwargs)
				times[i] = time.process_time() - start

			# enable gc after run to return back to normal for prerun function of next round
			if not gc_active:
				gc.enable()

		self.__results[name] = collector.statistics()
		self.__results[name]['time'] = {'total': Evaluator.calculate_statistics(times, [25, 50, 75, 90, 95, 99], 4), 'raw': [round(t, 4) for t in times]}
		self.__print_results(name)

	def run_statistics(self, name: str) -> dict:
		"""return statistics for run name

		Args:
			name (str): name of existing run

		Returns:
			dict: {'cpu', 'ram', 'time'} of results of run in same format as returned by Evaluator.calculate_statistics
				value of key 'time' contains two entries. once statistics under subkey 'total' and also the raw value under 'raw' to see development over runs
				values of 'cpu' and 'ram' are rounded to 2 decimal points and 'time' to 4

		Raises:
			RunNotFound: is raised if no run with name name was run yet
		"""

		if name not in self.__results:
			raise RunNotFound(f'Results of run {name} not found')
		return deepcopy(self.__results[name])

	def __print_results(self, name: str) -> None:
		if name not in self.__results:
			raise RunNotFound(f'Results of run {name} not found')

		t = PrettyTable(['System Component', 'Max.', 'Mean', 'Std. Dev.', '25th perc.', '50th perc.', '75th perc.', '90th perc.', '95th perc.', '99th perc.'])
		t.add_row(['CPU (%) ', *self.__results[name]['cpu']['total'].values()])
		t.add_row(['RAM (Bytes)', *self.__results[name]['ram']['total'].values()])
		t.add_row(['Time (Seconds)', *self.__results[name]['time']['total'].values()])
		print(t)