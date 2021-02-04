from PIL import Image
import requests
from io import BytesIO
import json
import base64
from shapely.geometry.polygon import Polygon
from Layout_App import example_data_v3          # temporal

def get_floor_elements_p(floor_dict: dict, floor_loc=None):
    """
    :param floor_dict: data given to smart layout
    :param floor_loc: FloorLocation object
    :return: Floor elements with his points coordinates in pixels
    """
    if floor_loc is None:
        floor_loc = init_floor(floor_dict)
    
    floor_polygons = floor_dict['selected_floor']['polygons']
    # Save floor elements here
    floor_elements = []

    border = 0
    plant_exterior = []
    points_ex = []
    for Area in floor_polygons:
        if Area.get('name') == 'WYS_AREA_UTIL':
            border = [(round(a.get('x') / 100, 2), round(a.get('y') / 100, 2)) for a in Area.get('points')]
    borde = Polygon(border)
    borde_buff = borde.buffer(0.5, cap_style=3, join_style=2)
    x, y = borde_buff.envelope.exterior.xy
    plant_exterior.append('WYS_PLANT_EXTERIOR')
    for i in range(len(x)):
        points_ex.append((x[i], y[i]))
    plant_exterior.append(points_ex)
    element = FloorPolygon(0, plant_exterior[0])
    i = 0
    for point in plant_exterior[1]:
        # (point_m - origin) multiplied for the pixel/meters reason.
        point_position_x = (point[0] - floor_loc.x_0) * floor_loc.x_pixel_m
        # Y coordinate is always positive
        point_position_y = (point[1] - floor_loc.y_0) * -1 * floor_loc.y_pixel_m
        element.add_point(i, abs(point_position_x), abs(point_position_y))
        i += 1
    floor_elements.append(element.to_dict())

    for fp in floor_polygons:
        element = FloorPolygon(fp['id'], fp['name'])

        for point in fp['points']:
            # (point_m - origin) multiplied for the pixel/meters reason.
            point_position_x = (point['x']/100.0 - floor_loc.x_0) * floor_loc.x_pixel_m

            # Y coordinate is always positive
            point_position_y = (point['y']/100.0 - floor_loc.y_0) * -1 * floor_loc.y_pixel_m

            element.add_point(point['order'], abs(point_position_x), abs(point_position_y))

        floor_elements.append(element.to_dict())
    
    return floor_elements

def get_extremes_m(polygons: []):
    """
    Returns the extremes points in meters
    :param polygons: list with all floor polygons
    :return: extreme points in meters.
    """
    width = 0.0
    height = 0.0
    points = []

    x_coords = []
    y_coords = []

    for pol in polygons:
        points += pol['points']

    for point in points:
        # Get all X points and save in a list
        x_coords.append(point['x'])
        # Get all Y points and save in a list
        y_coords.append(point['y'])

    # Getting max and min points

    x_max = max(x_coords)
    y_max = max(y_coords)

    x_min = min(x_coords)
    y_min = min(y_coords)

    return x_min, y_min, x_max, y_max

def init_floor(floor_dict: dict):
    """
    :param floor_dict: data given to smart layout
    :return: FloorLocation object
    """

    # Init floor
    floor_loc = FloorLocation()

    # Polygons or elements of floor

    floor_polygons = floor_dict['selected_floor']['polygons']

    # Give width and length of a floor

    x_min, y_min, x_max, y_max = get_extremes_m(floor_polygons)

    floor_loc.width_m = (x_max - x_min) / 100.0
    floor_loc.height_m = (y_max - y_min) / 100.0

    # Give give the most left/up point
    floor_loc.x_0, floor_loc.y_0 = x_min / 100.0, y_max / 100.0

    # Get Pixel/Meters relation for a floor
    try:

        width_p, height_p = get_image_size(floor_dict['selected_floor']['image_link'])

    except Exception as e:
        raise e

    floor_loc.x_pixel_m = width_p * 1.0 / floor_loc.width_m  # pixels/meters
    floor_loc.y_pixel_m = height_p * 1.0 / floor_loc.height_m  # pixels/meters

    return floor_loc


