import random
import time
import math
import rtree
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
from shapely import geometry, affinity
from shapely.geometry import Point, box, LineString, MultiLineString, MultiPolygon
from shapely.geometry.polygon import Polygon
from shapely.ops import unary_union, polygonize, linemerge, substring
import matplotlib.pyplot as plt

import viewer
import restrictions
from randrange import randrange
from get_areas import get_area
from get_areas2 import get_area2
#from lines_areas_test import get_pol_zones
random.seed(100)

def get_input(dictionary):
    Planta = dictionary.get('selected_floor').get('polygons')
    Workspaces = dictionary.get('workspaces')
    plant = []

    outline = []
    holes = []
    areas = []

    for Area in Planta:
        plant.append(
            [Area.get('name'), [(round(a.get('x') / 100, 1), round(a.get('y') / 100, 1)) for a in Area.get('points')]])

    for p in plant:
        if p[0] == 'WYS_AREA_UTIL':
            outline.append(p)
        elif p[0] == 'WYS_HOLE':
            holes.append(p)
        else:
            areas.append(p)

    input_list = []

    for ws in Workspaces:
        input_list.append([ws.get('name'), ws.get('quantity'), ws.get('width'), ws.get('height'), ws.get('category_id')])

    return outline, holes, areas, input_list


class Floor:
    def __init__(self, outline_points, holes_list):
        self.outline = outline_points
        self.holes = holes_list


class Module:
    def __init__(self, x, y, rotation, name, identificator, width_value, height_value, qty, fitval1, fitval2):
        self.x = x
        self.y = y
        self.rot = rotation
        self.name = name
        self.id = identificator
        self.width = width_value
        self.height = height_value
        self.qty = qty
        self.fitval1 = fitval1
        self.fitval2 = fitval2

    def show(self):
        print(self.name, self.x, self.y, self.rot, self.id, self.width, self.height, self.qty)

    def get_box(self):
        return box(self.x - self.width / 2, self.y - self.height / 2, self.x + self.width / 2, self.y + self.height / 2)


makeposcnt = 0
curr_bx = []

def select_zone(zones, zone, mod_cat, n):
    
    z_names_qty = 0
    if mod_cat == 1:
        z_names = [k for k,v in zones.items() if 'ZONA SALAS REUNION FORMAL' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA SALAS REUNION FORMAL ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA SALAS REUNION FORMAL 0']
    elif mod_cat == 2:
        z_names = [k for k,v in zones.items() if 'ZONA PUESTOS DE TRABAJO' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA PUESTOS DE TRABAJO ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA PUESTOS DE TRABAJO 0']
    elif mod_cat == 3:
        z_names = [k for k,v in zones.items() if 'ZONA TRABAJO PRIVADO' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA TRABAJO PRIVADO ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA TRABAJO PRIVADO 0']
    elif mod_cat == 4:
        z_names = [k for k,v in zones.items() if 'ZONA SERVICIOS' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA SERVICIOS ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA SERVICIOS 0']
    elif mod_cat == 5:
        z_names = [k for k,v in zones.items() if 'ZONA SOPORTE' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA SOPORTE ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA SOPORTE 0']
    elif mod_cat == 6:
        z_names = [k for k,v in zones.items() if 'ZONA REUNIONES INFORMALES' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA REUNIONES INFORMALES ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA REUNIONES INFORMALES 0']
    elif mod_cat == 7:
        z_names = [k for k,v in zones.items() if 'ZONA ESPECIALES' in k]
        z_names_qty = len(z_names)
        if z_names_qty > 1:
            zone = zones['ZONA ESPECIALES ' + str(n%(z_names_qty))]
        elif z_names_qty == 1:
            zone = zones['ZONA ESPECIALES 0']

    return zone, z_names_qty

def makePos(planta, in_list, zones):
    make_time = time.time()
    global makeposcnt
    global curr_bx
    in_cnt = 0
    z = []

    mod = Module(0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

    for j in range(len(in_list)):
        for n in range(in_list[j][1]):
            if in_cnt == makeposcnt:
                mod.name = in_list[j][0]
                mod.qty = in_list[j][1]
                mod.width = round(in_list[j][2], 1)
                mod.height = round(in_list[j][3], 1)
                mod_cat = in_list[j][4]
            in_cnt+=1

    '''if mod_cat == 1:
        z = [z[0] for z in zones if 'ZONA SALAS REUNION FORMAL' in z[1]]
    elif mod_cat == 2:
        z = [z[0] for z in zones if 'ZONA PUESTOS DE TRABAJO' in z[1]]
    elif mod_cat == 3:
        z = [z[0] for z in zones if 'ZONA TRABAJO PRIVADO' in z[1]]
    elif mod_cat == 4:
        z = [z[0] for z in zones if 'ZONA SERVICIOS' in z[1]]
    elif mod_cat == 5:
        z = [z[0] for z in zones if 'ZONA SOPORTE' in z[1]]
    elif mod_cat == 6:
        z = [z[0] for z in zones if 'ZONA REUNIONES INFORMALES' in z[1]]
    elif mod_cat == 7:
        z = [z[0] for z in zones if 'ZONA ESPECIALES' in z[1]]'''

    zone = None
    zone, zones_qty = select_zone(zones, zone, mod_cat, makeposcnt)
    
    if zone:
        minx, miny, maxx, maxy = zone.bounds
    else:
        minx, miny, maxx, maxy = planta.bounds
    
    #print(round(time.time() - start_time, 2), len(curr_bx), mod.name)
    #print(mod.name)
    rot = False
    larger_than_zone = False
    pos_retries = 0
    zones_idx = makeposcnt
    positional_time_limit = 0.08
    overlap_time_limit = 0.05
    while True:
        if time.time() - make_time > 3*(positional_time_limit + overlap_time_limit) and not larger_than_zone:
            make_time = time.time()
            zones_idx += 1
            pos_retries += 1
            zone, zones_qty = select_zone(zones, zone, mod_cat, zones_idx)
            minx, miny, maxx, maxy = zone.bounds
        elif larger_than_zone:
            minx, miny, maxx, maxy = planta.bounds

        if rot:
            b = affinity.rotate(b, 90)
        else:
            p = Point(round(randrange(minx, maxx, 20), 1), round(randrange(miny, maxy, 20), 1))
            b = box(p.x - mod.width / 2, p.y - mod.height / 2, p.x + mod.width / 2, p.y + mod.height / 2)

        if pos_retries < zones_qty and zone:
            condition1 = zone.contains(b) and planta.contains(b)
            if time.time() - make_time >= positional_time_limit and not condition1:
                condition1 = zone.intersects(b) and planta.contains(b)
        elif not larger_than_zone:
            larger_than_zone = True
            #print(mod.name)
            condition1 = planta.contains(b)
        else:
            condition1 = planta.contains(b)
        
        if time.time() - make_time >= overlap_time_limit and condition1:
            mod.x, mod.y = p.x, p.y
            curr_bx.append(b)
            makeposcnt += 1
            if makeposcnt >= in_cnt:
                makeposcnt = 0
                curr_bx = []
            return mod

        condition2 = True

        if not curr_bx:
            condition2 = True
        else:
            for bx in curr_bx:
                if b.intersects(bx):
                    condition2 = False

        if condition1 and condition2:
            mod.x, mod.y = p.x, p.y
            curr_bx.append(b)
            makeposcnt += 1
            if makeposcnt >= in_cnt:
                makeposcnt = 0
                curr_bx = []
            return mod
        rot = not rot


def min_dist_to_area(lista):
    my_output = []
    i = 0
    curr_min = lista[0]
    if len(lista) == 1:
        my_output.append(curr_min)
        return (my_output)

    for j in range(i + 1, len(lista)):
        B = lista[j]
        # print(i, j, curr_min, B)
        if curr_min[0] == B[0]:
            if B[1] <= curr_min[1]:
                curr_min = B
            if j + 1 == len(lista):
                my_output.append(curr_min)
                # print('append', curr_min)

        else:
            my_output.append(curr_min)
            # print('append', curr_min)
            curr_min = B
            if j + 1 == len(lista):
                my_output.append(curr_min)

        i = j
    return my_output

#deprecado
def make_areas(planta,core):
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    c_minx, c_miny, c_maxx, c_maxy = core.bounds

    core_bbox_points = [Point(c_minx, c_miny), Point(c_maxx, c_maxy)]

    lines = []
    for p in core_bbox_points:
        line_v = LineString([(p.x, p_miny), (p.x, p_maxy)])
        line_h = LineString([(p_minx, p.y), (p_maxx, p.y)])

        lines.append(line_v)
        lines.append(line_h)
    lu = unary_union(lines)

    inter = unary_union([planta.intersection(lu), planta.exterior, planta.boundary])

    pols = list(polygonize(MultiLineString(inter)))
    centroids_dist = [p.centroid.distance(core.centroid) for p in pols]
    min_centroid_value, min_centroid_idx = min((val, idx) for (idx, val) in enumerate(centroids_dist))
    del pols[min_centroid_idx]
    pols = [pols[i] for i in range(len(pols)) if pols[i].area > 30]
        
    areas_dict = {}
    areas_idx = rtree.index.Index()
    for i, p in enumerate(pols):
        areas_idx.insert(i, p.bounds)
    start_point = Point(p_minx, p_miny)
    sp_centroid_dist = [p.centroid.distance(start_point) for p in pols]
    min_dist_value, min_area_idx = min((val, idx) for (idx, val) in enumerate(sp_centroid_dist))
    visited_list = [pols[min_area_idx]]
    areas_dict[0] = pols[min_area_idx]

    ref_point = Point(p_minx, p_maxy)
    max_centroid_dist = [p.centroid.distance(ref_point) for p in pols]
    max_dist_value, max_area_idx = max((val, idx) for (idx, val) in enumerate(max_centroid_dist))
    for i in range(len(pols)):
        areas_adj = [pols[pid] for pid in list(areas_idx.nearest(visited_list[-1].bounds)) if pols[pid] != visited_list[-1] and not pols[pid] in visited_list]
        min_area_idx = 0
        if len(areas_adj) > 1 and not pols[max_area_idx] in areas_adj:
            min_centroid_dist = [a.centroid.distance(ref_point) for a in areas_adj]
            min_dist_value, min_area_idx = min((val, idx) for (idx, val) in enumerate(min_centroid_dist))
        elif pols[max_area_idx] in areas_adj:
            min_area_idx = areas_adj.index(pols[max_area_idx])
        elif len(areas_adj) == 0:
            break
        areas_dict[i+1] = areas_adj[min_area_idx]
        visited_list.append(areas_adj[min_area_idx])

    
    return areas_dict

def feasible_polygon(dims, polygon):

    pol_centroid = polygon.centroid
    base_polygon = box(pol_centroid.x - dims['max_width'] / 2, pol_centroid.y - dims['max_height'] / 2, pol_centroid.x + dims['max_width'] / 2, pol_centroid.y + dims['max_height'] / 2)

    diff_polygon = base_polygon.difference(polygon)
    
    if diff_polygon.area > 0.2*base_polygon.area:
        return False
    
    pol_minx, pol_miny, pol_maxx, pol_maxy = polygon.bounds

    pol_d1 = abs(pol_maxx-pol_minx)
    pol_d2 = abs(pol_maxy-pol_miny)
    pol_max_dim = max(pol_d1, pol_d2)
    pol_min_dim = min(pol_d1, pol_d2)

    base_d1 = dims['max_width']
    base_d2 = dims['max_height']
    base_max_dim = max(base_d1, base_d2)
    base_min_dim = min(base_d1, base_d2)

    '''print("pol_max_dim", pol_max_dim)
    print("pol_min_dim", pol_min_dim)
    print("base_max_dim", base_max_dim)
    print("base_min_dim", base_min_dim)
    print("-----")'''

    if pol_max_dim >= base_max_dim and pol_min_dim >= base_min_dim:
        return True
    return False

def assign_services_zone(has_shaft, circs_bounds, elements_idx, cat_area, factor, prev_sv_selected_zone, 
                        sv_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                        entrances_adj_qty, core_adj_qty, zones, cat_dims):

    if has_shaft:
        sv_candidate_idx = [k for k, v in shafts_adj_qty.items() if v > min(shafts_adj_qty.values()) and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
        if not sv_candidate_idx:
            sv_candidate_idx = [k for k, v in core_adj_qty.items() if v > min(core_adj_qty.values()) and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
            if not sv_candidate_idx:
                sv_candidate_idx = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
                if not sv_candidate_idx:
                    sv_candidate_idx = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values())]
    else:
        sv_candidate_idx = [k for k, v in core_adj_qty.items() if v > min(core_adj_qty.values()) and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
        if not sv_candidate_idx:
            sv_candidate_idx = [k for k, v in core_adj_qty.items() if v > min(core_adj_qty.values())]
        sv_candidate_idx_filter = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values()) and k in sv_candidate_idx]
        if sv_candidate_idx_filter:
            sv_candidate_idx = sv_candidate_idx_filter
    
    #print("Candidatos zona de servicios:", sv_candidate_idx)
    sv_candidate_zones = {}
    for c in sv_candidate_idx:
        sv_candidate_zones[c] = areas[c]
    sv_candidate_zones_areas = {k: v.area for k, v in sv_candidate_zones.items()}
    sv_candidate_idx = max(sv_candidate_zones_areas, key=sv_candidate_zones_areas.get)
    
    sv_selected_zone = areas[sv_candidate_idx]
    areas.pop(sv_candidate_idx, None)
    shafts_adj_qty.pop(sv_candidate_idx, None)
    crystal_adj_qty.pop(sv_candidate_idx, None)
    entrances_adj_qty.pop(sv_candidate_idx, None)
    core_adj_qty.pop(sv_candidate_idx, None)
    sv_banned_idx = []
    if prev_sv_selected_zone:
        prev_area = prev_sv_selected_zone.area
    else:
        prev_area = 0
    while sv_selected_zone.area + prev_area < cat_area[4] + factor*cat_area[4] and len(areas) > 0:
        sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zone.bounds, objects=True))))
        sv_nearest_idx = [k for k,v in areas.items() if v.bounds in sv_nearest and not k in sv_banned_idx]
        nearest_len = {idx: sv_selected_zone.intersection(areas[idx]).length for idx in sv_nearest_idx}
        if nearest_len:
            nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
            sv_candidate_zone = unary_union([sv_selected_zone, areas[nearest_candidate_idx]])
            if sv_candidate_zone.geom_type == 'Polygon' and (sv_candidate_zone.area / sv_candidate_zone.minimum_rotated_rectangle.area) > .90:
                sv_selected_zone = sv_candidate_zone
                areas.pop(nearest_candidate_idx, None)
                shafts_adj_qty.pop(nearest_candidate_idx, None)
                crystal_adj_qty.pop(nearest_candidate_idx, None)
                entrances_adj_qty.pop(nearest_candidate_idx, None)
                core_adj_qty.pop(nearest_candidate_idx, None)
                sv_banned_idx = []
            else:
                sv_banned_idx.append(nearest_candidate_idx)
        else:
            break

    if not prev_sv_selected_zone:
        zones['ZONA SERVICIOS 0'] = sv_selected_zone
        sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zone.bounds, objects=True))))
        sv_nearest_idx = [k for k,v in areas.items() if v.bounds in sv_nearest]
        for circ in circs_bounds:
            if sv_selected_zone.intersects(box(*circ)):
                circ_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(circ, objects=True))))
                circ_nearest_idx = [k for k,v in areas.items() if v.bounds in circ_nearest and not k in sv_nearest_idx]
                sv_nearest_idx += circ_nearest_idx
    else:
        sv_selected_zones = [prev_sv_selected_zone, sv_selected_zone]
        sv_nearest_idx = []
        for i in range(len(sv_selected_zones)):
            zones['ZONA SERVICIOS ' + str(i)] = sv_selected_zones[i]
            sv_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sv_selected_zones[i].bounds, objects=True))))
            for k,v in areas.items():
                if v.bounds in sv_nearest and not k in sv_nearest_idx:
                    sv_nearest_idx.append(k)
            for circ in circs_bounds:
                if sv_selected_zone.intersects(box(*circ)):
                    circ_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(circ, objects=True))))
                    circ_nearest_idx = [k for k,v in areas.items() if v.bounds in circ_nearest and not k in sv_nearest_idx]
                    sv_nearest_idx += circ_nearest_idx
    
    return sv_selected_zone, sv_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones


