import json
from dataclasses import dataclass


@dataclass
class ControllerConnection:
    serial_device: str
    serial_bauds: str
    socket_host: str
    socket_port: int

@dataclass
class AntennaPosition:
    latitude: float
    longitude: float
    amsl: float

@dataclass
class AntennaLimits:
    max_azimuth: float
    min_azimuth: float
    max_elevation: float
    min_elevation: float

@dataclass
class AntennaConfig:
    position: AntennaPosition
    limits: AntennaLimits
    controller_connection: ControllerConnection

def read_antenna_config(filepath: str) -> AntennaConfig:
    """Read antenna configuration from a JSON file."""
    with open(filepath, "r") as f:
        data = json.load(f)

    position = AntennaPosition(**data["antenna_position"])
    limits = AntennaLimits(**data["antenna_limits"])
    controller_connection = ControllerConnection(**data["controller_connection"])

    return AntennaConfig(position=position, limits=limits, controller_connection=controller_connection)