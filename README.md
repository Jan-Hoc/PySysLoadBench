# PySysLoadBench
Benchmarking framework for Python to measure the system load and execution time of functions.

## Table of Contents
- [Overview](#overview)
- [Usage](#usage)
   * [Installation](#installation)
   * [Parameters](#parameters)
   * [Calculated Metrics](#calculated-metrics)
   * [Best Practices](#best-practices)
- [Examples](#examples)
   * [Run Class](#run-class)
   * [Benchmark Class](#benchmark-class)

## Overview
PySysLoadBench is a package, which allows you to benchmark functions with a special focus on system metrics. These include CPU load, RAM utilization. Further, the execution time is measured. Out of these, statistics are generated, such as the mean, max, standard deviation and various percentiles. The CPU and RAM utilization is sampled once every 0.05 seconds. CPU and RAM used by child processes, created by your benchmarked function, are also measured.

For additional isolation and more precise results, a new process is created for every run. However, the individual rounds in a run are executed in the same process. This allows for imports and defining global variables in a setup function, which can be used later. It also allows you to (de-)activate garbage collection, depending on your priorities (see `gc_active` in [Parameters](#parameters)). Garbage collection is also called before the execution of `benchmark` in every round to allow for more reproducible and accurate RAM measurements.

Be aware that the measurement process is created using `spawn` and not `fork`, since forking processes might lead to issues if CUDA is used in the functions which are benchmarked, as well as somewhere in the parent process. However, the start method is then set back to the default (for UNIX systems) `fork` to avoid any unexpected behavior, if new processes are created in the benchmarked function.

## Usage

### Installation
Install the package using `pip`
```
pip install git+https://github.com/Jan-Hoc/PySysLoadBench.git@v0.1.0
```

### Parameters
You have two options to use this benchmark. You can use the `Run` class, with which you can benchmark functions, retrieve the calculated statistics and generate graphs for the individual runs, displaying CPU, RAM and timing results in the console and generating graphs. The other option is the `Benchmark` class. This offers the possibility to gather several runs, return their statistics, save these into a JSON, including some system information, and also generate graphs according to the results of the different runs. See [examples](#examples) for their use.

When doing a run, either over `Run` or `Benchmark`, you have the following parameters you can set:

| Parameter Name | Type(s) | Default | Description |
| :---: | :---: | :---: | :---: |
| `name` | `str` | X | name of the run <br> must be unique for the `Benchmark` or `Run` object |
| `benchmark`| `Callable` | X | function, which should be benchmarked <br> must take arguments passed through `kwargs` |
| `setup` | `Callable`, `None` | `None` | function, which is called once at the start of the run <br> it's execution is not measured <br> must take arguments passed through `kwargs` |
| `prerun` | `Callable`, `None` | `None` | function, which is called before every execution of `benchmark` <br> it's execution is not measured <br> must take arguments passed through `kwargs` |
| `rounds` | `int` | `1` | amount of rounds for which `benchmark` should be executed <br> a higher amount of rounds gives more reliable results but takes more time | 
| `warmup_rounds` | `int` | `0` | amount of not measured warmup rounds at the beginning of the run <br> these rounds are also executed after `setup` is executed |
| `gc_active` | `bool` | `True` | `False` if garbage collection should be deactivated during single executions of `benchmark` <br> allows for more reproducible time measurements <br> activating it allows for more realistic system load metrics |
| `kwargs` | `dict`, `None` | `None` | dictionary of arguments, which are passed to `benchmark`, `setup` and `prerun` |


### Calculated Metrics
For timing, CPU and RAM the maximum value, the mean, the standard deviation, the 25th, 50th, 75th, 90th, 95th and 99th percentiles are calculated over the different rounds. 

Additionaly these metrics are also returned/saved for the individual rounds for the RAM and CPU measurements.

The metrics are also displayed in graphs, a seperate graph for timing, CPU load and RAM utilization as well as every run.

### Best Practices
- Do not run other programs on your system during benchmarking to allow for the most accurate results
- Use `setup` for any initializations which should not be measured and are only needed to be executed once
- Use `prerun` for any setup or cleanup which should be done for `benchmark`, but should not be measured (e.g. resetting or initializing global variables)
- Since garbage collection is called before any run of `benchmark`, ensure you delete unused variables in `setup` and `prerun` to profit from more accurate measurements of RAM
- Beware that maybe due to caching the first round might take longer than the following. Keep this in mind when deciding to use warmup rounds or not
- Run the benchmark for multiple rounds to average out potential inconsistencies
- Make sure the benchmarked function doesn't complete too quickly, since otherwhise due to the sampling interval, the system metrics will be inaccurate

## Examples
### Run Class
```python
from sysloadbench import Run

def example_func(x: int):
	l = []
	for i in range(x):
		l.append(i)

args = {'x': 1000000}

r = Run()
r.benchmark_run('run_example_func' , example_func, rounds=100, warmup_rounds=2, kwargs=args)

# return statistics of the run
stats = r.run_statistics('run_example_func')
# generate graphs for statistics
r.create_graphs('run_example_func', './benchmark_graphs')
```

### Benchmark Class
```python
from sysloadbench import Benchmark

def example_func_1(x: int):
	l = []
	for i in range(x):
		l.append(i)

def example_setup_2():
	import numpy as np

def example_func_2(x: int):
	l = np.array([])
	for i in range(100000):
		l = np.append(l, i)

args = {'x': 1000000}

b = Benchmark('Test Benchmark')
# example 1 without a setup function
b.add_run('Run example_func_1' , example_func_1, rounds=100, warmup_rounds=2, kwargs=args)

# retrieve statistics of just that run
stats_1 = b.run_statistics('Run example_func_1')

# example 2 including a setup function
b.add_run('Run example_func_2' , example_func_2, example_setup_2, rounds=100, warmup_rounds=2, kwargs=args)

# retrieve statistics of all runs
stats_all = b.statistics()

# save statistics and graphs to Path.cwd()/sysloadbench_results/<benchmark name> 
b.save_results()
```
