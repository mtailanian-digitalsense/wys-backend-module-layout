import random

from deap import base
from deap import creator
from deap import tools
from shapely.geometry import Point
from shapely.geometry import box
from shapely.geometry.polygon import Polygon

#import viewer


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
    def __init__(self, x, y, rotation, name, identificator, width_value, length_value):
        self.x = x
        self.y = y
        self.rot = rotation
        self.name = name
        self.id = identificator
        self.width = width_value
        self.length = length_value

    def show(self):
        print(self.name, self.x, self.y, self.rot, self.id, self.width, self.length)


def set_mod2area_matrix_value(mod_dic, area_dic, matrix, module_name, area_name, value):
    row, col = mod_dic.get(module_name), area_dic.get(area_name)
    if row is None or col is None:
        pass
    else:
        matrix[row][col] = value


def mod2area(mod_dic, area_dic, matrix, area_name, module_name):
    row, col = mod_dic[module_name], area_dic[area_name]
    return matrix[row][col]


def makePos(planta, minx, miny, maxx, maxy):
    while True:
        p = Point(random.uniform(minx, maxx), random.uniform(miny, maxy))

        if planta.contains(p):
            mod = Module(p.x, p.y, 0, 0, 0, 0, 0)
            return mod


def Smart_Layout(dictionary, POP_SIZE=20, GENERATIONS=50):
    outline, holes, areas, input_list = get_input(dictionary)

    voids = []

    border = outline[0][1]
    for h in holes:
        voids.append(h[1])

    # INPUT PARAMETERS
    N = 0  # number of modules to be placed in total
    for i in input_list:
        N += i[1]
    print('Number of modules: ', N)
    # GA PARAMETERS
    IND_SIZE = N  # should be equal or very close to N

    planta = Polygon(border, voids)
    As = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])

    X_MIN, Y_MIN, X_MAX, Y_MAX = planta.bounds

    module_dictionary = {
    }
    cnt = 0
    for i in range(100):
        module_dictionary[i] = cnt
        cnt += 1

    area_dictionary = {
        'WYS_ENTRANCE': 0,
        'WYS_FACADE_CRYSTAL': 1,
        'WYS_FACADE_OPAQUE': 2,
        'WYS_SHAFT': 3,
        'WYS_CORE': 4,
    }

    # create weight matrix
    mod2area_matrix = []

    for m in range(len(module_dictionary)):
        mod2area_matrix.append([0] * len(area_dictionary))

    # Add some prefered areas for some modules:
    for i in range(0, 30):  # All the workbenchs
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_ENTRANCE', -1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_CRYSTAL', 1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_OPAQUE', -1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_SHAFT', -1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_CORE', -1)
    for i in range(31, 70):  # All the workbenchs
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_ENTRANCE', -1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_CRYSTAL', -1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_FACADE_OPAQUE', 1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_SHAFT', -1)
        set_mod2area_matrix_value(module_dictionary, area_dictionary, mod2area_matrix, i, 'WYS_CORE', -1)

    def applysizeandid(pop, in_list):
        for ind in pop:
            cnt = 0
            for j in range(len(in_list)):
                for n in range(in_list[j][1]):
                    ind[cnt].length = in_list[j][2]
                    ind[cnt].width = in_list[j][3]
                    ind[cnt].name = in_list[j][0]
                    cnt += 1

    def mutMod(individual, mu, sigma, indpb):
        for i in individual:
            if random.random() < indpb:
                i.x += random.gauss(mu, sigma)
            if random.random() < indpb:
                i.y += random.gauss(mu, sigma)
            if random.random() < indpb:
                i.length, i.width = i.width, i.length
                i.rot += 90
                if i.rot >= 360:
                    i.rot = 0

    def distancebtwmods(ind):
        a = 99
        boxes = []
        for mod in ind:
            boxes.append(
                [box(mod.x - mod.width / 2, mod.y - mod.length / 2, mod.x + mod.width / 2, mod.y + mod.length / 2),
                 mod.name])
        nb = len(boxes)
        for i in range(nb):
            for j in range(i + 1, nb):
                d = boxes[i][0].distance(boxes[j][0])
                if d < a:
                    a = d
        return a

    def modinarea(As, ind):
        a = 0
        # print('Where is every module:')
        boxes = []
        for mod in ind:
            boxes.append(
                [box(mod.x - mod.width / 2, mod.y - mod.length / 2, mod.x + mod.width / 2, mod.y + mod.length / 2),
                 mod.name])
        for bx in boxes:
            for A in As:
                if (A[0].contains(bx[0])):
                    # print('module of id', bx[1], 'is in', A[1], 'it have a weight of:', mod2area(A[1], bx[1]))
                    a += mod2area(A[1], bx[1])
        return a

    def evaluateInd(ind):
        fit = []
        fit.append(modinarea(As, ind))
        fit.append(distancebtwmods(ind))
        a = sum(fit)
        return a,

    def feasible(ind):  # Need too add if boxes collide
        """Feasibility function for the individual. Returns True if feasible False
        otherwise."""
        boxes = []
        for mod in ind:
            boxes.append(
                box(mod.x - mod.width / 2, mod.y - mod.length / 2, mod.x + mod.width / 2, mod.y + mod.length / 2))
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
                [box(mod.x - mod.width / 2, mod.y - mod.length / 2, mod.x + mod.width / 2, mod.y + mod.length / 2),
                 mod.name])
        nb = len(boxes)
        for i in range(nb):
            for j in range(i + 1, nb):
                area += (boxes[i][0].intersection(boxes[j][0])).area
                # print('mod', i, 'intersects with mod', j,'in',area)

        # check for bounds collisions:

        # get the area of the module and substract the intersection with the building
        for i in range(nb):
            # print('area of',i,'module is', boxes[i][0].area)
            area += (boxes[i][0].area - (boxes[i][0].intersection(planta)).area)
        # print (area)
        return area

    creator.create("FitnessMax", base.Fitness, weights=(1.0,))
    creator.create("Individual", list, fitness=creator.FitnessMax)

    toolbox = base.Toolbox()
    toolbox.register("attr_pos", makePos, planta, X_MIN, Y_MIN, X_MAX, Y_MAX)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     (toolbox.attr_pos), n=IND_SIZE)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutMod, mu=0, sigma=0.5, indpb=0.2)
    toolbox.register("select", tools.selBest)
    toolbox.register("evaluate", evaluateInd)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)

    # implementar distancia para graduar la infactibilidad
    # delta -20 parametrizable, gama = factor para multiplicar por area de modulos superpuestos.
    toolbox.decorate("evaluate", tools.DeltaPenalty(feasible, 0.0, feas_distance))

    # Init of the algorithm

    pop = toolbox.population(n=POP_SIZE)

    applysizeandid(pop, input_list)
    CXPB, MUTPB, NGEN = 0.5, 0.2, GENERATIONS

    # Evaluate the entire population
    fitnesses = map(toolbox.evaluate, pop)

    for ind, fit in zip(pop, fitnesses):
        ind.fitness.values = fit

    print('Sample individual of Generation', 0, ':')
    # for mod in pop[0]:
    #    print('(',mod.x,',',mod.y,')','id:', mod.id)
    print('Fitness = ', pop[0].fitness)

    for g in range(NGEN):
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
    print('Best individual of Generation', g, ':')
    out = []
    for mod in pop[0]:
        out.append([mod.name, mod.id, mod.x, mod.y, mod.rot])
        print(mod.name, '(', mod.x, ',', mod.y, ')', 'id:', mod.id, 'rot:', mod.rot)
    print('Fitness = ', pop[0].fitness)
    #viewer.show_floor(planta, As, pop[0])
    return out
