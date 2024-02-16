from utils import find_subsystem_index, set_system_time, read_json, format_hydrophones, build_response, validate_json_payload, validate_dict, find_param_index, write_json, hardrestart_system
import subprocess
from flask import Flask, request

from flasgger import Swagger
from flasgger import swag_from
import datetime
from dotenv import dotenv_values
import requests

config = dotenv_values(".env")

LOCALHOST = "http://127.0.0.1:5000"

config_structure = {
    "JSON_DEVICES_FILE": str,
    "JSON_SYS_FILE": str,
    "VALID_SENSING_INTERVALS": str
}

valid_config, config_error = validate_dict(config_structure, config)
if not valid_config:
    raise RuntimeError(config_error)


JSON_DEVICES_FILE: str = str(config["JSON_DEVICES_FILE"])
JSON_SYS_FILE = str(config["JSON_DEVICES_FILE"])
VALID_SENSING_INTERVALS: list[int] = [int(interval) for interval in
                                      str(config["VALID_SENSING_INTERVALS"])
                                      .split(",")]


app = Flask(__name__)
swagger = Swagger(app)


# TODO: documentaion
@swag_from("./documentation/update_system.yaml")
@app.route("/system/update", methods=['POST'])
@validate_json_payload({
    "subsystem": str,
    "param_name": str,
    "param_value": str,
})
def update_system():
    payload = request.get_json()

    subsystem: str = payload["subsystem"]
    param_name: str = payload["param_name"]
    param_value: str = payload["param_value"]

    sys_json: dict = read_json(JSON_SYS_FILE)
    subsystems: dict = sys_json["subsystems"]

    subsystem_found, subsystem_idx = find_subsystem_index(
        subsystems, subsystem)

    if not subsystem_found:
        return build_response(False, "Subsistem no existe")

    subsystem_params = sys_json["subsystems"][subsystem_idx]["params"]
    param_found, param_idx = find_param_index(subsystem_params, param_name)

    if not subsystem_found:
        return build_response(False, f"Subsistema {subsystem} no contiene parametro {param_name}")

    sys_json["subsystems"][subsystem_idx]["params"][param_idx]["value"] = param_value

    write_json(sys_json, JSON_SYS_FILE)

    # TODO: restart system
    # TODO: response


@swag_from("./documentation/sensing_interval.yaml")
@app.route("/system/processor", methods=['POST'])
@validate_json_payload({
    "sensing_interval": int,
})
def update_sensing_interval():
    payload = request.get_json()

    interval = int(payload["sensing_interval"])

    if interval not in VALID_SENSING_INTERVALS:
        return build_response(False, "El intervalo de muestreo no es permitido")

    new_payload = {
        "subsystem": "processor",
        "param_name": "sensing_interval",
        "param_value": str(interval),
    }

    response = requests.post(f"{LOCALHOST}/system/update", json=new_payload)
    success = response.json()["success"]

    if not success:
        str_err = response.json()["str_err"]
        return build_response(False, str_err)

    return build_response(True, "")


@swag_from("./documentation/get_date.yaml")
@app.route("/system/date", methods=['GET'])
def get_system_date():
    timestamp = datetime.datetime.now().timestamp()
    return build_response(
        True, "",
        {"current_timestamp": int(timestamp), }
    )


@swag_from("./documentation/set_date.yaml")
@app.route("/system/sync_date", methods=['POST'])
@validate_json_payload({
    "current_timestamp": int,
})
def set_system_date():
    payload = request.get_json()
    target_timestamp = payload["current_timestamp"]

    sucess, str_err = set_system_time(target_timestamp)

    return build_response(sucess, str_err)


@swag_from("./documentation/get_hidrophones.yaml")
@app.route("/controller/hydrophone/all", methods=['GET'])
def get_hydrophones():

    success, devices = read_json(JSON_DEVICES_FILE)
    if not success:
        return build_response(
            False, "No se pudo abrir archivo de dispositivos JSON",
            {"hydrophones": []}
        )

    hydrophones = devices["hydrophones"]
    hydrophones_formatted = format_hydrophones(hydrophones)

    return build_response(
        True, "",
        {"hydrophones": hydrophones_formatted, }
    )


# TODO: documentaion
@swag_from("./documentation/get_hidrophone.yaml")
@app.route("/controller/hydrophone/<id>", methods=['GET'])
def get_hydrophone(id):
    return build_response(False, "Not implemented")


# TODO: documentaion
@swag_from("./documentation/soft_restart.yaml")
@app.route("/system/soft_restart", methods=['POST'])
def soft_restart():
    return build_response(False, "Not implemented")


# TODO: documentaion
@swag_from("./documentation/hard_restart.yaml")
@app.route("/system/hard_restart", methods=['POST'])
def hard_restart():
    hardrestart_system(5)
    return build_response(True, "")


if __name__ == "__main__":
    app.run(port=5000)
