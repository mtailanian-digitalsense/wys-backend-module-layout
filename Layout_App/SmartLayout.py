import random
import time
import math
from shapely.geometry import Point
from shapely.geometry import box
from shapely.geometry.polygon import Polygon
from shapely.ops import unary_union

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

    if mod_cat == 1:
        z = [z[0] for z in zones if z[1] == 'ZONA SALAS REUNION']
    elif mod_cat == 2:
        z = [z[0] for z in zones if 'ZONA PUESTOS DE TRABAJO' in z[1]]
    elif mod_cat == 4:
        z = [z[0] for z in zones if 'ZONA SERVICIOS' in z[1]]
    elif mod_cat == 5:
        z = [z[0] for z in zones if 'ZONA SOPORTE' in z[1]]

    if len(z) > 1 and (makeposcnt % 2) == 0:
        zone = z[1]
        minx, miny, maxx, maxy = zone.bounds
    elif z:
        zone = z[0]
        minx, miny, maxx, maxy = zone.bounds
    else:
        zone = []
        minx, miny, maxx, maxy = planta.bounds

    #print(round(time.time() - start_time, 2), len(curr_bx), mod.name)
    while True:
        p = Point(round(random.uniform(minx, maxx), 1), round(random.uniform(miny, maxy), 1))
        b = box(p.x - mod.width / 2, p.y - mod.height / 2, p.x + mod.width / 2, p.y + mod.height / 2)

        if zone and (time.time() - make_time) > 0.5:
            condition1 = zone.intersects(b) and planta.contains(b)
        elif zone:
            condition1 = zone.contains(b)
        else:
            condition1 = planta.contains(b)

        if (time.time() - make_time) > 0.1 and condition1:
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