def transform_coords(floor_dict: dict, coordinates: [], space_images_url, token):
    """

    :param token: Token for the connection
    :param space_images_url: Where we want to find the image for every space
    :param floor_dict: data given to smart layout
    :param coordinates: list of all spaces with their coordinates
    :return: spaces and floor elements with their coordinates in pixels
    """
    # Init floor
    floor_loc = init_floor(floor_dict)

    # build a dictionary of type of spaces
    spaces_dict = {}
    for space in floor_dict['workspaces']:
        spaces_dict[space['name']] = space

    # Save spaces here
    spaces = []
    # Save images if their was downloaded and resizing
    img_storage_by_name = {}

    # Read all spaces given by smart layout
    for space in coordinates:
        space_loc = SpaceLocation()
        space_name = space[0]
        xpos_m = space[2]
        ypos_m = space[3]
        rot = space[4]

        # (point_m - origin) multiplied for the pixel/meters reason.
        space_loc.position_x = (xpos_m - floor_loc.x_0) * floor_loc.x_pixel_m

        # Y coordinate is always positive
        space_loc.position_y = (ypos_m - floor_loc.y_0) * -1 * floor_loc.y_pixel_m
        space_loc.rotation = rot

        # Resizing image

        # Get width and height in meters
        space_info = spaces_dict[space_name]

        space_width_m = space_info['width']
        space_height_m = space_info['height']

        space_width_p = space_width_m * floor_loc.x_pixel_m
        space_height_p = space_height_m * floor_loc.y_pixel_m

        space_loc.width_p = space_width_p
        space_loc.height_p = space_height_p

        space_loc.space_id = space_info['id']

        if space_name not in img_storage_by_name:
            try:
                resp = requests.get(f"{space_images_url}/{space_loc.space_id}", headers={'Authorization': token})

                if resp.status_code != 200:
                    raise Exception(f"Can't get a space image. Error code {resp.status_code}")

                space_data = json.loads(resp.content.decode('utf-8'))

                space_loc.image = resize_base64_image(space_data['model_2d'],space_width_p, space_height_p)
                img_storage_by_name[space_name] = resize_base64_image(space_data['model_2d'],
                                                                      space_width_p, space_height_p)

            except Exception as e:
                raise e

        else:
            space_loc.image = img_storage_by_name[space_name]

        spaces.append(space_loc.to_dict())
    
    floor_elements = get_floor_elements_p(floor_dict, floor_loc)

    return spaces, floor_elements


class SpaceLocation:

    def __init__(self):
        self.position_x = 0
        self.position_y = 0
        self.width_p = 0
        self.height_p = 0
        self.rotation = 0
        self.space_id = 0
        self.image = ""

    def to_dict(self):
        return {
            'position_x': self.position_x,
            'position_y': self.position_y,
            'width': self.width_p,
            'height': self.height_p,
            'rotation': self.rotation,
            'space_id': self.space_id,
            'image': self.image
        }


class FloorLocation:

    def __init__(self):
        self.width_m = 0.0
        self.height_m = 0.0
        self.x_0 = 0
        self.y_0 = 0
        self.x_pixel_m = 0
        self.y_pixel_m = 0

    def to_dict(self):
        return {
            'width_m': self.width_m,
            'height_m': self.height_m,
            'x_pixel_m': self.x_pixel_m,
            'y_pixel_m': self.y_pixel_m
        }

class FloorPolygon:

    def __init__(self, _id, name):
        self.id = _id
        self.name = name
        self.points = []

    def add_point(self, order, position_x, position_y):
        point = PolygonPoint(order, position_x, position_y)
        self.points.append(point)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'points': [p.to_dict() for p in self.points],
        }

class PolygonPoint:
    def __init__(self, order, position_x, position_y):
        self.order = order
        self.position_x = position_x
        self.position_y = position_y

    def to_dict(self):
        return {
            'order': self.order,
            'position_x': self.position_x,
            'position_y': self.position_y
        }

def get_image_size(link):
    """
    Get the size of a image in pixels

    :param link: link of a image
    :return: width and height in pixels
    """

    # Get image from internet
    try:
        resp = requests.get(link)
        image: Image = Image.open(BytesIO(resp.content))
        return image.width, image.height

    except Exception as e:
        raise e


def resize_base64_image(image_base64: str, width_p: int, height_p: int):
    """
    Resize a image from base64
    :param image_base64: base64 image with header
    :param width_p: new width in pixels
    :param height_p: new height in pixels
    :return: base64 image resizing
    """
    image_str = image_base64.split(',')[1]
    image_bin = base64.b64decode(image_str)
    image: Image = Image.open(BytesIO(image_bin))
    image2 = image.resize((int(width_p), int(height_p)))
    io_bytes = BytesIO()
    image2.save(io_bytes, format='PNG')
    new_image_str: bytearray = base64.b64encode(io_bytes.getvalue())
    return f"{image_base64.split(',')[0]},{new_image_str.decode('utf-8')}"


#elementos = get_floor_elements_p(example_data_v3.dict_ex)