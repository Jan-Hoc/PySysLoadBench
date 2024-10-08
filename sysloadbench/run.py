from .util.collector import Collector
from .util.evaluator import Evaluator
from .util.illustrator import Illustrator
from pathos import pools as pp
import multiprocess as mp
from typing import Callable
from copy import deepcopy
from prettytable import PrettyTable
from pathlib import Path
import numpy as np
import psutil
import time
import gc
import os


class DuplicateRun(Exception):
	pass

class RunNotFound(Exception):
	pass

class Run:
	"""class to run benchmark runs and collect results

	Methods:
		benchmark_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=True, **kwargs) -> None: run benchmark run
		run_statistics(self, name: str) -> dict: return stats of run		
	"""
	def __init__(self):
		self.__results = {}

	def benchmark_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=True, **kwargs) -> None:
		"""runs benchmarks for given function benchmark

		Args:
			name (str): name of run, must be unique
			benchmark (Callable): function to benchmark
			setup (Callable | None, optional): setup function which is called once in beginning. Defaults to None.
			prerun (Callable | None, optional): setup function which is run once before every round of run. Defaults to None.
			rounds (int, optional): Amount of times benchmark should be called to measure for statistic. Defaults to 1.
			warmup_rounds (int, optional): amount of untracked warmup rounds for benchmark. Defaults to 0.
			gc_active(bool, optional): enable or disable garbage collection during benchmark. Defaults to True.
				Activating gives more "real world" results, while deactivating gives more reproducable results
			kwargs: arguments passed to setup, prerun and benchmark

		Raises:
			DuplicateRun: if benchmark with name was already called
		"""

		if name in self.__results:
			raise DuplicateRun(f'Run named {name} already exists. Choose a unique name')

		print(f'Starting Run {name}')

		if 'kwargs' in kwargs:
			kwargs = kwargs['kwargs']
		else:
			kwargs = {}

		def startup():
			# reset cpu affinity which is set by process pool
			pid = os.getpid()
			p = psutil.Process(pid)
			p.cpu_affinity(list(range(psutil.cpu_count())))

			# run setup		
			if setup is not None:
				setup(**kwargs)
			
			# run warm up rounds
			for _ in range(warmup_rounds):
				if prerun is not None:
					prerun(**kwargs)
				benchmark(**kwargs)

			gc.collect()

			return pid

		def run_prerun():
			if prerun is not None:
				prerun(**kwargs)
			gc.collect()

		def run_function():
			# disable garbage collection if set to do so
			if not gc_active:
				gc.disable()

			start = time.time()
			benchmark(**kwargs)
			t = time.time() - start

			# enable gc after run to return back to normal for prerun function of next round
			if not gc_active:
				gc.enable()

			return t

		# set starting process to spawn instead of fork
		# otherwise there might be issues with CUDA if used in the benchmark function
		mp.set_start_method('spawn', force=True)

		with pp._ProcessPool(1) as pool:
			# set start method back to fork since otherwise there might be an explosion
			# of memory usage if new processes get spawned inside callables
			mp.set_start_method('fork', force=True)

			pid = pool.apply(startup)
			collector = Collector(pid)

			times = [None] * rounds
			for i in range(rounds):
				pool.apply(run_prerun)
				with collector:
					times[i] = pool.apply(run_function)

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

	def create_graphs(self, name: str, path: Path | str, benchmark_name: str | None=None) -> None:
		"""given name of run, creates graphs to illustrate results

		Args:
			name (str): name of run
			path (Path | str): path where to save results
			benchmark_name (str | None, optional): name of benchmark of which run is part of. Defaults to None.
		"""
		path = Path(path)
		Illustrator.illustrate_results(self.run_statistics(name), path, benchmark_name, name)

	def __print_results(self, name: str) -> None:
		if name not in self.__results:
			raise RunNotFound(f'Results of run {name} not found')

		t = PrettyTable(['System Component', 'Max.', 'Mean', 'Std. Dev.', '25th perc.', '50th perc.', '75th perc.', '90th perc.', '95th perc.', '99th perc.'])
		t.add_row(['CPU (%) ', *self.__results[name]['cpu']['total'].values()])
		t.add_row(['RAM (MiB)', *(np.round(np.array(list(self.__results[name]['ram']['total'].values())) / 1024**2, 2))])
		t.add_row(['Time (Seconds)', *self.__results[name]['time']['total'].values()])
		print(t)
