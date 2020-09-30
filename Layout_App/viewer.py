import matplotlib.pyplot as plt
from shapely.geometry import box


def show_floor(planta, As,  pop, g):
    #print('SHOW FLOOR POP:')
    #for ind in pop:
    #    print('ind:')
    #    for mod in ind:
    #        mod.show()

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
            ind = pop[m*row+col]
            boxes = []
            for mod in ind:
                boxes.append(
                    [box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2),
                     mod.name])

            for b in boxes:
                x, y = b[0].exterior.xy
                ax[row, col].set_title('POP:'+str(m*row+col)+' Fitness:'+ str(round(ind.fitness.values[0],2)), fontsize=9)
                ax[row, col].plot(x, y, color='b')
                ax[row, col].text(x[2] + 0.1, y[2] - 1, b[1], fontsize=6)

    plt.show()













