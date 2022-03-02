import gurobipy as gp
from gurobipy import GRB
from optimizer.DS_unit import Unit
from optimizer.DS_utils import print_list
from optimizer.DS_feature import Feature, FeatureType
from optimizer.DS_calculations import calculate_adjacency_vars, calculate_same_partition_unit_item, \
	calculate_distance_between_flat_features

MIN_CIRCULATION_CONTACT = 100


class Constraint:
	def __init__(self, hierarchy=0, **kwargs):
		self.hierarchy = hierarchy
		self.signature = "GenericConstraint"

		self.parameters = kwargs

	def __str__(self):
		offset = "\t\t\t"
		str_ = f"{self.signature}\n"
		for key, val in self.parameters.items():
			if isinstance(val, list):
				str_ += print_list(val, n_columns=8, title=f"{key}:", offset=offset)
			else:
				str_ += offset + f"{key}:  {'None' if val is None else val}\n"
		str_ += "---------------------------\n"
		return str_[:-1]


class ConstraintUniquePartition(Constraint):
	def __init__(self, layout, units, hierarchy=0):
		super(ConstraintUniquePartition, self).__init__(hierarchy)
		self.signature = "Constr-UniquePartition"

		self.units = units
		self.layout = layout

	def apply(self, model, variables=None):
		for unit in self.units:
			if unit.type == 'A00':
				model.addGenConstrIndicator(unit.enabled, True, gp.quicksum(unit.part_ind) == 1,
				                            name=unit.name + "_unique_partition")
			else:
				model.addConstr(gp.quicksum(unit.part_ind) == 1, name=unit.name + "_unique_partition")


class ConstraintNoIntersection(Constraint):
	def __init__(self, units, items=None, absorb=False, hierarchy=0):
		super(ConstraintNoIntersection, self).__init__(hierarchy, units=units, items=items, absorb=absorb)
		self.signature = "Constr-NoIntersection"

		self.units = units
		self.items = items
		self.absorb = absorb

	def apply(self, model, variables):
		if self.items is None:
			for i, unit1 in enumerate(self.units):
				for unit2 in self.units[i + 1:]:
					self.apply_to_single_unit(model, unit1, unit2, variables)
		else:
			for unit in self.units:
				for item in self.items:
					if item.name == unit.name:
						continue
					self.apply_to_single_unit(model, unit, item, variables)
				# if self.absorb:
				#     no_intersection_with_absorb2(model, unit, item, variables[(unit.name, item.name)])
				# else:

	@staticmethod
	def apply_to_single_unit(model, unit, item, variables=None):
		"""
			Implements no-intersection restriction between two items:
				Two units
				A unit and a Features
			Always taking into account if they are in the same partition
			model: Gurobi model
			item1: Unit
			item2: Unit or Feature
		"""
		assert isinstance(unit, Unit), "First element (unit) must be Unit"
		assert isinstance(item, Unit) or isinstance(item, Feature), "Second element (item) must be Unit or Feature"
		if isinstance(item, Feature):
			assert (item.type != FeatureType.Entrance) and (
					item.type != FeatureType.Window), "Feature must be Column, Circulation or Other"
			# If feature is not inside any partition: do nothing
			if item.part_idx is None:
				return None

		name = f"Constr-NoIntersection-({unit.name},{item.name})"
		# u1 left u2
		x1 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-left")
		model.addGenConstrIndicator(x1, True, unit.x + unit.w <= item.x,
									name=f"{name}:genConstrInd-left")
		# u2 left u1
		x2 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-right")
		model.addGenConstrIndicator(x2, True, item.x + item.w <= unit.x,
									name=f"{name}:genConstrInd-right")
		# u1 above u2
		x3 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-above")
		model.addGenConstrIndicator(x3, True, unit.y + unit.h <= item.y,
									name=f"{name}:genConstrInd-above")
		# u2 above u1
		x4 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-below")
		model.addGenConstrIndicator(x4, True, item.y + item.h <= unit.y,
									name=f"{name}:genConstrInd-below")

		# Auxiliary variable
		if variables is not None and \
				(unit.name, item.name) in variables and "same-partition" in variables[(unit.name, item.name)]:
			same_partition = variables[(unit.name, item.name)]["same-partition"]
		else:
			same_partition = calculate_same_partition_unit_item(model, unit, item)

		# Actual restriction
		model.addGenConstrIndicator(same_partition, True, x1 + x2 + x3 + x4 >= 1,
									name=f"{name}:genConstrInd-noIntersection")

		# Saving variables
		if variables is not None:
			dict_to_variables = {
				"same-partition": same_partition,
				"booleans": {"Left": x1, "Right": x2, "Above": x3, "Below": x4}
			}
			if (unit.name, item.name) not in variables:
				variables[(unit.name, item.name)] = {"no-intersect-with-absorb": dict_to_variables}
			else:
				variables[(unit.name, item.name)]["no-intersect-with-absorb"] = dict_to_variables


