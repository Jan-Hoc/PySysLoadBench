import numpy as np

class Evaluator:
	"""Class to offer different methods needed for evaluations
	
	Methods
    -------
    calculate_statistics(data, percentiles, precision):
        returns the statistics of the given data with the keys
		- max: maximum
		- mean: mean
		- stddev: standard deviation
		- x: x'th percentile for x in [25, 50, 75, 90, 95, 99]
	"""

	def calculate_statistics(data: list, percentiles: list=[25, 50, 75, 90, 95, 99], precision: int=2) -> dict:
		"""Given list of data points, calculate the max, mean, standard deviation (stddev) and percentiles. 
		return calculated statistics as a dictionary

		Args:
			data (list): list of numerical datapoints
			percentiles (list | None, optional): list of percentiles to include in statistics. Defaults to [25, 50, 75, 90, 95, 99]
			precision (int, optional): to how many decimal points will the results be rounded. Defaults to 2

		Returns:
			dict: dict with calculated values and following keys
				- max: maximum
				- mean: mean
				- stddev: standard deviation
				- x: x'th percentile for x in percentiles
		"""
		
		stats = {}
		stats['max'] = round(np.max(data), precision)
		stats['mean'] = round(np.mean(data), precision)
		stats['stddev'] = round(np.std(data), precision)
		for p in percentiles:
			stats[str(p)] = round(np.percentile(data, p), precision)

		return stats