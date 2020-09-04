"""
This module run a microservice called Layout service. This module
manage all logic for wys Layouts

"""

import jwt
import os
import logging
import requests
import json
from sqlalchemy.exc import SQLAlchemyError
from flask import Flask, jsonify, abort, request
from flask_sqlalchemy import SQLAlchemy
from flask_swagger import swagger
from flask_swagger_ui import get_swaggerui_blueprint
from functools import wraps
from sqlalchemy.ext.hybrid import hybrid_property
from flask_cors import CORS
from http import HTTPStatus
from xlrd import open_workbook, XLRDError

# Loading Config Parameters
DB_USER = os.getenv('DB_USER', 'wys')
DB_PASS = os.getenv('DB_PASSWORD', 'rac3e/07')
DB_IP = os.getenv('DB_IP_ADDRESS', '10.2.19.195')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'wys')
APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
APP_PORT = os.getenv('APP_PORT', 5006)

#Buildings module info
BUILDINGS_MODULE_HOST = os.getenv('BUILDINGS_MODULE_HOST', '127.0.0.1')
BUILDINGS_MODULE_PORT = os.getenv('BUILDINGS_MODULE_PORT', 5004)
BUILDINGS_MODULE_API = os.getenv('BUILDINGS_MODULE_API', '/api/buildings/')
BUILDINGS_URL = f"http://{BUILDINGS_MODULE_HOST}:{BUILDINGS_MODULE_PORT}"

#Spaces module info
SPACES_MODULE_HOST = os.getenv('SPACES_MODULE_IP', '127.0.0.1')
SPACES_MODULE_PORT = os.getenv('SPACES_MODULE_PORT', 5002)
SPACES_MODULE_API = os.getenv('SPACES_MODULE_API', '/api/spaces/')
SPACES_URL = f"http://{SPACES_MODULE_HOST}:{SPACES_MODULE_PORT}"

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql://{DB_USER}:{DB_PASS}@{DB_IP}:{DB_PORT}/{DB_SCHEMA}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

try:
    f = open('oauth-public.key', 'r')
    key: str = f.read()
    f.close()
    app.config['SECRET_KEY'] = key
except Exception as e:
    app.logger.error(f'Can\'t read public key f{e}')
    exit(-1)

app.logger.setLevel(logging.DEBUG)
db = SQLAlchemy(app)

class LayoutGenerated(db.Model):
    """
    LayoutGenerated.
    Represents the spaces configured by the user in the layout.

    Attributes
    ----------
    id: Represent the unique id of a Layout Generated
    floor_id: ID of the floor selected by the user.
    workspaces: Spaces selected and positioned by the user in the layout.
    zones : Zones created by the user within the layout.
    """
    id = db.Column(db.Integer, primary_key=True)
    floor_id = db.Column(db.Integer, nullable=False)
    workspaces = db.relationship(
        "LayoutGeneratedWorkspace",
        backref="layout_generated",
        cascade="all, delete, delete-orphan")
    zones = db.relationship(
        "LayoutZone",
        backref="layout_generated",
        cascade="all, delete, delete-orphan")

    def to_dict(self):
        """
        Convert to dictionary
        """

        dict = {
            'id': self.id,
            'floor_id': self.floor_id,
            'workspaces': [workspace.to_dict() for workspace in self.workspaces],
            'zones': [zones.to_dict() for zones in self.zones]
        }
        return dict

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

class LayoutGeneratedWorkspace(db.Model):
    """
    LayoutGeneratedWorkspace.
    Represents the position per space configured by the user 
    or generated. All of this according to the positions in the layout of selected floor.

    Attributes
    ----------
    id: Represent the unique id of a M2 generated
    position_x: X coordinate of the position of the space figure in the layout.
    position_Y: Y coordinate of the position of the space figure in the layout.
    rotation: Direction of rotation of space.
    space_id: Foreign key of associated space.
    layout_gen_id: Foreign key of associated layout generated.
    """

    id = db.Column(db.Integer, primary_key=True)
    position_x = db.Column(db.Float, nullable=False)
    position_y =  db.Column(db.Float, nullable=False)
    rotation = db.Column(db.String(20), nullable=False)
    space_id = db.Column(db.Integer, nullable=False)
    layout_gen_id = db.Column(db.Integer, db.ForeignKey(
        'layout_generated.id'), nullable=False)

    def to_dict(self):
        """
        Convert to dictionary
        """

        dict = {
            'id': self.id,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'rotation': self.rotation,
            'space_id': self.space_id,
            'layout_gen_id': self.layout_gen_id
        }
        return dict

    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

