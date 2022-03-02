import gurobipy as gp
from typing import List
import numpy as np
from optimizer.DS_layout import Layout
from optimizer.DS_utils import print_list
from optimizer.DS_feature import FeatureType, Feature
from collections.abc import Iterable
from optimizer.DS_unit import WorkingStationUnit, Unit
from optimizer.DS_calculations import calculate_adjacency_vars, calculate_entrance_distance, calculate_distance_to_point, \
	calculate_partitions_occupied_by


class Objective:
	"""
	Base Objective class. All objective must inherit from this one.
	"""
	def __init__(self, hierarchy=0, weight=1, **kwargs):
		self.weight = weight
		self.hierarchy = hierarchy
		self.signature = 'GenericObjective'

		self.parameters = kwargs

	def __str__(self):
		offset = "\t\t\t"
		str_ = f"{self.signature}\n"
		for key, val in self.parameters.items():
			if isinstance(val, list):
				str_ += print_list(val, n_columns=8, title=f"{key}:", offset=offset)
			else:
				str_ += offset + f"{key}:  {'None' if val is None else val}\n"
		str_ += f"{'-' * 20}\n"
		return str_[:-1]


class ObjectiveMagnetization(Objective):
	"""
	apply method returns the average distance between units and features
	"""
	def __init__(self, layout, units, features=None, hierarchy=0, weight=1):
		super(ObjectiveMagnetization, self).__init__(hierarchy, weight, layout=layout, units=units, features=features)
		self.signature = "Objective-Magnetization"

		self.layout = layout
		self.units = units
		self.features = features

	def apply(self, model, variables=None):
		"""
		@param model:
		@param variables:
		@return: average distance between units and features
		"""
		funcs = []
		if self.features is None:
			for i, unit1 in enumerate(self.units):
				for unit2 in self.units[i + 1:]:
					funcs.append(self.apply_units(unit1, unit2))
		else:
			for unit in self.units:
				if self.features[0].type == FeatureType.Entrance:
					funcs.extend(self.apply_unit_entrances(model, unit, self.features))
				else:
					funcs.append(self.apply_unit_features(unit, self.features, variables))

		n_feature_types = len(set([f.type for f in self.features]))
		normalization_factor = n_feature_types * len(self.units)
		return self.weight * gp.quicksum(funcs) / normalization_factor

	def apply_units(self, unit1, unit2):
		raise NotImplementedError

	@staticmethod
	def apply_unit_features(unit, features, variables):
		obj_func = 0
		enabled = unit.enabled if isinstance(unit, WorkingStationUnit) else 1
		for feature_type in set([f.type for f in features]):
			min_dist = variables[(unit.name, feature_type)]["min-dist"]
			for dist in [min_dist] if not isinstance(min_dist, list) else min_dist:
				obj_func += (enabled * dist)
		return obj_func

	def apply_unit_entrances(self, model, unit, features, variables=None):
		if variables is not None and (unit.name, FeatureType.Entrance.name) in variables and \
			"distances" in variables[(unit.name, FeatureType.Entrance.name)] :
			distances_dict = variables[(unit.name, FeatureType.Entrance.name)]
		else:
			distances_dict = calculate_entrance_distance(model, self.layout, unit, features)
			if variables is not None:
				if (unit.name, FeatureType.Entrance.name) in variables:
					variables[(unit.name, FeatureType.Entrance.name)]["distances"] = distances_dict
				else:
					variables[(unit.name, FeatureType.Entrance.name)] = {"distances": distances_dict}
		return [val for key, val in distances_dict.items()]


class ObjectiveEnlarge(Objective):
	def __init__(self, layout: Layout, units: List[Unit],
	             orthogonal: bool = False, hierarchy: int = 0, weight: float = 1):
		"""
		Returns a normalized distance
		Calling the method self.apply will return a term to be summed in the objective function
		@param layout: object of type Layout.  We
		@param units: list of units to be expanded
		@param orthogonal: flag. Whether to expand in one direction or both
		@param hierarchy: for future updates. Represents the order of sequential optimization
		@param weight: Value multiplying the whole term of the objective function
		"""
		super(ObjectiveEnlarge, self).__init__(hierarchy, weight, layout=layout, units=units, orthogonal=orthogonal)
		self.signature = "Objective-Enlarge"

		self.layout = layout
		self.units = units
		self.orthogonal = orthogonal

	def apply(self, model, variables=None):
		"""
		Computes the
		@param model: Unused - For compatibility only
		@param variables: Unused - For compatibility only
		@return: Normalized distance. Value between 0 and 1. If the unit is the biggest it can be, value will be 1
		"""
		if self.orthogonal:
			sizes = []
			for u in self.units:
				for i, p in enumerate(self.layout.get_partitions()):
					orthogonal_size = (p.w >= p.h) * u.h / np.max(u.range_h) + (p.h >= p.w) * u.w / np.max(u.range_w)
					sizes.append(-u.part_ind[i] * orthogonal_size)
		else:
			sizes = [-0.5 * u.w / np.max(u.range_w) - 0.5 * u.h / np.max(u.range_h) for u in self.units]

		return self.weight * gp.quicksum(sizes) / len(self.units)


