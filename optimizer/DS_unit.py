import os
import cv2 as cv
import numpy as np
import gurobipy as gp
from gurobipy import GRB, quicksum
from optimizer.DS_utils import get_angled_box, rotate_image

# TODO: Check
UNITS_TYPE_EQUIVALENCE = {
	"WYS_SALAREUNION_RECTA6PERSONAS": "B04",
	"WYS_SALAREUNION_DIRECTORIO10PERSONAS": "B09",
	"WYS_PUESTOTRABAJO_CELL3PERSONAS": "A00",
	"WYS_PRIVADO_1PERSONA": "C03",
	"WYS_PRIVADO_1PERSONAESTAR": "C03",
	# "WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS": "",
	# "WYS_SOPORTE_KITCHENETTE": "",
	# "WYS_SOPORTE_SERVIDOR1BASTIDOR": "",
	# "WYS_SOPORTE_PRINT1": "",
	"WYS_RECEPCION_1PERSONA": "F01",
	# "WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS": "",
	"WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA": "H02",
	"WYS_COLABORATIVO_BARRA6PERSONAS": "D04"
}

UNITS_TYPE_EQUIVALENCE_INVERSE = {v: k for k, v in UNITS_TYPE_EQUIVALENCE.items()}

UNIT_INFO = {
	'A00': {"w": [382, 382], "h": [135, 135], "is-closed": False, "description": "Stacked Working Station"},
	'A01': {"w": [382, 573], "h": [140, 300], "is-closed": False, "description": "Puesto de trabajo para 2 personas"},
	'A02': {"w": [382, 573], "h": [270, 500], "is-closed": False, "description": "Puesto de trabajo para 4 personas"},
	'B04': {"w": [300, 600], "h": [405, 810], "is-closed": True, "description": "Sala de reunion"},
	'B05': {"w": [300, 450], "h": [230, 345], "is-closed": True, "description": "Sala de reunion"},
	'B09': {"w": [400, 800], "h": [605, 1200], "is-closed": True, "description": "Sala de reunion"},
	'C03': {"w": [350, 525], "h": [240, 360], "is-closed": True, "description": "Privado - Visitas"},
	'D03': {"w": [190, 190], "h": [220, 220], "is-closed": True, "description": "Colaborativo 2 personas"},
	'D04': {"w": [240, 240], "h": [220, 220], "is-closed": True, "description": "Colaborativo 4 personas"},
	'D09': {"w": [150, 300], "h": [200, 400], "is-closed": True, "description": "Reunión informal"},
	'E01': {"w": [225, 225], "h": [230, 230], "is-closed": False, "description": "Lounge"},
	'F01': {"w": [270, 540], "h": [325, 650], "is-closed": False, "description": "Recepcion"},
	'F03': {"w": [400, 400], "h": [340, 340], "is-closed": False, "description": "Recepcion"},
	'F04': {"w": [500, 500], "h": [340, 340], "is-closed": False, "description": "Recepcion"},
	'F05': {"w": [520, 520], "h": [700, 700], "is-closed": False, "description": "Recepcion"},
	'G01': {"w": [640, 640], "h": [440, 440], "is-closed": False, "description": "Workcoffee - Comedor"},
	'G04': {"w": [200, 600], "h": [80, 80], "is-closed": False, "description": "Workcoffee - Comedor - Barra"},
	'G05': {"w": [380, 380], "h": [315, 466], "is-closed": False, "description": "Workcoffee - Comedor - Sillas"},
	'G06': {"w": [640, 640], "h": [315, 466], "is-closed": False, "description": "Workcoffee - Comedor - Sillas"},
	'H02': {"w": [160, 160], "h": [190, 190], "is-closed": True, "description": "Phonebooth"},
	'I08': {"w": [150, 150], "h": [130, 130], "is-closed": True, "description": "Print - Simple"}
}


