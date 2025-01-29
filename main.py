import spid
import socket
import numpy as np
import threading
import time
import common
from datetime import datetime
from telescope import Controller

stop_signal = False
flag_track = False
def main():
    global stop_signal
    global flag_track
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((common.controller_ip, common.controller_port))
    print(f"[{datetime.now().strftime("%H:%M:%S")}] Connected to server {common.controller_ip}:{common.controller_port}")
    controller = Controller(sock)
    radec = []
    print("Avalaible commands: ")
    print("move az,el (moves the telescope to that position and keeps it there, in degrees)")
    print("track ra,dec (begins object tracking, radec in hours and degrees respectively)")
    print("example: move 200,75")
    print("example: track 8h35m24.41s,-45d10m33.5s")
    while not stop_signal:
        cmd = input("").split(" ")
        if cmd[0] == "move":
            coords = cmd[1].split(",")
            controller.send_position(coords[0], coords[1], True)
        elif cmd[0] == "track":
            coords = cmd[1].split(",")
            radec = [coords[0],coords[1]]
            controller.follow_radec(radec[0], radec[1])
            flag_track = True
            thread_track = threading.Thread(target=controller.follow_radec, args=(radec[0], radec[1]))
            thread_track.start()
        elif cmd[0] == "stop":
            controller.stop()
            flag_track = False
        elif cmd[0] == "restart":
            controller.restart()
        elif cmd[0] == "exit":
            stop_signal = True

if __name__ == "__main__":
    main()