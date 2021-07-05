import matplotlib.pyplot as plt
from shapely.geometry import box
from shapely.geometry.polygon import Polygon, LineString


def viz_end():
    plt.ioff()
    plt.show()


def viz_clear(viz, g, NGEN, viz_period, boxes):

    if viz and g < NGEN - 1 and (g + 1 if g > 0 else g) % viz_period == 0:
        for el in boxes:
            el[0][0].remove()
            el[1][0].remove()
            #el[1][1].remove()
            #el[1][2].remove()
            #el[1][3].remove()
            # el[1][4].remove()

def viz_update(viz, viz_period, g, pop,  fig, ax):

    rows = 2
    cols = 2
    if viz and (g + 1 if g > 0 else g) % viz_period == 0:
        fig.suptitle('Generation ' + str(g + 1), fontsize=12)
        boxes = []
        for row in range(rows):
            for col in range(cols):
                ind = pop[(cols * row + col)]     # ind = pop[2 * (cols * row + col)]
                ax[row, col].set_title(
                    # 'POP:' + str((cols * row + col)) + ' Fitness:' + str(round(ind.fitness.values[0], 2)), fontsize=9)
                    'POP:' + str((cols * row + col)), fontsize = 9)
                for mod in ind:
                    b = mod.get_box()
                    x, y = b.exterior.xy
                    b = ax[row, col].plot(x, y, color='b')
                    labels = []

                    #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.2, str(mod.id), fontsize=8, ma='center'))
                    labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 0.6, "Module_id: " + str(mod.id), fontsize=6, ma='center'))
                    #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.2, 'mod.name', fontsize=6, ma='center'))
                    #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.8, "fit_area: " + str(round(mod.fitval1, 2)), fontsize=6, ma='center'))
                    #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 2.4, "fit_mods: " + str(round(mod.fitval2, 2)), fontsize=6, ma='center'))
                    # labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 0.6, mod.x, fontsize=6, ma='center'))
                    # labels.append(ax[row, col].text(x[2] + 2, y[2] - 0.6, mod.y, fontsize=6, ma='center'))
                    boxes.append([b, labels])

                '''for b in boxes:
                    x, y = b[0].exterior.xy
                    ax[row, col].set_title('POP:'+str(2*(cols*row+col))+' Fitness:'+ str(round(ind.fitness.values[0],2)), fontsize=9)
                    ax[row, col].plot(x, y, color='b')
                    ax[row, col].text(x[2] + 0.1, y[2] - 1, b[1], fontsize=6)'''
        fig.canvas.draw()
        fig.canvas.flush_events()
        return boxes

def viz_update_1(viz, viz_period, g, pop,  fig, ax):

    if viz and (g + 1 if g > 0 else g) % viz_period == 0:
        fig.suptitle('Generation ' + str(g + 1), fontsize=12)
        boxes = []

        ind = pop     # ind = pop[2 * (cols * row + col)]
        ax.set_title(
            # 'POP:' + str((cols * row + col)) + ' Fitness:' + str(round(ind.fitness.values[0], 2)), fontsize=9)
            'POP:' + str((0)), fontsize = 9)
        for mod in ind:
            b = mod.get_box()
            x, y = b.exterior.xy
            b = ax.plot(x, y, color='b')
            labels = []

            #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.2, str(mod.id), fontsize=8, ma='center'))
            labels.append(ax.text(x[2] + 0.1, y[2] - 0.6, "Module_id: " + str(mod.id), fontsize=6, ma='center'))
            #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.2, 'mod.name', fontsize=6, ma='center'))
            #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 1.8, "fit_area: " + str(round(mod.fitval1, 2)), fontsize=6, ma='center'))
            #labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 2.4, "fit_mods: " + str(round(mod.fitval2, 2)), fontsize=6, ma='center'))
            # labels.append(ax[row, col].text(x[2] + 0.1, y[2] - 0.6, mod.x, fontsize=6, ma='center'))
            # labels.append(ax[row, col].text(x[2] + 2, y[2] - 0.6, mod.y, fontsize=6, ma='center'))
            boxes.append([b, labels])

        '''for b in boxes:
            x, y = b[0].exterior.xy
            ax[row, col].set_title('POP:'+str(2*(cols*row+col))+' Fitness:'+ str(round(ind.fitness.values[0],2)), fontsize=9)
            ax[row, col].plot(x, y, color='b')
            ax[row, col].text(x[2] + 0.1, y[2] - 1, b[1], fontsize=6)'''

        fig.canvas.draw()
        fig.canvas.flush_events()
        return boxes


