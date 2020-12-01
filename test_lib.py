import base64
import unittest
from io import BytesIO
from unittest import TestCase

from PIL import Image

from example_data_pol import dict_ex
from lib import get_extremes_m, get_image_size, resize_base64_image, transform_coords


class Test(TestCase):
    def setUp(self) -> None:
        self.token = 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJhdWQiOiIxIiwianRpIjoiNDUwY2E2NzBhZmY4M2IyMjBkOGZkNThkOTU4NDM2NTYxNGZjZWFmMjEwYzhkYjJjZjQ3NTQ4NjQzMThiNWEzOThjZjYyNTA3MTk5MzY4MGQiLCJpYXQiOjE1OTIzMDkxMTcsIm5iZiI6MTU5MjMwOTExNywiZXhwIjoxNjI0MjI1MDM4LCJzdWIiOiIyMyIsInVzZXJfaWQiOjIzLCJzY29wZXMiOltdLCJ1aWQiOjIzfQ.kXmM-nt7HdEmmWqgNLpssvrxjoVkRP0f0akOoDNWLEUAxTfUKx8Egk6PXodDuSl5T2AsO5fIth8E_k9z-sPCm1ayaSD-yGFxdp2cT_O4KjOuBF1uTaGdQ_e69My9hr0p08sQg9lvplmJyMRkdCtce8u_YMOMF9a18edzQsUe7f_u1ae0jllS4y2kA53mQ7ofdHeWtN8wcx31CBaVo3g0EndPK0sYS2DRgBRBNQuVAedS5rkogRNeQKhjZCqL1d-n8b1L1OdyOKwkgbfKQG4Ee6kdjrrZDDDeEja8ReMqzW0q2sjTkLDkNbBuqGS8Zz6Ai4blUyEI6o6o6SHh1qaeGVXBHiVO0971FcH9FjUy2T5amyAJ41e7A9xy6iOVnIxGJ9pRgDo-UAIgFMNGuQDSaKRXhqm76-CkTBqzY7imyx0W6pvHM4XEX3yAGXFsTL9prq64k8RqFfCWPYUy7f25LbyjL__YaXijCXZMN9FfY8LOnKHhthRNkIGD5M5PiiTNOmB0DA1xR_QXGYlO1y8SWeZ9p_S9XYVygNJTh44xyDYIRj40RjSlOnh5gLfquca2EZxgeTSIyDDSXD43_iYmBm8JX-fS2hzqgoL8_0ATlYbW32DAT2ecfIS3nSGqYSv519HOXjAguFVJ0bzU-ZPcXrkynC2f6zNCEJtnJNxdpQ4'
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

    def test_get_image_size(self):
        link = 'https://www.dropbox.com/s/oqgq76n52u89ho9/db69fb4f-09bb-4327-b7d9-7d6df4ae2eb5.png?raw=1'
        width, height = get_image_size(link)
        self.assertEqual(width, 688)
        self.assertEqual(height, 420)

    def test_resize_base64_image(self):
        with open('base64_image.txt') as f:
            base64_str = f.read()
        img_base64 = base64_str
        new_img = resize_base64_image(img_base64, 300, 300)
        image_str = new_img.split(',')[1]
        image_bin = base64.b64decode(image_str)
        image_res: Image = Image.open(BytesIO(image_bin))
        self.assertEqual(300, image_res.width)
        self.assertEqual(300, image_res.height)

    def test_transf_coords(self):
        spaces = [['WYS_PUESTOTRABAJO_CELL3PERSONAS', 0, 19.069390089952076, 3.554243675398348, 270],
                  ['WYS_PUESTOTRABAJO_CELL3PERSONAS', 0, -18.258312967581613, -7.936893373011155, 90],
                  ['WYS_PUESTOTRABAJO_CELL3PERSONAS', 0, 3.486004799555309, 6.409604623383016, 270],
                  ['WYS_SALAREUNION_RECTA6PERSONAS', 0, -15.589529485663157, 7.474004076229347, 90],
                  ['WYS_SALAREUNION_RECTA6PERSONAS', 0, -9.730322290808159, -1.4475386236755268, 90],
                  ['WYS_COLABORATIVO_BARRA6PERSONAS', 0, 11.261155484545492, -5.727458128298589, 0],
                  ['WYS_COLABORATIVO_MEETINGBOOTH2PERSONAS', 0, -1.4616880975647504, -8.851786132193698, 180]]

        spaces_data, floor_elements = transform_coords(dict_ex, spaces, 'https://wysdev.ac3eplatforms.com/api/spaces', self.token)
        f_width, f_height = get_image_size(dict_ex['selected_floor']['image_link'])
        for data in spaces_data:
            self.assertTrue(data['position_x'] <= f_width)
            self.assertTrue(data['position_y'] <= f_height)


if __name__ == '__main__':
    unittest.main()
