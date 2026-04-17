from SpidController_connection import SpidController_serial
from time import sleep
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
from astropy import units
import threading
import antenna_config

tracking_thread = None
is_tracking = False
config = antenna_config.read_antenna_config("antenna_config.json")
antena_control = SpidController_serial(baudrate=config.controller_connection.serial_bauds, port=config.controller_connection.serial_device)

print(config)

def track_object(ra, dec):
    # Define your telescope's location
    latitude = antenna_config.AntennaPosition.latitude
    longitude = antenna_config.AntennaPosition.longitude
    elevation = antenna_config.AntennaPosition.amsl

    # Telescope limits (adjust based on your telescope's safety and design)
    ALT_MIN = 0  # Minimum Altitude in degrees (avoid negative or below horizon)
    ALT_MAX = 180  # Maximum Altitude in degrees
    AZ_MIN = 0   # Minimum Azimuth in degrees
    AZ_MAX = 360 # Maximum Azimuth in degrees

    ra = float(ra.replace('−', '-'))
    dec = float(dec.replace('−', '-'))
    radec = SkyCoord(ra=ra*units.deg, dec=dec*units.deg, frame='icrs')
    antenna_location = EarthLocation(lat=latitude*units.deg, lon=longitude*units.deg, height=elevation*units.m)
    print("f{'Siguiendo las coordenadas RADEC'} {ra} {dec}")
    while is_tracking:
        now = Time.now()
        altaz_frame = AltAz(obstime=now,location=antenna_location)
        altaz = radec.transform_to(altaz_frame)
        alt = altaz.alt.deg
        az = altaz.az.deg
        print("f{'tracking'} {az} {el}")
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

    session = PromptSession()

    with patch_stdout():
        while(True):
            text = session.prompt(">")
            print(text)
            command = text.split(" ")
            if command[0] == "move":
                az = float(command[1])
                el = float(command[2])
                antena_control.set_position(az, el)
            elif command[0] == "track":
                if command[1] == "sun":
                    pass
                else:
                    ra = command[1]
                    dec = command[2]
                    is_tracking = True
                    tracking_thread = threading.Thread(target=track_object, args=(ra,dec), daemon=True)
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