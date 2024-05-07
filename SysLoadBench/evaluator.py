import numpy as np

class Evaluator:
	"""Class to offer different methods needed for evaluations
	"""
	__percentiles = [25, 50, 75, 90, 95, 99]

	def calculate_statistics(data: list, percentiles: list | None=None) -> dict:
		"""Given list of data points, calculate the max, mean, standard deviation (stddev) and percentiles. 
		return calculated statistics as a dictionary

		Args:
			data (list): list of numerical datapoints
			percentiles (list | None, optional): List of percentiles to include in statistics.
				If None given, chooses [25, 50, 75, 90, 95, 99]

		Returns:
			dict: dict with calculated values
		"""
		if percentiles is None:
			percentiles = Evaluator.__percentiles
		
		stats = {}
		stats['max'] = np.max(data)
		stats['mean'] = round(np.mean(data), 2)
		stats['stddev'] = round(np.std(data), 2)
		for p in percentiles:
			stats[str(p)] = round(np.percentile(data, p), 2)

		return stats