class Unit:
	def __init__(self, model, unit_type, layout, name):
		self.layout = layout
		self.name = name
		self.type = unit_type
		self.w = UNIT_INFO[unit_type]["w"][0]
		self.h = UNIT_INFO[unit_type]["h"][0]
		self.rot = 0
		self.orientation = [1, 1]
		self.door_is_below = True
		self.range_w = UNIT_INFO[unit_type]["w"]
		self.range_h = UNIT_INFO[unit_type]["h"]
		self.color = (0, 0, 0)

		n_partitions = len(layout.partitions)
		self.x = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name + "_x")
		self.y = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name + "_y")
		self.part_ind = model.addVars(n_partitions, vtype=GRB.BINARY, name=name + "_partition_vector")

	def get_image(self):
		if self.door_is_below:
			img_path = "../modules/" + self.type + "_below.png"
		else:
			img_path = "../modules/" + self.type + "_right.png"

		if not os.path.exists(img_path):
			return cv.imread("../modules/" + self.type + ".png")

		return cv.imread(img_path)

	def get_absolute_coordinates(self, layout):
		possibilities_x = [self.part_ind[i] * (self.x * np.cos(p.tita_glob) - self.y * np.sin(p.tita_glob) + p.x_glob)
						   for i, p in enumerate(layout.partitions)]
		possibilities_y = [self.part_ind[i] * (self.y * np.cos(p.tita_glob) + self.x * np.sin(p.tita_glob) + p.y_glob)
						   for i, p in enumerate(layout.partitions)]
		possibilities_tita = [self.part_ind[i] * p.tita_glob for i, p in enumerate(layout.partitions)]

		return quicksum(possibilities_x), quicksum(possibilities_y), quicksum(possibilities_tita)

	def get_absolute_coordinates_approximation(self, layout):
		possibilities_x = [self.part_ind[i] * (self.x + p.x_glob) for i, p in enumerate(layout.partitions)]
		possibilities_y = [self.part_ind[i] * (self.y + p.y_glob) for i, p in enumerate(layout.partitions)]
		return quicksum(possibilities_x), quicksum(possibilities_y)

	def get_box(self):
		x, y, tita = self.get_absolute_coordinates(self.layout)
		return x.getValue(), y.getValue(), self.w, self.h, tita.getValue(), self.rot

	def draw_in_layout(self, layout, show_unit_name=True, show_unit_art=False, show_contours=2):
		x, y, w, h, tita, rot = self.get_result_box()
		d = np.sqrt(w ** 2 + h ** 2)
		contour = get_angled_box([x, y, w, h], tita)
		if show_unit_art:
			layout = self.add_art(self.get_image(), w, h, tita, rot, self.orientation, self.type, contour, layout)
		if (show_contours >= 2) or (UNIT_INFO[self.type]["is-closed"] and show_contours):
			layout = cv.drawContours(layout, [contour[:, np.newaxis, :].astype(int)], -1, self.color, 8)
		if show_unit_name:
			layout = cv.putText(layout, str(self.type)[-3:],
								(int(sum(contour[:, 0]) / 4 - d // 8), int(sum(contour[:, 1]) / 4 - d // 8)),
								cv.FONT_HERSHEY_SIMPLEX, 2, self.color, 2, cv.LINE_AA)
			layout = cv.putText(layout, self.name,
								(int(sum(contour[:, 0]) / 4 - d // 8), int(sum(contour[:, 1]) / 4 - d // 8) + 100),
								cv.FONT_HERSHEY_SIMPLEX, 2, self.color, 2, cv.LINE_AA)
		return layout

	def draw_in_layout_abs_coords(self, layout, x, y, w, h, tita=0, rot=0, show_unit_name=True, show_unit_art=False,
								  show_contours=2):
		d = np.sqrt(w ** 2 + h ** 2)
		contour = get_angled_box([x, y, w, h], tita)
		if show_unit_art:
			layout = self.add_art(self.get_image(), w, h, tita, rot, self.orientation, self.type, contour, layout)
		if (show_contours >= 2) or (UNIT_INFO[self.type]["is-closed"] and show_contours):
			layout = cv.drawContours(layout, [contour[:, np.newaxis, :].astype(int)], -1, self.color, 8)
		if show_unit_name:
			layout = cv.putText(layout, str(self.type)[-3:],
								(int(sum(contour[:, 0]) / 4 - d // 8), int(sum(contour[:, 1]) / 4 - d // 8)),
								cv.FONT_HERSHEY_SIMPLEX, 2, self.color, 2, cv.LINE_AA)
			layout = cv.putText(layout, self.name,
								(int(sum(contour[:, 0]) / 4 - d // 8), int(sum(contour[:, 1]) / 4 - d // 8) + 100),
								cv.FONT_HERSHEY_SIMPLEX, 2, self.color, 2, cv.LINE_AA)
		return layout

	@staticmethod
	def add_art(art, w, h, tita, rot, orientation, type_, contour, layout):
		if int(rot + 0.5):
			# TODO: Emprolijar en una solución más genérica
			if type_ == 'C03':
				art = cv.rotate(art, cv.ROTATE_90_CLOCKWISE)
			else:
				art = cv.rotate(art, cv.ROTATE_90_COUNTERCLOCKWISE)

		if orientation[0] == -1:
			art = cv.flip(art, 1)
		if orientation[1] == -1:
			art = cv.flip(art, 0)

		art = cv.resize(art, (int(w + 0.5), int(h + 0.5)))
		if tita == 0.0:
			x, y = (contour[0] + 0.5).astype(np.int)
			mask = (art > 5) & (art < 255)
			ly, lx = layout[y:y + art.shape[0], x:x + art.shape[1], :].shape[:2]
			layout[y:y + art.shape[0], x:x + art.shape[1], :][mask[:ly, :lx]] = art[:ly, :lx][mask[:ly, :lx]]
		else:
			rotated_art = rotate_image(art, -180 * tita / np.pi)
			min_x, min_y = contour.min(axis=0)
			min_x = int(np.max([min_x, 0]))
			min_y = int(np.max([min_y, 0]))
			max_x = int(np.min([min_x + rotated_art.shape[1], layout.shape[1]]))
			max_y = int(np.min([min_y + rotated_art.shape[0], layout.shape[0]]))
			rotated_art = rotated_art[:max_y - min_y, :max_x - min_x]
			layout[min_y:max_y, min_x:max_x, :][(rotated_art > 5) & (rotated_art < 255)] = rotated_art[
				(rotated_art > 5) & (rotated_art < 255)]
		return layout

	@staticmethod
	def get_gurobi_val(variable):
		if isinstance(variable, gp.Var):
			value = variable.x
		elif isinstance(variable, gp.LinExpr) or isinstance(variable, gp.QuadExpr):
			value = variable.getValue()
		else:
			value = variable
		return value

	def get_result_values(self, variables_names):
		if not isinstance(variables_names, list):
			variables_names = [variables_names]
		results = []
		for vn in variables_names:
			results.append(self.get_gurobi_val(getattr(self, vn)))
		return results if len(results) > 1 else results[0]

	def get_result_values_int(self, variables_names):
		results = self.get_result_values(variables_names)
		return [int(r + 0.5) for r in (results if isinstance(results, list) else [results])]

	def get_result_box(self):
		x, y, tita = self.get_absolute_coordinates(self.layout)
		values = [self.get_gurobi_val(variable) for variable in [x, y, self.w, self.h, tita, self.rot]]
		return values

	def __str__(self):
		return f"{self.name}({self.type})"

	def to_dict(self):
		x, y, w, h, tita, _ = self.get_box()
		contour = get_angled_box([x, y, w, h], tita)

		x, y, w, h = self.get_result_values_int(['x', 'y', 'w', 'h'])
		return {"x": x, "y": y, "w": w, "h": h}


class AdaptableUnit(Unit):
	def __init__(self, model, unit_type, layout, name):
		super(AdaptableUnit, self).__init__(model, unit_type, layout, name)
		self.color = (100, 0, 0)
		self.w = model.addVar(lb=self.range_w[0], ub=self.range_w[1], vtype=GRB.CONTINUOUS, name=name + '_w')
		self.h = model.addVar(lb=self.range_h[0], ub=self.range_h[1], vtype=GRB.CONTINUOUS, name=name + '_h')

	def get_box(self):
		x, y, tita = self.get_absolute_coordinates(self.layout)
		return x.getValue(), y.getValue(), self.w.x, self.h.x, tita.getValue(), self.rot


class RotatingUnit(Unit):
	def __init__(self, model, unit_type, layout, name):
		super(RotatingUnit, self).__init__(model, unit_type, layout, name)
		self.rot = model.addVar(vtype=GRB.BINARY, name=name + '_rotated')
		w0 = UNIT_INFO[unit_type]["w"][0]
		h0 = UNIT_INFO[unit_type]["h"][0]
		# self.w = w0 * (1 - self.rot) + h0 * self.rot
		# self.h = h0 * (1 - self.rot) + w0 * self.rot

		self.w = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name + '_w')
		self.h = model.addVar(lb=0, vtype=GRB.CONTINUOUS, name=name + '_h')

		self.rot = model.addVar(vtype=GRB.BINARY, name=name + '_rotated')
		model.addGenConstrIndicator(self.rot, True, self.h == w0)
		model.addGenConstrIndicator(self.rot, True, self.w == h0)
		model.addGenConstrIndicator(self.rot, False, self.w == w0)
		model.addGenConstrIndicator(self.rot, False, self.h == h0)

	def get_box(self):
		x, y, tita = self.get_absolute_coordinates(self.layout)
		return x.getValue(), y.getValue(), self.w.x, self.h.x, tita.getValue(), self.rot.x


class FullUnit(AdaptableUnit, RotatingUnit):
	def __init__(self, model, unit_type, layout, name):
		super(FullUnit, self).__init__(model, unit_type, layout, name)
		w0 = model.addVar(lb=self.range_w[0], ub=self.range_w[1], vtype=GRB.CONTINUOUS, name=name + '_w')
		h0 = model.addVar(lb=self.range_h[0], ub=self.range_h[1], vtype=GRB.CONTINUOUS, name=name + '_h')
		self.rot = model.addVar(vtype=GRB.BINARY, name=name + '_rotated')
		model.addGenConstrIndicator(self.rot, True, self.h == w0)
		model.addGenConstrIndicator(self.rot, True, self.w == h0)
		model.addGenConstrIndicator(self.rot, False, self.w == w0)
		model.addGenConstrIndicator(self.rot, False, self.h == h0)

	def get_box(self):
		x, y, tita = self.get_absolute_coordinates(self.layout)
		return x.getValue(), y.getValue(), self.w.x, self.h.x, tita.getValue(), self.rot.x


class WorkingStationUnit(RotatingUnit):
	def __init__(self, model, unit_type, layout, name, min_positions=4, max_positions=8):
		assert unit_type == 'A00', "WorkingStationUnits must be of type A00"
		super(WorkingStationUnit, self).__init__(model, unit_type, layout, name)
		self.color = (150, 0, 0)

		self.enabled = model.addVar(vtype=GRB.BINARY, name=name + '_enabled')

		# Adaptive height
		min_stacked, max_stacked = int(min_positions // 2), int(max_positions // 2)
		self.stacked = model.addVar(lb=min_stacked, ub=max_stacked, vtype=GRB.SEMIINT, name=name + '_stacked')

		model.addGenConstrIndicator(self.enabled, False, self.stacked == 0)
		model.addGenConstrIndicator(self.enabled, True, self.stacked >= min_stacked)

		w0 = UNIT_INFO[unit_type]["w"][0]  # Fixed width
		# h0 = model.addVar(lb=min_stacked * self.range_h[0], ub=max_stacked * self.range_h[0], vtype=GRB.CONTINUOUS,
		#                   name=name + '_h0')
		h0 = model.addVar(lb=0, ub=max_stacked * self.range_h[0], vtype=GRB.CONTINUOUS,
						  name=name + '_h0')
		model.addConstr(h0 == self.stacked * self.range_h[0])

		# Rotation
		self.rot = model.addVar(vtype=GRB.BINARY, name=name + '_rotated')

		self.w = model.addVar(vtype=GRB.CONTINUOUS, name=name + '_w')
		self.h = model.addVar(vtype=GRB.CONTINUOUS, name=name + '_h')

		model.addGenConstrIndicator(self.rot, True, self.h == w0 * self.enabled)
		model.addGenConstrIndicator(self.rot, True, self.w == h0)
		model.addGenConstrIndicator(self.rot, False, self.w == w0 * self.enabled)
		model.addGenConstrIndicator(self.rot, False, self.h == h0)

		model.addGenConstrIndicator(self.enabled, False, gp.quicksum(self.part_ind) == 0)
		model.addGenConstrIndicator(self.enabled, False, self.x == 0)
		model.addGenConstrIndicator(self.enabled, False, self.y == 0)
		model.addGenConstrIndicator(self.enabled, False, self.w == 0)
		model.addGenConstrIndicator(self.enabled, False, self.h == 0)
		model.addGenConstrIndicator(self.enabled, False, self.rot == 0)

	def get_box(self):
		x, y, tita = self.get_absolute_coordinates(self.layout)
		return x.getValue(), y.getValue(), self.w.x, self.h.x, tita.getValue(), self.rot.x

	def draw_in_layout(self, layout, show_unit_name=True, show_unit_art=False, show_contours=False):
		if self.enabled.x < 0.1:
			return layout

		x, y, w, h, tita, rot = self.get_box()
		n_places = 2 * int(self.stacked.x + 0.5)
		d = np.sqrt(w ** 2 + h ** 2)
		contour = get_angled_box([x, y, w, h], tita)
		if show_unit_art:
			if cv.imread("../modules/" + self.type + f"_{n_places}.png") is None:
				print("../modules/" + self.type + f"_{n_places}.png", self.stacked.x)
			layout = self.add_art(cv.imread("../modules/" + self.type + f"_{n_places}.png"), w, h, tita, rot,
								  self.orientation, self.type, contour, layout)

		if (not UNIT_INFO[self.type]["is-closed"] and show_contours) or UNIT_INFO[self.type]["is-closed"]:
			layout = cv.drawContours(layout, [contour[:, np.newaxis, :].astype(int)], -1, self.color, 8)
		if show_unit_name:
			layout = cv.putText(layout, str(self.type)[-3:],
								(int(sum(contour[:, 0]) / 4 - d // 8), int(sum(contour[:, 1]) / 4 - d // 8)),
								cv.FONT_HERSHEY_SIMPLEX, 2, self.color, 2, cv.LINE_AA)
			layout = cv.putText(layout, self.name,
								(int(sum(contour[:, 0]) / 4 - d // 8), int(sum(contour[:, 1]) / 4 - d // 8) + 100),
								cv.FONT_HERSHEY_SIMPLEX, 2, self.color, 2, cv.LINE_AA)
		return layout

	def __str__(self):
		try:
			x, y, w, h, tita, rot = self.get_box()
			return f"{self.name}: enabled: {int(self.enabled.x + 0.5)} | stacked: {int(self.stacked.x + 0.5)} | " \
				   f"origin: ({int(y + 0.5):04d}, {int(x + 0.5):04d}) | " \
				   f"size: ({int(h + 0.5):04d}, {int(w + 0.5):04d}) | rot: {int(rot + 0.5)}"
		except:
			return super(WorkingStationUnit, self).__str__()
