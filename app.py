from utils import find_subsystem_index, set_system_time, read_json, format_hydrophones, build_response, validate_json_payload,  validate_dict, find_param_index, write_json, hardrestart_system,  getConfig, get_payload_as, get_payload_as_parameter, build_response, read_pid, send_signal, parse_date_to_timestamp, read_alarms
#  from utils import *
import subprocess
from flask import Flask, request
import api_data_models as api_models

from flasgger import Swagger
from flasgger import swag_from
import datetime
import requests

api_config = getConfig()

# TODO: don't use this variable maybe put it in the .env file
API_URL = "http://127.0.0.1:"+str(api_config).API_PORT


app = Flask(__name__)
swagger = Swagger(app)


@swag_from("./documentation/update_system.yaml")
@app.route("/system/update", methods=['POST'])
@validate_json_payload(api_models.UpdateSystemPayload,
                       api_models.UpdateSystemResponse)
@get_payload_as_parameter(api_models.UpdateSystemPayload)
def update_system(payload: api_models.UpdateSystemPayload):

    _, sys_json = read_json(api_config.JSON_SYS_FILE)
    #  print(sys_json)
    subsystems = sys_json["subsytems"]

    subsystem_found, subsystem_idx = find_subsystem_index(
        subsystems, payload.subsystem)

    if not subsystem_found:
        response = api_models.UpdateSystemResponse.buildFailure(
            "Subsistema no existe")
        return build_response(response)

    subsystem_params = sys_json["subsytems"][subsystem_idx]["params"]
    param_found, param_idx = find_param_index(
        subsystem_params, payload.param_name)

    if not subsystem_found:
        str_err = "Subsistema "+str(payload.subsystem) + \
            " no contiene parametro "+str(payload.param_name)
        response = api_models.UpdateSystemResponse.buildFailure(str_err)
        return build_response(response)

    sys_json["subsytems"][subsystem_idx]["params"][param_idx]["value"] = payload.param_value

    wirte_success, write_json_err = write_json(
        sys_json, api_config.JSON_SYS_FILE)
    if not write_json:
        response = api_models.UpdateSystemResponse.buildFailure(write_json_err)
        return build_response(response)

    # TODO: restart system
    # TODO: response
    soft_restart_payload = api_models.SofRestartPayload(payload.subsystem)
    soft_restart_res = api_models.SofRestartResponse(
        **soft_restart(soft_restart_payload).json())
    if not soft_restart_res.success:
        response = api_models.UpdateSystemResponse.buildFailure(
            soft_restart_res.str_err)
        return build_response(response)

    return build_response(api_models.UpdateSystemResponse.buildSuccess())


@swag_from("./documentation/sensing_interval.yaml")
@app.route("/system/processor", methods=['POST'])
@validate_json_payload(api_models.UpdateSensingIntervalPayload,
                       api_models.UpdateSensingIntervalResponse)
@get_payload_as_parameter(api_models.UpdateSensingIntervalPayload)
def update_sensing_interval(payload: api_models.UpdateSensingIntervalPayload):
    responseModel = api_models.UpdateSensingIntervalResponse

    if payload.sensing_interval not in api_config.VALID_SENSING_INTERVALS:
        return build_response(
            responseModel.buildFailure("El intervalo de muestreo no es permitido"))

    req_payload = api_models.UpdateSystemPayload(
        "processor", "sensing_interval", str(payload.sensing_interval))

    req_response = requests.post(API_URL+"/system/update",
                                 json=req_payload.as_dict()).json()
    system_update_response = api_models.UpdateSystemResponse(**req_response)

    return build_response(
        responseModel(system_update_response.success,
                      system_update_response.str_err)
    )


@swag_from("./documentation/get_date.yaml")
@app.route("/system/date", methods=['GET'])
def get_system_date():
    timestamp = datetime.datetime.now().timestamp()
    response = api_models.GetDateResponse.buildSuccess(timestamp)
    return build_response(response)