class ObjectiveEnlargeWorkingStation(Objective):
	"""
	Working stations may be disabled, as they can grow and hold more places (people).
	This objective term minimizes the number of enabled units (maximizes the number of disabled units), and thus, tries
	to keep as few working stations as possible, and thus, each one is as big WS as possible
	"""
	def __init__(self, units, hierarchy=0, weight=1):
		assert all([isinstance(u, WorkingStationUnit) for u in units]), "This objective only works with WorkingStations (A00)"
		super(ObjectiveEnlargeWorkingStation, self).__init__(hierarchy, weight, units=units)
		self.signature = "Objective-EnlargeWorkStation"
		self.units = units

	def apply(self, model, variables=None):
		"""
		Tries to get fewer units, each one of them bigger
		@return: objective function term, between 0 and 1.
			1 means all units are enabled, and therefore has the minimum capacity
			lower values means fewer units enabled, and thus bigger units

		Note: the term below has no effect. 1 unit of 8 equals 2 units of 4  --> 1 x stacked=4 == 2 x stacked == 2
			term = -weight * gp.quicksum([u.stacked for u in units])
		"""
		return self.weight * gp.quicksum([u.enabled for u in self.units]) / len(self.units)


class ObjectiveCentralize(Objective):
	"""
	This objective tries to position units as closest to the center as possible
	"""
	def __init__(self, units, layout, dist_type="l1", hierarchy=0, weight=1):
		assert dist_type in ["l2", "l1"], f"{dist_type} not supported as distance type. It must be 'l1' or 'l2'"
		super(ObjectiveCentralize, self).__init__(hierarchy, weight, units=units, layout=layout, dist_type=dist_type)
		self.signature = "Objective-Centralize"
		self.units = units
		self.layout = layout
		self.dist_type = dist_type

	def apply(self, model, variables=None):
		"""
		@param model:
		@param variables:
		@return: Average normalized distance from all units to the center of the layout
		"""
		center_distances = []
		max_dist = np.max([self.layout.w, self.layout.h]) / 2
		for unit in self.units:
			dist = self.calculate_distance_to_center(model, unit)
			center_distances.append(dist)

			if variables is not None:
				if (unit.name, "center") not in variables:
					variables[(unit.name, "center")] = {f"distance-{self.dist_type}": dist}
				elif f"distance-{self.dist_type}" not in variables[(unit.name, "center")]:
					variables[(unit.name, "center")][f"distance-{self.dist_type}"] = dist

		return self.weight * gp.quicksum(center_distances) / max_dist / len(self.units)

	def calculate_distance_to_center(self, model, unit):
		return calculate_distance_to_point(model, self.layout, unit, [self.layout.w / 2, self.layout.w / 2], self.dist_type)


# Unused: Check normalization before start using it
# class ObjectiveGroupByPartition(Objective):
# 	def __init__(self, layout, units, hierarchy=0, weight=1):
# 		super(ObjectiveGroupByPartition, self).__init__(hierarchy, weight, layout=layout, units=units)
# 		self.signature = "Objective-GroupByPartition"
#
# 		self.layout = layout
# 		self.units = units
#
# 	def apply(self, model, variables=None):
# 		objFuncs = []
# 		unit_type = self.units[0].type
# 		for i, partition in enumerate(self.layout.get_partitions()):
# 			if variables is not None and \
# 					(partition.ind, unit_type) in variables and "is-occupated" in variables[(partition.ind, unit_type)]:
# 				occ_partition = variables[(partition.ind, unit_type)]["is-occupated"]
# 			else:
# 				occ_partition = calculate_partitions_occupied_by(model, self.layout, self.units)[1]
#
# 			objFuncs.append(occ_partition)
#
# 			# Saving variables
# 			if variables is not None:
# 				if (partition.ind, unit_type) not in variables:
# 					variables[(partition.ind, unit_type)] = {"is-occupated": occ_partition}
# 				else:
# 					variables[(partition.ind, unit_type)]["is-occupated"] = occ_partition
#
# 		return self.weight * gp.quicksum(objFuncs)


class ObjectiveGroup(Objective):
	def __init__(self, units, hierarchy=0, weight=1):
		super(ObjectiveGroup, self).__init__(hierarchy, weight, units=units)
		self.signature = "Objective-Group"

		self.units = units

	def apply(self, model, variables=None):
		adj_vars = []
		n_combinations = 0
		for i, unit1 in enumerate(self.units):
			for unit2 in self.units[i+1:]:
				n_combinations += 1
				if variables is not None and (unit1.name, unit2.name) in variables and \
					"adjacency" in variables[(unit1.name, unit2.name)]:
					adj_var = variables[(unit1.name, unit2.name)]["adjacency"]["adjacency-var"]
				else:
					same_partition, adj_var, [r, l, a, b] = \
						calculate_adjacency_vars(model, unit1, unit2, variables).values()

					dict_to_save = {"adjacency-var": adj_var, "left": r, "right": l, "above": a, "below": b}
					if variables is not None:
						if (unit1.name, unit2.name) not in variables:
							variables[(unit1.name, unit2.name)] = {"adjacency": dict_to_save}
						else:
							variables[(unit1.name, unit2.name)]["adjacency"] = dict_to_save

				adj_vars.append(adj_var)

		try:
			return -self.weight / n_combinations * gp.quicksum(adj_vars)
		except ZeroDivisionError:
			return 0

# TODO: All code to check if variables exist and return them or compute/save/return them, must be in an aux function
