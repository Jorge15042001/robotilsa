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
        current_time = datetime.now()
        print("Current system time:", current_time.strftime("%Y-%m-%d %H:%M:%S"))

        # Check if the rechecked time is within a tolerance of a few seconds
        time_difference = abs(current_time.timestamp() - unix_timestamp)
        tolerance = 5  # Adjust this tolerance as needed
        if time_difference <= tolerance:
            return False, "Fallo al conigurar fecha y hora"
        return True, ""
    except subprocess.CalledProcessError as e:
        #  print(f"Error setting system time: {e}")
        return False, "Fallo al conigurar fecha y hora"
