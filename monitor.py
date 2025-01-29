import threading
import common
import socket
from datetime import datetime
from telescope import Controller


def main():    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((common.controller_ip, common.controller_port))
    print(f"[{datetime.now().strftime("%H:%M:%S")}] Connected to server {common.controller_ip}:{common.controller_port}")
    controller = Controller(sock)
    controller.receive_position_thread()

if __name__ == "__main__":
    main()