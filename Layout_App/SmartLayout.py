import random
import time
from deap import base
from deap import creator
from deap import tools
from deap import algorithms
from shapely.geometry import Point
from shapely.geometry import box
from shapely.geometry.polygon import Polygon
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
        input_list.append([ws.get('name'), ws.get('quantity'), ws.get('width'), ws.get('height')])

    return outline, holes, areas, input_list


class Floor:
    def __init__(self, outline_points, holes_list):
        self.outline = outline_points
        self.holes = holes_list


class Module:
    def __init__(self, x, y, rotation, name, identificator, width_value, height_value, fitval1, fitval2):
        self.x = x
        self.y = y
        self.rot = rotation
        self.name = name
        self.id = identificator
        self.width = width_value
        self.height = height_value
        self.fitval1 = fitval1
        self.fitval2 = fitval2

    def show(self):
        print(self.name, self.x, self.y, self.rot, self.id, self.width, self.height)

    def get_box(self):
        return box(self.x - self.width / 2, self.y - self.height / 2, self.x + self.width / 2, self.y + self.height / 2)


makeposcnt = 0
curr_bx = []


def makePos(planta, in_list):
    make_time = time.time()
    global makeposcnt
    global curr_bx
    in_cnt = 0
    minx, miny, maxx, maxy = planta.bounds

    mod = Module(0, 0, 0, 0, 0, 0, 0, 0, 0)

    for j in range(len(in_list)):
        for n in range(in_list[j][1]):
            if in_cnt == makeposcnt:
                mod.width = round(in_list[j][2], 1)
                mod.height = round(in_list[j][3], 1)
                mod.name = in_list[j][0]

            in_cnt += 1
    # print(round(time.time() - start_time, 2), len(curr_bx), mod.name)
    while True:

        p = Point(round(random.uniform(minx, maxx), 1), round(random.uniform(miny, maxy), 1))
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


start_time = time.time()


def Smart_Layout(dictionary, POP_SIZE, GENERATIONS, viz=False, viz_period=10):
    print(round(time.time() - start_time, 2), 'Start!')
    outline, holes, areas, input_list = get_input(dictionary)

    input_list = [['WYS_SALAREUNION_RECTA6PERSONAS', 1, 3, 4.05],
                  ['WYS_SALAREUNION_DIRECTORIO10PERSONAS', 1, 4, 6.05],
                  ['WYS_SALAREUNION_DIRECTORIO20PERSONAS', 0, 5.4, 6],
                  ['WYS_PUESTOTRABAJO_CELL3PERSONAS', 10, 3.37, 3.37],
                  ['WYS_PUESTOTRABAJO_RECTO2PERSONAS', 5, 3.82, 1.4],
                  ['WYS_PRIVADO_1PERSONA', 0, 3.5, 2.8],
                  ['WYS_PRIVADO_1PERSONAESTAR', 0, 6.4, 2.9],
                  ['WYS_SOPORTE_BAÑOBATERIAFEMENINO3PERSONAS', 1, 3.54, 3.02],
                  ['WYS_SOPORTE_BAÑOBATERIAMASCULINO3PERSONAS', 1, 3.54, 3.02],
                  ['WYS_SOPORTE_KITCHENETTE', 1, 1.6, 2.3],
                  ['WYS_SOPORTE_SERVIDOR1BASTIDOR', 0, 1.5, 2.4],
                  ['WYS_SOPORTE_PRINT1', 1, 1.5, 1.3],
                  ['WYS_RECEPCION_1PERSONA', 1, 2.7, 3.25],
                  ['WYS_TRABAJOINDIVIDUAL_QUIETROOM2PERSONAS', 0, 2.05, 1.9],
                  ['WYS_TRABAJOINDIVIDUAL_PHONEBOOTH1PERSONA', 0, 2.05, 2.01],
                  ['WYS_COLABORATIVO_BARRA6PERSONAS', 0, 1.95, 2.4]]
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

            min_list = min_dist_to_area(bx_dist)

            for d in min_list:
                w = restrictions.mod2area(restrictions.module_dictionary, restrictions.area_dictionary,
                                          restrictions.mod2area_matrix, boxes[i][1], d[0])
                if w != 0:
                    ind[i].fitval1 -= round((d[1] * w), 1)
                    a -= d[1] * w

            distances = []
            for j in range(nb):
                if i is not j:
                    distances.append([boxes[j][1], boxes[i][0].distance(boxes[j][0])])

            distances2 = min_dist_to_area(distances)
            for d in distances2:
                w = restrictions.mod2mod(restrictions.module_dictionary, restrictions.mod2mod_matrix,
                                         boxes[i][1], d[0])
                if w != 0:
                    ind[i].fitval2 -= round((d[1] * w), 1)
                    a -= d[1] * w
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
    toolbox.register("attr_pos", makePos, planta, input_list)
    toolbox.register("individual", tools.initRepeat, creator.Individual,
                     (toolbox.attr_pos), n=IND_SIZE)

    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", mutMod, planta=planta, mu=0, sigma=0.5, indpb=0.2)
    toolbox.register("select_best", tools.selBest)
    toolbox.register("select_roulette", tools.selRoulette)
    toolbox.register("select", tools.selTournament, tournsize=round(N * 0.4))
    # toolbox.register("select", tools.selNSGA2)
    toolbox.register("evaluate", evaluateInd)

    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.decorate("evaluate", tools.DeltaPenalty(feasible, -200.0, feas_distance))

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

                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1, mod.name, fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.8, round(mod.fitval1, 1), fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 2.6, round(mod.fitval2, 1), fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 0.1, y[2], mod.x, fontsize=6, ma='center'))
                        labels.append(ax[row, col].text(x[2] + 2, y[2], mod.y, fontsize=6, ma='center'))
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

        # if max_fit == max(fitn):
        #     max_count += 1
        # else:
        #     max_count = 0
        #
        # if max_count > round(NGEN / 8) or max_fit < 0:
        #     CXPB = 0.1
        #     MUTPB = 0.9
        # else:
        #     CXPB = 0.5
        #     MUTPB = 0.2
        #
        # max_fit = max(fitn)

        print('Time:', round(time.time() - start_time, 1), ' Generation ', g + 1, 'of', NGEN, 'POP SIZE:', len(pop),
              '  Min:', round(min(fitn), 1), 'Max:', round(max(fitn), 1), 'Avg:', round(sum(fitn) / len(fitn), 1),
              'Local sol. count:', max_count)

        # if (max(fitn)-min(fitn))/max(fitn) <= 0.001:
        #    print('Found local max')
        #    break

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

        # N = len(pop) - 1
        # if N < 20:
        #    N = 20
        # offspring = toolbox.select_best(offspring + pop, POP_SIZE)
        # The population is entirely replaced by the offspring
        pop[:] = offspring
        # viewer.show_floor(planta, As, pop, g)
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
    for o in out:
        print(o)

    return out
