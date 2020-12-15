
from shapely.geometry import box
from shapely.geometry.polygon import Polygon, LineString
from shapely.ops import unary_union, polygonize, linemerge
import matplotlib.pyplot as plt
def get_lines(planta, holes, boundbox_on_outline = True, boundbox_on_holes = True):
    in_outline = planta[0][1]
    print(in_outline)
    outline = []
    in_voids = []
    voids = []
    for h in holes:
        in_voids.append(h)
    if boundbox_on_holes:
        for v in in_voids:
            xmin, ymin, xmax, ymax = Polygon(v).bounds
            voids.append(list(box(xmin, ymin, xmax, ymax).exterior.coords))
    else:
        voids = in_voids
    if boundbox_on_outline:
        xmin, ymin, xmax, ymax = Polygon(in_outline).bounds
        outline = list(box(xmin, ymin, xmax, ymax).exterior.coords)
    else:
        outline = in_outline
    lines = []
    for i in range(len(outline) - 1):
        lines.append([[outline[i][0], outline[i][1]], [outline[i + 1][0], outline[i + 1][1]]])
    for void in voids:
        for i in range(len(void) - 1):
            lines.append([[void[i][0], void[i][1]], [void[i + 1][0], void[i + 1][1]]])
    planta_pol = Polygon(outline)
    minx, miny, maxx, maxy = planta_pol.bounds
    for pair in lines:
        x1 = pair[0][0]
        x2 = pair[1][0]
        y1 = pair[0][1]
        y2 = pair[1][1]
        if x1 == x2:
            if y1 < y2:
                pair[0][1] = miny
                pair[1][1] = maxy
            else:
                pair[0][1] = maxy
                pair[1][1] = miny
        if y1 == y2:
            if x1 < x2:
                pair[0][0] = maxx
                pair[1][0] = minx
            else:
                pair[0][0] = maxx
                pair[1][0] = minx
    # eliminar las lineas repetidas
    res = []
    for i in lines:
        if i not in res:
            res.append(i)
    return res
def xyxy2xxyy(pair):
    x1 = pair[0][0]
    x2 = pair[1][0]
    y1 = pair[0][1]
    y2 = pair[1][1]
    new_pair = [[x1, x2], [y1, y2]]
    return new_pair
def get_points(lines):
    points = []
    for i in range(len(lines)):
        for j in range(i+1, len(lines)):
            a = LineString(lines[i])
            b = LineString(lines[j])
            if a.intersects(b):
                p = a.intersection(b)
                points.append([p.x, p.y])
    s_points = sorted(points, key=lambda k: [k[1], k[0]])
    return s_points
def get_p_right_up(in_index, points):
    if in_index == len(points)-1:
        out_index_right = None
        out_index_up = None
    else:
        p1 = points[in_index]
        p2 = points[in_index + 1]
        for j in range(in_index+1, len(points)):
            if points[j][0] == p1[0]:
                out_index_up = j
                break
            else:
                out_index_up = None
        if p2[1] == p1[1]:
            out_index_right = in_index + 1
        else:
            out_index_right = None
    return [in_index, out_index_right, out_index_up]
def get_pols(points):
    polygons = []
    for i in range(len(points)):
        tmp = get_p_right_up(i, points)
        if None not in tmp:
            polygons.append(Polygon([points[tmp[2]+1], points[tmp[1]], points[tmp[0]], points[tmp[2]]]))
    return polygons
def polygon_merge(polygons, i , j):
    A = polygons[i]
    B = polygons[j]
    polygons[i] = unary_union([A, B])
    polygons.pop(j)
    return polygons
def process(polygons, min_area, min_dim):
    job_ok = False
    while not job_ok:
        for i in range(len(polygons)):
            if i == len(polygons) - 1:
                job_ok = True
            minx, miny, maxx, maxy = polygons[i].bounds
            dx = maxx - minx
            dy = maxy - miny
            min_dim_in_pol = min(dx, dy)
            if polygons[i].area <= min_area or min_dim_in_pol <= min_dim:
                options = get_overlap_pols(polygons, i)
                if options:
                    j = options[0][0]
                    polygon_merge(polygons, i, j)
                    break
    return polygons
def get_overlap_pols(polygons, index):
    A = polygons[index]
    out=[]
    tmp = 0.001
    for i in range(len(polygons)-1):
        if (index != i) and A.touches(polygons[i]):
            inter = A.intersection(polygons[i])
            if inter.length > tmp:
                out.append([i, inter.length, polygons[i].area])
    out.sort(key = lambda x: (-x[1], x[2]))
    return out
def get_pol_zones(outline, holes, min_area, min_dim, boundbox_on_outline, boundbox_on_holes):
    res = get_lines(outline, holes, boundbox_on_outline, boundbox_on_holes)
    points = get_points(res)
    polygons = get_pols(points)
    pol_holes= []
    for h in holes:
        pol_holes.append(Polygon(h))
    rmv_list = []
    for i in range(len(polygons)):
        tmp = polygons[i]
        planta = Polygon(outline[0][1])
        if planta.contains(tmp):
            pass
        else:
            rmv_list.append(i)
        for h in range(len(pol_holes)):
            if tmp.intersects(pol_holes[h]):
                tmp = tmp - pol_holes[h]
        if tmp.type == 'Polygon' and tmp.area > 0:
            polygons[i] = tmp
        else:
            rmv_list.append(i)
    rmv_list.reverse()
    for rl in rmv_list:
        polygons.pop(rl)
    polygons = process(polygons, min_area, min_dim) #post process
    print(len(polygons), "polygons created...")
    out = {i: polygons[i] for i in range(0, len(polygons))}
    return out
'''def main():
    outline, holes, areas, input_list = SmartLayout.get_input(example_data_v3.dict_ex)
    voids = []
    As = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])
    for h in holes:
        voids.append(h)
    pol_dict = get_pol_zones(outline, holes, min_area=2, min_dim=2, boundbox_on_outline=False, boundbox_on_holes=False)
    viewer.simple_show(outline, holes, areas, [pol_dict[i] for i in range(len(pol_dict))])
main()'''