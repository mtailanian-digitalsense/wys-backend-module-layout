# import cv2 as cv
import numpy as np
from optimizer.DS_feature import FeatureType
from optimizer.DS_utils import get_angled_box


class Partition:
	"""
	Partition of a layout.
	ind: Partition index in the layout.
	x: horizontal coordinate of partition in the layout.
	y: vertical coordinate of partition in the layout.
	tita: Angle with respect to horizontal of the partition in the layout.
	w: Width.
	h: Height.
	"""
	def __init__(self, ind: int, x: float, y: float, w: float, h: float, tita: float):
		self.ind = ind
		self.x_glob = x
		self.y_glob = y
		self.w = w
		self.h = h
		self.tita_glob = tita
		# self.units = []
		# self.features = []

		self.rot = 0

		self.base = np.array([[np.cos(self.tita_glob), np.sin(self.tita_glob)], [-np.sin(self.tita_glob), np.cos(self.tita_glob)]])
		self.base_t = self.base.transpose()
		self.contour = get_angled_box((self.x_glob, self.y_glob, self.w, self.h), self.tita_glob)

	def draw(self, layout_image, offset=0):
		if self.tita_glob == 0:
			return cv.rectangle(
				layout_image,
				(int(self.x_glob + offset), int(self.y_glob + offset)),
			    (int(self.x_glob + self.w + offset), int(self.y_glob + self.h + offset)),
				color=(0, 128, 0),
				thickness=6
			)
		else:
			contour = self.contour[:, np.newaxis, :].astype(int)
			return cv.drawContours(layout_image, [contour], -1, (0, 128, 0), 6)

	def get_rot_sense(self, features):
		windows = [f for f in features if f.type == FeatureType.Window]
		if not windows:
			self.rot = 0
		else:
			concerned = [w for w in windows if w.part_ind[self.ind-1]]
			if not concerned:
				self.rot = 0
			else:
				rots = np.array([w.w == 0 for w in concerned])
				sizes = np.array([max(w.w, w.h) for w in concerned])
				self.rot = int(rots[np.where(sizes == np.amax(sizes))[0]][0])

	def to_dict(self):
		return {
			"ind": self.ind, "x": self.x_glob, "y": self.y_glob, "w": self.w, "h": self.h, "tita": self.tita_glob
		}
