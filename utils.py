import syslog
import json as js
import time
import subprocess
from datetime import datetime


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

        # Recheck and print the current system time
        #  time.sleep(2)
        #  current_time = datetime.now()
        #  print("Current system time:", current_time.strftime("%Y-%m-%d %H:%M:%S"))
        #
        #  # Check if the rechecked time is within a tolerance of a few seconds
        #  time_difference = abs(current_time.timestamp() - unix_timestamp)
        #  tolerance = 5  # Adjust this tolerance as needed
        #  if time_difference <= tolerance:
        #      return False, "Fallo al confirmar fecha y hora fueron seteados correctamente"
        return True, ""
    except subprocess.CalledProcessError as e:
        #  print(f"Error setting system time: {e}")
        return False, "Fallo al conigurar fecha y hora"


def find_device_index(devices, device_id):
    for i, d in enumerate(devices):
        if d["id"] == device_id:
            return i
    raise Exception("device not found")


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
