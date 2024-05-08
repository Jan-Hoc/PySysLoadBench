from .run import Run
from copy import deepcopy
import platform
import psutil
import cpuinfo
import subprocess
from typing import Callable

class DuplicateBenchmark(Exception):
	pass

class Benchmark:
	__benchmarks = []

	def __init__(self, name: str):
		if name in Benchmark.__benchmarks:
			raise DuplicateBenchmark(f'Benchmark {name} already exists')
		Benchmark.__benchmarks.append(name)
		self.__name = name
		self.__run = Run()
		self.__runs = []
		self.__sysinfo = self.__gather_sysinfo()

	def __del__(self):
		pass

	def add_run(self, name: str, benchmark: Callable, setup: Callable | None=None, prerun: Callable | None=None, rounds: int=1, warmup_rounds: int=0, gc_active: bool=False, **kwargs) -> None:
		self.__run.benchmark_run(name, benchmark, setup, prerun, rounds, warmup_rounds, gc_active, kwargs)
		self.__runs.append(name)

	def run_statistics(self, name: str) -> dict:
		return self.__run.run_statistics(name)

	def statistics(self) -> dict:
		res = {}
		for run in self.__runs:
			res[run] = self.__run.run_statistics(run)
		return res

	def get_sysinfo(self) -> dict:
		return deepcopy(self.__sysinfo)

	def __gather_sysinfo(self) -> dict:
		sysinfo = {}
		sysinfo['python_version'] = platform.python_version()
		sysinfo['platform'] = platform.platform()
		sysinfo['operating_system'] = platform.uname().version
		sysinfo['host_name'] = platform.node()
		sysinfo['cpu'] = cpuinfo.get_cpu_info()['brand_raw'] if 'linux' in sysinfo['platform'].lower() else 'not found'
		raw_gpu_res = subprocess.check_output('nvidia-smi -L', shell=True).decode('ascii')
		sysinfo['gpu'] = '' if 'not found' in raw_gpu_res else raw_gpu_res.split(':', 1)[1].split('(')[0].strip()
		sysinfo['ram'] = str(round(psutil.virtual_memory().total / (1024.0**3), 4)) + " GB"
		return sysinfo

b = Benchmark('test')