@swag_from("./documentation/set_date.yaml")
@app.route("/system/sync_date", methods=['POST'])
@validate_json_payload(api_models.SetDatePayload, api_models.SetDateResponse)
@get_payload_as_parameter(api_models.SetDatePayload)
def set_system_date(payload: api_models.SetDatePayload):

    success, str_err = set_system_time(payload.current_timestamp)

    return build_response(api_models.SetDateResponse(success, str_err))


@swag_from("./documentation/get_hydrophones.yaml")
@app.route("/controller/hydrophone/all", methods=['GET'])
def get_hydrophones():

    success, devices = read_json(api_config.JSON_DEVICES_FILE)

    if not success:
        response = api_models.GetHydrophonesResponse.buildFailure(
            "No se pudo abrir archivo de dispositivos JSON")
        return build_response(response)

    hydrophones = devices["hydrophones"]
    hydrophones_formatted = format_hydrophones(hydrophones)

    return build_response(
        api_models.GetHydrophonesResponse.buildSuccess(hydrophones_formatted)

    )


@swag_from("./documentation/get_hydrophone.yaml")
@app.route("/controller/hydrophone", methods=['GET'])
@validate_json_payload(api_models.GetHydrophoneDataPayload,
                       api_models.GetHydrophoneDataResponse)
@get_payload_as_parameter(api_models.GetHydrophoneDataPayload)
def get_hydrophone(payload: api_models.GetHydrophoneDataPayload):
    print(payload)
    return build_response(api_models.GetHydrophoneDataResponse.buildFailure("Not implemented"))


@swag_from("./documentation/soft_reset_processor.yaml")
@app.route("/system/soft_reset_processor", methods=['POST'])
def soft_restart_processor():
    soft_restart_payload = api_models.SofRestartPayload("processor")
    soft_restart_response = api_models.SofRestartResponse(
        soft_restart(soft_restart_payload).json())

    return build_response(api_models.SofRestartProcessorResponse(
        soft_restart_response.success,
        soft_restart_response.str_err
    ))


@swag_from("./documentation/soft_reset.yaml")
@app.route("/system/soft_reset", methods=['POST'])
@validate_json_payload(api_models.SofRestartPayload,
                       api_models.SofRestartResponse)
@get_payload_as_parameter(api_models.SofRestartPayload)
def soft_restart(payload: api_models.SofRestartPayload):
    _, sys_json = read_json(api_config.JSON_SYS_FILE)

    subsystems = sys_json["subsytems"]

    subsystem_found, subsystem_idx = find_subsystem_index(
        subsystems, payload.subsystem)

    if not subsystem_found:
        response = api_models.SofRestartResponse.buildFailure(
            "Subsistema no existe")
        return build_response(response)
    subsystem_id = sys_json["subsytems"][subsystem_idx]["id"]
    pid_file = api_config.PID_SUBSYSTEM_FILE(str(subsystem_id))

    pid_read, subsystem_pid = read_pid(pid_file)
    if not pid_read:
        response = api_models.SofRestartResponse.buildFailure(
            "No se encontro pid del subsistema")
        return build_response(response)

    signal_sent = send_signal(subsystem_pid, api_config.RESTART_SIGNAL_NUMBER)
    if not signal_sent:
        response = api_models.SofRestartResponse.buildFailure(
            "Señal de reinicio no enviada al subsistema")
        return build_response(response)

    return build_response(api_models.SofRestartResponse.buildSuccess())


@ swag_from("./documentation/hard_reset.yaml")
@ app.route("/system/hard_reset", methods=['POST'])
def hard_restart():
    hardrestart_system(5)
    return build_response(api_models.HardRestartResponse.buildFailure("Not implemented"))


@swag_from("./documentation/get_alarms.yaml")
@app.route("/system/get_alamars", methods=['GET'])
def get_alarms():
    alarms_read, alarms = read_alarms(api_config.ALARMS_FILE)
    if not alarms_read:
        respnse = api_models.GetAlarmsResponse.buildFailure(
            "No se pudo leer alarmas")
        return build_response(respnse)

    response = api_models.GetAlarmsResponse.buildSuccess(alarms)
    return build_response(response)


if __name__ == "__main__":
    app.run(port=api_config.API_PORT, debug=api_config.DEBUG)
