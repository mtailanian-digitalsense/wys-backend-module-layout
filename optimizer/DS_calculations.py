import gurobipy as gp
from gurobipy import GRB
from optimizer.DS_unit import Unit
from optimizer.DS_feature import FeatureType, Feature


def windows_distance(model, layout, unit, windows):
	if not windows:
		return None

	assert all([w.type == FeatureType.Window for w in windows]), "Features must be windows"

	slack_vars = []
	for i, p in enumerate(layout.partitions):
		partition_widows = [w for w in windows if w.part_idx == i]
		if not partition_widows:
			continue

		n_part_windows = len(partition_widows)
		distances = model.addVars(n_part_windows, vtype=GRB.CONTINUOUS, name=f'{unit.name}_window_distances')
		for j, win in enumerate(partition_widows):
			if win.w == 0:  # Vertical window
				if win.x <= 1:
					model.addConstr(distances[j] == unit.x)
				else:
					model.addConstr(distances[j] == p.w - (unit.x + unit.w))
			else:  # (win.h == 0) Horizontal window
				if win.y <= 1:
					model.addConstr(distances[j] == unit.y)
				else:
					model.addConstr(distances[j] == p.h - (unit.y + unit.h))

		slack = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f'{unit.name}_slack')
		min_dist = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_min_window_dist')
		model.addConstr(min_dist == gp.min_(distances))
		model.addGenConstrIndicator(unit.part_ind[i], True, min_dist == slack)
		slack_vars.append(slack)

		# # Orientation
		# window_rots = [1 if win.w == 0 else 0 for win in windows]
		# closest_window = model.addVars(n_part_windows, vtype=GRB.BINARY, name=f'{unit.name}_closer-window')
		# model.addConstr(gp.quicksum(closest_window) == 1)
		# model.addConstr(gp.quicksum([closest_window[k] * distances[k] for k in range(n_part_windows)]) == min_dist)
		# model.addGenConstrIndicator(unit.part_ind[i], True, unit.rot == gp.quicksum([closest_window[k] * window_rots[k]
		#                                                                          for k in range(n_part_windows)]))

	return slack_vars


def circulation_distance(model, layout, unit, circulations, variables=None):
	if not circulations:
		return 0, {}
	name = circulations[0].type.name + '-' + unit.name

	n_f = len(circulations)
	n_part = len(layout.get_partitions())
	adj_vars = model.addVars(n_f, vtype=GRB.BINARY, name=name+"-AdjVars")
	differences1 = model.addVars(n_f, lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name=name + '_differences1circulations')
	differences2 = model.addVars(n_f, lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name=name + '_differences2circulations')
	distances = model.addVars(2*n_f, vtype=GRB.CONTINUOUS, name=name + '_distancecirculations')
	# distances1 = model.addVars(n_f, vtype=GRB.CONTINUOUS, name=name + '_distance1circulations')
	# distances2 = model.addVars(n_f, vtype=GRB.CONTINUOUS, name=name + '_distance2circulations')
	min_dist = model.addVar(vtype=GRB.CONTINUOUS, name=name + '_minDist')

	model.addConstr(min_dist == gp.min_(distances))

	for i, circulation in enumerate(circulations):
		model.addConstr(distances[2*i] == gp.abs_(differences1[i]))
		model.addConstr(distances[2*i+1] == gp.abs_(differences2[i]))
		if circulation.part_idx is None:
			model.addConstr(distances[i] == 1000000.0, name=name+"partIdxNone")
			continue

		if variables is None or (unit.name, circulation.name) not in variables or \
			"same-partition" not in variables[(unit.name, circulation.name)]:
			same_partition = gp.quicksum([unit.part_ind[idx] for idx in circulation.part_idx])
		else:
			same_partition = variables[(unit.name, circulation.name)]["same-partition"]

		pos_rel = [gp.quicksum([circulation.rel_positions[k][0] * unit.part_ind[k] for k in range(n_part)]),
				   gp.quicksum([circulation.rel_positions[k][1] * unit.part_ind[k] for k in range(n_part)])]

		# model.addConstr(distances[i] == gp.min_([distances1[i], distances2[i]]))

		model.addGenConstrIndicator(adj_vars[i], True, same_partition == 1, name=name + "same-Partition")

		model.addGenConstrIndicator(adj_vars[i], False, differences1[i] == 1000000.0, name=f'{name}-diff1DefaultNotInPart')
		model.addGenConstrIndicator(adj_vars[i], False, differences2[i] == 1000000.0, name=f'{name}-diff2DefaultNotInPart')
		if circulation.w <= circulation.h: # Vertical
			model.addGenConstrIndicator(adj_vars[i], True, differences1[i] == unit.x - pos_rel[0],
										name=f'{name}-diff1Constr')
			model.addGenConstrIndicator(adj_vars[i], True, differences2[i] == unit.x + unit.w - pos_rel[0],
										name=f'{name}-diff2Constr')
			model.addGenConstrIndicator(adj_vars[i], True, unit.y <= pos_rel[1] + 0.5 * circulation.h,
										name=f'{name}-range1Constr')
			model.addGenConstrIndicator(adj_vars[i], True, unit.y >= pos_rel[1] - 0.5 * circulation.h,
										name=f'{name}-range2Constr')
		else: # Horizontal

			model.addGenConstrIndicator(adj_vars[i], True, differences1[i] == unit.y - pos_rel[1],
										name=f'{name}-diff1Constr')
			model.addGenConstrIndicator(adj_vars[i], True, differences2[i] == unit.y + unit.h - pos_rel[1],
										name=f'{name}-diff2Constr')
			model.addGenConstrIndicator(adj_vars[i], True, unit.x <= pos_rel[0] + 0.5 * circulation.w,
										name=f'{name}-range1Constr')
			model.addGenConstrIndicator(adj_vars[i], True, unit.x >= pos_rel[0] - 0.5 * circulation.w,
										name=f'{name}-range2Constr')

	return min_dist, [[distances[2*i], distances[2*i+1]] for i in range(n_f)]


