import matplotlib.pyplot as plt
from shapely.geometry import box


def viz_end():
    plt.ioff()
    plt.show()


def viz_clear(viz, g, NGEN, viz_period, boxes):

    if viz and g < NGEN - 1 and (g + 1 if g > 0 else g) % viz_period == 0:
        for el in boxes:
            el[0][0].remove()
            el[1][0].remove()
            el[1][1].remove()
            el[1][2].remove()
            el[1][3].remove()
            el[1][4].remove()

def viz_update(viz, viz_period, g, pop,  fig, ax):

    rows = 2
    cols = 2

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
        return boxes


def viewer_viz(planta, As, zones, viz):

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
        return fig, ax
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













