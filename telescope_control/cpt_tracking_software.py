import time
import threading
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy.time import Time
import spid
import socket
from astropy import units as u
from datetime import datetime

#1.8 el, 1.6 az
# Define your telescope's location
latitude = -33.395720  # Replace with your latitude in degrees
longitude = -70.536856  # Replace with your longitude in degrees
elevation = 868  # Replace with your elevation in meters

# Telescope limits (adjust based on your telescope's safety and design)
ALT_MIN = 20  # Minimum Altitude in degrees (avoid negative or below horizon)
ALT_MAX = 150  # Maximum Altitude in degrees
AZ_MIN = 0   # Minimum Azimuth in degrees
AZ_MAX = 360 # Maximum Azimuth in degrees

# Global variables for tracking and target
tracking = False
current_target = None
stop_threads = False

host='10.17.89.223'
def send_angle(alt, az, host=host, port = 23):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((host, port))
        message = spid.encode_command(spid.build_command(round(float(az),1), round(float(alt))))
        client_socket.sendall(message)


def get_altz_coords(ra, dec):
    radec = SkyCoord(ra=ra*u.deg, dec=dec*u.deg, frame='icrs')
    # Calan GEOGRAPHIC_COORD
    calan_obs = EarthLocation(lat=latitude*u.deg, lon=longitude*u.deg, height=elevation*u.m)
    now = Time.now()
    altaz_frame = AltAz(obstime=now,location=calan_obs)
    altaz = radec.transform_to(altaz_frame)
    alt = altaz.alt.deg
    az = altaz.az.deg
    return alt, az


def is_within_limits(alt, az):
    """Check if the Alt/Az coordinates are within the telescope's limits."""
    return ALT_MIN <= alt <= ALT_MAX and AZ_MIN <= az <= AZ_MAX


def track_target():
    """Background thread function to update tracking and send data via socket."""
    global stop_threads

    while not stop_threads:
        if tracking and current_target:
            ra, dec = current_target["ra"], current_target["dec"]
            alt, az = get_altz_coords(ra, dec)

            if is_within_limits(alt, az):
                print(f"Tracking {current_target['name']}: Altitude = {alt:.2f}°, Azimuth = {az:.2f}°")
                data = f"{current_target['name']}: Altitude = {alt:.2f}, Azimuth = {az:.2f}\n"
                try:
                    send_angle(alt, az)
                except:
                    print("The controller is not responding")
            else:
                print(f"{current_target['name']} is outside the telescope limits: Alt = {alt:.2f}°, Az = {az:.2f}°")
        time.sleep(5)  # Update every 5 seconds



def main():
    global tracking, current_target, stop_threads

    print("Welcome to the telescope tracking program!")
    print("Commands: follow, stop, change, exit")

    # Start the tracking thread
    tracking_thread = threading.Thread(target=track_target, daemon=True)
    tracking_thread.start()

    while True:
        command = input("\nEnter command (follow, stop, change, exit): ").strip().lower()

        if command == "follow":
            if current_target:
                tracking = True
                print(f"[{datetime.now().strftime("%H:%M:%S")}] Started following {current_target['name']}...")
            else:
                print("No target selected. Use 'change' to select a target.")

        elif command == "stop":
            tracking = False
            print("Tracking stopped.")

        elif command == "change":
            name = input("Enter the name of the object: ").strip()
            ra = float(input("Enter the Right Ascension (RA) in degrees: "))
            dec = float(input("Enter the Declination (Dec) in degrees: "))

            current_target = {"name": name, "ra": ra, "dec": dec}
            print(f"Target changed to {name} (RA: {ra}, Dec: {dec}).")

        elif command == "exit":
            print("Exiting the program. Goodbye!")
            stop_threads = True
            tracking_thread.join()
            socket_thread.join()
            break

        else:
            print("Invalid command. Please try again.")


if __name__ == "__main__":
    main()