def center_distance(model, layout, unit, dist_type='l2'):
	x_glob, y_glob, _ = unit.get_absolute_coordinates(layout)

	dx = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_dist_x')
	dy = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_dist_y')
	model.addConstr(dx == x_glob - layout.w / 2)
	model.addConstr(dy == y_glob - layout.h / 2)

	# Option 1
	# dist = dx * dy

	# Option 2
	if dist_type == 'l1':
		abs_dx = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_abs_dist_x')
		abs_dy = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_abs_dist_y')
		model.addConstr(abs_dx == gp.abs_(dx))
		model.addConstr(abs_dy == gp.abs_(dy))
		dist = abs_dx + abs_dy
	# Option 3
	else:
		dx2 = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_squared_dist_x')
		dy2 = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_squared_dist_x')
		model.addConstr(dx2 == dx ** 2)
		model.addConstr(dy2 == dy ** 2)
		dist = dx2 + dy2

	return dist


def calculate_distance_to_point(model, layout, unit, point, dist_type='l2'):
	x_glob, y_glob, _ = unit.get_absolute_coordinates(layout)

	dx = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_dist_x')
	dy = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_dist_y')
	model.addConstr(dx == x_glob - point[0])
	model.addConstr(dy == y_glob - point[1])

	# Option 1
	# dist = dx * dy

	# Option 2
	if dist_type == 'l1':
		abs_dx = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_abs_dist_x')
		abs_dy = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_abs_dist_y')
		model.addConstr(abs_dx == gp.abs_(dx))
		model.addConstr(abs_dy == gp.abs_(dy))
		dist = abs_dx + abs_dy
	# Option 3
	else:
		dx2 = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_squared_dist_x')
		dy2 = model.addVar(vtype=GRB.CONTINUOUS, name=f'{unit.name}_center_squared_dist_x')
		model.addConstr(dx2 == dx ** 2)
		model.addConstr(dy2 == dy ** 2)
		dist = dx2 + dy2

	return dist