def assign_pt_zones(has_shaft, circs_bounds, elements_idx, cat_area, factor, sv_selected_zone,
                    sv_nearest_idx, pt_selected_zones, pt_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, cat_dims):
    pt_candidate_idx = []
    '''if sv_selected_zone:
        # Arreglo de indices de zonas cercanas al area de servicios
        if has_shaft:
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and (shafts_adj_qty[k] > 0 or k in sv_nearest_idx)]
        else:
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and k in sv_nearest_idx]
    if not pt_candidate_idx:
        pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values())]'''
    pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k])]
    pt_candidate_zones = {}
    #print("Candidatos puestos de trabajo:", pt_candidate_idx)

    if len(pt_candidate_idx) > 0:
        # Se asume que hay al menos 1 zona con muchas fachadas de cristal cercanas
        for c in pt_candidate_idx:
            pt_candidate_zones[c] = areas[c]
        if len(pt_candidate_zones) < 2:
            # Si hay una zona con area maxima absoluta, se selecciona la primera zona siguiente que tenga area maxima
            pt_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and v <= max(crystal_adj_qty.values()) and not k in pt_candidate_idx and feasible_polygon(cat_dims, areas[k])]
            pt_candidate_zones[pt_candidate_idx[0]] = areas[pt_candidate_idx[0]]
        # Se seleccionan solo 2 zonas de la lista de candidatas
        pt_selected_zones = []
        for i in range(2):
            pt_candidate_zones_areas = {k: v.area for k, v in pt_candidate_zones.items()}
            selected_zone_idx = max(pt_candidate_zones_areas, key=pt_candidate_zones_areas.get)
            selected_zone = pt_candidate_zones[selected_zone_idx]
            pt_selected_zones.append(selected_zone)
            #zones.append([selected_zone, 'ZONA PUESTOS DE TRABAJO'])
            del pt_candidate_zones[selected_zone_idx]
            del pt_candidate_zones_areas[selected_zone_idx]
            areas.pop(selected_zone_idx, None)
            shafts_adj_qty.pop(selected_zone_idx, None)
            crystal_adj_qty.pop(selected_zone_idx, None)
            entrances_adj_qty.pop(selected_zone_idx, None)
            core_adj_qty.pop(selected_zone_idx, None)
        selector = False
        stuck_z0 = False
        stuck_z1 = False

        pt0_banned_idx = []
        pt1_banned_idx = []
        while pt_selected_zones[0].area + pt_selected_zones[1].area < cat_area[2] + factor*cat_area[2] and len(areas) > 0:
            if selector:
                pt_selected_zone = pt_selected_zones[1]
                pt_banned_idx = pt1_banned_idx
            else:
                pt_selected_zone = pt_selected_zones[0]
                pt_banned_idx = pt0_banned_idx
            pt_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(pt_selected_zone.bounds, objects=True))))
            pt_nearest_idx = [k for k,v in areas.items() if v.bounds in pt_nearest and not k in pt_banned_idx]
            pt_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and k in pt_nearest_idx]
            if pt_nearest_idx_filter:
                pt_nearest_idx = pt_nearest_idx_filter
            nearest_len = {idx: pt_selected_zone.intersection(areas[idx]).length for idx in pt_nearest_idx}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                pt_candidate_zone = unary_union([pt_selected_zone, areas[nearest_candidate_idx]])
                if pt_candidate_zone.geom_type == 'Polygon' and (pt_candidate_zone.area / pt_candidate_zone.minimum_rotated_rectangle.area) > .80:
                    if selector:
                        pt_selected_zones[1] = pt_candidate_zone
                        pt1_banned_idx = []
                    else:
                        pt_selected_zones[0] = pt_candidate_zone
                        pt0_banned_idx = []
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    core_adj_qty.pop(nearest_candidate_idx, None)
                elif selector:
                    pt1_banned_idx.append(nearest_candidate_idx)
                else:
                    pt0_banned_idx.append(nearest_candidate_idx)

            elif stuck_z0 and stuck_z1:
                break
            elif selector:
                stuck_z1 = True
            else:
                stuck_z0 = True
            selector = not selector

        pt_nearest_idx = []
        for i in range(len(pt_selected_zones)):
            zones['ZONA PUESTOS DE TRABAJO ' + str(i)] = pt_selected_zones[i]
            pt_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(pt_selected_zones[i].bounds, objects=True))))
            for k,v in areas.items():
                if v.bounds in pt_nearest and not k in pt_nearest_idx:
                    pt_nearest_idx.append(k)
            for circ in circs_bounds:
                if pt_selected_zones[i].intersects(box(*circ)):
                    circ_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(circ, objects=True))))
                    circ_nearest_idx = [k for k,v in areas.items() if v.bounds in circ_nearest and not k in pt_nearest_idx]
                    pt_nearest_idx += circ_nearest_idx

    return pt_selected_zones, pt_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones

def assign_support_zone(core_bounds, entrances_bounds, circs_bounds, elements_idx, cat_area, factor, prev_sp_selected_zone,
                        sp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                        entrances_adj_qty, core_adj_qty, zones, cat_dims):
    
    sp_candidate_idx = [k for k, v in entrances_adj_qty.items() if v > 0]
    sp_candidate_filter = [idx for idx in sp_candidate_idx if feasible_polygon(cat_dims, areas[idx])]
    entrances_idx = True
    if not sp_candidate_filter:
        sp_candidate_idx = [k for k, v in core_adj_qty.items() if v > 0 ]
        sp_candidate_filter = [idx for idx in sp_candidate_idx if feasible_polygon(cat_dims, areas[idx])]
        entrances_idx = False

    sp_candidate_idx = sp_candidate_filter
    #print("Candidatos zona soporte:", sp_candidate_idx)
    if len(sp_candidate_idx) > 0:
        # Se asume que hay al menos 1 zona candidata
        if len(sp_candidate_idx) > 1:
            sp_candidate_zones = {}
            for c in sp_candidate_idx:
                sp_candidate_zones[c] = areas[c]

            if entrances_idx:
                sp_candidate_zones_areas = {}
                for e in entrances_bounds:
                    ent = box(*e)
                    entrances_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(e, objects=True))))
                    entrances_nearest_idx = [k for k,v in areas.items() if v.bounds in entrances_nearest]
                    for idx in entrances_nearest_idx:
                        inter_lenght = ent.intersection(areas[idx]).length
                        if idx in sp_candidate_zones_areas:
                            sp_candidate_zones_areas[idx] += inter_lenght
                        else:
                            sp_candidate_zones_areas[idx] = inter_lenght
                
                sp_selected_zone_idx = max(sp_candidate_zones_areas, key=sp_candidate_zones_areas.get)
            else:
                core = box(*core_bounds[0])
                core_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(core_bounds[0], objects=True))))
                core_nearest_idx = [k for k,v in areas.items() if v.bounds in core_nearest and k in sp_candidate_idx]
                sp_candidate_zones_areas = {idx: core.intersection(areas[idx]).length for idx in core_nearest_idx}
                sp_selected_zone_idx = max(sp_candidate_zones_areas, key=sp_candidate_zones_areas.get)

            sp_selected_zone = sp_candidate_zones[sp_selected_zone_idx]
        elif len(sp_candidate_idx) == 1:
            sp_selected_zone_idx = sp_candidate_idx[0]
            sp_selected_zone = areas[sp_selected_zone_idx]

        areas.pop(sp_selected_zone_idx, None)
        shafts_adj_qty.pop(sp_selected_zone_idx, None)
        crystal_adj_qty.pop(sp_selected_zone_idx, None)
        entrances_adj_qty.pop(sp_selected_zone_idx, None)
        core_adj_qty.pop(sp_selected_zone_idx, None)
        sp_banned_idx = []
        if prev_sp_selected_zone:
            prev_area = prev_sp_selected_zone.area
        else:
            prev_area = 0
        while sp_selected_zone.area + prev_area < cat_area[5] + factor*cat_area[5] and len(areas) > 0:
            sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zone.bounds, objects=True))))
            sp_nearest_idx = [k for k,v in areas.items() if v.bounds in sp_nearest and not k in sp_banned_idx]
            sp_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v == min(crystal_adj_qty.values()) and k in sp_nearest_idx]
            if sp_nearest_idx_filter:
                sp_nearest_idx = sp_nearest_idx_filter
            nearest_len = {idx: sp_selected_zone.intersection(areas[idx]).length for idx in sp_nearest_idx}
            if nearest_len:
                sp_nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                sp_candidate_zone = unary_union([sp_selected_zone, areas[sp_nearest_candidate_idx]])
                if sp_candidate_zone.geom_type == 'Polygon'  and (sp_candidate_zone.area / sp_candidate_zone.minimum_rotated_rectangle.area) > .90:
                    sp_selected_zone = sp_candidate_zone
                    areas.pop(sp_nearest_candidate_idx, None)
                    shafts_adj_qty.pop(sp_nearest_candidate_idx, None)
                    crystal_adj_qty.pop(sp_nearest_candidate_idx, None)
                    entrances_adj_qty.pop(sp_nearest_candidate_idx, None)
                    core_adj_qty.pop(sp_nearest_candidate_idx, None)
                    sp_banned_idx = []
                else:
                    sp_banned_idx.append(sp_nearest_candidate_idx)
            else:
                break
        
        if not prev_sp_selected_zone:
            zones['ZONA SOPORTE 0'] = sp_selected_zone
            sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zone.bounds, objects=True))))
            sp_nearest_idx = [k for k,v in areas.items() if v.bounds in sp_nearest]
            for circ in circs_bounds:
                if sp_selected_zone.intersects(box(*circ)):
                    circ_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(circ, objects=True))))
                    circ_nearest_idx = [k for k,v in areas.items() if v.bounds in circ_nearest and not k in sp_nearest_idx]
                    sp_nearest_idx += circ_nearest_idx
        else:
            sp_selected_zones = [prev_sp_selected_zone, sp_selected_zone]
            sp_nearest_idx = []
            for i in range(len(sp_selected_zones)):
                zones['ZONA SOPORTE ' + str(i)] = sp_selected_zones[i]
                sp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(sp_selected_zones[i].bounds, objects=True))))
                for k,v in areas.items():
                    if v.bounds in sp_nearest and not k in sp_nearest_idx:
                        sp_nearest_idx.append(k)
                for circ in circs_bounds:
                    if sp_selected_zones[i].intersects(box(*circ)):
                        circ_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(circ, objects=True))))
                        circ_nearest_idx = [k for k,v in areas.items() if v.bounds in circ_nearest and not k in sp_nearest_idx]
                        sp_nearest_idx += circ_nearest_idx

    return sp_selected_zone, sp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones

def assign_ptp_zone(circs_bounds, sv_selected_zone, sv_nearest_idx, sp_selected_zone, sp_nearest_idx, elements_idx, 
                    cat_area, factor, ptp_selected_zone, ptp_nearest_idx, areas, shafts_adj_qty, 
                    crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones, cat_dims):

    # Indices de areas cercanas a zona de soporte
    if sp_selected_zone and sv_selected_zone:
        # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
        ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and (not k in sp_nearest_idx and not k in sv_nearest_idx) and feasible_polygon(cat_dims, areas[k])]
        if not ptp_candidate_idx:
            # En caso que NO se haya encontrado a lo menos un candidato que cumpla con el criterio, se relaja la restriccion
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and (not k in sp_nearest_idx or not k in sv_nearest_idx) and feasible_polygon(cat_dims, areas[k])]
            if not ptp_candidate_idx:
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sp_nearest_idx and feasible_polygon(cat_dims, areas[k])]
                if not ptp_candidate_idx:
                    ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k])]
    elif sp_selected_zone:
        # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
        ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and not k in sp_nearest_idx and feasible_polygon(cat_dims, areas[k])]
        if not ptp_candidate_idx:
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sp_nearest_idx and feasible_polygon(cat_dims, areas[k])]
            if not ptp_candidate_idx:
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k])]
    elif sv_selected_zone:
            # Se buscan candidatos que tengan fachadas de cristal adyacentes y que no esten cerca de la zona de soporte
        ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and not k in sv_nearest_idx and feasible_polygon(cat_dims, areas[k])]
        if not ptp_candidate_idx:
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if not k in sv_nearest_idx and feasible_polygon(cat_dims, areas[k])]
            if not ptp_candidate_idx:
                ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k])]
    else:
        ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k])]
        if not ptp_candidate_idx:
            ptp_candidate_idx = [k for k, v in crystal_adj_qty.items() if v >= min(crystal_adj_qty.values()) and feasible_polygon(cat_dims, areas[k])]
    
    #print("Candidatos puestos de trabajo privado:")
    #print(ptp_candidate_idx)
    if len(ptp_candidate_idx) > 0:
        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el que tenga mas fachadas de cristal
        if len(ptp_candidate_idx) > 1:
            ptp_candidate_zones = {}
            for c in ptp_candidate_idx:
                ptp_candidate_zones[c] = areas[c]
            ptp_candidate_zones_areas = {k: v.area for k, v in ptp_candidate_zones.items() if crystal_adj_qty[k] > min(crystal_adj_qty.values())}
            ptp_selected_zone_idx = max(ptp_candidate_zones_areas, key=ptp_candidate_zones_areas.get)
            ptp_selected_zone = ptp_candidate_zones[ptp_selected_zone_idx]
        elif len(ptp_candidate_idx) == 1:
            ptp_selected_zone_idx = ptp_candidate_idx[0]
            ptp_selected_zone = areas[ptp_selected_zone_idx]
        areas.pop(ptp_selected_zone_idx, None)
        shafts_adj_qty.pop(ptp_selected_zone_idx, None)
        crystal_adj_qty.pop(ptp_selected_zone_idx, None)
        entrances_adj_qty.pop(ptp_selected_zone_idx, None)
        core_adj_qty.pop(ptp_selected_zone_idx, None)
        ptp_banned_idx = []
        while ptp_selected_zone.area < cat_area[3] + factor*cat_area[3] and len(areas) > 0:
            ptp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(ptp_selected_zone.bounds, objects=True))))
            ptp_nearest_idx = [k for k,v in areas.items() if v.bounds in ptp_nearest and not k in ptp_banned_idx]
            ptp_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and k in ptp_nearest_idx]
            if ptp_nearest_idx_filter:
                ptp_nearest_idx = ptp_nearest_idx_filter
            nearest_len = {idx: ptp_selected_zone.intersection(areas[idx]).length for idx in ptp_nearest_idx}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                ptp_candidate_zone = unary_union([ptp_selected_zone, areas[nearest_candidate_idx]])
                if ptp_candidate_zone.geom_type == 'Polygon' and (ptp_candidate_zone.area / ptp_candidate_zone.minimum_rotated_rectangle.area) > .90 and feasible_polygon(cat_dims, ptp_candidate_zone.minimum_rotated_rectangle):
                    ptp_selected_zone = ptp_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    core_adj_qty.pop(nearest_candidate_idx, None)
                    ptp_banned_idx = []
                else:
                    ptp_banned_idx.append(nearest_candidate_idx)
            else:
                break
        zones['ZONA TRABAJO PRIVADO 0'] = ptp_selected_zone
        ptp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.intersection(ptp_selected_zone.bounds, objects=True))))
        ptp_nearest_idx = [k for k,v in areas.items() if v.bounds in ptp_nearest]
        for circ in circs_bounds:
            if ptp_selected_zone.intersects(box(*circ)):
                circ_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(circ, objects=True))))
                circ_nearest_idx = [k for k,v in areas.items() if v.bounds in circ_nearest and not k in ptp_nearest_idx]
                ptp_nearest_idx += circ_nearest_idx

    return ptp_selected_zone, ptp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones


def assign_rf_zone(sv_nearest_idx, sp_nearest_idx, ptp_selected_zone, ptp_nearest_idx,
                    elements_idx, cat_area, factor, prev_rf_selected_zone, rf_nearest_idx,
                    areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones):

    nearest_len = None
    if ptp_selected_zone:
        # Se buscan indices de areas disponibles cercanas a la zona seleccionada como trabajo privado
        if sp_nearest_idx and sv_nearest_idx:
            rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx and not k in sv_nearest_idx) and k in ptp_nearest_idx and crystal_adj_qty[k] > min(crystal_adj_qty.values())]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx or not k in sv_nearest_idx) and k in ptp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx and crystal_adj_qty[k] > min(crystal_adj_qty.values())]
                    if not rf_candidate_idx:
                        rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        elif sp_nearest_idx:
            rf_candidate_idx = [k for k, v in areas.items() if not k in sp_nearest_idx and k in ptp_nearest_idx and crystal_adj_qty[k] > min(crystal_adj_qty.values())]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sp_nearest_idx and k in ptp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
                    if not rf_candidate_idx:
                        rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        elif sv_nearest_idx:
            rf_candidate_idx = [k for k, v in areas.items() if not k in sv_nearest_idx and k in ptp_nearest_idx and crystal_adj_qty[k] > min(crystal_adj_qty.values())]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sv_nearest_idx and k in ptp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
                    if not rf_candidate_idx:
                        rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        else:
            rf_candidate_idx = [k for k, v in areas.items() if k in ptp_nearest_idx]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        rf_candidate_len = {idx: ptp_selected_zone.intersection(areas[idx]).length for idx in rf_candidate_idx if ptp_selected_zone.intersection(areas[idx]).geom_type == 'LineString' or ptp_selected_zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
    else:
        if sp_nearest_idx and sv_nearest_idx:
            rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx and not k in sv_nearest_idx) and crystal_adj_qty[k] > min(crystal_adj_qty.values())] 
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx and not k in sv_nearest_idx)] 
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in areas.items() if (not k in sp_nearest_idx or not k in sv_nearest_idx)]
                    if not rf_candidate_idx:
                        rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        elif sp_nearest_idx:
            rf_candidate_idx = [k for k, v in areas.items() if not k in sp_nearest_idx and crystal_adj_qty[k] > min(crystal_adj_qty.values())]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sp_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        elif sv_nearest_idx:
            rf_candidate_idx = [k for k, v in areas.items() if not k in sv_nearest_idx and crystal_adj_qty[k] > min(crystal_adj_qty.values())]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items() if not k in sv_nearest_idx]
                if not rf_candidate_idx:
                    rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
        else:
            rf_candidate_idx = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values())]
            if not rf_candidate_idx:
                rf_candidate_idx = [k for k, v in areas.items()]
    
    #print("Candidatos reuniones formales:")
    #print(rf_candidate_idx)
    rf_candidate_zones = {}
    if len(rf_candidate_idx) > 0:
        # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el de mayor area
        if len(rf_candidate_idx) > 1:
            if rf_candidate_len:
                rf_selected_zone_idx = max(rf_candidate_len, key=rf_candidate_len.get)
                rf_selected_zone = areas[rf_selected_zone_idx]
            else:
                for c in rf_candidate_idx:
                    rf_candidate_zones[c] = areas[c]
                rf_candidate_zones_areas = {k: v.area for k, v in rf_candidate_zones.items()}
                rf_selected_zone_idx = max(rf_candidate_zones_areas, key=rf_candidate_zones_areas.get)
                rf_selected_zone = rf_candidate_zones[rf_selected_zone_idx]
        elif len(rf_candidate_idx) == 1:
            rf_selected_zone_idx = rf_candidate_idx[0]
            rf_selected_zone = areas[rf_selected_zone_idx]

        areas.pop(rf_selected_zone_idx, None)
        shafts_adj_qty.pop(rf_selected_zone_idx, None)
        crystal_adj_qty.pop(rf_selected_zone_idx, None)
        entrances_adj_qty.pop(rf_selected_zone_idx, None)
        core_adj_qty.pop(rf_selected_zone_idx, None)
        rf_banned_idx = []
        if prev_rf_selected_zone:
            prev_area = prev_rf_selected_zone.area
        else:
            prev_area = 0
        while rf_selected_zone.area + prev_area < cat_area[1] + factor*cat_area[1]:
            rf_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(rf_selected_zone.bounds, objects=True))))
            rf_nearest_idx = [k for k,v in areas.items() if v.bounds in rf_nearest and not k in rf_banned_idx]
            rf_nearest_idx_filter = [k for k, v in crystal_adj_qty.items() if v > min(crystal_adj_qty.values()) and k in rf_nearest_idx]
            if rf_nearest_idx_filter:
                rf_nearest_idx = rf_nearest_idx_filter
            nearest_len = {idx: rf_selected_zone.intersection(areas[idx]).length for idx in rf_nearest_idx}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                rf_candidate_zone = unary_union([rf_selected_zone, areas[nearest_candidate_idx]])
                if rf_candidate_zone.geom_type == 'Polygon' and (rf_candidate_zone.area / rf_candidate_zone.minimum_rotated_rectangle.area) > .90:
                    rf_selected_zone = rf_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    core_adj_qty.pop(nearest_candidate_idx, None)
                    rf_banned_idx = []
                else:
                    rf_banned_idx.append(nearest_candidate_idx)
            else:
                break

        if not prev_rf_selected_zone:
            zones['ZONA SALAS REUNION FORMAL 0'] = rf_selected_zone
            rf_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(rf_selected_zone.bounds, objects=True))))
            rf_nearest_idx = [k for k,v in areas.items() if v.bounds in rf_nearest]
        else:
            rf_selected_zones = [prev_rf_selected_zone, rf_selected_zone]
            for i in range(len(rf_selected_zones)):
                zones['ZONA SALAS REUNION FORMAL ' + str(i)] = rf_selected_zones[i]
    
    return rf_selected_zone, rf_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones

def assign_esp_zone(sp_nearest_idx, elements_idx, cat_area, factor, esp_selected_zone, 
                    esp_nearest, esp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, cat_dims):
    if sp_nearest_idx:
        esp_candidate_idx = [k for k,v in areas.items() if k in sp_nearest_idx and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
        if not esp_candidate_idx:
            esp_candidate_idx = [k for k, v in entrances_adj_qty.items() if v > 0 and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
            if not esp_candidate_idx:
                esp_candidate_idx = [k for k, v in core_adj_qty.items() if v == max(core_adj_qty.values()) and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
                if not esp_candidate_idx:
                    esp_candidate_idx = [k for k,v in areas.items() if k in sp_nearest_idx and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
                    if not esp_candidate_idx:
                        esp_candidate_idx = [k for k,v in areas.items() if k in sp_nearest_idx]
                        if not esp_candidate_idx:
                            esp_candidate_idx = [k for k,v in areas.items()]
    else:
        esp_candidate_idx = [k for k, v in entrances_adj_qty.items() if v > 0 and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
        if not esp_candidate_idx:
            esp_candidate_idx = [k for k, v in core_adj_qty.items() if v == max(core_adj_qty.values()) and feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
            if not esp_candidate_idx:
                esp_candidate_idx = [k for k,v in areas.items() if feasible_polygon(cat_dims, areas[k].minimum_rotated_rectangle)]
                if not esp_candidate_idx:
                    esp_candidate_idx = [k for k,v in areas.items()]

    #print("Candidatos especiales:", esp_candidate_idx)
    if len(esp_candidate_idx) > 0:
        if len(esp_candidate_idx) > 1:
            esp_candidate_zones = {}
            for c in esp_candidate_idx:
                esp_candidate_zones[c] = areas[c]
            esp_candidate_zones_areas = {k: v.area for k, v in esp_candidate_zones.items()}
            esp_selected_zone_idx = max(esp_candidate_zones_areas, key=esp_candidate_zones_areas.get)
            esp_selected_zone = esp_candidate_zones[esp_selected_zone_idx]
        elif len(esp_candidate_idx) == 1:
            esp_selected_zone_idx = esp_candidate_idx[0]
            esp_selected_zone = areas[esp_selected_zone_idx]
        
        areas.pop(esp_selected_zone_idx, None)
        shafts_adj_qty.pop(esp_selected_zone_idx, None)
        crystal_adj_qty.pop(esp_selected_zone_idx, None)
        entrances_adj_qty.pop(esp_selected_zone_idx, None)
        core_adj_qty.pop(esp_selected_zone_idx, None)
        esp_banned_idx = []
        while esp_selected_zone.area < cat_area[7] + factor*cat_area[7] and len(areas) > 0:
            esp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(esp_selected_zone.bounds, objects=True))))
            esp_nearest_idx = [k for k,v in areas.items() if v.bounds in esp_nearest and not k in esp_banned_idx]
            nearest_len = {idx: esp_selected_zone.intersection(areas[idx]).length for idx in esp_nearest_idx}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                esp_candidate_zone = unary_union([esp_selected_zone, areas[nearest_candidate_idx]])
                if esp_selected_zone.geom_type == 'Polygon' and (esp_candidate_zone.area / esp_candidate_zone.minimum_rotated_rectangle.area) > .90:
                    esp_selected_zone = esp_candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
                    core_adj_qty.pop(nearest_candidate_idx, None)
                    esp_banned_idx = []
                else:
                    esp_banned_idx.append(nearest_candidate_idx)
            else:
                break
        zones['ZONA ESPECIALES 0'] = esp_selected_zone
        esp_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.intersection(esp_selected_zone.bounds, objects=True))))
        esp_nearest_idx = [k for k,v in areas.items() if v.bounds in esp_nearest]
    
    return esp_selected_zone, esp_nearest, esp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones

def assign_ri_zone(pt_nearest_idx, elements_idx, cat_area, factor, prev_ri_selected_zone, 
                    ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, ri_fill):

    if not prev_ri_selected_zone:
        # Se buscan como candidatos, indices de areas disponibles cercanas a la zonas seleccionadas como puestos de trabajo
        if pt_nearest_idx:
            ri_candidate_idx = [k for k,v in areas.items() if k in pt_nearest_idx]
            if not ri_candidate_idx:
                ri_candidate_idx = [k for k,v in areas.items()]
        else:
            ri_candidate_idx = [k for k,v in areas.items()]
        #print("Candidatos reuniones informales:", ri_candidate_idx)

        if len(ri_candidate_idx) > 0:
            # En caso que se haya encontrado mas de un candidato que cumpla con algun criterio, se elige el de mayor area
            if len(ri_candidate_idx) > 1:
                ri_candidate_zones = {}
                for c in ri_candidate_idx:
                    ri_candidate_zones[c] = areas[c]
                ri_candidate_zones_areas = {k: v.area for k, v in ri_candidate_zones.items()}
                ri_selected_zone_idx = max(ri_candidate_zones_areas, key=ri_candidate_zones_areas.get)
                ri_selected_zone = ri_candidate_zones[ri_selected_zone_idx]
            elif len(ri_candidate_idx) == 1:
                ri_selected_zone_idx = ri_candidate_idx[0]
                ri_selected_zone = areas[ri_selected_zone_idx]
            
            areas.pop(ri_selected_zone_idx, None)
            shafts_adj_qty.pop(ri_selected_zone_idx, None)
            crystal_adj_qty.pop(ri_selected_zone_idx, None)
            entrances_adj_qty.pop(ri_selected_zone_idx, None)
            core_adj_qty.pop(ri_selected_zone_idx, None)
            ri_banned_idx = []
            if ri_fill:
                expansion_condition = True
            else:
                expansion_condition = ri_selected_zone.area < cat_area[6] + factor*cat_area[6]
            while expansion_condition and len(areas) > 0:
                ri_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(ri_selected_zone.bounds, objects=True))))
                ri_nearest_idx = [k for k,v in areas.items() if v.bounds in ri_nearest and not k in ri_banned_idx]
                nearest_len = {idx: ri_selected_zone.intersection(areas[idx]).length for idx in ri_nearest_idx}
                if nearest_len:
                    nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                    ri_candidate_zone = unary_union([ri_selected_zone, areas[nearest_candidate_idx]])
                    if ri_candidate_zone.geom_type == 'Polygon' and (ri_candidate_zone.area / ri_candidate_zone.minimum_rotated_rectangle.area) > .90:
                        ri_selected_zone = ri_candidate_zone
                        areas.pop(nearest_candidate_idx, None)
                        shafts_adj_qty.pop(nearest_candidate_idx, None)
                        crystal_adj_qty.pop(nearest_candidate_idx, None)
                        entrances_adj_qty.pop(nearest_candidate_idx, None)
                        core_adj_qty.pop(nearest_candidate_idx, None)
                        ri_banned_idx = []
                    else:
                        ri_banned_idx.append(nearest_candidate_idx)
                else:
                    break
            zones['ZONA REUNIONES INFORMALES 0'] = ri_selected_zone
            ri_nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.intersection(ri_selected_zone.bounds, objects=True))))
            ri_nearest_idx = [k for k,v in areas.items() if v.bounds in ri_nearest]
            return ri_selected_zone, ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones
    else:
        ri_zones_list = [prev_ri_selected_zone]
        while len(areas) > 0:
            ri_candidate_idx = [k for k,v in areas.items()]
            for idx in ri_candidate_idx:
                if len(areas) < 1:
                    break
                ri_zones_list.append(areas[idx])
                areas.pop(idx, None)
                shafts_adj_qty.pop(idx, None)
                crystal_adj_qty.pop(idx, None)
                entrances_adj_qty.pop(idx, None)
                core_adj_qty.pop(idx, None)
        ri_zones = unary_union(ri_zones_list)
        if ri_zones.geom_type == 'Polygon':
            zones['ZONA REUNIONES INFORMALES 0'] = ri_zones
        else:
            ri_zones = list(ri_zones)
            for i in range(len(ri_zones)):
                zones['ZONA REUNIONES INFORMALES '+ str(i)] = ri_zones[i]
        
        return prev_ri_selected_zone, ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones
    

def make_zones(planta, shafts, core, circs, entrances, crystal_facs, areas, cat_area, cat_dims):
    zones = {}
    assigned_zones = {}
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    c_minx, c_miny, c_maxx, c_maxy = core.bounds
    factor = 0.1
    
    #cat_area = {1:80 ,2:200, 3:70, 4:70, 5:30, 6: 50, 7:20}
    #cat_area = {2:200, 3:40, 4:70, 5:30, 6: 50, 7:20}
    #cat_area = {4:70}
    #cat_area = {1: 68.75, 2: 56.78450000000001, 3: 28.36, 4: 30.6116, 5: 16.790499999999998}
    #cat_area = {1: 80, 2: 160, 3: 58.36, 4: 30.6116, 5: 16.790499999999998, 6: 30, 7:30}
    #cat_area = {1: 36.349999999999994, 2: 56.78450000000001, 3: 38.16, 4: 30.6116, 5: 30, 6:20}
    #cat_area = {1: 36.349999999999994, 2: 113.56900000000002, 3: 28.36, 4: 30.6116, 5: 8.775}

    core_bounds = [core.bounds]
    entrances_bounds = list(map(lambda x: x.bounds, entrances))
    crystal_facs_bounds = list(map(lambda x: x.bounds, crystal_facs))
    circs_bounds = list(map(lambda x: Polygon(x).bounds, circs))
    #areas = {k: a.buffer(0.0001, cap_style=3, join_style=2) for k, a in areas.items()}
    areas_bounds = []
    for key, area in areas.items():
        areas_bounds.append(area.bounds)

    elements_idx = rtree.index.Index()

    crystal_adj_qty = {}
    entrances_adj_qty = {}
    shafts_adj_qty = {}
    core_adj_qty = {}

    if len(shafts) > 0:
        has_shaft = True
    else:
        has_shaft = False

    if has_shaft:
        shafts_bounds = list(map(lambda x: x.bounds, shafts))
        elements = circs_bounds + core_bounds + shafts_bounds + entrances_bounds + crystal_facs_bounds + areas_bounds
        for i, e in enumerate(elements):
            elements_idx.insert(i, e)

        for key, area in areas.items():
            area_nearest = list(elements_idx.nearest(area.bounds, objects=True))
            crystal_adj = [obj for obj in area_nearest if tuple(obj.bbox) in crystal_facs_bounds]
            shafts_adj = [obj for obj in area_nearest if tuple(obj.bbox) in shafts_bounds]
            entrances_adj = [obj for obj in area_nearest if tuple(obj.bbox) in entrances_bounds]
            core_adj = [area.intersection(core).length for obj in area_nearest if tuple(obj.bbox) in core_bounds]
            crystal_adj_qty[key] = len(crystal_adj)
            shafts_adj_qty[key] = len(shafts_adj)
            entrances_adj_qty[key] = len(entrances_adj)
            core_adj_qty[key] = core_adj[0] if core_adj else 0
    else:
        elements = circs_bounds + core_bounds + entrances_bounds + crystal_facs_bounds + areas_bounds
        for i, e in enumerate(elements):
            elements_idx.insert(i, e)

        for key, area in areas.items():
            area_nearest = list(elements_idx.nearest(area.bounds, objects=True))
            crystal_adj = [obj for obj in area_nearest if tuple(obj.bbox) in crystal_facs_bounds]
            entrances_adj = [obj for obj in area_nearest if tuple(obj.bbox) in entrances_bounds]
            core_adj = [area.intersection(core).length for obj in area_nearest if tuple(obj.bbox) in core_bounds]
            crystal_adj_qty[key] = len(crystal_adj)
            entrances_adj_qty[key] = len(entrances_adj)
            core_adj_qty[key] = core_adj[0] if core_adj else 0
    #print("adyacentes a cristal:", crystal_adj_qty)
    #print("adyacentes al core:", core_adj_qty)
    # Zona de servicios
    # Se selecciona solo 1 area que tenga mas shafts o core cercanos
    sv_selected_zone = None
    sv_nearest_idx = None
    if 4 in cat_area and len(areas) > 0:
        sv_selected_zone, sv_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_services_zone(has_shaft, circs_bounds, elements_idx, cat_area, factor, sv_selected_zone, sv_nearest_idx, areas, shafts_adj_qty, 
                            crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones, cat_dims[4])
        assigned_zones[4] = sv_selected_zone
    
    # Zonas de puestos de trabajo
    pt_selected_zones = None
    pt_nearest_idx = None
    if 2 in cat_area and len(areas) > 0:
        pt_selected_zones, pt_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_pt_zones(has_shaft, circs_bounds, elements_idx, cat_area, factor, sv_selected_zone,
                    sv_nearest_idx, pt_selected_zones, pt_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, cat_dims[2])
        assigned_zones[2] = pt_selected_zones

    # Zona de soporte
    sp_selected_zone = None
    sp_nearest_idx = None
    if 5 in cat_area and len(areas) > 0:
        sp_selected_zone, sp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_support_zone(core_bounds, entrances_bounds, circs_bounds, elements_idx, cat_area, factor, sp_selected_zone,
                    sp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, cat_dims[5])
        assigned_zones[5] = sp_selected_zone

    # Zona de puestos de trabajo privado
    ptp_selected_zone = None
    ptp_nearest_idx = None
    if 3 in cat_area and len(areas) > 0:
        ptp_selected_zone, ptp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_ptp_zone(circs_bounds, sv_selected_zone, sv_nearest_idx, sp_selected_zone, sp_nearest_idx, elements_idx, cat_area, factor, ptp_selected_zone,
                    ptp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, cat_dims[3])
        assigned_zones[3] = ptp_selected_zone

    # Zona reuniones formales
    rf_selected_zone = None
    rf_nearest = None
    rf_nearest_idx = None
    if 1 in cat_area and len(areas) > 0:
        rf_selected_zone, rf_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_rf_zone(sv_nearest_idx, sp_nearest_idx, ptp_selected_zone, ptp_nearest_idx,
                        elements_idx, cat_area, factor, rf_selected_zone, rf_nearest_idx,
                        areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones)
        assigned_zones[1] = rf_selected_zone
    
    esp_selected_zone = None
    esp_nearest = None
    esp_nearest_idx = None
    # Zona especiales
    if 7 in cat_area and len(areas) > 0:
        esp_selected_zone, esp_nearest, esp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_esp_zone(sp_nearest_idx, elements_idx, cat_area, factor, esp_selected_zone, 
                    esp_nearest, esp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, cat_dims[7])
        assigned_zones[7] = esp_selected_zone

    ri_selected_zone = None
    ri_nearest_idx = None
    # Zona reuniones informales (o puestos de trabajo informal)
    if 6 in cat_area and len(areas) > 0:
        ri_fill = False
        ri_selected_zone, ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_ri_zone(pt_nearest_idx, elements_idx, cat_area, factor, ri_selected_zone, 
                    ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, ri_fill)
        assigned_zones[6] = ri_selected_zone
    ri_fill = True

    if(len(areas) > 0):
        diff_zones_areas = {}
        for k, zone in assigned_zones.items():
            if isinstance(zone, list):
                area_zone = 0
                for z in zone:
                    area_zone += z.area
                diff_area = area_zone - cat_area[k]
            else:
                diff_area = zone.area - cat_area[k]
            if diff_area < 0:
                diff_zones_areas[k] = diff_area
        #print(diff_zones_areas)
        if diff_zones_areas:
            diff_zones_areas = {k: v for k, v in sorted(diff_zones_areas.items(), key=lambda item: item[1])}
            for k,v in diff_zones_areas.items():
                if k == 1:
                    rf_selected_zone, rf_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
                            assign_rf_zone(sv_nearest_idx, sp_nearest_idx, ptp_selected_zone, ptp_nearest_idx,
                                        elements_idx, cat_area, factor, rf_selected_zone, rf_nearest_idx,
                                        areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones)
                    assigned_zones[k] = rf_selected_zone
                if k == 4:
                    sv_selected_zone, sv_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
                            assign_services_zone(has_shaft, circs_bounds, elements_idx, cat_area, factor, sv_selected_zone, sv_nearest_idx, areas, shafts_adj_qty, 
                            crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones, cat_dims[4])
                    assigned_zones[k] = sv_selected_zone
                if k == 5:
                    sp_selected_zone, sp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
                        assign_support_zone(core_bounds, entrances_bounds, circs_bounds, elements_idx, cat_area, factor, sp_selected_zone,
                            sp_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                            entrances_adj_qty, core_adj_qty, zones, cat_dims[5])
                    assigned_zones[k] = sp_selected_zone

    last_areas_len = len(areas)
    while len(areas) > 0:
        for zone_name, zone in zones.items():
            nearest = list(map(lambda x: tuple(x.bbox), list(elements_idx.nearest(zone.bounds, objects=True))))
            nearest_idx = [k for k,v in areas.items() if v.bounds in nearest]
            nearest_len = {idx: zone.intersection(areas[idx]).length for idx in nearest_idx if zone.intersection(areas[idx]).geom_type == 'LineString' or zone.intersection(areas[idx]).geom_type == 'MultiLineString'}
            if nearest_len:
                nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                candidate_zone = unary_union([zone, areas[nearest_candidate_idx]])
                if candidate_zone.geom_type == 'Polygon':
                    zones[zone_name] = candidate_zone
                    areas.pop(nearest_candidate_idx, None)
                    shafts_adj_qty.pop(nearest_candidate_idx, None)
                    crystal_adj_qty.pop(nearest_candidate_idx, None)
                    entrances_adj_qty.pop(nearest_candidate_idx, None)
            elif len(areas) < 1:
                break

        if last_areas_len == len(areas):
            break
        else:
            last_areas_len = len(areas)

    while len(areas) > 0:
        ri_selected_zone = zones['ZONA REUNIONES INFORMALES 0'] if 'ZONA REUNIONES INFORMALES 0' in zones.keys() else None
        ri_selected_zone, ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, entrances_adj_qty, core_adj_qty, zones = \
            assign_ri_zone(pt_nearest_idx, elements_idx, cat_area, factor, ri_selected_zone, 
                    ri_nearest_idx, areas, shafts_adj_qty, crystal_adj_qty, 
                    entrances_adj_qty, core_adj_qty, zones, ri_fill)
                    
    return zones