def viewer_viz_1(planta, As, viz, zones={}, areas={}, circ=[]):
    if viz:
        rows = 1
        cols = 1
        plt.ion()

        fig, ax = plt.subplots(rows, cols)
        x, y = planta.exterior.xy
        ax.plot(x, y, color='black')
        ax.axis('equal')
        ax.grid(True)
        ax.tick_params(axis="x", labelsize=7)
        ax.tick_params(axis="y", labelsize=7)

        for pi in planta.interiors:
            x, y = pi.xy
            ax.plot(x, y, color='black')

        for a in As:
            xa, ya = a[0].exterior.xy
            if a[1] == 'WYS_ENTRANCE':
                ax.fill(xa, ya, color='#a8e4a0')
            if a[1] == 'WYS_FACADE_CRYSTAL':
                ax.fill(xa, ya, color='#89cff0')
            if a[1] == 'WYS_FACADE_OPAQUE':
                ax.fill(xa, ya, color='#ffeac4')
            if a[1] == 'WYS_SHAFT':
                ax.fill(xa, ya, color='#779ecb')
            if a[1] == 'WYS_CORE':
                ax.fill(xa, ya, color='#ffb1b1')

        for z_name, zone in zones.items():
            xz, yz = zone.exterior.xy
            if 'ZONA PUESTOS DE TRABAJO' in z_name:
                ax.plot(xz, yz, color='r')
                ax.fill(xz, yz, color='peachpuff')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='r')
            elif 'ZONA SERVICIOS' in z_name:
                ax.plot(xz, yz, color='darkolivegreen')
                ax.fill(xz, yz, color='palegreen')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='darkolivegreen')
            elif 'ZONA SOPORTE' in z_name:
                ax.plot(xz, yz, color='purple')
                ax.fill(xz, yz, color='pink')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='purple')
            elif 'ZONA SALAS REUNION FORMAL' in z_name:
                ax.plot(xz, yz, color='indigo')
                ax.fill(xz, yz, color='thistle')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='indigo')
            elif 'ZONA TRABAJO PRIVADO' in z_name:
                ax.plot(xz, yz, color='brown')
                ax.fill(xz, yz, color='wheat')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='brown')
            elif 'ZONA ESPECIALES' in z_name:
                ax.plot(xz, yz, color='darkturquoise')
                ax.fill(xz, yz, color='lightcyan')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='darkturquoise')
            elif 'ZONA REUNIONES INFORMALES' in z_name:
                ax.plot(xz, yz, color='orangered')
                ax.fill(xz, yz, color='bisque')
                ax.text(zone.centroid.x - 5, zone.centroid.y, z_name, weight='bold', fontsize=6,
                                  ma='center', color='orangered')

        for key, value in areas.items():
            xz, yz = value.exterior.xy
            ax.plot(xz, yz, 'g', linewidth=1)
            ax.text(value.centroid.x, value.centroid.y, 'area: ' + str(key), weight='bold',
                              fontsize=6, ma='center', color='g')

            for ai in value.interiors:
                x, y = ai.xy
                ax.plot(x, y, color='g', linewidth=2)

        i = 1
        for c in circ:
            x, y = c.exterior.xy
            ax.plot(x, y, color='r', linewidth=1)
            ax.text(c.centroid.x, c.centroid.y, str(i), weight='bold', fontsize=6, ma='center',
                              color='b')
            i += 1
            for ci in c.interiors:
                x, y = ci.xy
                ax.plot(x, y, color='r', linewidth=2)

        return fig, ax

        '''x, y = lines.exterior.xy
        for row in range(rows):
            for col in range(cols):
                ax[row, col].plot(x, y, 'g', linewidth=2)
                #ax[row, col].text(line.centroid.x, line.centroid.y, str(i), weight='bold', fontsize=6, ma='center', color='b')
                ax[row, col].fill(x, y, color='yellow')
        return fig, ax'''
    return 0, 0