def calculate_entrance_distance(model, layout, unit, entrances, max_dist=220):
	n_en = len(entrances)
	partitions = layout.get_partitions()
	n_part = len(partitions)
	name = "EntrancesDist-{}".format(unit.name)

	closed_vars = model.addVars(n_en, vtype=GRB.BINARY, name=name + "_closedVars")
	orientations = model.addVars(n_en, vtype=GRB.BINARY, name=name + "_orientations")
	distances = model.addVars(n_en, vtype=GRB.CONTINUOUS, name=name + "_distances")
	distances1 = model.addVars(n_en, vtype=GRB.CONTINUOUS, name=name + "_distances")
	distances2 = model.addVars(n_en, vtype=GRB.CONTINUOUS, name=name + "_distances")
	differences1 = model.addVars(n_en, lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name=name + "_differences1")
	differences2 = model.addVars(n_en, lb=-GRB.INFINITY, vtype=GRB.CONTINUOUS, name=name + "_differences2")

	model.addConstr(gp.quicksum(closed_vars) == 1)

	distances_dict = {}
	for i, entrance in enumerate(entrances):
		model.addConstr(distances1[i] == gp.abs_(differences1[i]))
		model.addConstr(distances2[i] == gp.abs_(differences2[i]))

		pos_rel = [gp.quicksum([entrance.relative_info[k]["center"][0] * unit.part_ind[k] for k in range(n_part)]),
				   gp.quicksum([entrance.relative_info[k]["center"][1] * unit.part_ind[k] for k in range(n_part)])]
		model.addConstr(orientations[i] == gp.quicksum([int(entrance.tita_glob == p.tita_glob) * unit.part_ind[k]
														for k, p in enumerate(partitions)]))

		model.addGenConstrIndicator(orientations[i], False, closed_vars[i] == 0, name=name+"-wellOriented")
		model.addGenConstrIndicator(closed_vars[i], False, differences1[i] == 0)
		model.addGenConstrIndicator(closed_vars[i], False, differences2[i] == 0)
		model.addConstr(distances[i] == gp.min_([distances1[i], distances2[i]]))
		if entrance.w == 0:  # Vertical
			model.addGenConstrIndicator(closed_vars[i], True, differences1[i] == unit.x - pos_rel[0], name=name+"-diff1")
			model.addGenConstrIndicator(closed_vars[i], True, differences2[i] == unit.x + unit.w - pos_rel[0], name=name+"-diff2")
			model.addGenConstrIndicator(closed_vars[i], True, unit.y + 0.5 * unit.h == pos_rel[1], name=name+"-centering")
		elif entrance.h == 0:  # Horizontal
			model.addGenConstrIndicator(closed_vars[i], True, differences1[i] == unit.y - pos_rel[1], name=name+"-diff1")
			model.addGenConstrIndicator(closed_vars[i], True, differences2[i] == unit.y + unit.h - pos_rel[1], name=name+"-diff2")
			model.addGenConstrIndicator(closed_vars[i], True, unit.x + 0.5 * unit.w == pos_rel[0], name=name+"centering")

		distances_dict[entrance.name] = distances[i]
	if max_dist is not None:
		model.addConstrs((distances[i] <= max_dist for i in range(n_en)))

	return distances_dict


def calculate_distance_between_flat_features(model, layout, unit, features, variables):
	'''
	Calcula las variables gurobi de min_dist y closest_rotation entre la unidad y
	los features
	:param model:
	:param unit:
	:param features:
	:return:
	'''
	if not features:
		return 0, 0
	name = features[0].type.name + '-' + unit.name

	n_f = len(features)
	p = model.addVars(n_f, vtype=GRB.BINARY)
	d = model.addVars(n_f, vtype=GRB.CONTINUOUS, name=name + '_distancefeatures')
	min_dist = model.addVar(vtype=GRB.CONTINUOUS, name=name + '_minDist')
	distance_closest = model.addVar(vtype=GRB.CONTINUOUS, name=name + '_dist-closest')
	closest_feature_1hot = model.addVars(n_f, vtype=GRB.BINARY, name=name + "_closest-window")

	model.addConstr(min_dist == gp.min_(d))
	model.addConstr(gp.quicksum(closest_feature_1hot) == 1)

	model.addConstr(distance_closest == min_dist)
	model.addConstr(distance_closest == gp.quicksum([closest_feature_1hot[i] * d[i] for i in range(n_f)]))

	same_partitions = {}
	features_rotation = []
	partitions = layout.partitions
	for i, w in enumerate(features):
		if w.part_idx is None:
			model.addConstr(d[i] == 1000000.0)
			features_rotation.append(0)
			continue

		# Calculating if they are in the same partition
		if (unit.name, w.name) not in variables or "same-partition" not in variables[(unit.name, w.name)]:
			same_partitions[(unit.name, w.name)] = calculate_same_partition_unit_item(model, unit, w)
		else:
			same_partitions[(unit.name, w.name)] = variables[(unit.name, w.name)]["same-partition"]

		model.addConstr(p[i] == same_partitions[(unit.name, w.name)])

		if len(w.part_idx) > 1:
			partition_w = gp.quicksum([p.w * unit.part_ind[i] for i, p in enumerate(partitions) if i in w.part_idx])
			partition_h = gp.quicksum([p.h * unit.part_ind[i] for i, p in enumerate(partitions) if i in w.part_idx])
		else:
			partition_w = partitions[w.part_idx[0]].w
			partition_h = partitions[w.part_idx[0]].h

		if w.w == 0:  # Vertical
			features_rotation.append(1)
			if w.x <= 1:
				model.addGenConstrIndicator(p[i], True, d[i] == unit.x + 0.5 * unit.w)
			else: #if w.x >= partition_w - 1:
				model.addGenConstrIndicator(p[i], True, d[i] == partition_w - unit.x - 0.5 * unit.w)
		elif w.h == 0:  # Horizontal
			features_rotation.append(0)
			if w.y <= 1:
				model.addGenConstrIndicator(p[i], True, d[i] == unit.y + 0.5 * unit.h)
			else:#if w.y >= partition_h - 1:
				model.addGenConstrIndicator(p[i], True, d[i] == partition_h - unit.y - 0.5 * unit.h)
		model.addGenConstrIndicator(p[i], False, d[i] == 1000000.0)

	rotation_closest = gp.quicksum(
						[closest_feature_1hot[i] * features_rotation[i] for i in range(len(features_rotation))]
	)

	return min_dist, rotation_closest, same_partitions


