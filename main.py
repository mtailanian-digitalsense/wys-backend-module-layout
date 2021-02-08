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
from mockup_layout import layout
from Layout_App.SmartLayout import Smart_Layout, smart_layout_async
from lib import transform_coords, resize_base64_image, get_floor_elements_p
from rq.job import Job
from redis_resc import redis_conn, redis_queue

# Loading Config Parameters
DB_USER = os.getenv('DB_USER', 'wys')
DB_PASS = os.getenv('DB_PASSWORD', 'rac3e/07')
DB_IP = os.getenv('DB_IP_ADDRESS', '10.2.19.195')
DB_PORT = os.getenv('DB_PORT', '3307')
DB_SCHEMA = os.getenv('DB_SCHEMA', 'wys')
APP_HOST = os.getenv('APP_HOST', '127.0.0.1')
APP_PORT = os.getenv('APP_PORT', 5006)

# Buildings module info
BUILDINGS_MODULE_HOST = os.getenv('BUILDINGS_MODULE_HOST', '127.0.0.1')
BUILDINGS_MODULE_PORT = os.getenv('BUILDINGS_MODULE_PORT', 5004)
BUILDINGS_MODULE_API = os.getenv('BUILDINGS_MODULE_API', '/api/buildings/')
BUILDINGS_URL = f"http://{BUILDINGS_MODULE_HOST}:{BUILDINGS_MODULE_PORT}"

# Spaces module info
SPACES_MODULE_HOST = os.getenv('SPACES_MODULE_IP', '127.0.0.1')
SPACES_MODULE_PORT = os.getenv('SPACES_MODULE_PORT', 5002)
SPACES_MODULE_API = os.getenv('SPACES_MODULE_API', '/api/spaces/')
SPACES_URL = f"http://{SPACES_MODULE_HOST}:{SPACES_MODULE_PORT}"