def make_circ_ring(planta, core, shafts, entrances, voids, ring_width):
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    c_minx, c_miny, c_maxx, c_maxy = core.bounds
    #e_minx, e_miny, e_maxx, e_maxy = entrances.bounds
    ring_distance_factor = 0.38

    planta_bbox_points = [Point(p_minx, p_miny), Point(p_maxx, p_maxy)]
    core_bbox_points = [Point(c_minx, c_miny), Point(c_maxx, c_maxy)]

    core_bbox_lines = []
    for p in core_bbox_points:
        line_v = LineString([(p.x, p_miny), (p.x, p_maxy)])
        line_h = LineString([(p_minx, p.y), (p_maxx, p.y)])

        core_bbox_lines.append(line_v)
        core_bbox_lines.append(line_h)
    
    planta_bbox_lines = []
    planta_h_bbox_lines = []
    planta_v_bbox_lines = []
    for p in planta_bbox_points:
        line_v = LineString([(p.x, p_miny), (p.x, p_maxy)])
        line_h = LineString([(p_minx, p.y), (p_maxx, p.y)])

        planta_bbox_lines.append(line_v)
        planta_bbox_lines.append(line_h)
        planta_h_bbox_lines.append(line_h)
        planta_v_bbox_lines.append(line_v)

    entrances_bbox_lines = []
    for e in entrances:
        e_minx, e_miny, e_maxx, e_maxy = e.bounds
        entrance_bbox_points = [Point(e_minx, e_miny), Point(e_maxx, e_maxy)]
        dist_minx_maxx = abs(e_maxx - e_minx)
        dist_miny_maxy = abs(e_maxy - e_miny)
        if(dist_minx_maxx > dist_miny_maxy):
            for ep in entrance_bbox_points:
                e_line_v = LineString([(ep.x, p_miny), (ep.x, p_maxy)])
                entrances_bbox_lines.append(e_line_v)
        else:
            for ep in entrance_bbox_points:
                e_line_h = LineString([(p_minx, ep.y), (p_maxx, ep.y)])
                entrances_bbox_lines.append(e_line_h)

    ring_core_candidates = []
    for cb in core_bbox_lines:
        for eb in entrances_bbox_lines:
            if not cb.intersects(eb):
                ring_core_candidates.append(cb)

    if len(shafts) > 0:
        for s in shafts:
            ring_core_candidates = [l for l in ring_core_candidates if not l.intersects(s)]
    if len(ring_core_candidates) > 1:
        line_planta_dists = []
        for lr in ring_core_candidates:
            tmp_dist = []
            for pb in planta_bbox_lines:
                dist = lr.distance(pb)
                if(dist>0):
                    tmp_dist.append(dist)
            line_planta_dists.append(min(tmp_dist))
        #core_inter_len = [l.intersection(core).length for l in ring_core_candidates]
        #max_len_idx = core_inter_len.index(min(core_inter_len))
        min_len_idx = line_planta_dists.index(min(line_planta_dists))
        ring_core_candidates = [ring_core_candidates[min_len_idx]]
    
    
    ring_core_line = ring_core_candidates[0]

    rcl_x_points = []
    rcl_points = list(ring_core_line.coords)
    for p in rcl_points:
        rcl_x_points.append(p[0])
    rcl_diff_x = rcl_x_points[1] - rcl_x_points[0]
    
    if(rcl_diff_x == 0): #vertical
        if(rcl_points[0][0] > core.centroid.x):
            rcl_width = Point(ring_width, 0)
        else:
            rcl_width = Point(-ring_width, 0)
    else: #horizontal
        if(rcl_points[0][1] > core.centroid.y):
            rcl_width = Point(0, ring_width)
        else:
            rcl_width = Point(0, -ring_width)
    rcl_ring_points = []        
    for p in rcl_points:
        rcl_ring_points.append(Point(p[0]+rcl_width.x ,p[1]+rcl_width.y))
    
    rcl_ring_line = LineString(rcl_ring_points)

    ring_core_lines = [ring_core_line, rcl_ring_line]

    ring_lines = list(ring_core_lines)

    core_candidates_lines = [c for c in core_bbox_lines if not ring_core_line.equals(c)]

    #Primera linea espaciada desde el core
    line_planta_dists = []
    core_spaced_lines = []
    for cl in core_candidates_lines:
        cl_x_points =[]
        cl_points = list(cl.coords)
        for p in cl_points:
            cl_x_points.append(p[0])
        cl_diff_x = cl_x_points[1] - cl_x_points[0]
        if(cl_diff_x == 0): #vertical
            tmp_dist = []
            for pl in planta_v_bbox_lines:
                dist = cl.distance(pl)
                if(dist>0):
                    tmp_dist.append(dist)
            min_dist = min(tmp_dist)
            ring_distance = min_dist*ring_distance_factor
            if(cl_points[0][0] > core.centroid.x):
                cl_width = Point(ring_distance, 0)
            else:
                cl_width = Point(-ring_distance, 0)
        else: #horizontal
            tmp_dist = []
            for pl in planta_h_bbox_lines:
                dist = cl.distance(pl)
                if(dist>0):
                    tmp_dist.append(dist)
            min_dist = min(tmp_dist)
            ring_distance = min_dist*ring_distance_factor
            if(cl_points[0][1] > core.centroid.y):
                cl_width = Point(0, ring_distance)
            else:
                cl_width = Point(0, -ring_distance)
        cl_ring_points = []        
        for p in cl_points:
            cl_ring_points.append(Point(p[0]+cl_width.x ,p[1]+cl_width.y))
        core_spaced_lines.append(LineString(cl_ring_points))

    ring_lines += core_spaced_lines

    #Linea de grosor de lineas espaciadas realizadas anteriormente
    core_spaced_width_lines = []
    for cl in core_spaced_lines:
        cl_x_points =[]
        cl_points = list(cl.coords)
        for p in cl_points:
            cl_x_points.append(p[0])
        cl_diff_x = cl_x_points[1] - cl_x_points[0]
        if(cl_diff_x == 0): #vertical
            if(cl_points[0][0] > core.centroid.x):
                cl_width = Point(ring_width, 0)
            else:
                cl_width = Point(-ring_width, 0)
        else: #horizontal
            if(cl_points[0][1] > core.centroid.y):
                cl_width = Point(0, ring_width)
            else:
                cl_width = Point(0, -ring_width)
        cl_ring_points = []        
        for p in cl_points:
            cl_ring_points.append(Point(p[0]+cl_width.x ,p[1]+cl_width.y))
        core_spaced_width_lines.append(LineString(cl_ring_points))

    ring_lines += core_spaced_width_lines
    lu = unary_union(ring_lines + entrances_bbox_lines + [e.exterior for e in entrances] +  list(planta.interiors))
    pols = list(polygonize(planta.intersection(lu)))
    pols = [p for p in pols if p.area < 50]

    entrances_bounds = list(map(lambda x: x.bounds, entrances))
    pols_bounds = list(map(lambda x: x.bounds, pols))

    holes_idx = rtree.index.Index()
    for i, e in enumerate(pols_bounds + entrances_bounds):
        holes_idx.insert(i, e)
    
    #Filtrado de areas que queden dentro del anillo
    for eb in entrances_bounds:
        entrances_circ = [tuple(obj.bbox) for obj in list(holes_idx.nearest(eb, objects=True)) if tuple(obj.bbox) in pols_bounds]
        if len(entrances_circ) > 1:
            entrances_circ_areas = [box(*p).area for p in entrances_circ]
            entrances_circ = [p for p in entrances_circ if box(*p).area == min(entrances_circ_areas)]
        entrances_circ = entrances_circ[0]
        nearest_ec = [tuple(obj.bbox) for obj in list(holes_idx.nearest(entrances_circ, objects=True)) if tuple(obj.bbox) != entrances_circ]
        nearest_ec_areas = [box(*p).area for p in nearest_ec]
        for p in nearest_ec:
            if box(*p).area == max(nearest_ec_areas):
                pols_bounds.remove(p)

    #Se crea la lista de elementos del anillo y se filtran los hoyos de la planta que vayan quedando en la lista
    # circ_ring_pols = []
    # void_pols = [Polygon(v) for v in voids]
    # for pol in pols_bounds:
    #     box_pol = box(*pol)
    #     is_void = False
    #     for v in void_pols:
    #         if box_pol.equals(v):
    #             is_void = True
    #             break
    #     if not is_void:
    #         circ_ring_pols.append(box_pol)
    #         # circ_ring_pols.append(box_pol.buffer(-0.0001, cap_style=3, join_style=2))

    circ_ring_pols = []
    void_pols = [Polygon(v) for v in voids]
    for pol in pols_bounds:
        box_pol = box(*pol)
        is_void = False
        for v in void_pols:
            if box_pol.equals(v):
                is_void = True
                break
        if not is_void:
            #circ_ring_pols.append(box_pol.buffer(-0.0001, cap_style=3, join_style=2))
            circ_ring_pols.append(box_pol)

    #Se genera el poligono completo del anillo
    '''circ_ring = circ_ring_pols[0]
    circ_ring_pols.remove(circ_ring)
    p_candidates = [p for p in circ_ring_pols if p.intersects(circ_ring)]
    while p_candidates:
        for pc in p_candidates:
            circ_ring = circ_ring.union(pc)
            circ_ring_pols.remove(pc)
        p_candidates = [p for p in circ_ring_pols if p.intersects(circ_ring)]'''

    return circ_ring_pols