def calculate_partitions_occupied_by(model, layout, units):
	partitions = layout.get_partitions()
	n_parts = len(partitions)
	occupied_partitions = model.addVars(n_parts, vtype=GRB.BINARY, name="occupiedPartitions")
	n_units_in_partitions = model.addVars(n_parts, vtype=GRB.INTEGER, name="NumberOfUnitForPartition")
	for i, partition in enumerate(partitions):
		model.addConstr(n_units_in_partitions[i] == gp.quicksum([u.part_ind[i] for u in units]),
						name=str(partition.ind)+"_group-Number")
		model.addConstr(occupied_partitions[i] == gp.min_([1, n_units_in_partitions[i]]),
						name=str(partition.ind)+"_group-OccupiedBool")

	return n_units_in_partitions, occupied_partitions


def calculate_same_partition_unit_item(model, unit, item):
	"""
	Calcula las variables gurobi de same_partition entre la unidad y el item (unit o feature)
	:param model:
	:param unit:
	:param item:
	:return:
	"""
	name = unit.name + '-' + item.name
	# Auxiliary variable
	same_partition = model.addVar(vtype=GRB.BINARY, name=f'{name}_same_partition')
	if len(unit.part_ind) == 1:
		model.addConstr(same_partition == 1, name=f'{name}_same_partition_constraint(SiglePartition)')
		return same_partition

	if isinstance(item, Unit):
		model.addConstr(same_partition == gp.quicksum([unit.part_ind[i] * item.part_ind[i]
													   for i in range(len(unit.part_ind))]),
						name=f'{name}_same_partition_constraint')
	elif isinstance(item, Feature):
		if item.part_idx is None:
			model.addConstr(same_partition == 0, name=f'{name}_same_partition_constraint')
		else:
			model.addConstr(same_partition == gp.quicksum([unit.part_ind[idx] for idx in item.part_idx]),
							name=f'{name}_same_partition_constraint')

	return same_partition


def calculate_adjacency_vars(model, unit, item, variables, same_rot=False):
	name = f"AdjacencyVarsCalculation({unit.name},{item.name})"
	x1 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-left")
	x2 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-right")
	x3 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-above")
	x4 = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-below")
	adj_var = model.addVar(vtype=GRB.BINARY, name=f"{name}:boolVar-adjacency")

	if variables is not None and (unit.name, item.name) in variables.keys() \
			and "same-partition" in variables[(unit.name, item.name)].keys():
		same_partition = variables[(unit.name, item.name)]["same-partition"]
	else:
		same_partition = calculate_same_partition_unit_item(model, unit, item)

	model.addGenConstrIndicator(adj_var, True, same_partition == 1,
								name=f"{name}:genConstrInd-adjacency>>same-partition")
	model.addGenConstrIndicator(adj_var, True, x1 + x2 + x3 + x4 == 1,
								name=f"{name}:genConstrInd-adjacency")

	# Left
	model.addGenConstrIndicator(x1, True, unit.x == item.x + item.w,
								name=f"{name}:genConstrInd-left")
	model.addGenConstrIndicator(x1, True, unit.y + 0.5 * unit.h == item.y + 0.5 * item.h,
								name=f"{name}:genConstrInd-left-inline")
	# Right
	model.addGenConstrIndicator(x2, True, unit.x + unit.w == item.x,
								name=f"{name}:genConstrInd-right")
	model.addGenConstrIndicator(x2, True, unit.y + 0.5 * unit.h == item.y + 0.5 * item.h,
								name=f"{name}:genConstrInd-right-inline")
	# Above
	model.addGenConstrIndicator(x3, True, unit.y == item.y + item.h,
								name=f"{name}:genConstrInd-above")
	model.addGenConstrIndicator(x3, True, unit.x + 0.5 * unit.w == item.x + 0.5 * item.w,
								name=f"{name}:genConstrInd-above-inline")
	# Below
	model.addGenConstrIndicator(x4, True, unit.y + unit.h == item.y,
								name=f"{name}:genConstrInd-below")
	model.addGenConstrIndicator(x4, True, unit.x + 0.5 * unit.w == item.x + 0.5 * item.w,
								name=f"{name}:genConstrInd-below-inline")

	if same_rot:
		model.addGenConstrIndicator(adj_var, True, unit.rot == item.rot)

	return {
			"same-partition": same_partition,
			"adj_var": adj_var,
			"bool_LRAB": [x1, x2, x3, x4]
	}