class ConstraintBelongPartitions(Constraint):
	def __init__(self, layout, units, hierarchy=0):
		super(ConstraintBelongPartitions, self).__init__(hierarchy, layout=layout, units=units)
		self.signature = "Constr-BelongPartitions"

		self.units = units
		self.layout = layout

	def apply(self, model, variables=None):
		partitions = self.layout.partitions
		for unit in self.units:
			self.apply_to_single_unit(model, unit)

			partition_width = gp.quicksum([unit.part_ind[i] * p.w for i, p in enumerate(partitions)])
			partition_height = gp.quicksum([unit.part_ind[i] * p.h for i, p in enumerate(partitions)])
			if unit.type == 'A00':
				model.addGenConstrIndicator(unit.enabled, True, unit.x + unit.w <= partition_width,
				                            name=f'unit_{unit.name} width bounded to partition')
				model.addGenConstrIndicator(unit.enabled, True, unit.y + unit.h <= partition_height,
				                            name=f'unit_{unit.name} height bounded to partition')
			else:
				model.addConstr(unit.x + unit.w <= partition_width, name=f'unit_{unit.name} width bounded to partition')
				model.addConstr(unit.y + unit.h <= partition_height, name=f'unit_{unit.name} height bounded to partition')

	@staticmethod
	def apply_to_single_unit(model, unit):
		if unit.type == 'A00':
			model.addGenConstrIndicator(unit.enabled, True, gp.quicksum(unit.part_ind) == 1,
			                            name=unit.name + "_unique_partition")
		else:
			model.addConstr(gp.quicksum(unit.part_ind) == 1, name=unit.name + "_unique_partition")


class ConstraintAdjacency(Constraint):
	def __init__(self, layout, units, items=None, hierarchy=0, same_rot=False):
		super(ConstraintAdjacency, self).__init__(hierarchy, layout=layout, units=units, items=items)
		self.signature = "Constr-Adjacency"

		self.units = units
		self.items = items
		self.layout = layout
		self.same_rot = same_rot

	def apply(self, model, variables=None):
		for i, unit in enumerate(self.units):
			if self.items is None:
				items = [u for u in self.units if u.name != unit.name]
			else:
				items = [i for i in self.items if i.name != unit.name]

			self.apply_unit_items(model, unit, items, variables)

	def apply_unit_items(self, model, unit, items, variables):
		if not items:
			return None

		name = f"{self.signature}({unit.name},{items[0].type})"
		adj_vars = []
		for i, item in enumerate(items):
			# Direct adjacency
			if variables is not None and (unit.name, item.name) in variables and \
					"adjacency" in variables[(unit.name, item.name)]:

				adj_var = variables[(unit.name, item.name)]["adjacency"]["adjacency-var"]
			else:
				same_partition, adj_var, [r, l, a, b] = calculate_adjacency_vars(model,
																				 unit,
																				 item,
																				 variables,
																				 self.same_rot
																				 ).values()
				# Saving variables
				dict_to_save = {
					"adjacency-var": adj_var,
					"left": r,
					"right": l,
					"above": a,
					"below": b,
				}
				if variables is not None:
					if (unit.name, item.name) not in variables:
						variables[(unit.name, item.name)] = {"adjacency": dict_to_save}
					else:
						variables[(unit.name, item.name)]["adjacency"] = dict_to_save
			adj_vars.append(adj_var)

		model.addConstr(gp.quicksum(adj_vars) >= 1, name=f"{name}:genConstrInd-adjacency")


