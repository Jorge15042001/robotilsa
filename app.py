#  from util import *


from utils import find_subsystem_index, set_system_time, read_json, format_hydrophones, validate_key
from flask import Flask, request, jsonify, make_response

from flasgger import Swagger
from flasgger import swag_from
import datetime
from dotenv import dotenv_values

config = dotenv_values(".env")
if "JSON_DEVICES_FILE" not in config:
    raise RuntimeError("Missing 'JSON_DEVICES_FILE' in .env file")

JSON_DEVICES_FILE: str = str(config["JSON_DEVICES_FILE"])

if "JSON_SYS_FILE" not in config:
    raise RuntimeError("Missing 'JSON_SYS_FILE' in .env file")
JSON_SYS_FILE = str(config["JSON_DEVICES_FILE"])

if "VALID_SENSING_INTERVALS" not in config:
    raise RuntimeError("Missing 'VALID_SENSING_INTERVALS' in .env file")
VALID_SENSING_INTERVALS: list[int] = [int(interval) for interval in
                                      str(config["VALID_SENSING_INTERVALS"])
                                      .split(",")]


app = Flask(__name__)
swagger = Swagger(app)


def response_setup(response):
    if response["success"]:
        return make_response(response, 200)
    return make_response(response, 400)


@swag_from("./documentation/update_system.yaml")
@app.route("/system/update", methods=['POST'])
def update_system():
    payload = request.get_json()

    validate_key(payload, "subsystem", str)
    validate_key(payload, "param_name", str)
    validate_key(payload, "param_value", str)

    subsystem: str = payload["subsystem"]
    param_name: str = payload["param_name"]
    param_value: str = payload["param_value"]
    return response_setup({
        "success": False,
        "str_err": "Not implemented"
    })


@swag_from("./documentation/sensing_interval.yaml")
@app.route("/system/processor", methods=['POST'])
def update_sensing_interval():
    payload = request.get_json()
    if "sensing_interval" not in payload:
        return response_setup({
            "success": False,
            "str_err": "key 'sensing_interval' no esta presente en payload del request"
        })

    if type(payload["sensing_interval"]) is not int:
        return response_setup({
            "success": False,
            "str_err": "key 'sensing_interval' debe ser entereo"
        })

    interval = int(payload["sensing_interval"])
    if interval not in VALID_SENSING_INTERVALS:
        return response_setup({
            "success": False,
            "str_err": "El intervalo de muestreo no es permitido"
        })
    sys_json: dict = read_json(JSON_SYS_FILE)
    subsystem_idx = find_subsystem_index(sys_json["subsystems"], "processor")
    sys_json[]

    return response_setup({
        "success": False,
        "str_err": "Not implemented"
    })


@swag_from("./documentation/get_date.yaml")
@app.route("/system/date", methods=['GET'])
def get_system_date():
    timestamp = datetime.datetime.now().timestamp()
    return response_setup({
        "success": True,
        "current_timestamp": int(timestamp),
        "str_err": ""
    })


@swag_from("./documentation/set_date.yaml")
@app.route("/system/sync_date", methods=['POST'])
def set_system_date():
    payload = request.get_json()
    target_timestamp = payload["current_timestamp"]
    if type(target_timestamp) is not int:
        return response_setup({
            "success": False,
            "str_err": "Timestamp en formato incorrecto"
        })
    sucess, str_err = set_system_time(target_timestamp)

    return response_setup({
        "success": sucess,
        "str_err": str_err
    })


@swag_from("./documentation/get_hidrophones.yaml")
@app.route("/controller/hydrophone/all", methods=['GET'])
def get_hydrophones():

    success, devices = read_json(JSON_DEVICES_FILE)
    if not success:
        return response_setup({
            "success": False,
            "hydrophones": [],
            "str_err": "No se pudo abrir archivo de dispositivos JSON"
        })
    if "hydrophones" not in devices or len(devices["hydrophones"]) == 0:
        return response_setup({
            "success": False,
            "hydrophones": [],
            "str_err": "No hay hidrófonos en el archvio de dispositivos JSON"
        })

    hydrophones = devices["hydrophones"]
    hydrophones_formatted = format_hydrophones(hydrophones)

    return response_setup({
        "success": True,
        "hydrophones": hydrophones_formatted,
        "str_err": ""
    })


@swag_from("./documentation/get_hidrophone.yaml")
@app.route("/controller/hydrophone/<id>", methods=['GET'])
def get_hydrophone(id):
    return response_setup({
        "success": False,
        "str_err": "Not implemented"
    })


if __name__ == "__main__":
    app.run(port=80)