class LayoutZone(db.Model):
    """
    LayoutZone.
    Represent the Zone created by the user within the layout.

    Attributes
    ----------
    id: Represent the unique id of a Zone.
    name: Name of a Zone.
    color: Name of region where the Zone are located
    position_x: X coordinate of the position of the space figure in the layout.
    position_Y: Y coordinate of the position of the space figure in the layout.
    height: Height of the created Zone by the user.
    width: Width of the created Zone by the user.
    layout_gen_id: ID of the Layout Generated associated.
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    position_x = db.Column(db.Float, nullable=False)
    position_y =  db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    layout_gen_id = db.Column(db.Integer, db.ForeignKey(
        'layout_generated.id'), nullable=False)
 
    def to_dict(self):
        """
        Convert to dictionary
        """

        obj_dict = {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'height': self.height,
            'width': self.width,
            'layout_gen_id': self.layout_gen_id
        }

        return obj_dict
    
    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())

db.create_all() # Create all tables

# Swagger Config

SWAGGER_URL = '/api/layouts/docs/'
API_URL = '/api/layouts/spec'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={  # Swagger UI config overrides
        'app_name': "WYS API - Layout Service"
    }
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

def get_space_by_id(space_id, token):
    headers = {'Authorization': token}
    api_url = SPACES_URL + SPACES_MODULE_API + str(space_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the spaces module")
    return None

def get_floor_polygons_by_ids(building_id, floor_id, token):
    headers = {'Authorization': token}
    api_url = BUILDINGS_URL + BUILDINGS_MODULE_API + str(building_id) + '/floors/'+ str(floor_id) + '/polygons'
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
      raise Exception("Cannot connect to the buildings module")
    return None

def token_required(f):
    @wraps(f)
    def decorator(*args, **kwargs):

        bearer_token = request.headers.get('Authorization', None)
        try:
            token = bearer_token.split(" ")[1]
        except Exception as ierr:
            app.logger.error(ierr)
            return jsonify({'message': 'a valid bearer token is missing'}), 500

        if not token:
            app.logger.debug("token_required")
            return jsonify({'message': 'a valid token is missing'})

        app.logger.debug("Token: " + token)
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'],
                              algorithms=['RS256'], audience="1")
            user_id: int = data['user_id']
            request.environ['user_id'] = user_id
        except Exception as err:
            return jsonify({'message': 'token is invalid', 'error': err})
        except KeyError as kerr:
            return jsonify({'message': 'Can\'t find user_id in token', 'error': kerr})

        return f(*args, **kwargs)

    return decorator

@app.route("/api/layouts/spec", methods=['GET'])
@token_required
def spec():
    swag = swagger(app)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "WYS Layout API Service"
    swag['tags'] = [{
        "name": "Layouts",
        "description": "Methods to configure layouts"
    }]
    return jsonify(swag)

@app.route("/api/layout/<project_id>", methods=['POST'])
@token_required
def generate_layout(project_id):
    """
        Return the information necessary to find floors
        ---
        consumes:
        - "application/json"
        tags:
        - Layouts
        produces:
        - application/json
        parameters:
        - in: path
          name: project_id
          type: integer
          description: Project ID
        - in: "body"
          name: "body"
          required:
          - selected_floor
          - workspaces
          properties:
            selected_floor:
                type: object
                description: Data of the floor selected by the user.
                properties:
                    id:
                        type: integer
                        description: Unique ID of each building floor.
                    wys_id:
                        type: string
                        description: Unique internal ID of each building floor.
                    rent_value:
                        type: number
                        format: float
                        description: Rent value of the floor
                    m2:
                        type: number
                        format: float
                        description: Square meter value of the floor.
                    elevators_number:
                        type: integer
                        description: Numbers of elevators in the floor.
                    image_link:
                        type: string
                        description: Link of the floor image.
            workspaces:
                type: array
                items:
                    type: object
                    properties:
                        id:
                            type: integer
                            description: Unique ID of each space.
                        quantity:
                            type: integer
                            description: Quantity of the space
                        name:
                            type: string
                            description: Name of the space
                        model_2d:
                            type: string
                            description: Base64 file
                        model_3d:
                            type: string
                            description: Base64 file
                        height:
                            type: number
                            description: Height of the space
                        width:
                            type: number
                            description: width of the space
                        active:
                            type: boolean
                            description: indicate if this space is active
                        regular:
                            type: boolean
                            description: indicate if this space is a regular space
                        up_gap:
                            type: number
                            description: up padding
                        down_gap:
                            type: number
                            description: down padding
                        left_gap:
                            type: number
                            description: left padding
                        right_gap:
                            type: number
                            description: right padding
                        subcategory_id:
                            type: integer
                            description: subcategory Id
                        points:
                            type: array
                            items:
                                type: object
                                properties:
                                    x:
                                        type: number
                                        format: float
                                        description: X coordinate of the vertex/point.
                                    y:
                                        type: number
                                        format: float
                                        description: Y coordinate of the vertex/point.
        responses:
            200:
                description: Return Countries, Zones, Regions
            500:
                description: Internal Error Server
    """
    try:
        params = {'selected_floor', 'workspaces'}
        if request.json.keys() != params:
            return "A required field is missing in the body", 400

        floor = request.json['selected_floor']
        floor_params = {'id', 'wys_id','rent_value','m2','elevators_number','image_link','active','building_id'}
        if floor.keys() != floor_params:
             return "A floor data field is missing in the body", 400

        workspaces = request.json['workspaces']

        if len(workspaces) == 0:
            return "No spaces were entered in the body.", 400
        workspace_params = {'id','quantity','name','model_2d','model_3d','height','width','active','regular','up_gap','down_gap','left_gap','right_gap','subcategory_id','points'}
        for workspace in workspaces:
            if workspace.keys() != workspace_params:
             return "A space data field is missing in the body", 400

        token = request.headers.get('Authorization', None)
        floor_polygons = get_floor_polygons_by_ids(floor['building_id'], floor['id'], token)
        if floor_polygons is None:
            return "The floor doesn't exist or not have a polygons.", 404
        floor['polygons'] = floor_polygons
        layout_data = {'selected_floor': floor, 'workspaces': workspaces}
        
        return jsonify(layout_data), 201
    except SQLAlchemyError as e:
        db.session.rollback()
        return f'Error saving data: {e}', 500
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


if __name__ == '__main__':
  app.run(host = APP_HOST, port = APP_PORT, debug = True)