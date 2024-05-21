from .run import Run
from copy import deepcopy
import platform
import psutil
import cpuinfo
import subprocess
from typing import Callable
from pathlib import Path
import json

class DuplicateBenchmark(Exception):
	pass

class Benchmark:
	"""class to batch runs into benchmark, save results and handle user interaction

	Attributes:
		name (str): name of benchmark

	Methods:
		add_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=True, **kwargs) -> None: adds a run to the current benchmark
		run_statistics(self, name: str) -> dict: return statistics of specific run
		statistics(self) -> dict: return stats of all runs in benchmark
		get_sysinfo(self) -> dict: return gathered system information

	Raises:
		DuplicateBenchmark: Is raised if there currently is a benchmark with the same name, must be unique
	"""

	__benchmarks = []

	def __init__(self, name: str):
		if name in Benchmark.__benchmarks:
			raise DuplicateBenchmark(f'Benchmark {name} already exists')
		Benchmark.__benchmarks.append(name)
		self.__name = name
		self.__run = Run()
		self.__runs = []
		self.__sysinfo = self.__gather_sysinfo()

	def add_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=True, **kwargs) -> None:
		"""adds a run to the current benchmark

		Args:
			name (str): name of the run, needs to be unique in the benchmark
			benchmark (Callable): function to be benchmarked in the run
			setup (Callable | None, optional): setup function which is called once at run. Defaults to None.
			prerun (Callable | None, optional): function called once before the every run of benchmark. Defaults to None.
			rounds (int, optional): amount of rounds to run benchmark run for. Defaults to 1.
			warmup_rounds (int, optional):amount of warmup rounds to execture in run. Defaults to 0.
			gc_active (bool, optional): activate or deactivate garbage colletion using benchmark. Defaults to True.
				Activating gives more "real world" results, while deactivating gives more reproducable results
			kwargs: arguments passed to setup, prerun and benchmark
		"""

		self.__run.benchmark_run(name, benchmark, setup, prerun, rounds, warmup_rounds, gc_active, **kwargs)
		self.__runs.append(name)

	def run_statistics(self, name: str) -> dict:
		"""get the statistics of a specific run

		Args:
			name (str): name of the run

		Returns:
			dict: result of run as returned by run_statistics of Run class
		"""

		return self.__run.run_statistics(name)

	def statistics(self) -> dict:
		"""return all statistics of benchmark

		Returns:
			dict: dictionary where keys are run names and values are their corresponding statistics
		"""

		res = {}
		for run in self.__runs:
			res[run] = self.__run.run_statistics(run)
		return res

	def get_sysinfo(self) -> dict:
		"""return gathered system information, which is saved with benchmark results

		Returns:
			dict: system information with keys ['python_version', 'platform', 'operating_system', 'host_name', 'cpu', 'gpu', 'ram']
		"""

		return deepcopy(self.__sysinfo)


	def save_results(self, path: str | Path | None=None) -> None:
		"""saves results (if any) of benchmark runs into results folder (sysloadbench_results, or given Path)
		there is a subfolder for every host name in which the benchmark is saved by its name
		the results are saved in a JSON file and corresponding graphs
		if there are any previous benchmark results at the same location, they will be overwritten
		this function is also called in the object's __del__ function to avoid having unsaved results

		Args:
			path (str | Path | None): override default saving location. defaults to None
		"""
		# Do not save anything if there are no results
		if len(self.__runs) == 0:
			return

		if path is None:
			path = Path.cwd() / 'sysloadbench_results' / self.__name
		if isinstance(path, str):
			path = Path(path)
		
		path = path / self.__sysinfo['host_name']
		path.mkdir(parents=True, exist_ok=True)
		result_file_path = path / ('results.json')

		result_data = {'system_information': self.__sysinfo, 'run_results': self.statistics()}

		with open(result_file_path, 'w') as result_file: 
			json.dump(result_data, result_file, indent=4)

		path = path / 'graphs'
		for run_name in self.__runs:
			(path / run_name).mkdir(parents=True, exist_ok=True)
			self.__run.create_graphs(run_name, path / run_name, self.__name)

	def __gather_sysinfo(self) -> dict:
		"""helper function to gather system information

		Returns:
			dict: dict containing various gathered system information
		"""
		sysinfo = {}
		sysinfo['python_version'] = platform.python_version()
		sysinfo['platform'] = platform.platform()
		sysinfo['operating_system'] = platform.uname().version
		sysinfo['host_name'] = platform.node()
		sysinfo['cpu'] = cpuinfo.get_cpu_info()['brand_raw'] if 'linux' in sysinfo['platform'].lower() else 'not found'
		try:
			raw_gpu_res = subprocess.check_output('nvidia-smi -L', shell=True).decode('ascii')
			sysinfo['gpu'] = raw_gpu_res.split(':', 1)[1].split('(')[0].strip() if 'GPU' in raw_gpu_res else ''
		except:
			sysinfo['gpu'] = ''
		sysinfo['ram'] = str(round(psutil.virtual_memory().total / (1024.0**3), 4)) + " GB"
		return sysinfo