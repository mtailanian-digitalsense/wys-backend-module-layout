import time
import logging
import cv2 as cv
from shapely.geometry.polygon import Polygon

from optimizer.DS_layout_optimizer import LayoutOptimizer
from optimizer.DS_unit import UNITS_TYPE_EQUIVALENCE_INVERSE

logging.basicConfig(
    filename='smart_layout.log',
    level=logging.DEBUG,
    format='%(levelname)s | %(asctime)s | %(name)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
logger = logging.getLogger(__name__)
logger.info("init script")


def Smart_Layout(dictionary, POP_SIZE=None, GENERATIONS=None, viz=False, viz_period=10):

    start_time = time.time()
    logger.debug(f"Start: {round(time.time() - start_time, 2)}")

    # Get data
    planta, shafts, entrances, windows, circulations, cores, workspaces = get_input_cm(dictionary)

    # Convert data to our classes
    layout_optimizer = LayoutOptimizer.load(planta, cores, shafts, circulations, entrances, windows, workspaces, show=0)

    # Optimize
    _ = layout_optimizer.execute(log=True, display=False)
    # layout_optimizer.post_process()
    # layout_optimizer.add_wildcards()

    # Show results
    optimized_layout = layout_optimizer.draw(
        show_unit_name=True, show_contours=2, show_unit_art=False, show_features=True
    )
    cv.namedWindow("Final Layout", cv.WINDOW_NORMAL)
    cv.imshow("Final Layout", optimized_layout)
    cv.waitKey()

    # TODO: Falta traducir a las coordenadas originales. sumar el origin y pasar a metros
    # Output Units
    out = []
    for u in layout_optimizer.units:
        name = UNITS_TYPE_EQUIVALENCE_INVERSE[u.type]
        x, y, w, h, tita, rot = u.get_result_box()
        out.append([name, 0, x, y, rot, w, h])

    return out


def get_input_cm(dictionary):
    """
    Divides the polygons in the input dictionary by type
    Returns the point coordinates in centimeters
    """
    logger.debug("\tget_input_cv start")
    floor_polygons = dictionary.get('selected_floor').get('polygons')
    workspaces = dictionary.get('workspaces')

    outline, holes, shafts, entrances, windows, circulations, cores = [], [], [], [], [], [], []
    key_to_variable = {
        'WYS_AREA_UTIL': outline,
        'WYS_HOLE': holes,
        'WYS_CORE': cores,
        'WYS_SHAFT': shafts,
        'WYS_ENTRANCE': entrances,
        'WYS_FACADE_CRYSTAL': windows,
        'WYS_CIRCULATION': circulations
    }

    for p in floor_polygons:
        name = p.get('name')
        polygon = Polygon([(round(a.get('x'), 1), round(a.get('y'), 1)) for a in p.get('points')])
        try:
            key_to_variable[name].append(polygon)
        except KeyError:
            logger.error(f"[LOADING LAYOUT] No action taken for {name}")

    border_pts = list(zip(*outline[0].exterior.xy))
    holes_pts = [list(zip(*h.exterior.xy)) for h in holes]
    planta = Polygon(border_pts, holes_pts)

    logger.debug("\tget_input_cv end")
    return planta, shafts, entrances, windows, circulations, cores, workspaces


def smart_layout_async(dictionary, POP_SIZE=50, GENERATIONS=50):
    result = Smart_Layout(dictionary, POP_SIZE, GENERATIONS)
    return result, dictionary


def main():
    from configs.example_data_v3 import dict_ex

    floor = dict_ex['selected_floor']
    workspaces = dict_ex['workspaces']
    layout_data = {'selected_floor': floor, 'workspaces': workspaces}

    layout_workspaces = Smart_Layout(layout_data)


if __name__ == '__main__':
    main()
