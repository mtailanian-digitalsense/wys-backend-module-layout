import random
import time
from deap import base
from deap import creator
from deap import tools
from shapely.geometry import Point
from shapely.geometry import box
from shapely.geometry.polygon import Polygon
import matplotlib.pyplot as plt

import viewer
import restrictions


def get_input(dictionary):
    Planta = dictionary.get('selected_floor').get('polygons')
    Workspaces = dictionary.get('workspaces')
    plant = []

    outline = []
    holes = []
    areas = []

    for Area in Planta:
        plant.append(
            [Area.get('name'), [(round(a.get('x') / 100, 2), round(a.get('y') / 100, 2)) for a in Area.get('points')]])

    for p in plant:
        if p[0] == 'WYS_AREA_UTIL':
            outline.append(p)
        elif p[0] == 'WYS_HOLE':
            holes.append(p)
        else:
            areas.append(p)

    input_list = []

    for ws in Workspaces:
        input_list.append([ws.get('name'), ws.get('quantity'), ws.get('width'), ws.get('height')])

    # print('Outline:')
    # for o in outline:
    #     print(o)
    # print('Holes:')
    # for h in holes:
    #     print(h)
    # print('Areas:')
    # for a in areas:
    #     print(a)
    # print('InputList:')
    # for i in input_list:
    #     print(i)

    return outline, holes, areas, input_list


class Floor:
    def __init__(self, outline_points, holes_list):
        self.outline = outline_points
        self.holes = holes_list


class Module:
    def __init__(self, x, y, rotation, name, identificator, width_value, height_value):
        self.x = x
        self.y = y
        self.rot = rotation
        self.name = name
        self.id = identificator
        self.width = width_value
        self.height = height_value

    def show(self):
        print(self.name, self.x, self.y, self.rot, self.id, self.width, self.height)




makeposcnt = 0
curr_bx = []


def makePos(planta, in_list):

    make_time = time.time()
    global makeposcnt
    global curr_bx
    in_cnt = 0
    minx, miny, maxx, maxy = planta.bounds

    mod = Module(0, 0, 0, 0, 0, 0, 0)

    for j in range(len(in_list)):
        for n in range(in_list[j][1]):
            if in_cnt == makeposcnt:
                mod.width = in_list[j][2]
                mod.height = in_list[j][3]
                mod.name = in_list[j][0]

            in_cnt+=1
    print(round(time.time() - start_time, 2), len(curr_bx), mod.name)
    while True:

        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))
        b = box(p.x - mod.width / 2, p.y - mod.height / 2, p.x + mod.width / 2, p.y + mod.height / 2)
        condition1 = planta.contains(b)
        if (time.time() - make_time) > 0.5 and condition1:
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
            #for cb in curr_bx:
            #    x, y = cb.exterior.xy
            #    plt.plot(x, y, color='b')
            makeposcnt+=1
            if makeposcnt>=in_cnt:
                makeposcnt = 0
                curr_bx = []
            return mod


def min_dist_to_area(lista):
    my_output = []
    i = 0
    curr_min = lista[0]

    for j in range(i+1, len(lista)):
        B = lista[j]
        #print(i, j, curr_min, B)
        if curr_min[0] == B[0]:
            if B[1] <= curr_min[1]:
                curr_min = B
            if j+1 == len(lista):
                my_output.append(curr_min)
                #print('append', curr_min)


        else:
            my_output.append(curr_min)
            #print('append', curr_min)
            curr_min = B
            if j+1 == len(lista):
                my_output.append(curr_min)

        i = j
    return my_output

start_time = time.time()

