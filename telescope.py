import spid
from datetime import datetime
import time
import common
from astropy.coordinates import EarthLocation, AltAz, SkyCoord
from astropy import units as u
from astropy.time import Time

class Controller:
    def __init__(self, socket):
        self.socket = socket
        self.stop_flag = False
        self.position = EarthLocation(lat=common.latitude*u.deg, lon=common.longitude*u.deg, height=common.elevation*u.m)

    def send_position(self, azimuth, elevation, f_show):
        msg = spid.encode_command(spid.build_command(float(azimuth),float(elevation)))
        self.socket.sendall(msg)
        if f_show:
            print(f"[{datetime.now().strftime("%H:%M:%S")}] Moving to {elevation},{azimuth} (az-el)")

    def read_position(self):
        msg = spid.encode_command(spid.status_str)
        self.socket.sendall(msg)
        message = self.socket.recv(1024)
        position = spid.decode_command(message)
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Current position: {position[0]}°,{position[1]}°")

    def stop(self):
        msg = spid.encode_command(spid.stop_str)
        self.socket.sendall(msg)
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Stoping Telescope Movement")

    def restart(self):
        msg = spid.encode_command(spid.restart_str)
        self.socket.sendall(msg)
        print(f"[{datetime.now().strftime("%H:%M:%S")}] Restarting controller")

    def receive_position_thread(self):
        while not self.stop_flag:
            self.read_position()
            time.sleep(1)
    
    def follow_radec(self, ra, dec):
        radec = SkyCoord(ra=ra, dec=dec, frame='icrs')
        print(f"Tracking {ra},{dec}")
        while not self.stop_flag:
            altaz_frame = AltAz(obstime=Time.now(),location=self.position)
            altaz = radec.transform_to(altaz_frame)
            self.send_position(altaz.az.deg, altaz.alt.deg, False)
            time.sleep(1)