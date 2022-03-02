import cv2 as cv
import numpy as np
from optimizer.DS_unit import UNIT_INFO
from shapely.geometry import Polygon
from optimizer.DS_utils import print_list
from optimizer.DS_feature import FeatureType


def draw_polygon(image, p):
    int_coords = lambda x: np.array(x).round().astype(np.int32)
    exterior = [int_coords(p.exterior.coords)]
    return cv.polylines(image, exterior, False, 255)


def polygon_from_box(x, y, w, h):
    return Polygon([[x, y], [x + w, y], [x + w, y + h], [x, y + h], [x, y]])


def polygon_from_unit(unit):
    x, y, w, h = unit.get_result_values_int(['x', 'y', 'w', 'h'])
    return polygon_from_box(x, y, w, h)


def get_segments_intersection(s1_origin, s1_length, s2_origin, s2_length):
    return list(range(max(s1_origin, s2_origin), min(s1_origin + s1_length, s2_origin + s2_length) + 1))


def intersect_segments(s1_origin, s1_length, s2_origin, s2_length):
    return len(get_segments_intersection(s1_origin, s1_length, s2_origin, s2_length)) > 1


def intersect_segment_point(point, s1_origin, s1_length):
    return (s1_origin <= point) and (point <= s1_origin + s1_length)


class PostProcess:
    def __init__(self, **kwargs):
        self.signature = "GenericPostProcess"
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


class PostProcessOrientToCirculation(PostProcess):
    def __init__(self, units, circulations):
        super(PostProcessOrientToCirculation, self).__init__(units=units, circulations=circulations)
        self.signature = "PostProcess-OrientToCirculation"

        self.units = units
        self.circulations = circulations

    def apply(self, variables):
        for unit in self.units:
            self.apply_to_single_unit(unit, self.circulations, variables)

    @staticmethod
    def apply_to_single_unit(unit, circulations, variables):
        # HYPOTHESIS: The default orientation for a unit (unit.orientation = [1, 1]) is meant to be correct for the module
        # being above or at the left of the circulation
        assert variables is not None, "The variables must be provided to this task!"

        for circulation in circulations:
            if (unit.name, circulation.name) not in variables:
                print(f"Could not retrieve information about {unit.name} and {circulation.name}")
                continue

            adj_var = variables[(unit.name, circulation.name)]["Constr-MakeItAccessible"]["booleans"]["adjacency"]
            left_above = variables[(unit.name, circulation.name)]["Constr-MakeItAccessible"]["booleans"][
                "left-or-above"]
            right_below = variables[(unit.name, circulation.name)]["Constr-MakeItAccessible"]["booleans"][
                "right-or-below"]

            if int(adj_var.x + 0.5):
                # Setting orientation
                if int(left_above.x + 0.5):
                    unit.orientation = [1, 1]
                elif int(right_below.x + 0.5):
                    unit.orientation = [-1, -1]
                    print(f"Unit:{unit.name} flipped!")

                # Setting door placement
                if circulation.w >= circulation.h:  # Horizontal case
                    unit.door_is_below = (int(unit.rot.x + 0.5) == 0)
                else:  # Vertical case
                    unit.door_is_below = (int(unit.rot.x + 0.5) == 1)


def orient_unit_according_to_the_circulation(unit, circulations, variables):
    # HYPOTHESIS: The default orientation for a unit (unit.orientation = [1, 1]) is meant to be correct for the module
    # being above or at the left of the circulation
    assert variables is not None, "The variables must be provided to this task!"

    for circulation in circulations:
        if (unit.name, circulation.name) not in variables:
            print(f"Could not retrieve information about {unit.name} and {circulation.name}")
            continue

        print(unit.name, variables[(unit.name, circulation.name)].keys())
        try:
            adj_var = variables[(unit.name, circulation.name)]["booleans"]["adjacency"]
            left_above = variables[(unit.name, circulation.name)]["booleans"]["left-or-above"]
            right_below = variables[(unit.name, circulation.name)]["booleans"]["right-or-below"]
        except:
            continue

        if int(adj_var.x + 0.5):
            # Setting orientation
            if int(left_above.x + 0.5):
                unit.orientation = [1, 1]
            elif int(right_below.x + 0.5):
                unit.orientation = [-1, -1]
                print(f"Unit:{unit.name} flipped!")

            # Setting door placement
            if circulation.w >= circulation.h:  # Horizontal case
                unit.door_is_below = (int(unit.rot.x + 0.5) == 0)
            else:  # Vertical case
                unit.door_is_below = (int(unit.rot.x + 0.5) == 1)
    print()


