import argparse
from SpidController_connection import SpidController_connection
from time import sleep
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from astropy.coordinates import EarthLocation, AltAz, SkyCoord, get_body, solar_system_ephemeris
from astropy.time import Time
from astropy import units
import threading
import antenna_config

tracking_thread = None
is_tracking = False
antena_control = None

def track_object(antenna_location, object):
    print(f"{'Siguiendo '} {object}")
    while is_tracking:
        now = Time.now()
        altaz_frame = AltAz(obstime=now, location=antenna_location)
        tracked_object = get_body(object, now, antenna_location)
        tracked_object_altaz = tracked_object.transform_to(altaz_frame)
        az = tracked_object_altaz.az.deg
        el = tracked_object_altaz.alt.deg
        antena_control.set_position(az, el)
        sleep(1)

def track_fixed_position(ra, dec, antenna_location):
    ra = float(ra.replace('−', '-'))
    dec = float(dec.replace('−', '-'))
    radec = SkyCoord(ra=ra*units.deg, dec=dec*units.deg, frame='icrs')
    print(f"{'Siguiendo las coordenadas RADEC'} {ra} {dec}")
    while is_tracking:
        now = Time.now()
        altaz_frame = AltAz(obstime=now,location=antenna_location)
        altaz = radec.transform_to(altaz_frame)
        alt = altaz.alt.deg
        az = altaz.az.deg
        antena_control.set_position(az, alt)
        sleep(1)

def help():
    print("Comandos disponibles:")
    print("move az el")
    print(" Mueve la antena hacia una posición determinada y la mantiene (azimuth, elevacion)")
    print(" ej: move 100 20 -> mueve la antena hacia 100°, 20°")
    print("track ra dec")
    print(" Inicia el seguimiento del objeto en las coordenadas especificadas (ascención recta, declinación) en grados")
    print(" ej: track 128.8359 −45.1764 -> Iniciar seguimiento del objeto en las coordenadas 128.8359°,−45.1764°")
    print(" ej: track sun -> Inicia el seguimiento del sol")
    print("stop")
    print(" Detiene un movimiendo o seguimiento en curso")
    print("help")
    print(" Muestra este texto")
    print("")

def main():
    global is_tracking
    global tracking_thread
    global antena_control

    parser = argparse.ArgumentParser(description="Control software for MD-01/02 controllers")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--serial", action="store_true")
    group.add_argument("--tcp", action="store_true")
    config = antenna_config.read_antenna_config("antenna_config.json")

    args = parser.parse_args()
    if args.serial:
        antena_control = SpidController_connection(connection_type = "serial")
    elif args.tcp:
        antena_control = SpidController_connection(connection_type = "tcp")
    # Define your telescope's location
    latitude = config.position.latitude
    longitude = config.position.longitude
    #Altura sobre el nivel del mar
    elevation = config.position.amsl
    antenna_location = EarthLocation(lat=latitude*units.deg, lon=longitude*units.deg, height=elevation*units.m)
    session = PromptSession()
    help()
    with patch_stdout():
        while(True):
            text = session.prompt(">")
            command = text.split(" ")
            if command[0] == "move":
                az = float(command[1])
                el = float(command[2])
                antena_control.set_position(az, el)
            elif command[0] == "track":
                if len(command) == 2:
                    #track object
                    tracked_object = command[1]
                    if tracked_object in solar_system_ephemeris.bodies:
                        is_tracking = True
                        tracking_thread = threading.Thread(target=track_object, daemon=True, args=(antenna_location, tracked_object))
                        tracking_thread.start()
                    else:
                        print("Objeto no disponible en las efemérides usadas")
                        print(f"efemérides disponibles: {solar_system_ephemeris.bodies}")
                elif len(command == 3):
                    ra = command[1]
                    dec = command[2]
                    is_tracking = True
                    tracking_thread = threading.Thread(target=track_fixed_position, args=(ra,dec,antenna_location), daemon=True)
                    tracking_thread.start()

            elif command[0] == "stop":
                is_tracking = False
                antena_control.stop()

            elif command[0] == "help":
                help()
            #print(command)
            #sleep(1)

if __name__ == "__main__":
    main()