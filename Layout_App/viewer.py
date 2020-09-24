import matplotlib.pyplot as plt
from shapely.geometry import box


def show_floor(planta, As,  ind):
    boxes = []
    x, y = planta.exterior.xy
    plt.plot(x, y, color='black')

    for pi in planta.interiors:
        xh, yh = pi.xy
        plt.plot(xh, yh, color='black')

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

    for mod in ind:
        boxes.append([box(mod.x - mod.width / 2, mod.y - mod.height / 2, mod.x + mod.width / 2, mod.y + mod.height / 2), mod.name])

    for b in boxes:
        x, y = b[0].exterior.xy
        #print(b[1])
        plt.plot(x, y, color='b')
        plt.text(x[2]+0.1, y[2]-1, b[1], fontsize = 8)

    plt.axis('equal')
    plt.grid(True)
    plt.show()