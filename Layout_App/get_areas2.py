"""
This module contains the code necessary to divide the plant into smaller areas.
Previous step for zoning.
"""
import numpy as np
from rtree import index
from shapely.geometry import Point, MultiLineString
from shapely.geometry.polygon import LineString     # ,Polygon
from shapely.ops import unary_union, polygonize

# import matplotlib.pyplot as plt
# from Layout_App import example_data_v3, example_data_v4
# from Layout_App.SmartLayout import make_circ_ring


def crear_areas(planta, core, circ_pols, min_dim_area, proporcional=True):
    """Divide the plant into subareas whose dimensions will depend on the min_dim_area parameter
    ___
    parameters:

        planta: Plant
        core: Core of the floor
        circ_pols: Polygons that make up the circulation
        min_dim_area: Minimum dimension for subareas
        proporcional: It establishes if the division of the plant will be proportional (True) or if this division will
                      be carried out depending on the core (False).
    """
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    c_minx, c_miny, c_maxx, c_maxy = core.bounds
    core_bbox_points = [Point(c_minx, c_miny), Point(c_maxx, c_maxy)]
    circulacion = unary_union(circ_pols)

    num_divisions_x = int(np.ceil((p_maxx - p_minx) / min_dim_area))
    num_divisions_y = int(np.ceil((p_maxy - p_miny) / min_dim_area))

    if proporcional == True:
        # Crea líneas equidistantes a lo largo y ancho de la planta
        lines = []
        for lx in range(1, num_divisions_x):
            line_x = LineString([(p_minx + min_dim_area * lx, p_miny), (p_minx + min_dim_area * lx, p_maxy)])
            lines.append(line_x)
        for ly in range(1, num_divisions_y):
            line_y = LineString([(p_minx, p_miny + min_dim_area * ly), (p_maxx, p_miny + min_dim_area * ly)])
            lines.append(line_y)
    else:
        # Crea las líneas alrededor del core y subdivide esas mismas áreas
        num_divisions = int(num_divisions_x/3)
        lines = []
        for p in core_bbox_points:
            line_v = LineString([(p.x, p_miny), (p.x, p_maxy)])
            line_h = LineString([(p_minx, p.y), (p_maxx, p.y)])
            lines.append(line_v)
            lines.append(line_h)
            if p.x == c_minx:
                longy = (c_miny - p_miny) / num_divisions
                longx = (c_minx - p_minx) / num_divisions
                longxc = (c_maxx - c_minx) / num_divisions
                longyc = (c_maxy - c_miny) / num_divisions
                for lm in range(1, num_divisions):
                    line_x = LineString([(p_minx + longx*lm, p_miny), (p_minx + longx*lm, p_maxy)])
                    line_y = LineString([(p_minx, p_miny + longy*lm), (p_maxx, p_miny + longy*lm)])
                    line_cx = LineString([(c_minx + longxc*lm, p_miny), (c_minx + longxc*lm, p_maxy)])
                    line_cy = LineString([(p_minx, c_miny + longyc * lm), (p_maxx, c_miny + longyc * lm)])
                    lines.append(line_x)
                    lines.append(line_y)
                    lines.append(line_cx)
                    lines.append(line_cy)
            if p.x == c_maxx:
                longy = (p_maxy - c_maxy) / num_divisions
                longx = (p_maxx - c_maxx) / num_divisions
                for lm in range(1, num_divisions):
                    line_x = LineString([(c_maxx + longx*lm, p_miny), (c_maxx + longx*lm, p_maxy)])
                    line_y = LineString([(p_minx, c_maxy + longy*lm), (p_maxx, c_maxy + longy*lm)])
                    lines.append(line_x)
                    lines.append(line_y)
    lu = unary_union(lines)
    inter = unary_union([planta.intersection(lu), circulacion.intersection(lu), planta.boundary, circulacion.boundary])
    # Poligoniza las áreas
    pols = list(polygonize(MultiLineString(inter)))
    pols_planta = list(polygonize(MultiLineString(planta.boundary)))

    # Se eliminan las áreas que corresponden a los pilares y al core
    for i, p in enumerate(pols_planta):
        if p.area < 1:
            for e, po in enumerate(pols):
                if p.bounds == po.bounds:
                    del pols[e]
    # # Busca el centroide del core para eliminar esa área
    centroids_dist = [p.centroid.distance(core.centroid) for p in pols]
    min_centroid_value, min_centroid_idx = min((val, idx) for (idx, val) in enumerate(centroids_dist))
    del pols[min_centroid_idx]

    # Se eliminan las áreas dentro de la circulación
    areas_del = []
    for idx, a in enumerate(pols):
        if circulacion.contains(pols[idx]):
            areas_del.append(idx)
    areas_del.sort(reverse=True)
    for e in areas_del:
        del pols[e]

    return pols