def expand(unit_orig, unit_length, feat_orig, feat_length, vect_mask, tol, partition_length, partition_tol):
    new_origin, new_length = unit_orig, unit_length
    expanded = False
    if intersect_segment_point(unit_orig + unit_length, feat_orig - tol, feat_length + tol):
        new_length = feat_orig + feat_length - unit_orig
        new_origin = unit_orig
        expanded = True
    elif intersect_segment_point(unit_orig, feat_orig, feat_length + tol):
        new_length = unit_orig + unit_length - feat_orig
        new_origin = feat_orig
        expanded = True

    # Check for features interference
    start, end = None, None
    if new_origin < unit_orig:
        start, end = unit_orig, new_origin
    elif (new_origin == unit_orig) and new_length > unit_length:
        start, end = unit_orig + unit_length, unit_orig + new_length

    if start is not None:
        direction = 1 if start < end else -1
        range_min, range_max = np.min([start, end]), np.max([start, end])
        for candidate in range(start + direction, end + direction, direction):
            range_min, range_max = np.min([candidate, start + direction]), np.max([candidate, start + direction])
            if np.sum(vect_mask[range_min:range_max]) > 2:
                break
        new_origin = np.min([unit_orig, range_min])
        new_length = np.max([unit_orig + unit_length, range_max]) - new_origin

    # If close to borders, expand more
    if new_origin < partition_tol:
        new_length = new_length + new_origin
        new_origin = 0
        expanded = True
    if (new_origin + new_length) > (partition_length - partition_tol):
        new_length = partition_length - new_origin
        expanded = True

    return expanded, new_origin, new_length


class DummyUnit:
    def __init__(self, x, y, w, h):
        self.x, self.y, self.w, self.h = x, y, w, h


def create_mask(partitions, p_ind, features, units):
    partition_units = [u for u in units if u.part_ind[p_ind].x > 0.5]
    partition_features = [f for f in features if f.type != FeatureType.Column and f.part_ind[p_ind] > 0.5]
    mask = np.zeros((partitions[p_ind].h, partitions[p_ind].w))
    for f in partition_features:
        mask = cv.rectangle(mask, (f.x, f.y), (f.x + f.w, f.y + f.h), 1, -1)
    for u in partition_units:
        x, y, w, h = u.get_result_values_int(['x', 'y', 'w', 'h'])
        mask = cv.rectangle(mask, (x, y), (x + w, y + h), 1, -1)
    return mask


def column_modulation(partitions, all_units, all_features, tol_cm=50, border_tol_cm=50):
    columns = [f for f in all_features if f.type == FeatureType.Column]

    closed_units = [u for u in all_units if UNIT_INFO[u.type]["is-closed"]]
    open_units = [u for u in all_units if not UNIT_INFO[u.type]["is-closed"]]
    in_closed_units = [DummyUnit(*u.get_result_values_int(['x', 'y', 'w', 'h'])) for u in closed_units]

    for p_ind, p in enumerate(partitions):
        p_mask = create_mask(partitions, p_ind, all_features, all_units)
        # original_polygons = [polygon_from_unit(u) for u in units if u.part_ind[p_ind].x > 0.5]
        for u in closed_units:
            if u.part_ind[p_ind].x < 0.5:
                continue
            x, y, w, h = u.get_result_values_int(['x', 'y', 'w', 'h'])
            for f in columns:
                if u.part_ind[p_ind].x < 0.5:
                    continue
                if any([aux is None for aux in [x, y, w, h, f.x, f.y, f.w, f.h]]):
                    continue

                expanded = False
                # Expand vertically
                if intersect_segments(x, w, f.x, f.w):
                    _, y, h = expand(y, h, f.y, f.h, np.sum(p_mask[:, x+1:x+w], axis=1), tol_cm, p.h, border_tol_cm)
                # Expand horizontally
                if intersect_segments(y, h, f.y, f.h):
                    expanded, x, w = expand(x, w, f.x, f.w, np.sum(p_mask[y+1:y+h, :], axis=0), tol_cm, p.w, border_tol_cm)
                # If expanded horizontally, expand vertically again
                if expanded and intersect_segments(x, w, f.x, f.w):
                    _, y, h = expand(y, h, f.y, f.h, np.sum(p_mask[:, x+1:x+w], axis=1), tol_cm, p.h, border_tol_cm)

                # Update unit
                u.x, u.y, u.w, u.h = x, y, w, h

        # Detect overlapping units
        for i in range(len(closed_units)):
            for j in range(i + 1, len(closed_units)):
                if (closed_units[i].part_ind[p_ind].x < 0.5) or (closed_units[j].part_ind[p_ind].x < 0.5):
                    continue
                xi, yi, wi, hi = closed_units[i].get_result_values_int(['x', 'y', 'w', 'h'])
                xj, yj, wj, hj = closed_units[j].get_result_values_int(['x', 'y', 'w', 'h'])
                pi, pj = polygon_from_unit(closed_units[i]), polygon_from_unit(closed_units[j])

                if pi.intersection(pj).area > 1:
                    intersection_h = get_segments_intersection(xi, wi, xj, wj)
                    intersection_v = get_segments_intersection(yi, hi, yj, hj)
                    if len(intersection_h) / ((wi + wj) / 2) > len(intersection_v) / ((hi + hj) / 2):
                        above, below = [i, j] if yi + hi / 2 < yj + hj / 2 else [j, i]
                        mid_point = (in_closed_units[above].y + in_closed_units[above].h + in_closed_units[below].y) / 2
                        closed_units[above].h = mid_point - in_closed_units[above].y
                        closed_units[below].h = in_closed_units[below].y + in_closed_units[below].h - mid_point
                        closed_units[below].y = mid_point
                    else:
                        left, right = [i, j] if xi + wi / 2 < xj + wj / 2 else [j, i]
                        mid_point = (in_closed_units[left].x + in_closed_units[left].w + in_closed_units[right].x) / 2
                        closed_units[left].w = mid_point - in_closed_units[left].x
                        closed_units[right].w = in_closed_units[right].x + in_closed_units[right].w - mid_point
                        closed_units[right].x = mid_point

    return closed_units + open_units
