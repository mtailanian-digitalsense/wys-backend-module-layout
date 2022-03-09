import json
# import cv2 as cv
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon


def load_json(json_path):
	with open(json_path, 'r') as jsf:
		data = json.load(jsf)
	return data


def translate_layout_polygon(layout_polygon, show=False):

	# Partition
	partition = layout_polygon.convex_hull

	# Holes
	rectangle_polygons = []
	for hole in layout_polygon.convex_hull.difference(layout_polygon):  # layout_polygon.interiors:
		rectangle_polygons.extend(
			decompose_polygon_into_rectangles(hole)
		)

	if show:
		# Plot input
		plt.figure()
		plt.plot(*layout_polygon.exterior.xy)
		for pts in layout_polygon.interiors:
			plt.plot(*pts.xy)
		plt.axis('equal')

		# Plot translation
		plt.figure()
		plt.plot(*partition.exterior.xy)
		for p in rectangle_polygons:
			plt.plot(*p.exterior.xy)
		plt.axis('equal')

		plt.show()

	return partition, rectangle_polygons


def decompose_polygon_into_rectangles(polygon):
	poly_min_x, poly_min_y, poly_max_x, poly_max_y = polygon.bounds

	pts = np.array(polygon.exterior.xy).T
	pts -= np.array([poly_min_x, poly_min_y])  # Move origin to (0, 0)
	pts = np.array(pts, dtype=np.int)  # Already in centimeters

	mask_shape = (pts[:, 1].max() + 1, pts[:, 0].max() + 1)
	mask = np.zeros(mask_shape, dtype=np.uint8)
	cv.fillPoly(mask, [pts], 255)

	all_lines_mask = 255 * np.ones(mask_shape, dtype=np.uint8)
	for i in range(pts.shape[0] - 1):
		pt1 = pts[i]
		pt2 = pts[i + 1]

		if pt1[0] == pt2[0]:  # vertical line
			all_lines_mask[:, pt1[0]] = 0
		elif pt1[1] == pt2[1]:  # horizontal line
			all_lines_mask[pt1[1], :] = 0
		else:
			print("Diagonal line")

	all_lines_mask[mask == 0] = 0
	ret, markers = cv.connectedComponents(all_lines_mask)
	markers[mask == 0] = -1

	merged_markers, _ = merge_rectangles(markers, mask_shape)

	rectangle_polygons = []
	markers_ids = set(merged_markers.ravel()).difference({-1, 0})
	for m in markers_ids:
		blob = np.array(255 * (merged_markers == m), dtype=np.uint8)
		contour = np.vstack(cv.findContours(blob, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]).squeeze()

		# Convert coordinates again
		contour = contour.astype(np.float)
		contour += np.array([poly_min_x, poly_min_y])

		mins = np.min(contour, axis=0)
		maxs = np.max(contour, axis=0)
		x, y = mins
		w, h = maxs - mins

		rectangle_polygons.append(Polygon([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]]))

	return rectangle_polygons


def merge_rectangles(markers, mask_shape):
	labels = sorted(set(markers.ravel()).difference({-1, 0}))
	for i in labels:
		blob = np.array(255 * (markers == i), dtype=np.uint8)
		contour = np.vstack(cv.findContours(blob, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]).squeeze()
		mins = np.min(contour, axis=0) - 1
		maxs = np.max(contour, axis=0) + 1

		left = markers[mins[1] + 1:maxs[1], np.max([0, mins[0] - 1])]
		right = markers[mins[1] + 1:maxs[1], np.min([mask_shape[1] - 1, maxs[0] + 1])]
		top = markers[np.max([0, mins[1] - 1]), mins[0] + 1:maxs[0]]
		bottom = markers[np.min([mask_shape[0] - 1, maxs[1] + 1]), mins[0] + 1:maxs[0]]

		candidates = set.difference(
			set.union(set(left), set(right), set(bottom), set(top)),
			{-1, 0, i}
		)

		for c in sorted(candidates):
			candidate_blob = np.array(255 * (markers == c), dtype=np.uint8)
			candidate_contour = np.vstack(cv.findContours(candidate_blob, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)[0]).squeeze()
			merged_contour = np.vstack([contour, candidate_contour])
			merged_mins = np.min(merged_contour, axis=0)
			merged_maxs = np.max(merged_contour, axis=0)

			merged_zones = set(markers[merged_mins[1]:merged_maxs[1] + 1, merged_mins[0]:merged_maxs[0] + 1].ravel())
			merged_is_rectangle = merged_zones.issubset({0, i, c})

			if merged_is_rectangle:
				markers[markers == c] = i
				print(f"Merged {c} into {i}")
				markers, finished = merge_rectangles(markers, mask_shape)
				if finished:
					return markers, True

	return markers, True


def get_angled_box(box, tita):
	x, y, w, h = box
	return np.array([[x, y],
					 [x + np.cos(tita) * w, y + np.sin(tita) * w],
					 [x + np.cos(tita) * w - np.sin(tita) * h, y + np.sin(tita) * w + np.cos(tita) * h],
					 [x - np.sin(tita) * h, y + np.cos(tita) * h]])


def rotate_image(image, angle):

	h, w = image.shape[0], image.shape[1]
	c_y, c_x = h // 2, w // 2

	rotationMatrix = cv.getRotationMatrix2D((c_x, c_y), angle, 1.0)
	cos_a = np.abs(rotationMatrix[0][0])
	sin_a = np.abs(rotationMatrix[0][1])

	# Compute out image size
	w_out = int((h * sin_a) + (w * cos_a))
	h_out = int((h * cos_a) + (w * sin_a))

	# Update rotation matrix
	rotationMatrix[0][2] += (w_out / 2) - c_x
	rotationMatrix[1][2] += (h_out / 2) - c_y

	# Rotate
	out = cv.warpAffine(image, rotationMatrix, (w_out, h_out))

	return out


def get_in_size(str_, as_size):
	payload_pre = (as_size - len(str_)) // 2
	payload_post = (as_size - len(str_)) - payload_pre
	return " " * payload_pre + str_ + " " * payload_post


def print_list(list_, n_columns, title="", offset=""):
	n = len(list_)
	n_rows = n // n_columns + 1
	if n == 0:
		return offset + title + "[]\n"
	str_ = offset + title
	title_offset = len(title) * " "
	size_columns = []
	for j in range(n_columns):
		column = [s for s in [list_[j+ i * n_columns] for i in range(n_rows) if j + i * n_columns < n]]
		size_columns.append(0 if not column else max([len(str(s)) for s in column]))
	for i in range(max(n_rows, 1)):
		if i > 0:
			str_ += offset + title_offset
		for j in range(n_columns):
			if j + i * n_columns < n:
				str_ += get_in_size(str(list_[n_columns * i + j]), size_columns[j] + 4)
			else:
				str_ += ((size_columns[j] + 4) * " ")
		str_ += "\n"
	return str_