def areas_union(min_area, pols):
    """Finds the areas smaller than the minimum area and joins them to the neighbor with the greatest adjacency
    ___
    parameters:

        min_area: Minimum area
        pols: Polygons from the previous stage (create_areas)
    """
    areas_idx = index.Index()
    for i, p in enumerate(pols):
        areas_idx.insert(i, p.bounds)
    areas_dict = {k:v for k, v in enumerate(pols)}
    calc_areas_dict = {idx:area.area for idx, area in areas_dict.items()}
    min_areas_idx = {idx for idx, area in calc_areas_dict.items() if area < min_area}
    while len(min_areas_idx) > 0:
        indice = []
        for idx in min_areas_idx:
            if idx in areas_dict and idx not in indice:
                # Encontrar áreas adyacentes
                areas_vecinas = list(areas_idx.intersection(pols[idx].bounds))
                adj_max = []
                for v in areas_vecinas:
                    if idx != v and v in areas_dict and v not in indice:
                        adj = pols[idx].intersection(pols[v]).length
                        adj_max.append([v, adj])
                if len(adj_max) > 0:
                    adj_max = sorted(adj_max, key=lambda max: max[1])
                    q = adj_max[-1][0]
                else:
                    continue
                # Se agregan los polinomios resultados de la union
                if pols[idx].intersects(pols[q]):
                    pols.append(pols[idx].union(pols[q]))
                    areas_dict.pop(idx);   areas_dict.pop(q)
                    areas_dict.setdefault(idx, pols[idx].union(pols[q]))
                    indice.append(idx); indice.append(q)

        # Se eliminan las áreas que se unieron a otras
        pols = []
        for e, f in areas_dict.items():
            pols.append(f)
        # Se vuelven a crear los ïndices
        areas_idx = index.Index()
        for i, p in enumerate(pols):
            areas_idx.insert(i, p.bounds)
        # Se vuelven a crear los diccionarios
        areas_dict = {k: v for k, v in enumerate(pols)}
        calc_areas_dict = {idx:area.area for idx, area in areas_dict.items()}
        min_areas_idx = {idx for idx, area in calc_areas_dict.items() if area < min_area}
        # min_areas_idx = {}
    return areas_dict


def get_area2(planta, core, circ_pols, min_dim_area, proporcional):
    """Function calling main functions"""
    pols = crear_areas(planta, core, circ_pols, min_dim_area, proporcional)
    # pols_a = pols.copy()
    min_area = min_dim_area
    areas_dict = areas_union(min_area, pols)
    return areas_dict   # , pols_a



# def get_input(data):
#     Planta = data.get('selected_floor').get('polygons')
#     plant = []
#     outline = []
#     holes = []
#     areas = []
#     for Area in Planta:
#         plant.append(
#             [Area.get('name'), [(round(a.get('x') / 100, 1), round(a.get('y') / 100, 1)) for a in Area.get('points')]])
#     for p in plant:
#         if p[0] == 'WYS_AREA_UTIL':
#             outline.append(p)
#         elif p[0] == 'WYS_HOLE':
#             holes.append(p)
#         else:
#             areas.append(p)
#     return outline, holes, areas
#
# outline, holes, areas = get_input(example_data_v3.dict_ex)
#
# voids = []
# border = outline[0][1]
# pilares = [] #### para graficar
# for h in holes:
#     voids.append(h[1])
#     pilares.append(Polygon(h[1]))
# planta = Polygon(border, voids)
#
# As = []
# shafts = []
# entrances = []
# for a in areas:
#     As.append([Polygon(a[1]), a[0]])
#     if a[0] == 'WYS_CORE':
#         core = As[-1][0]
#     if a[0] == 'WYS_SHAFT':
#         shafts.append(As[-1][0])
#     if a[0] == 'WYS_ENTRANCE':
#         entrances.append(As[-1][0])
# circ_width = 1.2
# circ_pols = make_circ_ring(planta, core, shafts, entrances, voids, circ_width)
# #circulacion = unary_union(circ_pols)
#
# areas_dict, pols_a = get_area2(planta, core, circ_pols, min_dim_area=3, proporcional=True)
#
# for e,f in areas_dict.items():
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='#a8e4a0')
#     plt.text(f.centroid.x, f.centroid.y, 'A: '+ str(e), weight='bold', fontsize=6, ma='center', color='g')
# x, y = planta.exterior.xy
# plt.plot(x, y, color='black')
#
# # for e, f in enumerate(pols_a):    # Areas en polígonos
# #     x, y = f.exterior.xy
# #     plt.plot(x, y, color='#a8e4a0')
# #     plt.text(f.centroid.x, f.centroid.y, 'A: '+ str(e), weight='bold', fontsize=6, ma='center', color='g')
#
# for f in shafts:
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='black')
# for f in pilares:
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='black')
# plt.show()