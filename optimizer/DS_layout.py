# import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as plp

from optimizer.DS_partition import Partition
from optimizer.DS_utils import translate_layout_polygon
from optimizer.DS_feature import Feature, FeatureType
from optimizer.DS_utils import load_json, get_angled_box, decompose_polygon_into_rectangles


class Layout:
	def __init__(self, partitions, features, background):
		self.partitions = partitions
		self.features = features
		self.start_point = background['spoint']
		self.final_point = background['fpoint']
		self.background = background['img']

		# Define width and height
		self.w, self.h = 0, 0
		for p in self.partitions:
			box = get_angled_box([p.x_glob, p.y_glob, p.w, p.h], p.tita_glob).astype(int)
			self.w = np.max([self.w] + list(box[:, 0]))
			self.h = np.max([self.h] + list(box[:, 1]))

		# Locate features in partitions
		for f in self.features:
			f.locate_in_partition(self.partitions)

	@classmethod
	def load(cls, ac3e_planta, ac3e_cores, ac3e_shafts, ac3e_circulations, ac3e_entrances, ac3e_windows, show=0):

		if show >= 2:
			plt.figure()
			plt.plot(*ac3e_planta.exterior.xy, color='k')
			for c in ac3e_cores:
				plt.plot(*c.exterior.xy, color='k')
			for c in ac3e_circulations:
				plt.plot(*c.exterior.xy, color='m')
			for s in ac3e_shafts:
				plt.plot(*s.exterior.xy, color='r')
			for s in ac3e_entrances:
				plt.plot(*s.exterior.xy, color='g')
			for w in ac3e_windows:
				plt.plot(*w.exterior.xy, color='b')
			plt.axis('equal')
			plt.title('Original data')

		partition_polygon, decomposed_polygons = translate_layout_polygon(ac3e_planta)

		decomposed_circulations = []
		for c in ac3e_circulations:
			decomposed_circulations.extend(decompose_polygon_into_rectangles(c))

		min_x, min_y, max_x, max_y = ac3e_planta.exterior.bounds
		h = int(np.round(max_y - min_y))
		w = int(np.round(max_x - min_x))
		origin_x = min_x
		origin_y = min_y

		# TODO: faltan zonas de circulacion
		# TODO pueden haber cosas repetidas. por ejemplo la planta ya incluye el core y el shaft
		partition = cls.load_partition(partition_polygon, origin_x, origin_y)
		features = cls.load_ac3e_features(decomposed_polygons, FeatureType.Other, origin_x, origin_y)
		entrances = cls.load_ac3e_features(ac3e_entrances, FeatureType.Entrance, origin_x, origin_y)
		cores = cls.load_ac3e_features(ac3e_cores, FeatureType.Core, origin_x, origin_y)
		shafts = cls.load_ac3e_features(ac3e_shafts, FeatureType.Shaft, origin_x, origin_y)
		windows = cls.load_ac3e_features(ac3e_windows, FeatureType.Window, origin_x, origin_y)
		circulations = cls.load_ac3e_features(decomposed_circulations, FeatureType.Circulation, origin_x, origin_y)

		# TODO: background
		offset = 200
		background = {
			'img': 255 * np.ones((h + 2 * offset, w + 2 * offset, 3), dtype=np.uint8),
			'spoint': (offset, offset),
			'fpoint': (w - offset, h - offset)
		}

		if show >= 2:
			def draw_features(features: list, offset: int, color: str):
				for f in features:
					plt.gca().add_patch(plp.Rectangle((int(f.x_glob + offset), int(f.y_glob + offset)), int(f.w), int(f.h),
					                                  edgecolor=color,
					                                  facecolor='none',
					                                  lw=1)
					                    )
			plt.figure()
			plt.imshow(background['img'])
			draw_features([partition], offset, 'black')
			draw_features(features, offset, 'black')
			draw_features(entrances, offset, 'green')
			draw_features(windows, offset, 'blue')
			draw_features(cores, offset, 'black')
			draw_features(shafts, offset, 'red')
			draw_features(circulations, offset, 'magenta')
			plt.title('Translated')
			plt.gca().invert_yaxis()
			plt.show()

		features += entrances + windows + cores + shafts + circulations

		return cls([partition], features, background)

	@classmethod
	def load_ac3e_features(cls, ac3e_features, feature_type, origin_x, origin_y):
		if not isinstance(ac3e_features, list):
			ac3e_features = [ac3e_features]

		features = []
		for i, feature_polygon in enumerate(ac3e_features):
			min_x, min_y, max_x, max_y = feature_polygon.exterior.bounds
			features.append(
				Feature(
					feature_type,
					min_x - origin_x,
					min_y - origin_y,
					max_x - min_x,
					max_y - min_y,
					tita=0,
					name=f"{feature_type.name}_{i:02d}"
				)
			)
		return features

	@classmethod
	def load_partition(cls, planta, origin_x, origin_y):
		min_x, min_y, max_x, max_y = planta.exterior.bounds
		return Partition(1, min_x - origin_x, min_y - origin_y, max_x - min_x, max_y - min_y, 0)

	@classmethod
	def load_legacy(cls, config_path):
		data = load_json(config_path)

		# Partitions
		partitions = [Partition(**dp) for dp in data["partitions"]]

		# Features
		i = 0
		for df in data["features"]:
			if "name" not in df or df["name"] == "":
				df["name"] = "feature_{0:04d}".format(i)
				i += 1
		features = [Feature(**df) for df in data["features"]]

		# Background
		background = {'img': 255 * np.ones([100, 100, 3]).astype(np.uint8), 'spoint': (0, 0), 'fpoint': (100, 100)}
		if "background" in data.keys():
			bg_data = data["background"]
			if (bg_data is not None) and \
			   ("img_path" in bg_data.keys()) and ("spoint" in bg_data.keys()) and ("fpoint" in bg_data.keys()):
				background = {'img': cv.imread(bg_data["img_path"])[:, :, [2, 1, 0]],
				              'spoint': bg_data["spoint"], 'fpoint': bg_data["fpoint"]}

		return cls(partitions, features, background)

	def get_features(self, *feature_types):
		return self.features if not feature_types else [f for f in self.features if f.type in feature_types]

	def get_partitions(self):
		return self.partitions

	def get_occupation_map_with_units(self, units):
		mask = np.zeros([self.h, self.w])
		for f in self.features:
			mask[f.y_glob:f.y_glob + f.h + 1, f.x_glob:f.x_glob + f.w + 1] = 1
		for u in units:
			x, y, w, h = u.get_result_values_int(['x', 'y', 'w', 'h'])
			mask = cv.rectangle(mask, (x, y), (x + w, y + h), 1, -1)
		return mask

	def draw(self, show_features=False):
		# Adding background
		fx = self.w / (self.final_point[0] - self.start_point[0])
		fy = self.h / (self.final_point[1] - self.start_point[1])
		sp = (int(self.start_point[0] * fx), int(self.start_point[1] * fy))
		fp = (int(self.final_point[0] * fx), int(self.final_point[1] * fy))

		background_img = cv.resize(self.background, None, fx=fx, fy=fy)[sp[1]:fp[1], sp[0]:fp[0], :]
		background_img = cv.rectangle(background_img, (0, 0), (self.w, self.h), (0, 0, 0), 4)

		offset = 0
		layout_img = 255 * np.ones(background_img.shape + np.array([2 * offset, 2 * offset, 0]), dtype=np.uint8)

		for p in self.partitions:
			layout_img = p.draw(layout_img, offset)
		for f in self.features:
			if (f.type == FeatureType.Window) or (f.type == FeatureType.Entrance):

				origin_int = (int(f.x_glob) + offset, int(f.y_glob) + offset)
				end_int = (int(f.x_glob + f.w + offset), int(f.y_glob + f.h + offset))
				layout_img = cv.rectangle(layout_img, origin_int, end_int, f.color, -1)

				# layout_img = cv.line(
				# 	layout_img,
				#     (int(f.x_glob), int(f.y_glob)),
				#     (int(f.x_glob + f.w * f.norm[0] + f.h * f.norm[1]), int(f.y_glob + f.w * f.norm[1] + f.h * f.norm[0])),
				#     f.color,
				# 	16
				# )

			elif f.type == FeatureType.Column or f.type == FeatureType.Other or f.type == FeatureType.Circulation or \
					f.type == FeatureType.Shaft:
				if show_features:
					# TODO: fix and do not use the following if statement
					if f.tita_glob == 0.0:
						origin_int = (int(f.x_glob) + offset, int(f.y_glob) + offset)
						end_int = (int(f.x_glob + f.w) + offset, int(f.y_glob + f.h) + offset)
						layout_img = cv.rectangle(layout_img, origin_int, end_int, f.color, -1)
					else:
						contour = get_angled_box([f.x_glob, f.y_glob, f.w, f.h], f.tita_glob)[:, np.newaxis, :].\
							astype(int)

						# TODO: check for offset != 0
						layout_img = cv.drawContours(layout_img, [contour + np.array([offset, offset])], -1, f.color,
						                             thickness=-1)
		return layout_img
