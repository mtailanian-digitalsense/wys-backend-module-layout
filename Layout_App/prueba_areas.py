from rtree import index
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiLineString
from shapely.geometry.polygon import Polygon, LineString
from shapely.ops import unary_union, polygonize, linemerge
from Layout_App import example_data_v3, example_data_v4

#%%

num_divisions = 7
min_area = 2
proporcional = True

def get_input(data):
    Planta = data.get('selected_floor').get('polygons')
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
    return outline, holes, areas

#%%
# Obtener la Planta
outline, holes, areas = get_input(example_data_v3.dict_ex)
voids = []
border = outline[0][1]
pilares = [] #### para graficar
for h in holes:
    voids.append(h[1])
    pilares.append(Polygon(h[1]))
planta = Polygon(border, voids)
#%%%
# # Extracción de la planta y el core
As = []
shaft = []
for a in areas:
    As.append([Polygon(a[1]), a[0]])
    if a[0] == 'WYS_CORE':
        core = As[-1][0]
    if a[0] == 'WYS_SHAFT':
        shaft.append(As[-1][0])
p_minx, p_miny, p_maxx, p_maxy = planta.bounds
c_minx, c_miny, c_maxx, c_maxy = core.bounds
core_bbox_points = [Point(c_minx, c_miny), Point(c_maxx, c_maxy)]

#%%
# Se crean las áreas sobre la planta
if proporcional == True:
    # Crea líneas equidistantes a lo largo y ancho de la planta
    longy = (p_maxy - p_miny) / num_divisions
    longx = (p_maxx - p_minx) / num_divisions
    lines = []
    for lm in range(1, num_divisions):
        line_x = LineString([(p_minx + longx * lm, p_miny), (p_minx + longx * lm, p_maxy)])
        line_y = LineString([(p_minx, p_miny + longy * lm), (p_maxx, p_miny + longy * lm)])
        lines.append(line_x)
        lines.append(line_y)
    lu = unary_union(lines)
    inter = unary_union([planta.intersection(lu), planta.boundary])
    # Poligoniza las áreas
    pols = list(polygonize(MultiLineString(inter)))
    pols_planta = list(polygonize(MultiLineString(planta.boundary)))
else:
    # Crea las líneas alrededor del core y subdivide esas mismas áreas
    num_divisions = int(num_divisions/3)
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
    inter = unary_union([planta.intersection(lu), planta.boundary])
    # Poligoniza las áreas
    pols = list(polygonize(MultiLineString(inter)))
    pols_planta = list(polygonize(MultiLineString(planta.boundary)))

#%%
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

#%%
# Busca las áreas menores al área mínima y las une al vecino de mayor adyacencia
areas_idx = index.Index()
for i, p in enumerate(pols):
    areas_idx.insert(i, p.bounds)
areas_del = []
areas_dict = {k:v for k, v in enumerate(pols)}
calc_areas_dict = {idx:area.area for idx, area in areas_dict.items()}
min_areas_idx = {idx for idx, area in calc_areas_dict.items() if area < min_area}
while len(min_areas_idx) > 0:
    for idx in min_areas_idx:
        if idx in areas_dict:
            # Encontrar áreas adyacentes
            areas_vecinas = list(areas_idx.intersection(pols[idx].bounds))
            adj_max = []
            for v in areas_vecinas:
                if idx != v and v in areas_dict:
                    adj = pols[idx].intersection(pols[v]).length
                    adj_max.append([v, adj])
            if len(adj_max) > 0:
                adj_max = sorted(adj_max, key=lambda max: max[1])
                q = adj_max[-1][0]
            else:
                continue
            # Se agregan los polinomios resultados de la union
            pols.append(pols[idx].union(pols[q]))
            areas_del.append(idx); areas_del.append(q)
            areas_dict.pop(idx);   areas_dict.pop(q)
            areas_dict.setdefault(idx, pols[idx].union(pols[q]))
    # Se eliminan las áreas que se unieron a otras
    areas_del.sort(reverse=True)
    for e in areas_del:
        del pols[e]
    areas_del = []
    # Se vuelven a crear los ïndices
    areas_idx = index.Index()
    for i, p in enumerate(pols):
        areas_idx.insert(i, p.bounds)
    # Se vuelven a crear los diccionarios
    areas_dict = {k: v for k, v in enumerate(pols)}
    calc_areas_dict = {idx:area.area for idx, area in areas_dict.items()}
    min_areas_idx = {idx for idx, area in calc_areas_dict.items() if area < min_area}

#%%
# Plot de la figura
#for e,f in areas_dict.items():
#for f in visited_list:
for e, f in enumerate(pols):
    x, y = f.exterior.xy
    plt.plot(x, y, color='#a8e4a0')
    plt.text(f.centroid.x, f.centroid.y, 'A: '+ str(e), weight='bold', fontsize=6, ma='center', color='g')

x, y = planta.exterior.xy
plt.plot(x, y, color='black')
for f in shaft:
    x, y = f.exterior.xy
    plt.plot(x, y, color='black')
for f in pilares:
    x, y = f.exterior.xy
    plt.plot(x, y, color='black')
plt.show()

#%%
# # Busca el área más cercana al origen (punto inferior izquierdo de la planta)
# start_point = Point(p_minx, p_miny)
# sp_centroid_dist = [p.centroid.distance(start_point) for p in pols]
# min_dist_value, min_dist_idx = min((val, idx) for (idx, val) in enumerate(sp_centroid_dist))
# visited_list = [pols[min_dist_idx]]
# areas_dict[0] = pols[min_dist_idx]
# # Busca el área más lejana a la esquina superior izquierda
# ref_point = Point(p_minx, p_maxy)
# max_centroid_dist = [p.centroid.distance(ref_point) for p in pols]
# max_dist_value, max_dist_idx = max((val, idx) for (idx, val) in enumerate(max_centroid_dist))
#
# #%%
# for i in range(len(pols)):
#     areas_adj = [pols[pid] for pid in list(areas_idx.nearest(visited_list[-1].bounds)) if
#                  pols[pid] != visited_list[-1] and not pols[pid] in visited_list]
#     min_area_idx = 0
#     if len(areas_adj) > 1 and not pols[max_dist_idx] in areas_adj:
#         min_centroid_dist = [a.centroid.distance(ref_point) for a in areas_adj]
#         min_dist_value, min_area_idx = min((val, idx) for (idx, val) in enumerate(min_centroid_dist))
#     elif pols[max_dist_idx] in areas_adj:
#         min_area_idx = areas_adj.index(pols[max_dist_idx])
#     elif len(areas_adj) == 0:
#         break
#     areas_dict[i + 1] = areas_adj[min_area_idx]
#     visited_list.append(areas_adj[min_area_idx])