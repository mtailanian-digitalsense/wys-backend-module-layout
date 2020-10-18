import random
import time
import math
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
from shapely.geometry import Point
from shapely.geometry import box
from shapely.geometry.polygon import Polygon
from shapely.ops import unary_union, polygonize, linemerge
import matplotlib.pyplot as plt

import viewer
import restrictions

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

        if zone:
            condition1 = zone.contains(b)
        else:
            condition1 = planta.contains(b)

        if (time.time() - make_time) > 0.05 and condition1:
            mod.x, mod.y = p.x, p.y
            curr_bx.append(b)
            # for cb in curr_bx:
            #    x, y = cb.exterior.xy
            #    plt.plot(x, y, color='b')
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
            # for cb in curr_bx:
            #    x, y = cb.exterior.xy
            #    plt.plot(x, y, color='b')
            makeposcnt += 1
            if makeposcnt >= in_cnt:
                makeposcnt = 0
                curr_bx = []
            return mod


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

def make_zones(planta, shafts, core, entrances, cat_area):
    zones = []
    s_zones = []
    e_zones = []
    p_minx, p_miny, p_maxx, p_maxy = planta.bounds
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
                    zone = z[0]
                    if tmp.intersects(zone):
                        tmp = tmp.difference(zone)
                        if tmp.geom_type == 'MultiPolygon':
                            tmp = max(tmp, key=lambda a: a.area)
                zones.append([tmp, "ZONA SERVICIOS"])

    return zones

start_time = time.time()


