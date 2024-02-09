#  from util import *

from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import syslog
import subprocess

import uuid
import hashlib
from functools import wraps
import jwt
import daemon

from flasgger import Swagger
from flasgger import swag_from


#  from flasgger import Swagger,swag_from

from dotenv import dotenv_values

app = Flask(__name__)
swagger = Swagger(app)
#  app.config['SECRET_KEY'] = str(uuid.uuid4())


@swag_from("./documentation/sensing_interval.yaml")
@app.route("/system/processor", methods=['POST'])
def update_sensing_interval():
    return {
        "success": True,
        #  "str_err": str(e)
    }


@swag_from("./documentation/get_date.yaml")
@app.route("/system/date", methods=['GET'])
def get_system_date():
    return {
        "success": True,
        "value": "",
        "str_err": ""
    }


@swag_from("./documentation/set_date.yaml")
@app.route("/system/sync_date", methods=['POST'])
def set_system_date():
    return {
        "success": True,
        "value": "",
        "str_err": ""
    }


@swag_from("./documentation/get_hidrophones.yaml")
@app.route("/controller/hydrophone/all>", methods=['GET'])
def get_hydrophones():
    return {
        "success": True,
        "value": "",
        "str_err": ""
    }


@swag_from("./documentation/get_hidrophone.yaml")
@app.route("/controller/hydrophone/<id>>", methods=['GET'])
def get_hydrophone(id):
    return {
        "success": True,
        "value": "",
        "str_err": ""
    }

#  @swag_from("./documentation/sensors.getall.yaml")


if __name__ == "__main__":
    app.run(port=80)