def make_zones(planta, shafts, core, entrances, cat_area):
    zones = []
    s_zones = []
    e_zones = []
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
    print(core)
    c_minx, c_miny, c_maxx, c_maxy = core.bounds
    print(core.bounds)

    # Zona salas de reuniones
    if 1 in cat_area:
        dist_x = abs(p_maxx - p_minx)
        dist_y = abs(p_maxy - p_miny)
        size_offset = math.sqrt(cat_area[1])
        factor = 1.2
        if(dist_x >= dist_y):
            px_med = (p_maxx + p_minx)/2
            zsr = box(px_med - factor*size_offset, p_maxy - factor*size_offset, px_med + factor*size_offset, p_maxy + factor*size_offset).intersection(planta)
        elif(dist_x < dist_y):
            py_med = (p_maxy + p_miny)/2
            zsr = box(p_maxx - size_offset, py_med - size_offset, p_maxx + size_offset, py_med + size_offset).intersection(planta)
        zones.append([zsr, "ZONA SALAS REUNION"])

    # Zonas puestos de trabajo
    if 2 in cat_area:
        dist_x = abs(p_maxx - p_minx)
        dist_y = abs(p_maxy - p_miny)
        if(dist_x >= dist_y):
            zpt = box(p_minx, p_miny, p_minx + dist_x*0.3, p_miny + dist_y*0.8).intersection(planta)
            zpt2 = box(p_maxx - dist_x*0.3, p_miny, p_maxx, p_miny + dist_y*0.8).intersection(planta)
        elif(dist_x < dist_y):
            zpt = box(p_minx, p_miny, p_minx + dist_x*0.7, p_miny + dist_y*0.3).intersection(planta)
            #zpt2 = box(p_minx, p_miny, p_minx + dist_x*0.3, p_miny + dist_y*0.7).intersection(planta)

        zones.append([zpt, "ZONA PUESTOS DE TRABAJO 1"])
        zones.append([zpt2, "ZONA PUESTOS DE TRABAJO 2"])

    # Zonas soporte
    if 5 in cat_area:
        for en in entrances:
            size_offset = math.sqrt(cat_area[5])
            print('e_off:', size_offset)
            e_minx, e_miny, e_maxx, e_maxy = en.bounds
            dist_x = abs(e_maxx - e_minx)
            dist_y = abs(e_maxy - e_miny)
            px_med = (e_maxx + e_minx)/2
            py_med = (e_maxy + e_miny)/2
            e_zone = box(px_med - size_offset, py_med - size_offset, px_med + size_offset, py_med + size_offset)
            e_zones.append(e_zone.intersection(planta))

        if len(e_zones) > 1:
            tmp = unary_union(e_zones)
            if tmp.geom_type == 'MultiPolygon':
                for i in range(len(tmp)):
                    zones.append([unary_union(tmp[i]), "ZONA SOPORTE " + str(i)])
            else:
                zones.append([tmp, "ZONA SOPORTE"])

    # Zonas servicios
    if 4 in cat_area:
        for sh in shafts:
            size_offset = math.sqrt(cat_area[4])
            s_minx, s_miny, s_maxx, s_maxy = sh.bounds
            px_med = (s_maxx + s_minx)/2
            py_med = (s_maxy + s_miny)/2
            factor = 1.1
            s_zone = box(px_med - factor*size_offset, py_med - factor*size_offset, px_med + factor*size_offset, py_med + factor*size_offset)
            s_zones.append(s_zone.intersection(planta))
        # Posibles uniones entre otras areas de servicio y filtro de area en interseccion con otras mas importantes
        if len(s_zones) > 1:
            tmp = unary_union(s_zones)
            if tmp.geom_type == 'MultiPolygon':
                for i in range(len(tmp)):
                    pol = tmp[i]
                    for z in zones:
                        if 'ZONA SOPORTE' in z[1]:
                            continue
                        zone = z[0]
                        if pol.intersects(zone):
                            if pol.geom_type == 'MultiPolygon':
                                pol = max(pol, key=lambda a: a.area)
                            pol = pol.difference(zone)
                        if pol.geom_type == 'MultiPolygon':
                                pol = max(pol, key=lambda a: a.area)
                    zones.append([pol, "ZONA SERVICIOS " + str(i)])
            else:
                for z in zones:
                    if 'ZONA SOPORTE' in z[1]:
                        continue
                    zone = z[0]
                    if tmp.intersects(zone):
                        tmp = tmp.difference(zone)
                        if tmp.geom_type == 'MultiPolygon':
                            tmp = max(tmp, key=lambda a: a.area)
                zones.append([tmp, "ZONA SERVICIOS"])

    return zones


def smart_layout_async(dictionary, POP_SIZE=50, GENERATIONS=50):
    result = Smart_Layout(dictionary, POP_SIZE, GENERATIONS)
    return result, dictionary


start_time = time.time()


def Smart_Layout(dictionary, POP_SIZE, GENERATIONS, viz=False, viz_period=10):

    print(round(time.time() - start_time, 2), 'Start!')
    outline, holes, areas, input_list = get_input(dictionary)

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

    print(round(time.time() - start_time, 2), 'Load and compute all the inputs')
    print('Number of modules: ', N)

    planta = Polygon(border, voids)
    As = []
    shafts = []
    entrances = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])
        if a[0] == 'WYS_CORE':
            core = As[-1][0]
        if a[0] == 'WYS_SHAFT':
            shafts.append(As[-1][0])
            '''if(shaft_minx > s_minx):
                shaft_minx = s_minx
                shaft = As[-1][0]'''
        if a[0] == 'WYS_ENTRANCE':
            entrances.append(As[-1][0])

    zones = make_zones(planta, shafts, core, entrances, cat_area)

    pop_1 = []
    for k in range(N):
        pop_mod = makePos(planta, input_list, zones)
        pop_1.append(pop_mod)


    out = []
    for mod in pop_1:
        out.append([mod.name, mod.id, mod.x, mod.y, mod.rot])
    return out
