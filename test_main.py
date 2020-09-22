import unittest
import os
import json
import jwt
import random
import pprint
from io import BytesIO
from main import LayoutGenerated, LayoutGeneratedWorkspace, LayoutZone, LayoutConfig, app, db

class LayoutTest(unittest.TestCase):
    def setUp(self):
        db.session.remove()
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + \
        os.path.join('.', 'test.db')
        self.app = app.test_client()
        f = open('oauth-private.key', 'r')
        self.key = f.read()
        f.close()

        db.create_all()
        #Mock layout creation
        config = LayoutConfig(pop_size=50, generations=50)
        db.session.add(config)
        
        db.session.commit()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    @staticmethod
    def build_token(key, user_id=1):
        payload = {
            "aud": "1",
            "jti": "450ca670aff83b220d8fd58d9584365614fceaf210c8db2cf4754864318b5a398cf625071993680d",
            "iat": 1592309117,
            "nbf": 1592309117,
            "exp": 1624225038,
            "sub": "23",
            "user_id": user_id,
            "scopes": [],
            "uid": 23
        }
        return ('Bearer ' + jwt.encode(payload, key, algorithm='RS256').decode('utf-8')).encode('utf-8')

    def test_get_layout_config(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            rv = client.get('/api/layouts/configs')
            resp_dict = json.loads(rv.data.decode("utf-8"))
            self.assertEqual(rv.status_code, 200)
    
    def test_update_layout_config(self):
        with app.test_client() as client:
            client.environ_base['HTTP_AUTHORIZATION'] = self.build_token(self.key)
            sent = {'pop_size': 50, 'generations': 70}
            rv = client.put('/api/layouts/configs', data = json.dumps(sent), content_type='application/json')
            self.assertEqual(rv.status_code, 200)
            resp_dict = json.loads(rv.data.decode("utf-8"))
            self.assertEqual(sent['pop_size'], resp_dict['pop_size'])
            self.assertEqual(sent['generations'], resp_dict['generations'])
            sent = {'pop_size': 10, 'generations': 70}
            rv = client.put('/api/layouts/configs', data = json.dumps(sent), content_type='application/json')
            self.assertEqual(rv.status_code, 400)

if __name__ == '__main__':
    unittest.main()