import numpy as np
from enum import Enum
from optimizer.DS_utils import get_angled_box


class FeatureType(Enum):
	Window = 1
	Entrance = 2
	Column = 3
	Circulation = 4
	Core = 5
	Shaft = 6
	Other = 7


class Feature:
	def __init__(self, feature_type: FeatureType,
	             x: float, y: float, w: float, h: float, tita: float = 0, name: str = ''):
		"""
		Feature object such as Window, column or entrance.
		:param feature_type: One of {FeatureType.Window, FeatureType.Column, FeatureType.Entrance}
		:param x: horizontal coordinate of partition in the layout.
		:param y: vertical coordinate of partition in the layout.
		:param w: width
		:param h: height
		:param tita: angle
		:param name: descriptive unique name
		"""
		if feature_type in FeatureType:
			self.type = FeatureType(feature_type)
		else:
			self.type = FeatureType[feature_type]
		self.x_glob = x
		self.y_glob = y
		self.w = w
		self.h = h
		self.tita_glob = tita
		self.name = name
		self.part_ind = []
		self.part_idx = None
		self.x = None
		self.y = None
		self.tita = None
		self.norm = np.r_[np.cos(self.tita_glob), np.sin(self.tita_glob)]
		self.relative_info = {}
		self.color = {FeatureType.Window: (0, 0, 220),
		              FeatureType.Column: (255, 0, 0),
		              FeatureType.Entrance: (0, 100, 0),
		              FeatureType.Circulation: (35, 35, 35),
		              FeatureType.Core: (255, 255, 0),
		              FeatureType.Shaft: (220, 120, 120),
		              FeatureType.Other: (180, 220, 220)
		              }[self.type]

	def is_in_contact(self, feature, oriented=False):
		points = [[max(self.x_glob, feature.x_glob), max(self.y_glob, feature.y_glob)],
				  [min(self.x_glob + self.w, feature.x_glob + feature.w),
				   min(self.y_glob + self.h, feature.y_glob + feature.h)]]
		if oriented:
			same_oriented = (self.w >= self.h) and (feature.w >= self.h) or (self.w < self.h) and (feature.w < self.h)
			return points[0][0] <= points[1][0] and points[0][1] <= points[1][1] \
				   and feature.tita_glob == self.tita_glob \
				   and same_oriented
		else:
			return points[0][0] <= points[1][0] and points[0][1] <= points[1][1]

	def get_pos_relative_to_partition(self, partition):
		contour = get_angled_box([self.x_glob, self.y_glob, self.w, self.h], self.tita_glob)
		box = np.array([partition.base.dot(u - np.r_[partition.x_glob, partition.y_glob]) for u in contour])
		new_bot = (min(box[:, 0]), min(box[:, 1]))
		new_w, new_h = (max(max(box[:, 0])-new_bot[0], 0), max(max(box[:, 1])-new_bot[1], 0))

		return map(int, [new_bot[0], new_bot[1], new_w, new_h])

	def get_center_relative_to_partition(self, partition):
		c_glob = np.r_[self.x_glob + 0.5 * self.w * np.cos(self.tita_glob) - 0.5 * self.h * np.sin(self.tita_glob),
					   self.y_glob + 0.5 * self.h * np.cos(self.tita_glob) + 0.5 * self.w * np.sin(self.tita_glob)]

		return partition.base.dot(c_glob - np.r_[partition.x_glob, partition.y_glob]).astype(int)

	def get_absolute_center(self, c_rel, partition):
		return (partition.base_t.dot(c_rel) + np.r_[partition.x_glob, partition.y_glob]).astype(int)

	def locate_in_partition(self, partitions):
		'''
		Getting the coordinates of the feature for the given partitions
		'''
		for i, p in enumerate(partitions):
			x, y, w, h = self.get_pos_relative_to_partition(p)
			c = self.get_center_relative_to_partition(p)

			if self.type == FeatureType.Circulation:
				c = np.r_[max(0, min(p.w, c[0])), max(0, min(p.h, c[1]))]
			self.relative_info[i] = {
								"position": np.r_[x, y],
								"center": c,
								"same-orientation": self.tita_glob == p.tita_glob,
			}
			if self.type == FeatureType.Entrance:
				print(max(x + p.x_glob, p.x_glob), min(x + w + p.x_glob, p.x_glob + p.w))
				print(max(y + p.y_glob, p.y_glob), min(y + h + p.y_glob, p.y_glob + p.h))
				print(self.tita_glob, p.tita_glob)
				print("----")

			if (max(x + p.x_glob, p.x_glob) <= min(x + w + p.x_glob, p.x_glob + p.w)) and \
					(max(y + p.y_glob, p.y_glob) <= min(y + h + p.y_glob, p.y_glob + p.h)) and self.tita_glob == p.tita_glob:

				if self.part_idx is None:
					self.part_idx = []
				# self.x, self.y = max(0, min(x, p.w)), max(0, min(y, p.h))
				self.x, self.y = x, y
				self.tita = 0

				self.part_ind.append(1)
				self.part_idx.append(i)
			else:
				self.part_ind.append(0)

	def to_dict(self):
		return {
			"feature_type": self.type.value, "x": self.x_glob, "y": self.y_glob, "w": self.w, "h": self.h,
			"tita": self.tita_glob, "name": self.name
		}

	def __str__(self):
		return f"{self.name}({self.type.name})"
