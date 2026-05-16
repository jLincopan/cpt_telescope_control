import argparse
from SpidController_connection import SpidController_connection
from antenna_pointing_calibration import antenna_pointing_calibration
from AntennaTracking import AntennaTracking
from time import sleep
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from astropy.coordinates import EarthLocation, solar_system_ephemeris
from astropy import units
import threading
import antenna_config

def help():
    print("Comandos disponibles:")
    print("move az el")
    print("     Mueve la antena hacia una posición determinada y la mantiene (azimuth, elevacion)")
    print("     ej: move 100 20 -> mueve la antena hacia 100°, 20°")
    print("track ra dec")
    print("     Inicia el seguimiento del objeto en las coordenadas especificadas (ascención recta, declinación) en grados")
    print("     ej: track 128.8359 −45.1764 -> Iniciar seguimiento del objeto en las coordenadas 128.8359°,−45.1764°")
    print("     ej: track sun -> Inicia el seguimiento del sol")
    print("stop")
    print("     Detiene un movimiendo o seguimiento en curso")
    print("calibrate")
    print("     Inicia el modo de calibración (usando la sombra del sol en el feed como referencia)")
    print("help")
    print("     Muestra este texto")
    print("")

def main():
    parser = argparse.ArgumentParser(description="Control software for MD-01/02 controllers")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--serial", action="store_true")
    group.add_argument("--tcp", action="store_true")
    config = antenna_config.read_antenna_config("antenna_config.json")

    args = parser.parse_args()
    antenna_control = None
    if args.serial:
        antenna_control = SpidController_connection(connection_type = "serial")
    elif args.tcp:
        antenna_control = SpidController_connection(connection_type = "tcp")
    # Define your telescope's location
    latitude = config.position.latitude
    longitude = config.position.longitude
    #Altura sobre el nivel del mar
    elevation = config.position.amsl
    antenna_location = EarthLocation(lat=latitude*units.deg, lon=longitude*units.deg, height=elevation*units.m)
    antenna_tracking = AntennaTracking(antenna_control)
    session = PromptSession()
    help()
    with patch_stdout():
        while(True):
            text = session.prompt(">")
            command = text.split(" ")
            if command[0] == "move":
                az = float(command[1])
                el = float(command[2])
                antenna_control.set_position(az, el, False)
            elif command[0] == "track":
                if len(command) == 2:
                    #track object
                    tracked_object = command[1]
                    if tracked_object in solar_system_ephemeris.bodies:
                        antenna_tracking.is_tracking = True
                        tracking_thread = threading.Thread(target=antenna_tracking.track_object, daemon=True, args=(antenna_location, tracked_object))
                        tracking_thread.start()
                    else:
                        print("Objeto no disponible en las efemérides usadas")
                        print(f"efemérides disponibles: {solar_system_ephemeris.bodies}")
                elif len(command == 3):
                    ra = command[1]
                    dec = command[2]
                    antenna_tracking.is_tracking = True
                    tracking_thread = threading.Thread(target=antenna_tracking.track_fixed_position, args=(ra,dec,antenna_location), daemon=True)
                    tracking_thread.start()

            elif command[0] == "stop":
                antenna_tracking.is_tracking = False
                antenna_control.stop()

            elif command[0] == "calibrate":
                antenna_tracking.is_tracking = True
                tracking_thread = threading.Thread(target=antenna_tracking.pointing_calibration, args=(antenna_location,), daemon=True)
                tracking_thread.start()
                antenna_pointing_calibration(antenna_tracking)
                antenna_tracking.is_tracking = False
            elif command[0] == "help":
                help()
            #print(command)
            #sleep(1)

if __name__ == "__main__":
    main()