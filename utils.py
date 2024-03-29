import syslog
from glob import glob
import time
import json as js
from os.path import getsize

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
from typing import Callable, Type, Tuple, List


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


def validate_dict(type_lut: dict[str, type], _dict) -> Tuple[bool, str]:
    for key in type_lut:
        if key not in _dict:
            return (False, f"json no contiene clasve {key}")
        if type(_dict[key]) is not type_lut[key]:
            return (
                False,
                f"clasve {key} debe ser {type_lut[key].__name__}"
            )
    return (True, "")


def get_payload_as_parameter(model: Type):
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

                return build_response(api_models.BaseApiResponse.buildFailure("Error desconocido durante obtención de parametro"))
        return wrapper
    return decorator


def validate_json_payload(model: Type, response_model: Type = api_models.BaseApiResponse):
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
                return build_response(response_model(False, "Error desconocido durante validación de payload"))
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


def read_pid(path) -> (bool, int):
    try:
        pid_file = open(path)
        content = pid_file.read()
        return True, int(content)
    except Exception as e:
        # todo syslog
        print(e)
        return False, -1


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

    def pid_path_formatter(subsystem_id):
        return pid_subsystem_file_format.replace("subsystem_id", str(subsystem_id))

    def parse_bool(bool_str: str) -> bool:
        if (bool_str == "true" or bool_str == "1"):
            return True
        if (bool_str == "false" or bool_str == "0"):
            return False
        return False
    debug = parse_bool(config.DEBUG)

    return api_models.API_CONFIG(json_devices_file,
                                 json_sys_file,
                                 valid_sensing_intervals,
                                 api_port,
                                 debug,
                                 pid_path_formatter,
                                 int(config.RESTART_SIGNAL_NUMBER),
                                 config.ALARMS_FILE,
                                 config.RESULTS_FILE,
                                 config.AUDIO_FOLDER
                                 )


def get_payload_as(model: Type):
    json_data = request.get_json()
    return model(**json_data)


def send_signal(pid: int, signal_number: int) -> (bool):
    try:
        os.kill(pid, signal_number)
        print(f"Signal {signal_number} sent to process with PID {pid}")
        return True
    # todo: log
    except ProcessLookupError:
        print(f"Process with PID {pid} not found.")
    except PermissionError:
        print(
            f"Permission error: Unable to send signal to process with PID {pid}.")
    except OSError as e:
        print(f"Error: {e}")
    return False


def parse_date_to_timestamp(date_string: str, date_format: str = "%Y_%m_%d__%H:%M:%S.%f") -> Tuple[bool, float]:
    try:
        # Parse the date string
        parsed_date = datetime.strptime(date_string, date_format)

        # Convert the parsed date to a Unix timestamp
        timestamp = parsed_date.timestamp()

        return True, timestamp

    except ValueError as e:
        print(f"Error: {e}")
        return False, 0


def read_alarms(alarms_path) -> Tuple[bool, list[dict]]:
    try:
        alarms_file = open(alarms_path)
        lines = alarms_file.readlines()
        lines = [line.strip() for line in lines]
        splitted_lines = [line.split(';') for line in lines]
        parsed_lines = [(parse_date_to_timestamp(date_str),  js.loads(json_str))
                        for date_str, json_str in splitted_lines]
        parsed_lines = [pl for pl in parsed_lines if pl[0][0]]

        def add_timestamp_json(json_obj, timestamp):
            json_obj["timestamp"] = timestamp[1]
            # todo fix this in ShrimpSoftware
            if "id_divice" in json_obj:
                json_obj["id_device"] = json_obj["id_divice"]
                del json_obj["id_divice"]

            return json_obj
        alarms_formatted = [add_timestamp_json(json_alarm, timestamp)
                            for timestamp, json_alarm in parsed_lines]
        return True, alarms_formatted
    except Exception as e:
        # todo: log
        print(e)
        return False, []


def read_last_result(filename:str, hydrophone_id: int)->Tuple[bool, api_models.HydrophoneData]:
    try:
        file = open(filename)
        lines = file.readlines()
        lines = [line.strip() for line in lines]
        splitted_lines = [line.split(';') for line in lines]
        parsed_lines = [(parse_date_to_timestamp(date_str),  js.loads(json_str))
                        for date_str, json_str in splitted_lines]
        results = [(pl[0][1], pl[1]) for pl in parsed_lines if pl[0][0]]

        results_of_id = [result for result in results
                         if result[1]["device_id"] == hydrophone_id]

        #  print(results_of_id)
        now = datetime.now().timestamp()
        latets_result_of_id = min(results_of_id, key=lambda r: now - r[0])[1]
        print(latets_result_of_id)
        #  del latets_result_of_id["device_id"]

        hydrophone_results = api_models.HydrophoneData(**latets_result_of_id)
        return True, hydrophone_results

        print(parsed_lines)

    except Exception as e:
        print(e)

    return False, api_models.HydrophoneData()

def parse_audio_path(audio_path: str) -> Tuple[bool, api_models.AudioData]:
    date_format = "%d-%m-%Y_%H:%M:%S.wav"
    try:
        audio_name = audio_path.split("/")[-1]
        _, id_str, date_str_1, date_str_2 = audio_name.split("_")
        date_str = "_".join([date_str_1, date_str_2])
        hydrophone_id = int(id_str)
        valid_timestamp, timestamp = parse_date_to_timestamp(date_str, date_format)
        return valid_timestamp, api_models.AudioData(audio_name, int(timestamp), hydrophone_id, getsize(audio_path))
    except Exception as e:
        print(e)
        return False, api_models.AudioData()

def get_avialable_audios(audio_folder:str) -> List[api_models.AudioData]:
    audio_files = glob(f"{audio_folder}/*")
    parsed_names = [parse_audio_path(a_name) for a_name in audio_files]
    valid_parsed = [pn[1] for pn in parsed_names if pn[0]]
    return valid_parsed