class ConstraintAlignOrientation(Constraint):
	def __init__(self, layout, units, features, hierarchy=0):
		super(ConstraintAlignOrientation, self).__init__(hierarchy, layout=layout, units=units, features=features)
		self.signature = "Constr-AlignOrientation"

		self.units = units
		self.features = features
		self.layout = layout

	def apply(self, model, variables=None):
		alignments = {}
		for unit in self.units:
			for ftype in set([f.type for f in self.features]):
				self.apply_to_single_unit(model, unit, ftype, variables)

	def apply_to_single_unit(self, model, unit, ftype, variables):
		name = ftype.name + '-' + unit.name
		if variables is None or (unit.name, ftype) not in variables or \
				"rotation-closest" not in variables[(unit.name, ftype)]["rotation-closest"]:
			features = [f for f in self.features if f.type == ftype]
			min_dist, rot_closest, same_part = calculate_distance_between_flat_features(model, self.layout, unit, features, variables)
		else:
			min_dist = variables[(unit.name, ftype)]["min-dist"]
			rot_closest = variables[(unit.name, ftype)]["rotation-closest"]
			same_part = variables[(unit.name, ftype)]["same-partition"]

		model.addConstr(unit.rot == rot_closest, name=name + "_Alignment")

		# Saving variables
		if variables is not None:
			dict_to_act = {"rotation-closest": rot_closest,
						   "min-dist": min_dist,
						   "same-partition": same_part}
			if (unit.name, ftype) not in variables:
				variables[(unit.name, ftype)] = {}
			for key, val in dict_to_act.items():
				variables[(unit.name, ftype)][key] = val