# deprecado
def filter_areas(circ_pols, areas):
    while not all([all([a.intersection(circ).area == 0 for circ in circ_pols]) for a in areas.values()]):
        i = 0
        k = 0
        while k + i != len(areas):
            v = areas[k]
            for circ in circ_pols:
                if v.intersection(circ).area > 0:
                    new_area = v.difference(circ)
                    if new_area.geom_type == 'MultiPolygon':
                        new_areas = list(new_area)
                        areas[k] = new_areas.pop(0)
                        for na in new_areas:
                            areas[len(areas)] = na
                            i += 1
                    else:
                        areas[k] = new_area
                elif v.geom_type == 'MultiPolygon':
                    new_areas = list(v)
                    areas[k] = new_areas.pop(0)
                    for na in new_areas:
                        areas[len(areas)] = na
                        i += 1
            k += 1
    return areas

def merge_min_areas(areas, max_dim):
    
    while not all([a.area > max_dim for a in areas.values()]):
        areas_idx = rtree.index.Index()
        for i, e in enumerate([a.bounds for a in areas.values()]):
            areas_idx.insert(i, e)

        new_areas_list = []
        merged_idx = []
        
        for i, a in areas.items():
            if not i in merged_idx:
                if a.area < max_dim:
                    nearest_idx = list(areas_idx.nearest(a.bounds))
                    nearest_len = {idx: a.intersection(areas[idx]).length for idx in nearest_idx if idx != i}
                    nearest_candidate_idx = max(nearest_len, key=nearest_len.get)
                    merged_idx.append(i)
                    merged_idx.append(nearest_candidate_idx)
                    new_area = unary_union([a, areas[nearest_candidate_idx]])
                    new_areas_list.append(new_area)

        leftover_areas = [v for k,v in areas.items() if not k in merged_idx]

        new_areas = {}
        for i, a in enumerate(leftover_areas + new_areas_list):
            new_areas[i] = a
        areas = new_areas

    while not all([all([a1.intersection(a2).area == 0 for a2 in areas.values() if a1 != a2]) for a1 in areas.values()]):
        areas_idx = rtree.index.Index()
        for i, e in enumerate([a.bounds for a in areas.values()]):
            areas_idx.insert(i, e)

        new_areas_list = []
        merged_idx = []

        for i, a in areas.items():
            if not i in merged_idx:
                nearest_idx = [idx for idx in list(areas_idx.nearest(a.bounds)) if idx != i and not idx in merged_idx]
                for idx in nearest_idx:
                    if a.intersection(areas[idx]).area > 0:
                        merged_idx.append(i)
                        merged_idx.append(idx)
                        new_area = unary_union([a, areas[idx]])
                        new_areas_list.append(new_area)
                        break

        leftover_areas = [v for k,v in areas.items() if not k in merged_idx]

        new_areas = {}
        for i, a in enumerate(leftover_areas + new_areas_list):
            new_areas[i] = a
        areas = new_areas

    while not all([a.geom_type == 'Polygon' for a in areas.values()]):
        k = 0
        i = 0
        while k + i != len(areas):
            v = areas[k]
            if v.geom_type == 'MultiPolygon':
                new_areas = list(v)
                areas[k] = new_areas.pop(0)
                for na in new_areas:
                    areas[len(areas)] = na
                    i += 1
            k += 1
    return areas

def merge_voids(voids, circ_pols):
    voids_pols = [Polygon(v) for v in voids]

    circ_voids_pols = list(unary_union(voids_pols + circ_pols))

    return [list(circ.exterior.coords) for circ in circ_voids_pols]

def get_category_max_dims(inlist):
    cat_max_dims = {}
    for mod in inlist:
        cat_id = mod[4]
        cat_max_dims[cat_id] = {} if cat_id not in cat_max_dims else cat_max_dims[cat_id]
        cat_max_dims[cat_id]['max_width'] = mod[2] if 'max_width' not in cat_max_dims[cat_id] else max(mod[2], cat_max_dims[cat_id]['max_width'])
        cat_max_dims[cat_id]['max_height'] = mod[3] if 'max_height' not in cat_max_dims[cat_id] else max(mod[3], cat_max_dims[cat_id]['max_height']) 
        cat_max_dims[cat_id]['max_area'] = cat_max_dims[cat_id]['max_width']*cat_max_dims[cat_id]['max_height']
    return cat_max_dims

start_time = time.time()

