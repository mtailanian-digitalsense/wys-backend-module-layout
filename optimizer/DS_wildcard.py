# import cv2 as cv
import numpy as np
import gurobipy as gp
from itertools import product
from optimizer.DS_unit import Unit, UNIT_INFO
from optimizer.DS_feature import Feature, FeatureType


class Wildcard:
	def __init__(self, type, height, width):
		self.name = type
		self._height = height
		self._width = width

	@property
	def contour(self):
		return np.array([[0, 0], [0, self._height], [self._width, self._height], [self._width, 0]])

	@property
	def height(self):
		return self._height

	@property
	def width(self):
		return self._width

	def shift_contour(self, offset):
		row, col = offset
		return self.contour + np.array([col, row])

	def transpose(self):
		return Wildcard(self.name, self._width, self._height)


def bounding_box_limits(contour):
	top_left = np.array([contour[:, :, 1].min(), contour[:, :, 0].min()])
	bottom_right = np.array([contour[:, :, 1].max(), contour[:, :, 0].max()])
	return top_left, bottom_right


def draw_module(module_contour, output):
	cv.drawContours(output, [module_contour], 0, (80, 80, 80), thickness=cv.FILLED)
	cv.drawContours(output, [module_contour], 0, (0, 0, 0), thickness=2)


def add_module(layout, module, free_space_contour, mask):
	free_space_mask = cv.drawContours(np.zeros_like(mask), [free_space_contour], 0, (255, 255, 255),
									  thickness=cv.FILLED)
	free_space_mask[np.where(mask != 255)] = 0

	top_left, bottom_right = bounding_box_limits(free_space_contour)
	n_rows = (bottom_right[0] - top_left[0]) // module.height
	n_cols = (bottom_right[1] - top_left[1]) // module.width
	offsets = [np.array([0, 0]),
			   np.array([module.height // 2, module.width // 2]),
			   np.array([module.height // 4, module.width // 4])]
	modules = []
	for offset, n_col, n_row in product(offsets, range(n_cols), range(n_rows)):
		module_contour = module.shift_contour(top_left + np.array([(module.height + 1) * n_row,
																   (module.width + 1) * n_col]) + offset)
		module_mask = cv.drawContours(np.zeros_like(mask), [module_contour], 0, (255, 255, 255),
									  thickness=cv.FILLED)
		if can_be_placed(module_mask, free_space_mask):

			draw_module(module_contour, mask)
			remove_module_from_free_space(module_mask, free_space_mask)

			# Create dummy unit
			m = [top_left[1] + (module.width + 1) * n_col + offset[1],
				top_left[0] + (module.height + 1) * n_row + offset[0],
				module.width, module.height]
			u = Unit(gp.Model("Tmp"), module.name, layout, "")
			f_aux = Feature(FeatureType.Other, *m)
			f_aux.locate_in_partition(layout.partitions)
			u.part_ind = f_aux.part_ind
			u.x, u.y, u.w, u.h = f_aux.x, f_aux.y, module.width, module.height
			if np.sum(f_aux.part_ind) >= 1:
				modules.append(u)

	return modules


def remove_module_from_free_space(module_mask, free_space_mask):
	free_space_mask[np.where(module_mask == 255)] = 0


def can_be_placed(module_mask, free_space_mask):
	return np.all(module_mask & free_space_mask == module_mask)


def discard_small_contours(module, free_space_contours):
	return [contour for contour in free_space_contours if cv.contourArea(contour) >= cv.contourArea(module.contour)]


def add_wildcard_units(layout, units, wildcard_types):
	if not isinstance(wildcard_types, list):
		wildcard_types = [wildcard_types]
	mask = layout.get_occupation_map_with_units(units)
	mask = (255 * (1 - mask)).astype(np.uint8)
	output = mask.copy()
	wildcards = []
	for t in wildcard_types:
		module = Wildcard(t, UNIT_INFO[t]["w"][0], UNIT_INFO[t]["h"][0])
		free_space_contours = cv.findContours(output, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]
		free_space_contours = discard_small_contours(module, free_space_contours)
		for free_space_contour in free_space_contours:
			wildcards.extend(add_module(layout, module, free_space_contour, output))
			wildcards.extend(add_module(layout, module.transpose(), free_space_contour, output))
	return wildcards