class ConstraintMakeItAccessible(Constraint):
	def __init__(self, layout, units, hierarchy=0):
		super(ConstraintMakeItAccessible, self).__init__(hierarchy, layout=layout, units=units)
		self.signature = "Constr-MakeItAccessible"

		self.units = units
		self.layout = layout

	def apply(self, model, variables=None):
		for unit in self.units:
			self.apply_in_single_unit(model, unit, variables)

	def apply_in_single_unit(self, model, unit, variables):
		circulations = self.layout.get_features(FeatureType.Circulation)
		if not circulations:
			return None

		name = f"{self.signature}({unit.name})"

		n_f = len(circulations)
		n_part = len(self.layout.partitions)
		adj_vars = model.addVars(n_f, vtype=GRB.BINARY, name=f"{name}:boolVars-adjacency")
		x1 = model.addVars(n_f, vtype=GRB.BINARY, name=f"{name}:boolVars-left-or-above")
		x2 = model.addVars(n_f, vtype=GRB.BINARY, name=f"{name}:boolVars-right-or-below")

		model.addConstr(gp.quicksum(adj_vars) >= 1, name=f'{name}:constr-adjacency')

		for i, circulation in enumerate(circulations):
			name_ = f"{self.signature}({unit.name},{circulation.name})"
			if circulation.part_idx is None:
				model.addConstr(adj_vars[i] == 0, name=f'{name_}:constr-inaccessible-circulation')
				continue

			if variables is None or (unit.name, circulation.name) not in variables or \
					"same-partition" not in variables[(unit.name, circulation.name)]:
				same_partition = gp.quicksum([unit.part_ind[idx] for idx in circulation.part_idx])
			else:
				same_partition = variables[(unit.name, circulation.name)]["same-partition"]

			pos_rel = [
				gp.quicksum([circulation.relative_info[k]["position"][0] * unit.part_ind[k] for k in range(n_part)]),
				gp.quicksum([circulation.relative_info[k]["position"][1] * unit.part_ind[k] for k in range(n_part)])]

			model.addGenConstrIndicator(adj_vars[i], True, same_partition == 1,
										name=f'{name_}:genConstrInd-adjacency>>same-partition')
			model.addGenConstrIndicator(adj_vars[i], True, x1[i] + x2[i] >= 1,
										name=f'{name_}:genConstrInd-adjacency')

			if circulation.w <= circulation.h:  # Vertical
				if unit.range_w[0] > unit.range_h[0]:
					model.addGenConstrIndicator(adj_vars[i], True, unit.rot == 0)
				else:
					model.addGenConstrIndicator(adj_vars[i], True, unit.rot == 1)

				model.addGenConstrIndicator(x1[i], True, unit.x + unit.w == pos_rel[0],
											name=f'{name_}:genConstrInd-left')
				model.addGenConstrIndicator(x2[i], True, unit.x == pos_rel[0] + circulation.w,
											name=f'{name_}:genConstrInd-right')
				model.addGenConstrIndicator(adj_vars[i], True, unit.y + MIN_CIRCULATION_CONTACT <= pos_rel[1] + circulation.h,
											name=f'{name_}:genConstrInd-adjacency>>inRange1')
				model.addGenConstrIndicator(adj_vars[i], True, unit.y + unit.h - MIN_CIRCULATION_CONTACT >= pos_rel[1],
											name=f'{name_}:genConstrInd-adjacency>>inRange2')
			else:  # Horizontal
				if unit.range_w[0] > unit.range_h[0]:
					model.addGenConstrIndicator(adj_vars[i], True, unit.rot == 1)
				else:
					model.addGenConstrIndicator(adj_vars[i], True, unit.rot == 0)
				model.addGenConstrIndicator(x1[i], True, unit.y + unit.h == pos_rel[1],
											name=f'{name_}:genConstrInd-above')
				model.addGenConstrIndicator(x2[i], True, unit.y == pos_rel[1] + circulation.h,
											name=f'{name_}:genConstrInd-below')
				model.addGenConstrIndicator(adj_vars[i], True, unit.x + MIN_CIRCULATION_CONTACT <= pos_rel[0] + circulation.w,
											name=f'{name_}:genConstrInd-adjacency>>inRange1')
				model.addGenConstrIndicator(adj_vars[i], True, unit.x + unit.w - MIN_CIRCULATION_CONTACT >= pos_rel[0],
											name=f'{name_}:genConstrInd-adjacency>>inRange2')

			if variables is not None:
				dict_to_variables = {
					"same-partition": same_partition,
					"booleans": {"adjacency": adj_vars[i],
								 "left-or-above": x1[i],
								 "right-or-below": x2[i]
								 }
				}
				if (unit.name, circulation.name) not in variables:
					variables[(unit.name, circulation.name)] = dict_to_variables
				else:
					for k, v in dict_to_variables.items():
						variables[(unit.name, circulation.name)][k] = v


class ConstraintSetNumberOfWorkstations(Constraint):
	def __init__(self, layout, units, number_workstations, hierarchy=0):
		super(ConstraintSetNumberOfWorkstations, self).__init__(hierarchy,
																layout=layout,
																units=units,
																number_workstations=number_workstations)
		self.signature = "Constraint-SetNumberOfWorkstations"

		self.units = units
		self.layout = layout
		self.n_workstations = number_workstations

	def apply(self, model, variables=None):
		n_workstation_0 = sum([2 for u in self.units if u.type == 'A01']) + \
						  sum([4 for u in self.units if u.type == 'A02'])
		a00s = [u for u in self.units if u.type == 'A00']
		n_workstation_adaptable = gp.quicksum([2 * a00.stacked for a00 in a00s])

		model.addConstr(n_workstation_0 + n_workstation_adaptable == self.n_workstations)

		# Saving variables
		if variables is not None:
			dict_to_variables = {
				"number_workstations_fixed": n_workstation_0,
				"number_workstations_adaptable": n_workstation_adaptable
			}
			variables[f"{self.signature}"] = dict_to_variables