def Smart_Layout(dictionary, POP_SIZE, GENERATIONS, viz=False, viz_period=10):

    print(round(time.time() - start_time, 2), 'Start!')
    outline, holes, areas, input_list = get_input(dictionary)

    input_list= [   ['WYS_SALAREUNION_RECTA6PERSONAS',              1, 3, 4.05, 1],
                    ['WYS_SALAREUNION_DIRECTORIO10PERSONAS',        1, 4, 6.05, 1],
                    ['WYS_SALAREUNION_DIRECTORIO20PERSONAS',        0, 5.4, 6, 1],
                    ['WYS_PUESTOTRABAJO_CELL3PERSONAS',             10, 3.37, 3.37, 2],
                    #['WYS_PUESTOTRABAJO_RECTO2PERSONAS',            2, 3.82, 1.4],
                    ['WYS_PRIVADO_1PERSONA',                        1, 3.5, 2.8, 3],
                    ['WYS_PRIVADO_1PERSONAESTAR',                   1, 6.4, 2.9, 3],
                    ['WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS',    1, 3.54, 3.02, 4],
                    ['WYS_SOPORTE_BAÑOBATERIAMASCULINO3PERSONAS',   1, 3.54, 3.02, 4],
                    ['WYS_SOPORTE_KITCHENETTE',                     1, 1.6, 2.3, 4],
                    ['WYS_SOPORTE_SERVIDOR1BASTIDOR',               1, 1.5, 2.4, 4],
                    ['WYS_SOPORTE_PRINT1',                          1, 1.5, 1.3, 4],
                    ['WYS_RECEPCION_1PERSONA',                      1, 2.7, 3.25, 5],
                    ['WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS',    0, 2.05, 1.9, 5],
                    ['WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA',    0, 2.05, 2.01, 5],
                    ['WYS_COLABORATIVO_BARRA6PERSONAS',             2, 1.95, 2.4, 6],
                    ['WYS_ESPECIALES_TALLERLABORATORIO4PERSONAS',   1, 4, 5, 7]]
    
    '''input_list= [   ['WYS_SALAREUNION_RECTA6PERSONAS',              0, 3, 4.05, 1],
                    ['WYS_SALAREUNION_DIRECTORIO10PERSONAS',        0, 4, 6.05, 1],
                    ['WYS_SALAREUNION_DIRECTORIO20PERSONAS',        0, 5.4, 6, 1],
                    ['WYS_PUESTOTRABAJO_CELL3PERSONAS',             0, 3.37, 3.37, 2],
                    #['WYS_PUESTOTRABAJO_RECTO2PERSONAS',            2, 3.82, 1.4],
                    ['WYS_PRIVADO_1PERSONA',                        0, 3.5, 2.8, 3],
                    ['WYS_PRIVADO_1PERSONAESTAR',                   0, 6.4, 2.9, 3],
                    ['WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS',    0, 3.54, 3.02, 4],
                    ['WYS_SOPORTE_BAÑOBATERIAMASCULINO3PERSONAS',   0, 3.54, 3.02, 4],
                    ['WYS_SOPORTE_KITCHENETTE',                     0, 1.6, 2.3, 4],
                    ['WYS_SOPORTE_SERVIDOR1BASTIDOR',               0, 1.5, 2.4, 4],
                    ['WYS_SOPORTE_PRINT1',                          0, 1.5, 1.3, 4],
                    ['WYS_RECEPCION_1PERSONA',                      0, 2.7, 3.25, 5],
                    ['WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS',    0, 2.05, 1.9, 5],
                    ['WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA',    0, 2.05, 2.01, 5],
                    ['WYS_COLABORATIVO_BARRA6PERSONAS',             0, 1.95, 2.4, 6],
                    ['WYS_ESPECIALES_TALLERLABORATORIO4PERSONAS',   0, 4, 5, 7]]'''
    voids = []

    border = outline[0][1]
    for h in holes:
        voids.append(h[1])

    cat_area = {}

    # INPUT PARAMETERS
    N = 0  # number of modules to be placed in total
    for i in input_list:
        qty = i[1]
        N += qty
        total_area = qty*i[2]*i[3]
        cat_id = i[4]
        if qty > 0:
            if cat_id in cat_area:
                cat_area[cat_id] += total_area
            else:
                cat_area[cat_id] = total_area
    #print(cat_area)
    cat_dims = get_category_max_dims(input_list)

    #min_cat_area, min_cat_key = min(((v1,k0) for k0,v0 in cat_dims.items() for k1,v1 in v0.items() if k1 == 'max_area'))
    max_cat_width, min_cat_key = max(((v1,k0) for k0,v0 in cat_dims.items() for k1,v1 in v0.items() if k1 == 'max_width'))
    max_cat_height, min_cat_key = max(((v1,k0) for k0,v0 in cat_dims.items() for k1,v1 in v0.items() if k1 == 'max_height'))
    
    max_dim = max(max_cat_width, max_cat_height)

    #print('cat_dims:', cat_dims)
    #print('max_dim:', max_dim)
    #print("min cat area, key", (min_cat_area, min_cat_key))
    #print(round(time.time() - start_time, 2), 'Load and compute all the inputs')
    #print('Number of modules: ', N)
    # GA PARAMETERS
    IND_SIZE = N  # should be equal or very close to N

    planta = Polygon(border, voids)

    As = []
    shafts = []
    entrances = []
    crystal_facs = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])
        if a[0] == 'WYS_CORE':
            core = As[-1][0]
        if a[0] == 'WYS_SHAFT':
            shafts.append(As[-1][0])
        if a[0] == 'WYS_ENTRANCE':
            entrances.append(As[-1][0])
        if a[0] == 'WYS_FACADE_CRYSTAL':
            crystal_facs.append(As[-1][0])
    
    circ_width = 1.2
    circ_pols = make_circ_ring(planta, core, shafts, entrances, voids, circ_width)
    #areas = make_areas(planta, core)

    #areas = get_area(planta, core, min_area=2, divisiones=15, proporcional=True)
    
    areas = get_area2(planta, core, circ_pols, min_dim_area=max_dim, proporcional=False)

    #areas = get_pol_zones(outline, voids, min_area=3, min_dim=3, boundbox_on_outline=False, boundbox_on_holes=True)
    
    #areas = filter_areas(circ_pols, areas)
    #areas = get_pol_zones(outline, circ_voids_coords, min_area=min_cat_area, min_dim=min_cat_area, boundbox_on_outline=False, boundbox_on_holes=False)
    
    areas = merge_min_areas(areas, max_dim*3)

    def circ_buffer(circ_pols):
        circ_polygons = []
        for c in circ_pols:
            r_minx, r_miny, r_maxx, r_maxy = c.bounds
            line1 = LineString([(r_minx, r_miny), (r_minx, r_maxy)])
            line2 = LineString([(r_minx, r_maxy), (r_maxx, r_maxy)])
            line3 = LineString([(r_maxx, r_maxy), (r_maxx, r_miny)])
            line4 = LineString([(r_maxx, r_miny), (r_minx, r_miny)])
            if line1.length > line2.length:
                line1_buf = substring(line1, start_dist=0.0001, end_dist=-0.0001)
                line3_buf = substring(line3, start_dist=0.0001, end_dist=-0.0001)
                l1_min, l1_max = line1_buf.boundary
                l3_max, l3_min = line3_buf.boundary
                rectan1 = Polygon([l1_min, l1_max, l3_max, l3_min, l1_min])
                circ_polygons.append(rectan1)
            elif line1.length < line2.length:
                line2_buf = substring(line2, start_dist=0.0001, end_dist=-0.0001)
                line4_buf = substring(line4, start_dist=0.0001, end_dist=-0.0001)
                l2_min, l2_max = line2_buf.boundary
                l4_max, l4_min = line4_buf.boundary
                rectan2 = Polygon([l2_min, l2_max, l4_max, l4_min, l2_min])
                circ_polygons.append(rectan2)
            else:
                circ_polygons.append(c)
                #continue
        return circ_polygons

    circ_pols = circ_buffer(circ_pols)
    #circ_pols = [c.buffer(-0.0001, cap_style=3, join_style=2) for c in circ_pols]

    circ_voids_coords = merge_voids(voids, circ_pols)
    print("planta valida:", planta.is_valid)
    planta = Polygon(border, circ_voids_coords)
    print("planta valida:", planta.is_valid)
    zones = make_zones(planta, shafts, core, circ_voids_coords, entrances, crystal_facs, areas, cat_area, cat_dims)
    #zones = {}

    def mutMod(individual, planta, mu, sigma, indpb):
        minx, miny, maxx, maxy = planta.bounds
        for i in individual:

            if random.random() < indpb:
                dx = round(random.gauss(mu, sigma), 1)
                i.x += dx
                if not planta.contains(i.get_box()):
                    if i.x > maxx - i.width / 2:
                        i.x = round(maxx - i.width / 2 - 0.05, 1)
                    elif i.x < minx + i.width / 2:
                        i.x = round(minx + i.width / 2 + 0.05, 1)

            if random.random() < indpb:
                dy = round(random.gauss(mu, sigma), 1)
                i.y += dy
                if not planta.contains(i.get_box()):
                    if i.y > maxy - i.height / 2:
                        i.y = round(maxy - i.height / 2 - 0.05, 1)
                    elif i.y < miny + i.height / 2:
                        i.y = round(miny + i.height / 2 + 0.05, 1)

            if random.random() < indpb:
                i.height, i.width = i.width, i.height
                i.rot += 90
                if not planta.contains(i.get_box()):
                    i.height, i.width = i.width, i.height
                    i.rot -= 90
                else:
                    if i.rot >= 360:
                        i.rot = 0
            i.x, i.y = round(i.x, 1), round(i.y, 1)
        return individual,

    def acond_distance(d):
        return 10 * math.exp(-d / 3)
        #return d

    def modtoareas(As, ind):
        a = 0
        boxes = []
        print("Comienza modtoareas")
        for mod in ind:
            boxes.append(
                [mod.get_box(),
                 mod.name])
            mod.fitval1 = 0
            mod.fitval2 = 0
        nb = len(boxes)

        for i in range(nb):
            bx_dist = []
            for A in As:
                bx_dist.append([A[1], boxes[i][0].distance(A[0])])

            bx_dist2 = min_dist_to_area(bx_dist)

            for d in bx_dist2:
                w = restrictions.mod2area(restrictions.module_dictionary, restrictions.area_dictionary,
                                          restrictions.mod2area_matrix, boxes[i][1], d[0])
                if w != 0:
                    #print("fitval1")
                    ind[i].fitval1 += round((acond_distance(d[1]) * w)/(ind[i].qty), 2)
                    a += (acond_distance(d[1]) * w)/(ind[i].qty)

            distances = []
            for j in range(nb):
                if i is not j:
                    distances.append([boxes[j][1], boxes[i][0].distance(boxes[j][0])])

            distances2 = min_dist_to_area(distances)
            for d in distances2:
                w = restrictions.mod2mod(restrictions.module_dictionary, restrictions.mod2mod_matrix,
                                         boxes[i][1], d[0])
                if w != 0:
                    #print("fitval2")
                    ind[i].fitval2 += round((acond_distance(d[1]) * w)/(ind[i].qty), 2)
                    a += (acond_distance(d[1]) * w)/(ind[i].qty)
        return a

    def evaluateInd(ind):
        pond = -10
        fit_list = []
        fit_list.append(modtoareas(As, ind))
        fit_list.append(pond * feas_distance(ind))
        a = sum(fit_list)
        print("Evaluate Ind = " + str(a))
        return a,

    def feasible(ind):  # Need too add if boxes collide
        """Feasibility function for the individual. Returns True if feasible False
        otherwise."""
        boxes = []
        for mod in ind:
            boxes.append(mod.get_box())
        nb = len(boxes)
        print("¿ Is Feasible ? Boxes = "+str(nb))
        for i in range(nb):
            if not planta.contains(boxes[i]):
                print("Feasible.boxes 1 " + str(len(boxes)))
                return False
            for j in range(i + 1, nb):
                if boxes[i].intersects(boxes[j]):
                    print("Feasible.boxes 2 " + str(j))
                    # print(i,j)
                    return False
        print("Yes")
        return True


    def feas_distance(ind):
        # check for intermods collisions:
        area = 0
        boxes = []
        for mod in ind:
            boxes.append(
                [mod.get_box(),
                 mod.name])
        nb = len(boxes)
        for i in range(nb):
            if not planta.contains(boxes[i][0]):
                area += boxes[i][0].area - boxes[i][0].intersection(planta).area
            for j in range(i + 1, nb):
                if boxes[i][0].intersects(boxes[j][0]):
                    area += boxes[i][0].intersection(boxes[j][0]).area
        print("Feas Distance Area: " + str(area))
        return area

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_pos", makePos, planta, input_list, zones)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     (toolbox.attr_pos), n=IND_SIZE)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutMod, planta=planta, mu=0, sigma=0.5, indpb=0.2)
    toolbox.register("select_best", tools.selBest)
    toolbox.register("select_roulette", tools.selRoulette)
    toolbox.register("select", tools.selTournament, tournsize=3)
    # toolbox.register("select", tools.selTournament, tournsize=round(POP_SIZE*0.4))
    # toolbox.register("select", tools.selNSGA2)
    toolbox.register("evaluate", evaluateInd)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    # toolbox.decorate("evaluate", tools.DeltaPenalty(feasible, -10.0, feas_distance))

    # Init of the algorithm
    print(round(time.time() - start_time, 1), 'Generate population:')

    pop = toolbox.population(n=POP_SIZE)
    print("Cantidad de Población: "+str(len(pop)))
    print(round(time.time() - start_time, 1), '...Done')

    CXPB, MUTPB, NGEN = 0.5, 0.2, GENERATIONS

    # Evaluate the entire population
    fitnesses = map(toolbox.evaluate, pop)

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit
        print(fit)

    #fig, ax = viewer.viewer_viz(planta, As, viz, areas= areas, zones=zones)
    fig, ax = viewer.viewer_viz(planta, As, viz)

    print(round(time.time() - start_time, 2), 'Start of genetic evolution:')

    max_count = 0
    max_fit = -9999999
    for g in range(NGEN):

        boxes = viewer.viz_update(viz, viz_period, g, pop, fig, ax)
        fitn = [o.fitness.values[0] for o in pop]
        print('Time:', round(time.time() - start_time, 1), ' Generation ', g + 1, 'of', NGEN, 'POP SIZE:', len(pop),
              '  Min:', round(min(fitn), 2), 'Max:', round(max(fitn), 2), 'Avg:', round(sum(fitn) / len(fitn), 1),
              'Local sol. count:', max_count)

        if max(fitn) < 0:
            CXPB = 0.1
            MUTPB = 0.6
        else:
            CXPB = 0.5
            MUTPB = 0.2
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))
        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        if pop[0]:
            # Apply crossover and mutation on the offspring
            for child1, child2 in zip(offspring[::2], offspring[1::2]):
                if random.random() < CXPB:  # probabilidad de mate?? mejor hacer que hagan mate si o si... linea de select
                    toolbox.mate(child1, child2)
                    del child1.fitness.values
                    del child2.fitness.values

            for mutant in offspring:
                if random.random() < MUTPB:
                    toolbox.mutate(mutant)
                    del mutant.fitness.values

            # Evaluate the individuals with an invalid fitness
            invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
            print("Debiera entrar")
            fitnesses = map(toolbox.evaluate, invalid_ind)
            for ind, fit in zip(invalid_ind, fitnesses):
                ind.fitness.values = fit

            #offspring = toolbox.select(offspring + pop, POP_SIZE)
            best_ind = toolbox.select_best(pop, k=int(POP_SIZE*0.4))
            pop[:] = offspring + best_ind

            pop.sort(key=lambda x: x.fitness, reverse=True)
            pop = pop[:POP_SIZE]

        viewer.viz_clear(viz, g, NGEN, viz_period, boxes)

    viewer.viz_end()
    print(round(time.time() - start_time, 1), 'Finish')
    print('Best individual of Generation', g + 1, ':')
    out = []
    # pop.sort(key=lambda x: x.fitness, reverse=True)
    for mod in pop[0]:
        out.append([mod.name, mod.id, mod.x, mod.y, mod.rot])
        # print(mod.name, '(', mod.x, ',', mod.y, ')', 'id:', mod.id, 'rot:', mod.rot)
    print('Fitness = ', pop[0].fitness.values)
    # viewer.show_floor(planta, As, pop, g)
    '''for o in out:
        print(o)'''

    return out
