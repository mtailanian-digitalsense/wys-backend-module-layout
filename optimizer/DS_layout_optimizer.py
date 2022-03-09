import os
import logging
# import cv2 as cv
import gurobipy as gp
from gurobipy import GRB
from optimizer.DS_layout import Layout
from optimizer.DS_utils import load_json
from optimizer.DS_feature import FeatureType
from optimizer.DS_wildcard import add_wildcard_units
from optimizer.DS_unit import UNIT_INFO, RotatingUnit, FullUnit, WorkingStationUnit, UNITS_TYPE_EQUIVALENCE
from optimizer.DS_postprocessing import orient_unit_according_to_the_circulation, column_modulation
from optimizer.DS_objectives import ObjectiveEnlarge, ObjectiveMagnetization, ObjectiveEnlargeWorkingStation, \
	ObjectiveCentralize, ObjectiveGroup
from optimizer.DS_constraints import ConstraintBelongPartitions, ConstraintNoIntersection, ConstraintAlignOrientation, \
	ConstraintMakeItAccessible, ConstraintSetNumberOfWorkstations, ConstraintSetReceptionToEntrance, \
	ConstraintAdjacencyThroughCirculation, ConstraintAdjacency, ConstraintPairAdjacency

logging.basicConfig(
    filename='smart_layout.log',
    level=logging.DEBUG,
    format='%(levelname)s | %(asctime)s | %(name)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
logger = logging.getLogger(__name__)


class LayoutOptimizer:
	def __init__(self, optimizer, layout, units):
		self.optimizer = optimizer
		self.layout = layout
		self.units = units

		self.objectives = self.get_objectives()
		self.constraints = self.get_constraints()
		self.variables = {}

	@classmethod
	def load(cls, planta, cores, shafts, circulations, entrances, windows, workspaces, show=0):
		logger.debug("Creating optimizer")
		# Optimizer
		optimizer = gp.Model('Wys')
		# Layout
		layout = Layout.load(planta, cores, shafts, circulations, entrances, windows, show)
		# Units
		unit_requirements = {}
		for ws in workspaces:
			try:
				unit_requirements[UNITS_TYPE_EQUIVALENCE[ws["name"]]] = ws["quantity"]
				print(f"[SUCCESS] {ws['name']} loaded")
			except KeyError:
				print(f"[ERROR] Could not load {ws['name']}. Missing key in UNITS_TYPE_EQUIVALENCE")

		units = cls.load_units(unit_requirements.items(), layout, optimizer)

		if show >= 1:
			layout_image = layout.draw(show_features=True)
			cv.namedWindow("Input Layout", cv.WINDOW_NORMAL)
			cv.imshow("Input Layout", layout_image)
			cv.waitKey()

		return cls(optimizer, layout, units)

	@classmethod
	def load_legacy(cls, config_path):
		# Gurobi model: Optimizer
		optimizer = gp.Model('Wys')
		# Layout
		layout = Layout.load_legacy(config_path)
		# Units
		unit_requirements = load_json(config_path)["units"].items()
		units = cls.load_units(unit_requirements, layout, optimizer)

		return cls(optimizer, layout, units)

	@staticmethod
	def load_units(unit_requirements, layout, optimizer):
		i, units = 0, []
		for unit_type, quantity in unit_requirements:
			for _ in range(quantity):
				is_closed = True if "is-closed" not in UNIT_INFO[unit_type] else UNIT_INFO[unit_type]["is-closed"]
				if is_closed:
					units.append(FullUnit(optimizer, unit_type, layout, name='unit_{0:04d}'.format(i)))
					i += 1
				else:
					if unit_type == 'A00':  # Working station
						units.append(WorkingStationUnit(optimizer, unit_type, layout, name='unit_{0:04d}'.format(i)))
						i += 1
					else:  # Any other open unit
						units.append(RotatingUnit(optimizer, unit_type, layout, name='unit_{0:04d}'.format(i)))
						i += 1
		return units

	@classmethod
	def load_from_file(cls):
		raise NotImplementedError

	def get_units(self, *unit_types):
		return self.units if not unit_types else [u for u in self.units if u.type in unit_types]

	def get_constraints(self):
		closed_units_types = [unit_type for unit_type in UNIT_INFO.keys() if UNIT_INFO[unit_type]["is-closed"]]
		open_units_types = [unit_type for unit_type in UNIT_INFO.keys() if not UNIT_INFO[unit_type]["is-closed"]]
		n_ws = 4 * len(self.get_units('A00')) + 2 * len(self.get_units('A01')) + 4 * len(self.get_units('A02'))

		constraints = [
			# Bound to partition
			ConstraintBelongPartitions(self.layout, units=self.get_units()),
			# No intersection
			ConstraintNoIntersection(units=self.get_units()),
			ConstraintNoIntersection(units=self.get_units(*open_units_types),
			                         items=self.layout.get_features(FeatureType.Column, FeatureType.Other,
			                                                        FeatureType.Circulation, FeatureType.Core)),
			# TODO: por qué en las cerradas se pide por separado NoIntersection con las columnas?
			ConstraintNoIntersection(units=self.get_units(*closed_units_types),
			                         items=self.layout.get_features(FeatureType.Other, FeatureType.Circulation,
			                                                        FeatureType.Core)),
			ConstraintNoIntersection(units=self.get_units(*closed_units_types),
			                         items=self.layout.get_features(FeatureType.Column),
			                         absorb=False),
			# Alignment of working stations to the windows
			ConstraintAlignOrientation(
				layout=self.layout,
				units=self.get_units('A00', 'A02'),
				features=self.layout.get_features(FeatureType.Window)),
			# Make the closed units accessible (close to the circulation)
			ConstraintMakeItAccessible(layout=self.layout, units=self.get_units(*closed_units_types)),
			# Set number of work-stations
			ConstraintSetNumberOfWorkstations(layout=self.layout, units=self.get_units(), number_workstations=n_ws),
			# Collaborative modules
			ConstraintPairAdjacency(self.layout, self.get_units('D03')),
			ConstraintPairAdjacency(self.layout, self.get_units('D04'))
		]
		# Set the reception to the entrance
		if len(self.get_units('F01', 'F03', 'F04', 'F05')) > 0:
			constraints.append(
				ConstraintSetReceptionToEntrance(layout=self.layout,
				                                 unit=self.get_units('F01', 'F03', 'F04', 'F05')[0],
				                                 entrances=self.layout.get_features(FeatureType.Entrance)))
		# Work Coffee
		g04, g05 = self.get_units('G04'), self.get_units('G05')
		if len(g04) > 0 and len(g05) > 0:
			constraints.extend([
				# Get the work-coffee in place (through circulation if needed)
				ConstraintAdjacencyThroughCirculation(layout=self.layout, unit1=g04[0], unit2=g05[0],
				                                      same_rot=True, max_dist=250),
				# Get the work-coffee bar in contact with the core
				ConstraintAdjacency(layout=self.layout, units=g04, items=self.layout.get_features(FeatureType.Core),
				                    same_rot=False)
			])
		return constraints

	def get_objectives(self):
		objectives = [
			# Expand dimensions of B04 modules over the orthogonal direction
			ObjectiveEnlarge(layout=self.layout, units=self.get_units('B04', 'B09'), weight=1),
			# Get the PdTs close to the windows
			ObjectiveMagnetization(layout=self.layout, units=self.get_units('A00', 'A02'),
			                       features=self.layout.get_features(FeatureType.Window), weight=1),
			# Get the Receptions close to the entrances
			# ObjectiveMagnetization(layout=self.layout, units=self.get_units('F01'),
			#                        features=self.layout.get_features(FeatureType.Entrance), weight=100),
			# Enlarge A00
			ObjectiveEnlargeWorkingStation(units=self.get_units('A00'), weight=1000),
			# Get centrals modules
			# ObjectiveCentralize(units=self.get_units('C03', 'H02', 'E01'), dist_type="l1", weight=10000),
			# Group work-stations
			# ObjectiveGroup(units=self.get_units('A00', 'A02'), weight=1000),
			# Group B04s
			ObjectiveGroup(units=self.get_units('B04'), weight=1),
			# Group B05s y B09s
			ObjectiveGroup(units=self.get_units('B05', 'B09'), weight=1),
			# Group C03s
			# ObjectiveGroup(units=self.get_units('C03'), weight=1000000000),
		]
		return objectives

	def post_process(self):
		# Orientation
		closed_units_types = [unit_type for unit_type in UNIT_INFO.keys() if UNIT_INFO[unit_type]["is-closed"]]
		for unit in self.get_units(*closed_units_types, 'F01', 'F03', 'F04', 'F05'):
			orient_unit_according_to_the_circulation(unit, self.layout.get_features(FeatureType.Circulation),
			                                         self.variables)
		# Column absorption
		self.units = column_modulation(self.layout.partitions, self.get_units(), self.layout.get_features())

	def add_wildcards(self):
		self.units.extend(add_wildcard_units(self.layout, self.units, ['D09']))

	def summary(self):
		"""
		Model.resume
		Function to display all the information about the model, the units and the layout
		as well as all the constraints and objectives defined
		"""
		divisor = "#" * 20
		print(f"{divisor} CONSTRAINTS {divisor}")
		[print(c) for c in self.constraints]
		print(f"{divisor} OBJECTIVES {divisor}")
		[print(f) for f in self.objectives]

	def draw(self, show_unit_art=True, show_unit_name=True, show_features=False, show_contours=1):
		# Base layout
		layout_image = self.layout.draw(show_features=show_features)
		# Units results
		for u in self.units:
			layout_image = u.draw_in_layout(layout_image,
			                               show_unit_name=show_unit_name,
			                               show_unit_art=show_unit_art,
			                               show_contours=show_contours)
		return layout_image

	def execute(self, log=True, display=False, **kwargs):
		if log:
			self.summary()

		# Applying constraints
		for c in self.constraints:
			c.apply(self.optimizer, self.variables)

		# Creating objective function
		objFunc = 0
		for o in self.objectives:
			objFunc += o.apply(self.optimizer, self.variables)

		# Optimize
		self.optimizer.setObjective(objFunc, sense=GRB.MINIMIZE)
		self.optimizer.setParam('NonConvex', 2)
		self.optimizer.optimize()

		if self.optimizer.SolCount:
			# Log
			if log:
				self.summary()
			# Display
			if display:
				self.draw(**kwargs)
			return 0
		else:
			# Debugging
			self.optimizer.computeIIS()
			os.makedirs("../results", exist_ok=True)
			self.optimizer.write("../results/iis.ilp")
			print("No solution was found!\n\t-> IIS report was saved at ../results/iis.ilp")
			return -1


if __name__ == '__main__':
	config_file = "config/legacy/CL01.json"
	sl = LayoutOptimizer.load_legacy(config_file)

	# Optimize
	ret = sl.execute(log=True, display=False)

	# Get result
	result_base = sl.draw(show_unit_name=True, show_contours=0)
	# Post-Process
	sl.post_process()
	result_post = sl.draw(show_unit_name=False, show_contours=0)
	# Add wildcard units
	sl.add_wildcards()
	result_post_wild = sl.draw(show_unit_name=False, show_contours=0)

	# Show
	cv.namedWindow("Result base", cv.WINDOW_NORMAL)
	cv.imshow("Result base", result_base)
	cv.namedWindow("Result Post", cv.WINDOW_NORMAL)
	cv.imshow("Result Post", result_post)
	cv.namedWindow("Result Post Wildcards", cv.WINDOW_NORMAL)
	cv.imshow("Result Post Wildcards", result_post_wild)
	k = cv.waitKey(0)
	while (k != 27) and (k != ord('q')):
		k = cv.waitKey(0)
	cv.destroyAllWindows()

	# Save images
	os.makedirs("../results", exist_ok=True)
	cv.imwrite("../results/result.jpg", result_base)
	cv.imwrite("../results/result_post.jpg", result_post)
	cv.imwrite("../results/result_post_wild.jpg", result_post_wild)
