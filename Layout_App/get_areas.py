from rtree import index
from shapely.geometry import Point, MultiLineString
from shapely.geometry.polygon import LineString
from shapely.ops import unary_union, polygonize

def crear_areas(planta, core, num_divisions, proporcional=True):
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    c_minx, c_miny, c_maxx, c_maxy = core.bounds
    core_bbox_points = [Point(c_minx, c_miny), Point(c_maxx, c_maxy)]

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
    return pols

def areas_union(min_area, pols):
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
    return areas_dict

def get_area(planta, core, min_area, divisiones, proporcional):
    pols = crear_areas(planta, core, divisiones, proporcional)
    areas_dict = areas_union(min_area,pols)
    return (areas_dict)