def Smart_Layout(dictionary, POP_SIZE, GENERATIONS, viz=False, viz_period=10):


    if False:
        list_of_mods = []
        for key in restrictions.module_dictionary.keys():
            list_of_mods.append(key)

        for lm in list_of_mods:
            print(lm)


        fig, ax = plt.subplots()
        im = ax.matshow(restrictions.mod2mod_matrix, cmap = "RdYlGn")
        ax.set_xticks(range(len(list_of_mods)))
        ax.set_yticks(range(len(list_of_mods)))
        # ... and label them with the respective list entries
        ax.set_xticklabels(list_of_mods, fontsize= 5)
        ax.set_yticklabels(list_of_mods, fontsize= 5)
        ax.tick_params(top=True, bottom=False,
                       labeltop=True, labelbottom=False)
        plt.setp(ax.get_xticklabels(), rotation=-90, ha="right",
                 rotation_mode="anchor")

        # Loop over data dimensions and create text annotations.
        for i in range(len(list_of_mods)):
            for j in range(len(list_of_mods)):
                text = ax.text(j, i, restrictions.mod2mod_matrix[i][j],
                               ha="center", va="center", color="black", fontsize = 5)
        #fig.tight_layout()
        plt.show()


    print(round(time.time() - start_time, 2), 'Start!')
    outline, holes, areas, input_list = get_input(dictionary)


    input_list= [   ['WYS_SALAREUNION_RECTA6PERSONAS',              1, 3, 4.05, 1],
                    ['WYS_SALAREUNION_DIRECTORIO10PERSONAS',        1, 4, 6.05, 1],
                    ['WYS_SALAREUNION_DIRECTORIO20PERSONAS',        1, 5.4, 6, 1],
                    ['WYS_PUESTOTRABAJO_CELL3PERSONAS',             15, 3.37, 3.37, 2],
                    #['WYS_PUESTOTRABAJO_RECTO2PERSONAS',            2, 3.82, 1.4],
                    ['WYS_PRIVADO_1PERSONA',                        1, 3.5, 2.8, 3],
                    ['WYS_PRIVADO_1PERSONAESTAR',                   1, 6.4, 2.9, 3],
                    ['WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS',    1, 3.54, 3.02, 4],
                    ['WYS_SOPORTE_BAÑOBATERIAMASCULINO3PERSONAS',   1, 3.54, 3.02, 4],
                    ['WYS_SOPORTE_KITCHENETTE',                     1, 1.6, 2.3, 4],
                    ['WYS_SOPORTE_SERVIDOR1BASTIDOR',               1, 1.5, 2.4, 4],
                    ['WYS_SOPORTE_PRINT1',                          1, 1.5, 1.3, 4],
                    ['WYS_RECEPCION_1PERSONA',                      2, 2.7, 3.25, 5],
                    ['WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS',    1, 2.05, 1.9, 6],
                    ['WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA',    1, 2.05, 2.01, 6],
                    ['WYS_COLABORATIVO_BARRA6PERSONAS',             0, 1.95, 2.4, 6]]
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
    # GA PARAMETERS
    IND_SIZE = N  # should be equal or very close to N

    planta = Polygon(border, voids)

    As = []
    shafts = []
    entrances = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])
        if a[0] == 'WYS_CORE':
            core = As[-1][0]
        if a[0] == 'WYS_SHAFT':
            #s_minx, s_miny, s_maxx, s_maxy = As[-1][0].bounds
            shafts.append(As[-1][0])
            '''if(shaft_minx > s_minx):
                shaft_minx = s_minx
                shaft = As[-1][0]'''
        if a[0] == 'WYS_ENTRANCE':
            entrances.append(As[-1][0])

    zones = make_zones(planta, shafts, core, entrances, cat_area)

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

                    ind[i].fitval1 += round((acond_distance(d[1]) * w)/(ind[i].qty * N), 2)
                    a += (acond_distance(d[1]) * w)/(ind[i].qty * N)

            distances = []
            for j in range(nb):
                if i is not j:
                    distances.append([boxes[j][1], boxes[i][0].distance(boxes[j][0])])

            distances2 = min_dist_to_area(distances)
            for d in distances2:
                w = restrictions.mod2mod(restrictions.module_dictionary, restrictions.mod2mod_matrix,
                                         boxes[i][1], d[0])
                if w != 0:
                    ind[i].fitval2 += round((acond_distance(d[1]) * w)/(ind[i].qty * N), 2)
                    a += (acond_distance(d[1]) * w)/(ind[i].qty * N)
        return a

    def evaluateInd(ind):
        fit_list = []
        fit_list.append(modtoareas(As, ind))
        a = sum(fit_list)
        return a,

    def feasible(ind):  # Need too add if boxes collide
        """Feasibility function for the individual. Returns True if feasible False
        otherwise."""
        boxes = []
        for mod in ind:
            boxes.append(mod.get_box())
        nb = len(boxes)
        for i in range(nb):
            if not planta.contains(boxes[i]):
                return False
            for j in range(i + 1, nb):
                if boxes[i].intersects(boxes[j]):
                    return False
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
        return area

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_pos", makePos, planta, input_list, zones)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     (toolbox.attr_pos), n=IND_SIZE)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutMod, planta=planta, mu=0, sigma=1, indpb=0.2)
    toolbox.register("select_best", tools.selBest)
    toolbox.register("select_roulette", tools.selRoulette)
    toolbox.register("select", tools.selTournament, tournsize=5)
    # toolbox.register("select", tools.selNSGA2)
    toolbox.register("evaluate", evaluateInd)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.decorate("evaluate", tools.DeltaPenalty(feasible, -10.0, feas_distance))

    # Init of the algorithm
    print(round(time.time() - start_time, 1), 'Generate population:')

    pop = toolbox.population(n=POP_SIZE)
    print(round(time.time() - start_time, 1), '...Done')

    CXPB, MUTPB, NGEN = 0.5, 0.2, GENERATIONS

    # Evaluate the entire population
    fitnesses = map(toolbox.evaluate, pop)

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    # print('Sample individual of Generation', 0, ':')
    # for mod in pop[0]:
    #    print('(',mod.x,',',mod.y,')','id:', mod.id)
    # print('Fitness = ', pop[0].fitness)
    if viz:
        rows = 2
        cols = 2
        plt.ion()

        fig, ax = plt.subplots(rows, cols)
        x, y = planta.exterior.xy
        for row in range(rows):
            for col in range(cols):
                ax[row, col].plot(x, y, color='black')
                ax[row, col].axis('equal')
                ax[row, col].grid(True)
                ax[row, col].tick_params(axis="x", labelsize=7)
                ax[row, col].tick_params(axis="y", labelsize=7)

        for pi in planta.interiors:
            x, y = pi.xy
            for row in range(rows):
                for col in range(cols):
                    ax[row, col].plot(x, y, color='black')

        for a in As:
            xa, ya = a[0].exterior.xy
            for row in range(rows):
                for col in range(cols):
                    if a[1] == 'WYS_ENTRANCE':
                        ax[row, col].fill(xa, ya, color='#a8e4a0')
                    if a[1] == 'WYS_FACADE_CRYSTAL':
                        ax[row, col].fill(xa, ya, color='#89cff0')
                    if a[1] == 'WYS_FACADE_OPAQUE':
                        ax[row, col].fill(xa, ya, color='#ffeac4')
                    if a[1] == 'WYS_SHAFT':
                        ax[row, col].fill(xa, ya, color='#779ecb')
                    if a[1] == 'WYS_CORE':
                        ax[row, col].fill(xa, ya, color='#ffb1b1')
        for z in zones:
            xz, yz = z[0].exterior.xy
            for row in range(rows):
                for col in range(cols):
                    if 'ZONA PUESTOS DE TRABAJO' in z[1]:
                        ax[row, col].plot(xz, yz, color='r')
                        ax[row, col].text(xz[1], yz[1], z[1], weight='bold', fontsize=6, ma='center', color='r')
                    elif 'ZONA SERVICIOS' in z[1]:
                        ax[row, col].plot(xz, yz, color='g')
                        ax[row, col].text(xz[1], yz[1], z[1], weight='bold', fontsize=6, ma='center', color='g')
                    elif 'ZONA SOPORTE' in z[1]:
                        ax[row, col].plot(xz, yz, color='y')
                        ax[row, col].text(xz[1], yz[1], z[1], weight='bold', fontsize=6, ma='center', color='y')
                    elif 'ZONA SALAS REUNION' in z[1]:
                        ax[row, col].plot(xz, yz, color='indigo')
                        ax[row, col].text(xz[1], yz[1], z[1], weight='bold', fontsize=6, ma='center', color='indigo')

    print(round(time.time() - start_time, 2), 'Start of genetic evolution:')

    max_count = 0
    max_fit = -9999999
    for g in range(NGEN):

        # viewer.show_floor(planta, As, pop, g)
        if viz and (g + 1 if g > 0 else g) % viz_period == 0:
            fig.suptitle('Generation ' + str(g + 1), fontsize=12)
            boxes = []
            for row in range(rows):
                for col in range(cols):
                    ind = pop[2 * (cols * row + col)]
                    ax[row, col].set_title(
                        'POP:' + str(2 * (cols * row + col)) + ' Fitness:' + str(round(ind.fitness.values[0], 2)),
                        fontsize=9)
                    for mod in ind:
                        b = mod.get_box()
                        x, y = b.exterior.xy
                        b = ax[row, col].plot(x, y, color='b')
                        labels = []

                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.2, mod.name, fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.8, round(mod.fitval1, 2), fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 2.4, round(mod.fitval2, 2), fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 0.6, mod.x, fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 2, y[2] - 0.6, mod.y, fontsize=6, ma='center'))
                        boxes.append([b, labels])

                    '''for b in boxes:
                        x, y = b[0].exterior.xy
                        ax[row, col].set_title('POP:'+str(2*(cols*row+col))+' Fitness:'+ str(round(ind.fitness.values[0],2)), fontsize=9)
                        ax[row, col].plot(x, y, color='b')
                        ax[row, col].text(x[2] + 0.1, y[2] - 1, b[1], fontsize=6)'''
            fig.canvas.draw()
            fig.canvas.flush_events()
            time.sleep(0.0001)

        # Select the next generation individuals
        fitn = [o.fitness.values[0] for o in pop]

        print('Time:', round(time.time() - start_time, 1), ' Generation ', g + 1, 'of', NGEN, 'POP SIZE:', len(pop),
              '  Min:', round(min(fitn), 1), 'Max:', round(max(fitn), 1), 'Avg:', round(sum(fitn) / len(fitn), 1),
              'Local sol. count:', max_count)

        offspring = toolbox.select(pop, len(pop))

        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

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
        fitnesses = map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        #offspring = toolbox.select(offspring + pop, POP_SIZE)

        pop[:] = offspring

        pop.sort(key=lambda x: x.fitness, reverse=True)
        if (viz and g < NGEN - 1 and (g + 1 if g > 0 else g) % viz_period == 0):
            for el in boxes:
                el[0][0].remove()
                el[1][0].remove()
                el[1][1].remove()
                el[1][2].remove()
                el[1][3].remove()
                el[1][4].remove()

    plt.ioff()
    plt.show()
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
