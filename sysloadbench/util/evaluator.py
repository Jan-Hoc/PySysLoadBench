import numpy as np

class NoDataPoints(Exception):
	pass
class WrongDimensionality(Exception):
	pass

class Evaluator:
	"""dlass to offer different methods needed for evaluations
	
	Methods
    -------
    calculate_statistics(data, percentiles, precision):
        returns the statistics of the given data with the keys
		- max: maximum
		- mean: mean
		- stddev: standard deviation
		- x: x'th percentile for x in [25, 50, 75, 90, 95, 99] (x as int)
	"""

	def calculate_statistics(data: list, percentiles: list=[25, 50, 75, 90, 95, 99], precision: int=2) -> dict:
		"""given list of data points, calculate the max, mean, standard deviation (stddev) and percentiles. 
		return calculated statistics as a dictionary

		Args:
			data (list): 2D or 1D list of numerical data points (2D if list of runs), with at least one data point
			percentiles (list | None, optional): list of percentiles to include in statistics. Defaults to [25, 50, 75, 90, 95, 99]
			precision (int, optional):number of decimal points to round to. Defaults to 2

		Returns:
			dict: If 'data' is 1D: dict with calculated values and following keys
					- max: maximum
					- mean: mean
					- stddev: standard deviation
					- x: x'th percentile for x in percentiles (x as int)
				If 'data' ist 2D: dict where keys are run number (as int, starting at 0) + 'total', where each value is as above in 1D case.
				Returned are statistics per run / overall if key is 'total'

		Raises:
			NoDataPoints: if data is emtpy list or sublist of data is empty
			WrongDimensionality: if data is not 1D or 2D list
		"""

		if len(data) == 0:
			raise NoDataPoints('Empty list of data points given, need at least 1 data point')

		# 2D case:
		if isinstance(data[0], list):
			# make sure it is only 2D
			if len(data[0]) == 0:
				raise NoDataPoints('Empty list of data points given, need at least 1 data point')
			if isinstance(data[0][0], list):
				raise WrongDimensionality('Given list of data points is not 1D or 2D')

			stats = {}
			for i, d in enumerate(data):
				stats[i] = Evaluator.__calc_run(d, percentiles, precision)

			total_data = [run['mean'] for run in list(stats.values())]
			stats['total'] = Evaluator.__calc_run(total_data, percentiles, precision)

		else:
			stats = Evaluator.__calc_run(data, percentiles, precision)

		return stats

	def __calc_run(data: list, percentiles: list, precision: int) -> dict:
		"""unternal helper function to calculate statistics for a single run

		Args:
			data (list): 1D list with data points of run
			percentiles (list): percentiles to include in statistics
			precision (int): number of decimal points to round to

		Returns:
			dict: dict with calculated values and following keys
				- max: maximum
				- mean: mean
				- stddev: standard deviation
				- x: x'th percentile for x in percentiles (x as int)
		"""

		if len(data) == 0:
			raise NoDataPoints('Empty list of data points given, need at least 1 data point')

		stats = {}
		stats['max'] = float(round(np.max(data), precision))
		stats['mean'] = float(round(np.mean(data), precision))
		stats['stddev'] = float(round(np.std(data), precision))
		for p in percentiles:
			stats[p] = float(round(np.percentile(data, p), precision))

		return stats