import rtree
import matplotlib.pyplot as plt
from shapely.geometry import box
from shapely.strtree import STRtree
from shapely.ops import unary_union

def plot_boxes(boxes, core):

    fig, ax = plt.subplots()
    ax.axis('equal')
    ax.grid(True)
    ax.tick_params(axis="x", labelsize=7)
    ax.tick_params(axis="y", labelsize=7)
    for i in range(len(boxes)):
        x,y = boxes[i].exterior.xy
        ax.plot(x, y, color='b')
        ax.text(x[2], y[1]+0.1,'box: ' + str(i+1), fontsize=10)
    x,y = core.exterior.xy
    ax.plot(x, y, color='r')
    ax.text(x[2], y[1]+0.1,'core', fontsize=10)
    plt.show()

def main():
    idx = rtree.index.Index()
    '''b1 = box(1,1,3,3)
    b2 = box(2,2,4,4) 
    b3 = box(5,1,7,3) 
    b4 = box(5,3,7,5)
    b5 = box(2,5,4,7)
    b6 = box(0,0,8,6)
    boxes = [b1,b2,b3,b4,b5,b6]'''

    b1 = box(0,0,3,6)
    b2 = box(0,6,3,9)
    b3 = box(3,6,5,9)
    b4 = box(5,6,8,9)
    b5 = box(8,6,12,9)
    b6 = box(8,0,12,6)
    b7 = box(5,0,8,3)
    b8 = box(3,0,5,3)
    b9 = box(-1,-1,13,10) #planta
    b10 = box(*b9.bounds)
    boxes = [b1,b2,b3,b4,b5,b6,b7,b8, b9]
    core = box(3,3,8,6).buffer(0, cap_style=3, join_style=2)

    '''print(list(b1.exterior.coords))'''

    for i, b in enumerate(boxes):
        idx.insert(i, b.bounds)
    for i in range(len(boxes)):
        print('----- box {} info ------'.format(i+1))
        inters = ['box {} intersects box {}'.format(i+1, fid + 1) for fid in list(idx.intersection(boxes[i].bounds)) if boxes[fid].intersects(boxes[i]) and boxes[fid]!= boxes[i]]
        nearest = ['box {} nearest box {}'.format(i+1, fid + 1) for fid in list(idx.nearest(boxes[i].bounds)) if boxes[fid]!= boxes[i]]
        box_in = ['box {} contains box {}'.format(i+1, fid + 1) for fid in list(idx.intersection(boxes[i].bounds)) if boxes[i].contains(boxes[fid]) and boxes[fid]!= boxes[i]]
        '''print(inters)
        print(nearest)
        print(box_in)'''
    '''print(b1.intersection(b3).length)
    print(b1.intersection(b2).length)
    print(b9)
    print(b10)'''
    plot_boxes(boxes, core)
    
main()