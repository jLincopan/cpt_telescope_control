import spid
import socket
import numpy as np
import threading
import sys
import time
from astropy import units as u
from astropy.coordinates import get_sun, AltAz, EarthLocation, SkyCoord
from astropy.time import Time
from datetime import datetime, timezone

movement_monitor = False
stop_threads = False
position = 0,0
stop_position = 0,0
elaz = []

# Observer's location
latitude = -33.39571095  # Degrees
longitude = -70.53684399  # Degrees
elevation = 868  # Meters above sea level

# Local time offset (UTC)
delta_to_local = -3 * u.h

# Time range: one full day
utc_time = datetime.now(timezone.utc)
start_time = Time(utc_time, scale="utc")
time_list = np.linspace(0, 3, 180) * u.h  # 60 points over 1 hour
obstime1 = start_time + time_list

#Calan position
calan_obs = EarthLocation(lat=latitude * u.deg, lon=longitude * u.deg, height=elevation * u.m)
alt_az_frame = AltAz(location=calan_obs, obstime=obstime1)
#vela_coords = SkyCoord.
sun_coords = get_sun(obstime1)
sun_altaz = sun_coords.transform_to(alt_az_frame).to_string()
obstime1 = obstime1+delta_to_local

# Function to handle receiving messages from the server
def receive_messages(sock):
    global stop_threads
    global position
    global stop_position

    sock.settimeout(1.0)
    while not stop_threads:
        if stop_threads:
            break
        try:
            message = sock.recv(1024)
            if message:
                position = spid.decode_command(message)
                print(f"[{datetime.now().strftime("%H:%M:%S")}] Current position -> EL: {position[1]} AZ: {position[0]}")

            else:
                print(f"[{datetime.now().strftime("%H:%M:%S")}] Connection closed by the server.")
                stop_threads = True
        
        except socket.timeout:
            continue

        except OSError:
            break

        except ConnectionAbortedError:
            print("Connection was closed.")
            break
        except Exception as e:
            print(f"Error: {str(e)}")
            break

# Function to handle sending messages to the server
def send_messages(sock):
    global stop_threads
    global position
    global stop_position
    global movement_monitor
    global elaz

    while not stop_threads:
        message = input("").split(" ")
        
        if movement_monitor:
            msg = spid.encode_command(spid.status_str)
            if stop_position == position:
                movement_monitor = False

        if message[0] == "stop":
            msg = spid.encode_command(spid.stop_str)
            print("Stoping Telescope Movement")

        if message[0] == "restart":
            msg = spid.encode_command(spid.restart_str)

        if message[0].lower() == 'exit':
            print("Closing connection...")
            stop_threads = True
            sock.close()
            break

        try:
            sock.sendall(msg)
        except Exception as e:
            print(f"Error: {str(e)}")
            stop_threads = True
            break
    sys.exit()

def str_to_f(x):
    return round(float(x),1)

def follow_ra_dec(ra,dec):
    pass

def track_sun(sock):
    for a in sun_altaz:
        alt_az = a.split(" ")
        az = float(alt_az[0])
        el = float(alt_az[1])
        msg = spid.encode_command(spid.build_command(str_to_f(az),str_to_f(el)))
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Moving to El - Az {el} - {az}")
        if(el > 70 or az > 310):
            pass
        else:
            sock.sendall(msg)
            
        time.sleep(60)

def main():
    global stop_threads
    global position
    global stop_position

    # Define server address and port
    host = "10.17.89.223"  # or '127.0.0.1' or server IP address
    #host = "llaima.das.uchile.cl"
    port = 23 # Ensure this port matches the server's port
    #port = 2023

    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        sock.connect((host, port))
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Connected to server {host}:{port}")

        # Read the actual position of the antenna
        sock.sendall(spid.encode_command(spid.status_str))
        time.sleep(0.01)
        angles = spid.decode_command(sock.recv(1024))
        position = angles
        #angles = position
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Actual Position: Elevation: {position[1]} - Azimuth: {position[0]}")
    
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return

    # Start the receiving thread
    receive_thread = threading.Thread(target=receive_messages, args=(sock,))
    receive_thread.start()

    tracking_thread = threading.Thread(target=track_sun, daemon=True, args=(sock,))
    tracking_thread.start()

    # Start the sending thread (this is the main thread)
    send_messages(sock)

    # Wait for the receiving thread to finish (if connection closed)
    receive_thread.join()

    sys.exit()

if __name__ == "__main__":
    main()