def Smart_Layout(dictionary, POP_SIZE, GENERATIONS):


    print(round(time.time() - start_time, 2), 'Start!')
    outline, holes, areas, input_list = get_input(dictionary)


    input_list= [   ['WYS_SALAREUNION_RECTA6PERSONAS',              0, 3, 4.05],
                    ['WYS_SALAREUNION_DIRECTORIO10PERSONAS',        0, 4, 6.05],
                    ['WYS_PUESTOTRABAJO_CELL3PERSONAS',            0, 3.37, 3.37],
                    ['WYS_PRIVADO_1PERSONA',                        0, 3.5, 2.8],
                    ['WYS_PRIVADO_1PERSONAESTAR',                   0, 6.4, 2.9],
                    ['WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS',    0, 3.54, 3.02],
                    ['WYS_SOPORTE_KITCHENETTE',                     0, 1.6, 2.3],
                    ['WYS_SOPORTE_SERVIDOR1BASTIDOR',               0, 1.5, 2.4],
                    ['WYS_SOPORTE_PRINT1',                          0, 1.5, 1.3],
                    ['WYS_RECEPCION_1PERSONA',                      2, 2.7, 3.25],
                    ['WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS',    0, 2.05, 1.9],
                    ['WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA',    0, 2.05, 2.01],
                    ['WYS_COLABORATIVO_BARRA6PERSONAS',             0, 1.95, 2.4]]
    voids = []

    border = outline[0][1]
    for h in holes:
        voids.append(h[1])

    # INPUT PARAMETERS
    N = 0  # number of modules to be placed in total
    for i in input_list:
        N += i[1]
    print(round(time.time() - start_time, 2), 'Load and compute all the inputs')
    print('Number of modules: ', N)
    # GA PARAMETERS
    IND_SIZE = N  # should be equal or very close to N

    planta = Polygon(border, voids)

    As = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])


    def mutMod(individual, mu, sigma, indpb):
        for i in individual:
            if random.random() < indpb:
                i.x += random.gauss(mu, sigma)
            if random.random() < indpb:
                i.y += random.gauss(mu, sigma)
            if random.random() < indpb:
                i.height, i.width = i.width, i.height
                i.rot += 90
                if i.rot >= 360:
                    i.rot = 0

    def distancebtwmods(ind):
        a = 0
        boxes = []
        for mod in ind:
            boxes.append(
                [box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2),
                 mod.name])
        nb = len(boxes)
        for i in range(nb):
            for j in range(i + 1, nb):
                curr_first_mod_name = boxes[i][1]
                curr_sec_mod_name = boxes[j][1]
                d = boxes[i][0].distance(boxes[j][0])
                w = restrictions.mod2mod(restrictions.module_dictionary, restrictions.mod2mod_matrix,
                                         boxes[i][1], boxes[j][1])
                a+=w*(100-d)
        return a

    def modtoareas(As, ind):
        a = 0
        boxes = []
        for mod in ind:
            boxes.append(
                [box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2),
                 mod.name])

        for bx in boxes:
            bx_dist = []
            for A in As:
                bx_dist.append([A[1], bx[0].distance(A[0])])

            min_list = min_dist_to_area(bx_dist)
            for ml in min_list:
                w = restrictions.mod2area(restrictions.module_dictionary, restrictions.area_dictionary,
                                        restrictions.mod2area_matrix, bx[1], ml[0])
                a += w*(100-ml[1])
        return a

    def evaluateInd(ind):
        fit_list = []
        fit_list.append(modtoareas(As, ind))
        fit_list.append(distancebtwmods(ind))
        a = sum(fit_list)
        return a,

    def feasible(ind):  # Need too add if boxes collide
        """Feasibility function for the individual. Returns True if feasible False
        otherwise."""
        boxes = []
        for mod in ind:
            boxes.append(
                box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2))
        for bx1 in boxes:
            if planta.contains(bx1) is False:
                return False
            for bx2 in boxes:
                if bx1 != bx2:
                    if bx1.intersects(bx2):
                        return False
        return True

    def feas_distance(ind):
        # check for intermods collisions:
        area = 0
        boxes = []
        for mod in ind:
            boxes.append(
                [box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2),
                 mod.name])
        nb = len(boxes)
        for i in range(nb):
            for j in range(i + 1, nb):
                area += (boxes[i][0].intersection(boxes[j][0])).area
                # print('mod', i, 'intersects with mod', j,'in',area)

        # get the area of the module and substract the intersection with the building
        for i in range(nb):
            #print('area of',i,'module is', boxes[i][0].area)
            area += (boxes[i][0].area - (boxes[i][0].intersection(planta)).area)
        # print (area)
        return area

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_pos", makePos, planta, input_list)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     (toolbox.attr_pos), n=IND_SIZE)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutMod, mu=0, sigma=0.2, indpb=0.2)
    toolbox.register("select", tools.selBest)
    toolbox.register("evaluate", evaluateInd)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # implementar distancia para graduar la infactibilidad
    # delta -20 parametrizable, gama = factor para multiplicar por area de modulos superpuestos.
    toolbox.decorate("evaluate", tools.DeltaPenalty(feasible, -200.0, feas_distance))

    # Init of the algorithm
    print(round(time.time() - start_time, 2), 'Generate population:')

    for i in input_list:
        print(i)
    pop = toolbox.population(n=POP_SIZE)

    CXPB, MUTPB, NGEN = 0.5, 0.2, GENERATIONS

    # Evaluate the entire population
    fitnesses = map(toolbox.evaluate, pop)

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit


    #print('Sample individual of Generation', 0, ':')
    # for mod in pop[0]:
    #    print('(',mod.x,',',mod.y,')','id:', mod.id)
    #print('Fitness = ', pop[0].fitness)
    print(round(time.time() - start_time, 2),'Start of genetic evolution:')
    for g in range(NGEN):
        if g%25 == 0:
            print(round(time.time() - start_time, 2),': Generation ', g, 'of ', NGEN)
        # Select the next generation individuals
        offspring = toolbox.select(pop, len(pop))

        # Clone the selected individuals
        offspring = list(map(toolbox.clone, offspring))

        # Apply crossover and mutation on the offspring
        for child1, child2 in zip(offspring[::2], offspring[1::2]):
            if random.random() < CXPB:
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

        offspring = toolbox.select(offspring + pop, len(pop))
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # print('iteration number:',g)
        # for i in pop:
        #    print('individual:')
        #    for mod in i:
        #        print('X = ',mod.x)
        #        print('Y = ',mod.y)
        #    print('Fitness = ',i.fitness)
    print(round(time.time() - start_time, 2),'Finish')
    print('Best individual of Generation', g, ':')
    out = []
    for mod in pop[0]:
        out.append([mod.name, mod.id, mod.x, mod.y, mod.rot])
        #print(mod.name, '(', mod.x, ',', mod.y, ')', 'id:', mod.id, 'rot:', mod.rot)
    print('Fitness = ', pop[0].fitness)
    #for o in out:
    #    print(o)
    viewer.show_floor(planta, As, pop[0])
    return out