# Projects module info
PROJECTS_MODULE_HOST = os.getenv('PROJECTS_MODULE_HOST', '127.0.0.1')
PROJECTS_MODULE_PORT = os.getenv('PROJECTS_MODULE_PORT', 5000)
PROJECTS_MODULE_API = os.getenv('PROJECTS_MODULE_API', '/api/projects/')
PROJECTS_URL = f"http://{PROJECTS_MODULE_HOST}:{PROJECTS_MODULE_PORT}"

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
    building_id = db.Column(db.Integer, nullable=False)
    project_id = db.Column(db.Integer, nullable=False)
    workspaces = db.relationship(
        "LayoutGeneratedWorkspace",
        backref="layout_generated",
        cascade="all, delete, delete-orphan")

    def to_dict(self):
        """
        Convert to dictionary
        """

        dict = {
            'id': self.id,
            'building_id': self.building_id,
            'floor_id': self.floor_id,
            'workspaces': [workspace.to_dict() for workspace in self.workspaces]
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
    height: Height size of the space image in px.
    width: Width size of the space image in px.
    rotation: Direction of rotation of space.
    space_id: Foreign key of associated space.
    layout_gen_id: Foreign key of associated layout generated.
    """

    id = db.Column(db.Integer, primary_key=True)
    position_x = db.Column(db.Float, nullable=False)
    position_y =  db.Column(db.Float, nullable=False)
    height = db.Column(db.Float, nullable=False)
    width = db.Column(db.Float, nullable=False)
    rotation = db.Column(db.String(20))
    space_id = db.Column(db.Integer, nullable=False)
    layout_gen_id = db.Column(db.Integer, db.ForeignKey(
        'layout_generated.id'), nullable=False)
    layout_zone_id = db.Column(db.Integer, db.ForeignKey(
        'layout_zone.id'), nullable=True)

    def to_dict(self):
        """
        Convert to dictionary
        """

        dict = {
            'id': self.id,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'rotation': self.rotation,
            'height': self.height,
            'width': self.width,
            'space_id': self.space_id,
            'layout_gen_id': self.layout_gen_id,
            'layout_zone_id': self.layout_zone_id
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
    spaces_gen: List of spaces associated with this zone
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(45), nullable=False)
    color = db.Column(db.String(20), nullable=False)
    spaces_gen = db.relationship(
        "LayoutGeneratedWorkspace",
        backref="layout_zone",
        cascade="all, delete")

    def to_dict(self):
        """
        Convert to dictionary
        """
        space: LayoutGeneratedWorkspace
        obj_dict = {
            'id': self.id,
            'name': self.name,
            'color': self.color,
            'spaces_gen': [space.to_dict() for space in self.spaces_gen]
        }

        return obj_dict
    
    def serialize(self):
        """
        Serialize to json
        """
        return jsonify(self.to_dict())


class LayoutConfig(db.Model):
    """
    LayoutConfig.
    Represents the configuration model of parameters setted for the Smart Layout

    Attributes
    ----------
    id: Represent the unique id of a layout config.
    pop_size: Value of pop size.
    generations: Value of number of generations.
    """

    id = db.Column(db.Integer, primary_key=True)
    pop_size = db.Column(db.Integer, nullable=False)
    generations = db.Column(db.Integer, nullable=False)

    def to_dict(self):
        """
        Convert to dictionary
        """

        obj_dict = {
            'id': self.id,
            'pop_size': self.pop_size,
            'generations': self.generations
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


def get_project_by_id(project_id, token):
    headers = {'Authorization': token}
    api_url = PROJECTS_URL + PROJECTS_MODULE_API + str(project_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
        raise Exception("Cannot connect to the projects module")
    return None


def update_project_by_id(project_id, data, token):
    headers = {'Authorization': token}
    api_url = PROJECTS_URL + PROJECTS_MODULE_API + str(project_id)
    rv = requests.put(api_url, json=data, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
        raise Exception("Cannot connect to the projects module")
    return None


def get_space_by_id(space_id, token):
    headers = {'Authorization': token}
    api_url = SPACES_URL + SPACES_MODULE_API + str(space_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
        raise Exception("Cannot connect to the spaces module")
    return None


def get_floor_by_ids(building_id, floor_id, token):
    headers = {'Authorization': token}
    api_url = BUILDINGS_URL + BUILDINGS_MODULE_API + str(building_id) + '/floors/'+ str(floor_id)
    rv = requests.get(api_url, headers=headers)
    if rv.status_code == 200:
        return json.loads(rv.text)
    elif rv.status_code == 500:
        raise Exception("Cannot connect to the buildings module")
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


def get_subcategories(token):
    headers = {'Authorization': token}
    api_url = SPACES_URL + SPACES_MODULE_API + 'subcategories'
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


@app.route('/api/layouts/data/<layout_gen_id>', methods = ['GET'])
@token_required
def get_layout_by_layout_gen_id(layout_gen_id):
    """
        Get if there's complete the layout module, by finding a record from Project table.
        ---
        parameters:
          - in: path
            name: layout_gen_id
            type: integer
            description: Layout Gen Id
        tags:
        - "Layouts"
        responses:
          200:
            description: "completed" if there's a record
          404:
            description: Record Not Found.
          500:
            description: "Database error"
    """
    try:
        token = request.headers.get('Authorization', None)
        print(layout_gen_id)
        layout_generated = LayoutGenerated.query.filter_by(id=layout_gen_id).first()
        if layout_generated is not None:
          return jsonify({'layout': 'completed'}), 200
        else:
          return jsonify({'layout': ''}), 200
    except SQLAlchemyError as e:
      return f'Error getting data: {e}', 500
    except Exception as exp:
      msg = f"Error: mesg ->{exp}"
      app.logger.error(msg)
      return msg, 404


@app.route("/api/layouts/<project_id>", methods=['POST'])
@token_required
def generate_layout(project_id):
    """
        Generates the smart layout according to the floor and workspaces selected by the user in the current project.
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
                    active:
                        type: boolean
                        description: indicate if this floor is active.
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
                    building_id:
                        type: integer
                        description: Unique ID of each building associated to this floor.
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
            201:
                description: Return the Layout object data generated by the Smart Layout
            400:
                description: Data or missing field in body.
            404:
                description: Data object not found.
            500:
                description: Internal server error.
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
        workspace_params = {'id','quantity','name','height','width','active','regular','up_gap','down_gap','left_gap','right_gap','subcategory_id','points'}
        token = request.headers.get('Authorization', None)
        subcategories = get_subcategories(token)
        for workspace in workspaces:
            if workspace.keys() != workspace_params:
                return "A space data field is missing in the body", 400
            found = False
            for category in subcategories:
                for subcategory in category['subcategories']:
                    if subcategory['id'] == workspace['subcategory_id']:
                        workspace['category_id'] = category['id']
                        found = True
                        break
                if found:
                    break
            if not found:
                return "A Space subcategory doesn't exist", 404
        project = get_project_by_id(project_id, token)
        if project is None:
            return "The project doesn't exist", 404
        floor_polygons = get_floor_polygons_by_ids(floor['building_id'], floor['id'], token)
        if floor_polygons is None or len(floor_polygons) == 0:
            return "The floor doesn't exist or not have a polygons.", 404
        floor['polygons'] = floor_polygons
        config = LayoutConfig.query.order_by(LayoutConfig.id.desc()).first()
        layout_data = {'selected_floor': floor, 'workspaces': workspaces}

        layout_workspaces = Smart_Layout(layout_data, config.pop_size if config is not None else 50, config.generations if config is not None else 50)
        workspaces_coords, floor_elements = transform_coords(layout_data, layout_workspaces, SPACES_URL+SPACES_MODULE_API, token)

        layout_gen = LayoutGenerated.query.filter_by(project_id=project_id).first()
        if layout_gen is not None:
            db.session.delete(layout_gen)
            db.session.commit()
        layout_gen = LayoutGenerated()
        layout_gen.floor_id = floor['id']
        layout_gen.building_id = floor['building_id']
        layout_gen.project_id = project_id
        for l_workspace in workspaces_coords:
            layout_gen_workspace = LayoutGeneratedWorkspace()
            for key, value in l_workspace.items():
                setattr(layout_gen_workspace, key, value)
            layout_gen.workspaces.append(layout_gen_workspace)
        db.session.add(layout_gen)
        db.session.commit()
        project = update_project_by_id(project_id, {'layout_gen_id': layout_gen.id}, token)
        if project is None:
            return "The project could not be updated.", 404

        layout_gen = layout_gen.to_dict()
        del floor['polygons']
        layout_gen['selected_floor'] = floor
        for wk in layout_gen['workspaces']:
            wk['image'] = next((space['image'] for space in workspaces_coords if space["space_id"] == wk["space_id"]), None)

        layout_gen['floor_elements'] = floor_elements

        return jsonify(layout_gen), 201

    except SQLAlchemyError as e:
        msg = f'Error saving data: {e}'
        app.logger.error(msg)
        return msg, 500
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/<project_id>", methods=['GET'])
@token_required
def get_layout_by_project(project_id):
    """
        Get latest configuration of the layout made by the user for the current project.
        ---
        parameters:
          - in: path
            name: project_id
            type: integer
            description: Project ID
        tags:
        - Layouts
        responses:
          200:
            description: Layout data Object.
          404:
            description: Project Not Found or the Proyect doesn't have a Layout created.
          500:
            description: "Database error"
    """
    try:
        token = request.headers.get('Authorization', None)
        project = get_project_by_id(project_id, token)
        if project is None:
            return "The project doesn't exist", 404
        layout_gen = LayoutGenerated.query.get(project['layout_gen_id'])
        if layout_gen is None:
            return "The project doesn't have a layout created", 404

        layout_gen = layout_gen.to_dict()
        floor = get_floor_by_ids(layout_gen['building_id'], layout_gen['floor_id'], token)
        if floor is None:
            return "A layout floor doesn't exist", 404

        floor_polygons = get_floor_polygons_by_ids(floor['building_id'], floor['id'], token)
        if floor_polygons is None or len(floor_polygons) == 0:
            return "The floor doesn't exist or not have a polygons.", 404
        floor['polygons'] = floor_polygons

        floor_elements = get_floor_elements_p({'selected_floor': floor})

        layout_gen['floor_elements']  = floor_elements
        
        del floor['polygons']

        layout_gen['selected_floor'] = floor
        
        for wk in layout_gen['workspaces']:
            space = get_space_by_id(wk['space_id'], token)
            if space is None:
                return "A layout space doesn't exist", 404
            image = resize_base64_image(space['model_2d'], wk['width'], wk['height'])
            wk['image'] = image

        return jsonify(layout_gen), 200
    except SQLAlchemyError as e:
        msg = f'Error saving data: {e}'
        app.logger.error(msg)
        return msg, 500
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/<project_id>", methods=['PUT'])
@token_required
def update_layout_by_project(project_id):
    """
        Updates the configuration of the spaces in the layout made by the user in the current project.
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
          required: true
          schema:
            type: array
            items:
                type: object
                properties:
                    id:
                        type: integer
                        description: Unique ID of each layout workspace.
                    space_id:
                        type: integer
                        description: Unique ID of each space.
                    rotation:
                        type: string
                        description: Rotation of the space in layout.
                    height:
                        type: number
                        format: float
                        description: Height size of the space image in px.
                    width:
                        type: number
                        format: float
                        description: Width size of the space image in px.
                    position_x:
                        type: number
                        format: float
                        description: X coordinate of the space position in layout.
                    position_y:
                        type: number
                        format: float
                        description: Y coordinate of the space position in layout.
        responses:
            200:
                description: Layout data Object updated.
            400:
                description: Data or missing field in body.
            404:
                description: Data object not found.
            500:
                description: Internal Error Server
    """
    try:
        params = {'id', 'space_id', 'rotation','height','width', 'position_x', 'position_y'}
        if not request.json:
            return "The body isn\'t application/json", 400
        elif any(workspace.keys() != params for workspace in request.json):
            return "A required field is missing in worskpaces data", 400
        elif len(request.json) == 0:
            return 'Body data required', 400
        token = request.headers.get('Authorization', None)
        project = get_project_by_id(project_id, token)
        if project is None:
            return "The project doesn't exist", 404
        layout_gen = LayoutGenerated.query.get(project['layout_gen_id'])
        if layout_gen is None:
            return "The project doesn't have a layout created", 404
        for data in request.json:
            workspace = LayoutGeneratedWorkspace.query.filter_by(id=data['id'], layout_gen_id=layout_gen.id).first()
            if workspace is not None:
                for key, value in data.items():
                    setattr(workspace, key, value)
            else:
                workspace = LayoutGeneratedWorkspace(**data)
                layout_gen.workspaces.append(workspace)
                db.session.add(workspace)
            db.session.commit()
        
        return layout_gen.serialize(), 200
    except SQLAlchemyError as e:
        msg = f'Error saving data: {e}'
        app.logger.error(msg)
        return msg, 500
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/configs", methods=['GET'])
@token_required
def get_layout_config():
    """
        Get latest configuration for the Smart Layout (parameters values).
        ---
        tags:
        - Layouts/configs
        responses:
            200:
                description: Layout Config data Object.
            404:
                description: Layout Config data has not been created.
            500:
                description: "Database error"
    """
    try:
        config = LayoutConfig.query.order_by(LayoutConfig.id.desc()).first()
        if config is None:
            return "Layout Config data has not been created.", 404
        return config.serialize(), 200
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/configs", methods=['PUT'])
@token_required
def update_layout_config():
    """
        Update (or Create) the latest configuration for the Smart Layout (parameters values greater than 25).
        ---
        tags:
        - Layouts/configs
        parameters:
        - in: "body"
          name: "body"
          required:
          - pop_size
          - generations
          properties:
            pop_size:
                type: integer
                description: Value of pop size.
            generations:
                type: integer
                description: Value of number of generations.
        responses:
            200:
                description: Layout Config data Object.
            400:
                description: Data or missing field in body.
            500:
                description: "Database error"
    """
    try:
        params = {'pop_size', 'generations'}
        if not request.json:
            return "The body isn\'t application/json", 400
        elif request.json.keys() != params:
            return "A required field is missing in worskpaces data", 400
        elif request.json['pop_size'] < 25 or request.json['generations'] < 25:
            return 'The values must be greater than 25', 400

        config = LayoutConfig.query.order_by(LayoutConfig.id.desc()).first()
        if config is None:
            config = LayoutConfig()
            db.session.add(config)
        config.pop_size = request.json['pop_size']
        config.generations = request.json['generations']
        db.session.commit()

        return config.serialize(), 200
    except SQLAlchemyError as e:
        msg = f'Error saving data: {e}'
        app.logger.error(msg)
        return msg, 500
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/v2", methods=['POST'])
@token_required
def generate_layout_async():
    """
        Generates the smart layout according to the floor and workspaces selected by the user in the
        current project async
        ---
        consumes:
        - "application/json"
        tags:
        - Layouts
        produces:
        - application/json
        parameters:
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
                    active:
                        type: boolean
                        description: indicate if this floor is active.
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
                    building_id:
                        type: integer
                        description: Unique ID of each building associated to this floor.
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
            201:
                description: Return the task id generated by the Smart Layout
            400:
                description: Data or missing field in body.
            404:
                description: Data object not found.
            500:
                description: Internal server error.
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
        workspace_params = {'id','quantity','name','height','width','active','regular','up_gap','down_gap','left_gap','right_gap','subcategory_id','points'}
        token = request.headers.get('Authorization', None)
        subcategories = get_subcategories(token)
        for workspace in workspaces:
            if workspace.keys() != workspace_params:
                return "A space data field is missing in the body", 400
            found = False
            for category in subcategories:
                for subcategory in category['subcategories']:
                    if subcategory['id'] == workspace['subcategory_id']:
                        workspace['category_id'] = category['id']
                        found = True
                        break
                if found:
                    break
            if not found:
                return "A Space subcategory doesn't exist", 404

        floor_polygons = get_floor_polygons_by_ids(floor['building_id'], floor['id'], token)
        if floor_polygons is None or len(floor_polygons) == 0:
            return "The floor doesn't exist or not have a polygons.", 404
        floor['polygons'] = floor_polygons
        layout_data = {'selected_floor': floor, 'workspaces': workspaces}
        config = LayoutConfig.query.order_by(LayoutConfig.id.desc()).first()
        job = redis_queue.enqueue(smart_layout_async,
                                  args=(layout_data, config.pop_size, config.generations),
                                  job_timeout=7200)
        return jsonify({'job_id': job.id}), 201

    except SQLAlchemyError as e:
        msg = f'Error saving data: {e}'
        app.logger.error(msg)
        abort(500, description=msg)
    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/v2/job/<job_id>", methods=['GET'])
@token_required
def check_job(job_id):
    """
        Takes a job_id and checks its status in redis queue.
        ---
        consumes:
        - "application/json"
        tags:
        - Layouts
        produces:
        - application/json

        parameters:
        - in: path
          name: job_id
          type: string
          description: Job ID
    """

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as exception:
        abort(404, description=exception)

    job.refresh()

    progress = 0.0

    if "progress" in job.meta:
        progress = job.meta["progress"]

    if job.get_status() == "finished":
        progress = 100.0

    return jsonify({"job_id": job.id,
                    "job_status": job.get_status(),
                    "progress":  progress})


@app.route("/api/layouts/v2/job", methods=['POST'])
@token_required
def get_layout():
    """
        Takes a job_id and returns the job's result.
        ---
        consumes:
        - "application/json"
        tags:
        - Layouts
        produces:
        - application/json

        parameters:
        - in: "body"
          name: "body"
          required:
          - job_id
          - project_id
          properties:
            job_id:
                type: string
                description: Resultant Job ID.
            project_id:
                type: integer
                description: Project ID of the project that you want to assign the final layout
        responses:
            201:
                description: Return the final layout
            404:
                description: Job not found. The job doesn't exist or isn't ready.


    """
    req_params = ["project_id", "job_id"]
    for param in req_params:
        if param not in request.json.keys():
            abort(400, description=f"{param} isn't in body")

    job_id = request.json["job_id"]
    project_id = request.json["project_id"]

    try:
        job = Job.fetch(job_id, connection=redis_conn)
    except Exception as exception:
        abort(500, description=exception)

    if not job.result:
        abort(
            404,
            description=f"No result found for job_id {job.id}. Try checking the job's status.",
        )
    try:
        token = request.headers.get('Authorization', None)
        project = get_project_by_id(project_id, token)
        if project is None:
            return "The project doesn't exist", 404

        layout_workspaces, layout_data = job.result
        workspaces_coords, floor_elements = transform_coords(layout_data, layout_workspaces, SPACES_URL + SPACES_MODULE_API, token)

        floor = layout_data['selected_floor']

        layout_gen = LayoutGenerated.query.filter_by(project_id=project_id).first()
        if layout_gen is not None:
            db.session.delete(layout_gen)
            db.session.commit()
        layout_gen = LayoutGenerated()
        layout_gen.floor_id = floor['id']
        layout_gen.building_id = floor['building_id']
        layout_gen.project_id = project_id
        for l_workspace in workspaces_coords:
            layout_gen_workspace = LayoutGeneratedWorkspace()
            for key, value in l_workspace.items():
                setattr(layout_gen_workspace, key, value)
            layout_gen.workspaces.append(layout_gen_workspace)
        db.session.add(layout_gen)
        db.session.commit()
        project = update_project_by_id(project_id, {'layout_gen_id': layout_gen.id}, token)
        if project is None:
            return "The project could not be updated.", 404

        layout_gen = layout_gen.to_dict()
        del floor['polygons']
        layout_gen['selected_floor'] = floor
        for wk in layout_gen['workspaces']:
            wk['image'] = next((space['image'] for space in workspaces_coords if space["space_id"] == wk["space_id"]),
                               None)
                               
        layout_gen['floor_elements'] = floor_elements

        return jsonify(layout_gen), 201

    except SQLAlchemyError as e:
        msg = f'Error saving data: {e}'
        app.logger.error(msg)
        return msg, 500

    except Exception as exp:
        msg = f"Error: mesg ->{exp}"
        app.logger.error(msg)
        return msg, 500


@app.route("/api/layouts/zones", methods=['POST'])
@token_required
def create_zones():
    """
    Create Zones
    ---

    consumes:
    - "application/json"
    tags:
    - Zones
    produces:
    - application/json

    parameters:
    - in: "body"
      name: "body"
      required:
      - spaces_id
      - name
      - color
      properties:
        name:
            type: string
            description: Zone's name
        color:
            type: string
            description: RGB color code.
        w_spaces_id:
            type: array
            items:
                type: number
            description: Spaces id
    responses:
            201:
                description: Return the final layout
            404:
                description: Job not found. The job doesn't exist or isn't ready.
    """

    req_params = ['w_spaces_id', 'name', 'color']
    for param in req_params:
        if param not in request.json.keys():
            abort(400, description=f"{param} isn't in body")

    w_spaces_id: [] = request.json["w_spaces_id"]
    name: str = request.json["name"]
    color: str = request.json["color"]

    zone = LayoutZone()
    zone.name = name
    zone.color = color

    try:
        for w_space_id in w_spaces_id:
            w_space = db.session.query(LayoutGeneratedWorkspace).filter_by(id=w_space_id).first()
            if w_space is not None:
                zone.spaces_gen.append(w_space)


        db.session.add(zone)
        db.session.commit()

        return jsonify(zone.to_dict()), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f'Error saving data: {e}')
        abort(500, description=f'Error saving data: {e}')

    except Exception as e:
        abort(500, description=f'Error saving data: {e}')


@app.route("/api/layouts/zones/<zone_id>", methods=['PUT'])
@token_required
def updated_zone(zone_id: int):
    """
        Update Zones
        ---

        consumes:
        - "application/json"
        tags:
        - Zones
        produces:
        - application/json

        parameters:
        - in: path
          name: zone_id
          type: integer
          description: zone id
        - in: "body"
          name: "body"
          required:
          - spaces_id
          - name
          - color
          properties:
            name:
                type: string
                description: Zone's name
            color:
                type: string
                description: RGB color code.
            w_spaces_id:
                type: array
                items:
                    type: number
                description: Spaces id
        responses:
                200:
                    description: Updated

    """
    try:
        zone: LayoutZone = db.session.query(LayoutZone).filter_by(id=zone_id).first()
        if zone is None:
            abort(404, description='Layout Zone not found')

        req_params = ['w_spaces_id', 'name', 'color']
        for param in req_params:
            if param not in request.json.keys():
                abort(400, description=f"{param} isn't in body")

        # Empty w_spaces in zone
        zone.spaces_gen.clear()
        db.session.commit()

        # Add new w_spaces
        for w_space_id in request.json["w_spaces_id"]:
            w_space = db.session.query(LayoutGeneratedWorkspace).filter_by(id=w_space_id).first()
            if w_space is not None:
                zone.spaces_gen.append(w_space)
        # Update name
        zone.name = request.json["name"]
        # Update color
        zone.color = request.json["color"]
        db.session.commit()
        return jsonify(zone.to_dict())

    except SQLAlchemyError as e:
        db.session.rollback()
        abort(500, description=f'Database error: {e}')


@app.route("/api/layouts/zones/<zone_id>", methods=['DELETE'])
@token_required
def delete_zone(zone_id: int):
    """
        Update Zones
        ---

        consumes:
        - "application/json"
        tags:
        - Zones
        produces:
        - application/json

        parameters:
        - in: path
          name: zone_id
          type: integer
          description: zone id
        responses:
            204:
                description: Deleted
            500:
                description: Internal Error
    """
    try:
        # Verify inputs
        zone: LayoutZone = db.session.query(LayoutZone).filter_by(id=zone_id).first()
        if zone is None:
            return jsonify({'error': 'Zone Not Found'}), 404

        # Get w_spaces_ids for detach it from LayoutZone
        zone.spaces_gen.clear()

        # Delete Zone
        db.session.delete(zone)
        db.session.commit()
        return "", 204

    except SQLAlchemyError as e:
        db.session.rollback()
        logging.error(f'Database error: {e}')
        abort(500, description=f'Database error: {e}')

    except Exception as e:
        logging.error(f'Internal error: {e}')
        abort(500, description=f'Internal error: {e}')


@app.route("/api/layouts/zones/<zone_id>", methods=['GET'])
@token_required
def get_zone(zone_id: int):
    """
        Get Zones
        ---

        consumes:
        - "application/json"
        tags:
        - Zones
        produces:
        - application/json

        parameters:
        - in: path
          name: zone_id
          type: integer
          description: zone id
        responses:
            200:
                description: OK
            500:
                description: Internal Error
            404:
                description: Not Found
        """
    # Verify params
    try:
        zone: LayoutZone = db.session.query(LayoutZone).filter_by(id=zone_id).first()
        if zone is None:
            return jsonify({'error': 'Zone Not Found'}), 404

        # Return
        return zone.serialize()

    except SQLAlchemyError as e:
        logging.error(f'Database error: {e}')
        abort(500, description=f'Database error: {e}')

    except Exception as e:
        logging.error(f'Internal error: {e}')
        abort(500, description=f'Internal error: {e}')


@app.route("/api/layouts/zones", methods=['GET'])
@token_required
def get_all_zones():
    """
        Get All Zones
        ---

        consumes:
        - "application/json"
        tags:
        - Zones
        produces:
        - application/json

        responses:
            200:
                description: OK
            500:
                description: Internal Error
    """
    try:
        # Get all zones from db
        zones = LayoutZone.query.all()

        zone: LayoutZone
        # Return all zones as a list
        return jsonify([zone.to_dict() for zone in zones])

    except SQLAlchemyError as e:
        logging.error(f'Database error: {e}')
        abort(500, description=f'Database error: {e}')

    except Exception as e:
        logging.error(f'Internal error: {e}')
        abort(500, description=f'Internal error: {e}')


if __name__ == '__main__':
    app.run(host=APP_HOST, port=APP_PORT, debug=True)
