import syslog
import time
import json as js
import time
import threading
import os
import subprocess
from functools import wraps
from datetime import datetime
from flask import request, jsonify, make_response


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


def build_response(success: bool, str_err: str = "", extra_fields: dict = dict()):
    response = dict()
    for key in extra_fields:
        response[key] = extra_fields[key]
    response["success"] = success
    response["str_err"] = str_err

    if response["success"]:
        return make_response(response, 200)
    return make_response(response, 400)


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


def validate_json_payload(type_lut: dict[str, type]):
    def decorator(func):
        @ wraps(func)
        def wrapper(*args, **kwargs):
            try:
                json_data = request.get_json()
                success, str_err = validate_dict(type_lut, json_data)
                if not success:
                    return build_response(False, str_err)
                return func(*args, **kwargs)
            except Exception as e:
                # TODO: log
                return build_response(False, "Error desconocido")
        return wrapper
    return decorator


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


def write_json(data: dict, PATH: str):
    try:
        json_file = open(PATH, "w+")
        js_string = js.dumps(data, indent=4, separators=(',', ': '))
        json_file.write(js_string)
        json_file.close()
    except Exception as e:
        syslog.syslog(syslog.LOG_ERR, str(e))
        raise Exception("Failed to write json file: %s" % PATH)


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
