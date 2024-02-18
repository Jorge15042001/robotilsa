import syslog
import time
import json as js

from abc import ABC, abstractmethod
from dataclasses import dataclass, fields
import api_data_models as api_models


import time
from sys import argv
import threading
import os
from dotenv import dotenv_values
import subprocess
from functools import wraps
from datetime import datetime
from flask import request, jsonify, make_response
from dataclasses import dataclass
from typing import Callable


def set_system_time(unix_timestamp):
    # Convert the Unix timestamp to a formatted string
    current_time = datetime.now()

    # Check if the new timestamp is older than the current time
    if unix_timestamp < current_time.timestamp():
        return False, "Fecha enviada es menor a la fecha del dispositivo"

    time_string = time.strftime(
        "%Y-%m-%d %H:%M:%S", time.gmtime(unix_timestamp))

    try:
        # Execute the date command to set the system time
        subprocess.run(["sudo", "date", "-s", time_string], check=True)
        print("System time set successfully.")
        return True, ""

    except subprocess.CalledProcessError as e:
        #  print(f"Error setting system time: {e}")
        return False, "Fallo al conigurar fecha y hora"


def find_index_in_object_array(object_array, key, key_value):
    for i, obj in enumerate(object_array):
        if obj[key] == key_value:
            return True, i
    return False, -1


def find_subsystem_index(subsystems, subsystem_name):
    return find_index_in_object_array(subsystems, "name", subsystem_name)


def find_param_index(params, param_name):
    return find_index_in_object_array(params, "name", param_name)


def build_response(res_object: api_models.BaseApiResponse):
    http_response_code: int = 200 if res_object.success else 400
    return make_response(res_object.as_dict(), http_response_code)


#  def build_response(success: bool, str_err: str = "", extra_fields: dict = dict()):
#      response = dict()
#      for key in extra_fields:
#          response[key] = extra_fields[key]
#      response["success"] = success
#      response["str_err"] = str_err
#
#      if response["success"]:
#          return make_response(response, 200)
#      return make_response(response, 400)


def validate_dict(type_lut: dict[str, type], _dict) -> (bool, str):
    for key in type_lut:
        if key not in _dict:
            return (False, f"json no contiene clasve {key}")
        if type(_dict[key]) is not type_lut[key]:
            return (
                False,
                f"clasve {key} debe ser {type_lut[key].__name__}"
            )
    return (True, "")


def get_payload_as_parameter(model: api_models.BaseApiModel):
    def decorator(func):
        @ wraps(func)
        def wrapper(*args, **kwargs):
            try:
                json_data = request.get_json()
                model_data = model(**json_data)
                args = args + (model_data,)
                return func(*args, **kwargs)
            except Exception as e:
                # TODO: log
                print(e)

                return build_response(False, "Error desconocido")
        return wrapper
    return decorator


def validate_json_payload(model: api_models.BaseApiModel, response_model: api_models.BaseApiResponse = api_models.BaseApiResponse):
    def decorator(func):
        @ wraps(func)
        def wrapper(*args, **kwargs):
            try:
                json_data = request.get_json()
                success, str_err = model.validate_dict(json_data)
                response = response_model(success, str_err)
                if not success:
                    return build_response(response)
                return func(*args, **kwargs)
            except Exception as e:
                # TODO: log
                print(e)
                return build_response(False, "Error desconocido")
        return wrapper
    return decorator


#  def validate_json_payload(type_lut: dict[str, type]):
#      def decorator(func):
#          @ wraps(func)
#          def wrapper(*args, **kwargs):
#              try:
#                  json_data = request.get_json()
#                  success, str_err = validate_dict(type_lut, json_data)
#                  if not success:
#                      return build_response(False, str_err)
#                  return func(*args, **kwargs)
#              except Exception as e:
#                  # TODO: log
#                  print(e)
#                  return build_response(False, "Error desconocido")
#          return wrapper
#      return decorator


def find_key_index(params, key):
    for i, p in enumerate(params):
        if p["name"] == key:
            return i
    raise Exception("paramter not found")


def read_json(PATH: str) -> (bool, dict):
    try:
        json_file = open(PATH)
        json_data = js.load(json_file)
        json_file.close()
        return True, json_data
    except Exception as e:
        # TODO: setup syslog
        syslog.syslog(syslog.LOG_ERR, str(e))
        return False, dict()


def write_json(data: dict, PATH: str) -> (bool, str):
    try:
        json_file = open(PATH, "w+")
        js_string = js.dumps(data, indent=4, separators=(',', ': '))
        json_file.write(js_string)
        json_file.close()
        return True, ""
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, str(e))
        return False, "Fallo al escribir json"


def format_hydrophones(hydrophones):
    return [
        {
            "id": hydrophone["id"],
            "name": hydrophone["name"],
            "enabled": hydrophone["enabled"]
        }
        for hydrophone in hydrophones]


def hardrestart_system(delay: int = 0, wait: bool = False):
    def reboot():
        time.sleep(delay)
        os.system("reboot")

    restart_thread = threading.Thread(target=reboot).start

    if wait:
        restart_thread.join()


def get_member_types(data_class):
    return {field: field_type for field, field_type in data_class.__annotations__.items()}


def confg_file_path() -> str:
    return argv[1] if len(argv) == 2 else ".env"


def getConfig() -> api_models.API_CONFIG:

    config_file = confg_file_path()
    config: dict = dotenv_values(config_file)

    valid_config, config_error = api_models.API_CONFIG_INTITIAL.validate_dict(
        config)
    if not valid_config:
        raise RuntimeError(config_error)

    config: api_models.API_CONFIG_INTITIAL = api_models.API_CONFIG_INTITIAL(
        **config)

    json_devices_file: str = config.JSON_DEVICES_FILE
    json_sys_file = config.JSON_SYS_FILE
    valid_sensing_intervals: list[int] = [int(interval) for interval in
                                          config.VALID_SENSING_INTERVALS
                                          .split(",")]
    api_port = int(config.API_PORT)
    pid_subsystem_file_format = config.PID_SUBSYSTEM_FILE_FORMAT

    def pid_path_formatter(subsystem):
        return pid_subsystem_file_format + subsystem

    def parse_bool(bool_str: str) -> bool:
        if (bool_str == "true" or bool_str == "1"):
            return True
        if (bool_str == "false" or bool_str == "0"):
            return False
        return False
    debug = parse_bool(config.DEBUG)
    hide_internal = parse_bool(config.HIDE_INTERNAL_METHODS)

    return api_models.API_CONFIG(json_devices_file,
                                 json_sys_file,
                                 valid_sensing_intervals,
                                 api_port,
                                 pid_path_formatter,
                                 debug,
                                 hide_internal
                                 )


def get_payload_as(model: api_models.BaseApiModel):
    json_data = request.get_json()
    return model(**json_data)
