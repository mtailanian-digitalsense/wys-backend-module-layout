from unittest import TestCase

from example_data_pol import dict_ex
from lib import get_extremes_m


class Test(TestCase):
    def setUp(self) -> None:
        self.polygons = [{
            'floor_id': 11,
            'id': 968,
            'is_external': False,
            'is_internal': True,
            'name': 'WYS_HOLE',
            'points': [
                {
                    'id': 6728,
                    'order': 0,
                    'polygon_id': 968,
                    'x': -1362.19,
                    'y': -372.095
                },
                {
                    'id': 6729,
                    'order': 1,
                    'polygon_id': 968,
                    'x': -1404.19,
                    'y': -372.095
                },
                {
                    'id': 6730,
                    'order': 2,
                    'polygon_id': 968,
                    'x': -1404.19,
                    'y': -279.095
                },
                {
                    'id': 6731,
                    'order': 3,
                    'polygon_id': 968,
                    'x': -1362.19,
                    'y': -279.095
                },
                {
                    'id': 6732,
                    'order': 4,
                    'polygon_id': 968,
                    'x': -1362.19,
                    'y': -372.095
                }
            ]
        },
            {
                'floor_id': 11,
                'id': 969,
                'is_external': False,
                'is_internal': True,
                'name': 'WYS_HOLE',
                'points': [
                    {
                        'id': 6733,
                        'order': 0,
                        'polygon_id': 969,
                        'x': -1362.19,
                        'y': 197.155
                    },
                    {
                        'id': 6734,
                        'order': 1,
                        'polygon_id': 969,
                        'x': -1404.19,
                        'y': 197.155
                    },
                    {
                        'id': 6735,
                        'order': 2,
                        'polygon_id': 969,
                        'x': -1404.19,
                        'y': 293.155
                    }]
            }
        ]

    def test_get_extremes_m(self):
        g_x_min, g_y_min, g_x_max, g_y_max = get_extremes_m(self.polygons)
        x_min = -1404.19
        y_min = -372.095
        x_max = -1362.19
        y_max = 293.155

        self.assertEqual(x_max, g_x_max)
        self.assertEqual(y_max, g_y_max)
        self.assertEqual(x_min, g_x_min)
        self.assertEqual(y_min, g_y_min)

        nx_min, ny_min, nx_max, ny_max = get_extremes_m(dict_ex['selected_floor']['polygons'])
        print(f"{nx_min}, {ny_min}, {nx_max}, {ny_max}\n width = {nx_max - nx_min} length= {ny_max - ny_min}")