class ConstraintSetReceptionToEntrance(Constraint):
	def __init__(self, layout, unit, entrances, hierarchy=0):
		super(ConstraintSetReceptionToEntrance, self).__init__(hierarchy,
															   layout=layout,
															   unit=unit,
															   entrances=entrances)
		self.signature = "Constraint-SetReceptionToEntrance"

		self.unit = unit
		self.layout = layout
		self.entrances = entrances

	def apply(self, model, variables=None):
		assert self.entrances, "No entrances were provided"
		name = f"{self.signature}({self.unit.name})"

		n = len(self.entrances)
		partitions = self.layout.partitions
		n_part = len(partitions)
		adj_vars = model.addVars(n, vtype=GRB.BINARY, name=f"{name}:boolVar-adjacency")
		adj_circulations = [None for a in adj_vars]
		x1 = [None for a in adj_vars]
		x2 = [None for a in adj_vars]
		model.addConstr(gp.quicksum(adj_vars) >= 1, name=f"{name}:genConstrInd-adjacency-to-some-entrance")

		for i, entrance in enumerate(self.entrances):
			name_ = f"{self.signature}({self.unit.name},{entrance.name})"

			# Checking the circulation in contact with the entrance
			circulations = [c for c in self.layout.features if c.type == FeatureType.Circulation
							and entrance.is_in_contact(c, oriented=False)]
			if not adj_circulations:
				print(f"WARNING: The entrance {entrance.name} is not referred to any circulation")
				continue

			# Centering
			center = [gp.quicksum([entrance.relative_info[k]["center"][0] * self.unit.part_ind[k]
								   for k, p in enumerate(partitions)]),
					  gp.quicksum([entrance.relative_info[k]["center"][1] * self.unit.part_ind[k]
								   for k, p in enumerate(partitions)])]

			# TODO: Tidy
			THR = 500
			if entrance.w > entrance.h:
				model.addGenConstrIndicator(adj_vars[i], True, self.unit.x + 0.5 * self.unit.w - center[0] <= THR,
											name=f"{name}:genConstrInd-centering")
				model.addGenConstrIndicator(adj_vars[i], True, self.unit.x + 0.5 * self.unit.w - center[0] >= -THR,
											name=f"{name}:genConstrInd-centering")
			else:
				model.addGenConstrIndicator(adj_vars[i], True, self.unit.y + 0.5 * self.unit.h - center[1] <= THR,
											name=f"{name}:genConstrInd-centering")
				model.addGenConstrIndicator(adj_vars[i], True, self.unit.y + 0.5 * self.unit.h - center[1] >= -THR,
											name=f"{name}:genConstrInd-centering")

			# Make contact with the circulations
			adj_circulations[i] = model.addVars(len(circulations), vtype=GRB.BINARY)
			x1[i] = model.addVars(len(circulations), vtype=GRB.BINARY)
			x2[i] = model.addVars(len(circulations), vtype=GRB.BINARY)
			model.addGenConstrIndicator(adj_vars[i], True, gp.quicksum(adj_circulations[i]) >= 1,
										name=f"{name_}:genConstrInd-adjacency>>adj-circulation")

			for j, circulation in enumerate(circulations):
				name__ = f"{self.signature}({self.unit.name},{circulation.name})"
				if circulation.part_idx is None:
					model.addConstr(adj_circulations[i][j] == 0, name=f'{name__}:constr-inaccessible-circulation')
					continue

				if variables is None or (self.unit.name, circulation.name) not in variables or \
						"same-partition" not in variables[(self.unit.name, circulation.name)]:
					same_partition = gp.quicksum([self.unit.part_ind[idx] for idx in circulation.part_idx])
				else:
					same_partition = variables[(self.unit.name, circulation.name)]["same-partition"]

				pos_rel = [
					gp.quicksum(
						[circulation.relative_info[k]["position"][0] * self.unit.part_ind[k] for k in range(n_part)]),
					gp.quicksum(
						[circulation.relative_info[k]["position"][1] * self.unit.part_ind[k] for k in range(n_part)])]

				model.addGenConstrIndicator(adj_circulations[i][j], True, same_partition == 1,
											name=f'{name__}:genConstrInd-adjacency>>same-partition')
				model.addGenConstrIndicator(adj_circulations[i][j], True, x1[i][j] + x2[i][j] == 1,
											name=f'{name__}:genConstrInd-adjacency')

				if circulation.w <= circulation.h:  # Vertical
					model.addGenConstrIndicator(adj_circulations[i][j], True, self.unit.rot == 1)

					model.addGenConstrIndicator(x1[i][j], True, self.unit.x + self.unit.w == pos_rel[0],
												name=f'{name__}:genConstrInd-left')
					model.addGenConstrIndicator(x2[i][j], True, self.unit.x == pos_rel[0] + circulation.w,
												name=f'{name__}:genConstrInd-right')
				else:  # Horizontal
					model.addGenConstrIndicator(adj_circulations[i][j], True, self.unit.rot == 0)

					model.addGenConstrIndicator(x1[i][j], True, self.unit.y + self.unit.h == pos_rel[1],
												name=f'{name__}:genConstrInd-above')
					model.addGenConstrIndicator(x2[i][j], True, self.unit.y == pos_rel[1] + circulation.h,
												name=f'{name__}:genConstrInd-below')

			if variables is not None:
				dict_to_variables = {
					"adjacency": adj_vars[i],
					"adjacency-circulations": {c.name: adj_circulations[i][j] for j, c in enumerate(circulations)},
					"left-or-above": {c.name: x1[i][j] for j, c in enumerate(circulations)},
					"right-or-below": {c.name: x2[i][j] for j, c in enumerate(circulations)}
				}
				if (self.unit.name, entrance.name) not in variables:
					variables[(self.unit.name, entrance.name)] = {f"{self.signature}": dict_to_variables}
				else:
					variables[(self.unit.name, entrance.name)][f"{self.signature}"] = dict_to_variables
				for j, circulation in enumerate(circulations):
					dict_to_save = {
						"adjacency": adj_circulations[i][j],
						"left-or-above": x1[i][j],
						"right-or-below": x2[i][j]
					}
					if (self.unit.name, circulation.name) not in variables:
						variables[(self.unit.name, circulation.name)] = {"booleans": dict_to_save}
					else:
						variables[(self.unit.name, circulation.name)]["booleans"] = dict_to_save


