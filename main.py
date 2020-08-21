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
BUILDINGS_MODULE_HOST = os.getenv('BUILDINGS_MODULE_HOST', '127.0.0.1')
BUILDINGS_MODULE_PORT = os.getenv('BUILDINGS_MODULE_PORT', 5004)
BUILDINGS_MODULE_API_LOCS = os.getenv('BUILDINGS_MODULE_API_LOCS_GET', '/api/buildings/locations/')
SPACES_MODULE_HOST = os.getenv('SPACES_MODULE_IP', '127.0.0.1')
SPACES_MODULE_PORT = os.getenv('SPACES_MODULE_PORT', 5002)
SPACES_MODULE_API_CREATE = os.getenv('SPACES_MODULE_API_CREATE', '/api/spaces/create')
PROJECTS_MODULE_HOST = os.getenv('PROJECTS_MODULE_HOST', '127.0.0.1')
PROJECTS_MODULE_PORT = os.getenv('PROJECTS_MODULE_PORT', 5000)
PROJECTS_MODULE_API = os.getenv('PROJECTS_MODULE_API', '/api/projects/')
PROJECTS_URL = f"http://{PROJECTS_MODULE_HOST}:{PROJECTS_MODULE_PORT}"
SPACES_URL = f"http://{SPACES_MODULE_HOST}:{SPACES_MODULE_PORT}"
BUILDINGS_URL = f"http://{BUILDINGS_MODULE_HOST}:{BUILDINGS_MODULE_PORT}"

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

if __name__ == '__main__':
  app.run(host = APP_HOST, port = APP_PORT, debug = True)