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