def viewer_viz(planta, As, viz, zones={}, areas={}, circ=[]):

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
                        
        for z_name, zone in zones.items():
            xz, yz = zone.exterior.xy
            for row in range(rows):
                for col in range(cols):
                    if 'ZONA PUESTOS DE TRABAJO' in z_name:
                        ax[row, col].plot(xz, yz, color='r')
                        ax[row, col].fill(xz, yz, color='peachpuff')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='r')
                    elif 'ZONA SERVICIOS' in z_name:
                        ax[row, col].plot(xz, yz, color='darkolivegreen')
                        ax[row, col].fill(xz, yz, color='palegreen')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='darkolivegreen')
                    elif 'ZONA SOPORTE' in z_name:
                        ax[row, col].plot(xz, yz, color='purple')
                        ax[row, col].fill(xz, yz, color='pink')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='purple')
                    elif 'ZONA SALAS REUNION FORMAL' in z_name:
                        ax[row, col].plot(xz, yz, color='indigo')
                        ax[row, col].fill(xz, yz, color='thistle')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='indigo')
                    elif 'ZONA TRABAJO PRIVADO' in z_name:
                        ax[row, col].plot(xz, yz, color='brown')
                        ax[row, col].fill(xz, yz, color='wheat')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='brown')
                    elif 'ZONA ESPECIALES' in z_name:
                        ax[row, col].plot(xz, yz, color='darkturquoise')
                        ax[row, col].fill(xz, yz, color='lightcyan')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='darkturquoise')
                    elif 'ZONA REUNIONES INFORMALES' in z_name:
                        ax[row, col].plot(xz, yz, color='orangered')
                        ax[row, col].fill(xz, yz, color='bisque')
                        ax[row, col].text(zone.centroid.x-5, zone.centroid.y, z_name, weight='bold', fontsize=6, ma='center', color='orangered')

        for key, value in areas.items():
            xz, yz = value.exterior.xy
            for row in range(rows):
                for col in range(cols):
                    ax[row, col].plot(xz, yz, 'g', linewidth=1)
                    ax[row, col].text(value.centroid.x, value.centroid.y, 'area: '+ str(key), weight='bold', fontsize=6, ma='center', color='g')

            for ai in value.interiors:
                x, y = ai.xy
                for row in range(rows):
                    for col in range(cols):
                        ax[row, col].plot(x, y, color='g', linewidth=2)

        i = 1
        for c in circ:
            x, y = c.exterior.xy
            for row in range(rows):
                for col in range(cols):
                    ax[row, col].plot(x, y, color='r', linewidth=1)
                    ax[row, col].text(c.centroid.x, c.centroid.y, str(i), weight='bold', fontsize=6, ma='center', color='b')
            i += 1
            for ci in c.interiors:
                x, y = ci.xy
                for row in range(rows):
                    for col in range(cols):
                        ax[row, col].plot(x, y, color='r', linewidth=2)
        
        return fig, ax

        '''x, y = lines.exterior.xy
        for row in range(rows):
            for col in range(cols):
                ax[row, col].plot(x, y, 'g', linewidth=2)
                #ax[row, col].text(line.centroid.x, line.centroid.y, str(i), weight='bold', fontsize=6, ma='center', color='b')
                ax[row, col].fill(x, y, color='yellow')
        return fig, ax'''
    return 0, 0


def show_floor(planta, As,  pop, g):
    n = 2
    m = 2
    fig, ax = plt.subplots(n,m)
    fig.suptitle('Generation '+str(g), fontsize=12)
    x, y = planta.exterior.xy
    for row in range(n):
        for col in range(m):
            ax[row, col].plot(x, y, color='black')
            ax[row, col].axis('equal')
            ax[row, col].grid(True)
            ax[row, col].tick_params(axis="x", labelsize=7)
            ax[row, col].tick_params(axis="y", labelsize=7)

    for pi in planta.interiors:
        x, y = pi.xy
        for row in range(n):
            for col in range(m):
                ax[row, col].plot(x, y, color='black')

    for a in As:
        xa, ya = a[0].exterior.xy
        for row in range(n):
            for col in range(m):
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

    for row in range(n):
        for col in range(m):
            ind = pop[2*(m*row+col)]
            boxes = []
            for mod in ind:
                boxes.append(
                    [box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2),
                     mod.name])

            for b in boxes:
                x, y = b[0].exterior.xy
                ax[row, col].set_title('POP:'+str(2*(m*row+col))+' Fitness:'+ str(round(ind.fitness.values[0],2)), fontsize=9)
                ax[row, col].plot(x, y, color='b')
                ax[row, col].text(x[2] + 0.1, y[2] - 1, b[1], fontsize=6)

    plt.show()


def simple_show(outline, holes, areas, pols):
    voids = []
    border = outline[0][1]
    As = []
    for a in areas:
        As.append([Polygon(a[1]), a[0]])
    for h in holes:
        voids.append(h[1])
    planta = Polygon(border, voids)
    x, y = planta.exterior.xy
    plt.plot(x, y, color='black')
    for pi in planta.interiors:
        x, y = pi.xy
        plt.plot(x, y, color='black')
    for a in As:
        xa, ya = a[0].exterior.xy
        if a[1] == 'WYS_ENTRANCE':
            plt.fill(xa, ya, color='#a8e4a0')
        if a[1] == 'WYS_FACADE_CRYSTAL':
            plt.fill(xa, ya, color='#89cff0')
        if a[1] == 'WYS_FACADE_OPAQUE':
            plt.fill(xa, ya, color='#ffeac4')
        if a[1] == 'WYS_SHAFT':
            plt.fill(xa, ya, color='#779ecb')
        if a[1] == 'WYS_CORE':
            plt.fill(xa, ya, color='#ffb1b1')
    for p in pols:
        x, y = p.exterior.xy
        plt.plot(x, y)
    plt.show()












