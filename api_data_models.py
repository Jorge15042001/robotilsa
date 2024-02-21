
from abc import ABC, abstractmethod
from dataclasses import dataclass, fields, asdict
from typing import List
import json
from typing import Callable


class BaseApiModel(ABC):
    @classmethod
    def get_member_types(cls):
        return {field.name: field.type for field in fields(cls)}

    @classmethod
    def validate_dict(cls, data: dict):
        type_lut = cls.get_member_types()
        for key in type_lut:
            if key not in data:
                return (False, f"json no contiene clasve {key}")
            if type(data[key]) is not type_lut[key]:
                return (
                    False,
                    f"clasve {key} debe ser {type_lut[key].__name__}"
                )
        return (True, "")

    def dump_as_json(self):
        class_dict = asdict(self)
        return json.dumps(class_dict, indent=4)

    def as_dict(self):
        class_dict = asdict(self)
        return class_dict

    #  @classmethod
    #  def build(cls, *args, **kargs):
    #      print(args, kargs)
    #      return cls(*args, **kargs)


@dataclass
class API_CONFIG(BaseApiModel):
    JSON_DEVICES_FILE: str
    JSON_SYS_FILE: str
    VALID_SENSING_INTERVALS: list[int]
    API_PORT: int
    DEBUG: bool
    PID_SUBSYSTEM_FILE: Callable[[str], str]
    RESTART_SIGNAL_NUMBER: int
    ALARMS_FILE: str


@dataclass
class API_CONFIG_INTITIAL(BaseApiModel):
    JSON_DEVICES_FILE: str
    JSON_SYS_FILE: str
    VALID_SENSING_INTERVALS: str
    DEBUG: str
    API_PORT: str
    PID_SUBSYSTEM_FILE_FORMAT: str
    RESTART_SIGNAL_NUMBER: str
    ALARMS_FILE: str


@dataclass
class BaseApiResponse(BaseApiModel):
    success: bool = True
    str_err: str = ""

    @classmethod
    def buildSuccess(cls, *args, **kargs):
        response = cls(True, "", *args, **kargs)
        return response

    @classmethod
    def buildFailure(cls, error: str):
        response = cls(False, error)
        return response


@dataclass
class BaseApiPayload(BaseApiModel):
    pass


@dataclass
class UpdateSystemPayload(BaseApiPayload):
    subsystem: str
    param_name: str
    param_value: str


@dataclass
class UpdateSystemResponse(BaseApiResponse):
    pass


@dataclass
class UpdateSensingIntervalPayload(BaseApiPayload):
    sensing_interval: int


@dataclass
class UpdateSensingIntervalResponse(BaseApiResponse):
    pass


@dataclass
class GetDatePayload(BaseApiPayload):
    pass


@dataclass
class GetDateResponse(BaseApiResponse):
    current_timestamp: int = 0


@dataclass
class SetDatePayload(BaseApiPayload):
    current_timestamp: int


@dataclass
class SetDateResponse(BaseApiResponse):
    pass


@dataclass
class GetHydrophonesPayload(BaseApiPayload):
    pass


@dataclass
class GetHydrophonesResponse(BaseApiResponse):
    hydrophones: list[object] = None


@dataclass
class GetHydrophoneDataPayload(BaseApiPayload):
    id: int


@dataclass
class GetHydrophoneDataResponse(BaseApiResponse):
    pass


@dataclass
class SofRestartPayload(BaseApiPayload):
    subsystem: str


@dataclass
class SofRestartResponse(BaseApiResponse):
    pass


@dataclass
class SofRestartProcessorPayload(BaseApiPayload):
    pass


@dataclass
class SofRestartProcessorResponse(BaseApiResponse):
    pass


@dataclass
class HardRestartPayload(BaseApiPayload):
    pass


@dataclass
class HardRestartResponse(BaseApiResponse):
    pass


@dataclass
class GetAlarmsPayload(BaseApiPayload):
    pass


@dataclass
class GetAlarmsResponse(BaseApiResponse):
    alarms: list[object] = None
