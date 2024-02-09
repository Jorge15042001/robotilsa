#  from util import *

from flask import Flask, request, jsonify

from flasgger import Swagger
from flasgger import swag_from
import datetime

from utils import set_system_time


app = Flask(__name__)
swagger = Swagger(app)


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
    timestamp = datetime.datetime.now().timestamp()
    print(timestamp)
    return {
        "success": True,
        "current_timestamp": int(timestamp),
        "str_err": ""
    }


@swag_from("./documentation/set_date.yaml")
@app.route("/system/sync_date", methods=['POST'])
def set_system_date():
    payload = request.get_json()
    target_timestamp = payload["current_timestamp"]
    if type(target_timestamp) is not int:
        return {
            "success": False,
            "str_err": "Timestamp en formato incorrecto"
        }
    sucess, str_err = set_system_time(target_timestamp)

    return {
        "success": sucess,
        "str_err": str_err
    }


@swag_from("./documentation/get_hidrophones.yaml")
@app.route("/controller/hydrophone/all", methods=['GET'])
def get_hydrophones():
    return {
        "success": True,
        "value": "",
        "str_err": ""
    }


@swag_from("./documentation/get_hidrophone.yaml")
@app.route("/controller/hydrophone/<id>", methods=['GET'])
def get_hydrophone(id):
    return {
        "success": True,
        "value": "",
        "str_err": ""
    }

#  @swag_from("./documentation/sensors.getall.yaml")


if __name__ == "__main__":
    app.run(port=80)
