from rtree import index
import matplotlib.pyplot as plt
from shapely.geometry import Point, MultiLineString
from shapely.geometry.polygon import Polygon, LineString
from shapely.ops import unary_union, polygonize, linemerge
from Layout_App import example_data_v3, example_data_v4
from Layout_App.SmartLayout import make_circ_ring

#%%
# Ingreso de parámetros
num_divisions = 15
min_area = 2
proporcional = True

#%%
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
# Obtener la Planta
outline, holes, areas = get_input(example_data_v3.dict_ex)
voids = []
border = outline[0][1]
pilares = [] #### para graficar
for h in holes:
    voids.append(h[1])
    pilares.append(Polygon(h[1]))
planta = Polygon(border, voids)
# # Extracción de la planta y el core
As = []
shafts = []
entrances = []
for a in areas:
    As.append([Polygon(a[1]), a[0]])
    if a[0] == 'WYS_CORE':
        core = As[-1][0]
    if a[0] == 'WYS_SHAFT':
        shafts.append(As[-1][0])
    if a[0] == 'WYS_ENTRANCE':
        entrances.append(As[-1][0])
p_minx, p_miny, p_maxx, p_maxy = planta.bounds
c_minx, c_miny, c_maxx, c_maxy = core.bounds
core_bbox_points = [Point(c_minx, c_miny), Point(c_maxx, c_maxy)]

circ_width = 1.2
circ_pols = make_circ_ring(planta, core, shafts, entrances, voids, circ_width)
circulacion = unary_union(circ_pols)
pols_planta = list(polygonize(MultiLineString(planta.boundary)))
pols_circ = list(polygonize(MultiLineString(circulacion.boundary)))
for e in pols_circ:
    pols_planta.append(e)
pols_planta_p = unary_union(pols_planta)

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
inter = unary_union([planta.intersection(lu), circulacion.intersection(lu), planta.boundary, circulacion.boundary])
# Poligoniza las áreas
pols = list(polygonize(MultiLineString(inter)))

#%%
# Se eliminan las áreas que corresponden a los pilares y al core
for i, p in enumerate(pols_planta):
    if p.area < 2:
        for e, po in enumerate(pols):
            if p.bounds == po.bounds:
                del pols[e]
                break
# Busca el centroide del core para eliminar esa área
centroids_dist = [p.centroid.distance(core.centroid) for p in pols]
min_centroid_value, min_centroid_idx = min((val, idx) for (idx, val) in enumerate(centroids_dist))
del pols[min_centroid_idx]

#%%
# Se eliminan las áreas dentro de la circulación
areas_del = []
for idx, a in enumerate(pols):
    if circulacion.contains(pols[idx]):
        areas_del.append(idx)
areas_del.sort(reverse=True)
for e in areas_del:
    del pols[e]
areas_del = []
areas_dict = {k:v for k, v in enumerate(pols)}

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
print(planta.is_valid)

#%%
# Plot de la figura
for e,f in areas_dict.items():   # Areas en Diccionario
#for e, f in enumerate(pols):    # Areas en polígonos
    x, y = f.exterior.xy
    plt.plot(x, y, color='#a8e4a0')
    plt.text(f.centroid.x, f.centroid.y, 'A: '+ str(e), weight='bold', fontsize=6, ma='center', color='g')

# # Pilares y Core
# for f in pols_planta:
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='black')
# # Planta Exterior
# x, y = planta.exterior.xy
# plt.plot(x, y, color='black')
# # Shafts
# for f in shafts:
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='black')
# # Pilares y Core
# for f in pilares:
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='black')
# Circulación
# plantaxy = list(polygonize(MultiLineString(circulacion.boundary)))
# for f in plantaxy:
#     x, y = f.exterior.xy
#     plt.plot(x, y, color='black')

plt.show()