class ConstraintAdjacencyThroughCirculation(Constraint):
	def __init__(self, layout, unit1, unit2, same_rot=False, max_dist=0, hierarchy=0):
		super(ConstraintAdjacencyThroughCirculation, self).__init__(hierarchy, layout=layout, unit1=unit1, unit2=unit2,
																	max_dist=max_dist, same_rot=same_rot)
		self.signature = "Constr-AdjacencyThroughCirculation"

		self.unit1 = unit1
		self.unit2 = unit2
		self.layout = layout
		self.same_rot = same_rot
		self.max_dist = max_dist

	def apply(self, model, variables=None):
		name = f"{self.signature}({self.unit1.name},{self.unit2.name})"

		circulations = [c for c in self.layout.features if c.type == FeatureType.Circulation]
		n_circ = len(circulations)
		adj_var = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-adjacency")

		model.addConstr(adj_var == 1, name=f"{name}:constr-adjacency")

		# Direct adjacency
		if variables is not None and (self.unit1.name, self.unit2.name) in variables and \
				"adjacency" in variables[(self.unit1.name, self.unit2.name)]:

			adj_var_direct = variables[(self.unit1.name, self.unit2.name)]["adjacency"]["adjacency-var"]
		else:
			same_partition, adj_var_direct, [r, l, a, b] = calculate_adjacency_vars(model,
																					self.unit1,
																					self.unit2,
																					variables,
																					self.same_rot
																					).values()

		# Saving variables
		dict_to_save = {
			"adjacency-var": adj_var_direct,
			"left": r,
			"right": l,
			"above": a,
			"below": b,
		}
		if variables is not None:
			if (self.unit1.name, self.unit2.name) not in variables:
				variables[(self.unit1.name, self.unit2.name)] = {"adjacency": dict_to_save}
			else:
				variables[(self.unit1.name, self.unit2.name)]["adjacency"] = dict_to_save

		# Adjacency through circulation
		adj_vars_circ = model.addVars(n_circ, vtype=GRB.BINARY, name=f"{name}:boolVars-adjacency-through-circulation")
		x1_by2 = model.addVars(2*n_circ, vtype=GRB.BINARY)
		x2_by2 = model.addVars(2*n_circ, vtype=GRB.BINARY)
		adj_vars_circ_by2 = model.addVars(2*n_circ, vtype=GRB.BINARY)
		for i, circulation in enumerate(circulations):
			if circulation.part_idx is None:
				model.addConstr(adj_vars_circ[i] == 0, name=f'{circulation.name}:constr-inaccessible-circulation')
				continue

			x1s = [x1_by2[2*i], x1_by2[2*i+1]]
			x2s = [x2_by2[2*i], x2_by2[2*i+1]]
			adjs = [adj_vars_circ_by2[2*i], adj_vars_circ_by2[2*i+1]]

			model.addGenConstrIndicator(adj_vars_circ[i], True, gp.quicksum(adjs) == 2)
			for unit, x1, x2, adj, max_dist in zip([self.unit1, self.unit2], x1s, x2s, adjs, [self.max_dist, 0]):
				name__ = f"{self.signature}({unit.name},{circulation.name})"

				if variables is None or (unit.name, circulation.name) not in variables or \
						"same-partition" not in variables[(unit.name, circulation.name)]:
					same_partition = calculate_same_partition_unit_item(model, unit, circulation)
				else:
					same_partition = variables[(unit.name, circulation.name)]["same-partition"]

				pos_rel = [
					gp.quicksum(
						[circulation.relative_info[k]["position"][0] * unit.part_ind[k] for k in circulation.part_idx]),
					gp.quicksum(
						[circulation.relative_info[k]["position"][1] * unit.part_ind[k] for k in circulation.part_idx])
				]

				model.addGenConstrIndicator(adj, True, same_partition == 1,
											name=f'{name__}:genConstrInd-adjacency>>same-partition')
				model.addGenConstrIndicator(adj, True, x1 + x2 == 1,
											name=f'{name__}:genConstrInd-adjacency')

				if circulation.w <= circulation.h:  # Vertical
					# if unit.range_w[0] > unit.range_h[0]:
					#     model.addGenConstrIndicator(adj_vars_circ[i], True, unit.rot == 0)
					# else:
					model.addGenConstrIndicator(adj_vars_circ[i], True, unit.rot == 1)

					model.addGenConstrIndicator(x1, True, unit.x + unit.w >= pos_rel[0] - max_dist,
												name=f'{name__}:genConstrInd-left')
					model.addGenConstrIndicator(x1, True, unit.x + unit.w <= pos_rel[0],
												name=f'{name__}:genConstrInd-left')
					model.addGenConstrIndicator(x2, True, unit.x <= pos_rel[0] + circulation.w + max_dist,
												name=f'{name__}:genConstrInd-right')
					model.addGenConstrIndicator(x2, True, unit.x >= pos_rel[0] + circulation.w,
												name=f'{name__}:genConstrInd-right')
					model.addGenConstrIndicator(adj_vars_circ[i], True, unit.y + MIN_CIRCULATION_CONTACT <= pos_rel[1] + circulation.h,
												name=f'{name__}:genConstrInd-adjacency>>inRange1')
					model.addGenConstrIndicator(adj_vars_circ[i], True, unit.y + unit.h - MIN_CIRCULATION_CONTACT >= pos_rel[1],
												name=f'{name__}:genConstrInd-adjacency>>inRange2')
				else:  # Horizontal
					# if unit.range_w[0] > unit.range_h[0]:
					#     model.addGenConstrIndicator(adj_vars_circ[i], True, unit.rot == 1)
					# else:
					model.addGenConstrIndicator(adj_vars_circ[i], True, unit.rot == 0)
					model.addGenConstrIndicator(x1, True, unit.y + unit.h >= pos_rel[1] - max_dist,
												name=f'{name__}:genConstrInd-above')
					model.addGenConstrIndicator(x1, True, unit.y + unit.h <= pos_rel[1],
												name=f'{name__}:genConstrInd-above')
					model.addGenConstrIndicator(x2, True, unit.y <= pos_rel[1] + circulation.h + max_dist,
												name=f'{name__}:genConstrInd-below')
					model.addGenConstrIndicator(x2, True, unit.y >= pos_rel[1] + circulation.h,
												name=f'{name__}:genConstrInd-below')
					model.addGenConstrIndicator(adj_vars_circ[i], True, unit.x + MIN_CIRCULATION_CONTACT <= pos_rel[0] + circulation.w,
												name=f'{name__}:genConstrInd-adjacency>>inRange1')
					model.addGenConstrIndicator(adj_vars_circ[i], True, unit.x + unit.w - MIN_CIRCULATION_CONTACT >= pos_rel[0],
												name=f'{name__}:genConstrInd-adjacency>>inRange2')
			if self.same_rot:
				center = model.addVars(2, vtype=GRB.BINARY)
				model.addConstr(center[0] == adj_vars_circ[i] * (1 - self.unit1.rot))
				model.addConstr(center[1] == adj_vars_circ[i] * self.unit1.rot)
				model.addGenConstrIndicator(center[0], True,
											self.unit1.x + 0.5 * self.unit1.w == self.unit2.x + 0.5 * self.unit2.w,
											name=f"{(self.unit1.name, self.unit2.name)}:constr-centering")
				model.addGenConstrIndicator(center[1], True,
											self.unit1.y + 0.5 * self.unit1.h == self.unit2.y + 0.5 * self.unit2.h,
											name=f"{(self.unit1.name, self.unit2.name)}:constr-centering")

		# Saving variables
		if variables is not None:
			dict_to_variables = {
				"adjacency": adj_var,
				"adjacency-direct": adj_var_direct,
				"adjacency-ciuculation": gp.quicksum(adj_vars_circ),
				"by-circulation": {c.name: adj_vars_circ[k] for k, c in enumerate(circulations)},
			}
			if (self.unit1.name, self.unit2.name) not in variables:
				variables[(self.unit1.name, self.unit2.name)] = {"adjacency-through-circulation": dict_to_variables}
			else:
				variables[(self.unit1.name, self.unit2.name)]["adjacency-through-circulation"] = dict_to_variables

		# One or other
		model.addGenConstrIndicator(adj_var, True, adj_var_direct + gp.quicksum(adj_vars_circ) >= 1,
									name=f"{name}:genConstrInd-adjacency-through-circulation")


class ConstraintPairAdjacency(Constraint):
	def __init__(self, layout, units, hierarchy=0):
		super(ConstraintPairAdjacency, self).__init__(hierarchy)
		self.signature = "Constr-PairAdjacency"
		self.units = units
		self.layout = layout

	def apply(self, model, variables=None):
		n_units = len(self.units)
		if n_units > 0:
			assert n_units % 2 == 0, "Number of D03/D04 units must be even"
			for i in range(0, n_units, 2):
				ConstraintAdjacency(layout=self.layout, units=self.units[i:i + 2]).apply(model, variables)
