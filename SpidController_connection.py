import serial
import threading
import queue
import socket
import traceback
import antenna_config
from time import sleep
from SpidProtocol_rot2prog import Spid_rot2prog
from datetime import datetime

class SpidController_connection:
    def __init__(self, connection_type: str):
        config = antenna_config.read_antenna_config("antenna_config.json")
        self.controller_connection = None

        if connection_type == "serial":
            self.controller_connection = serial.Serial(port=config.controller_connection.serial_device, baudrate=config.controller_connection.serial_bauds, timeout=2)
            print(f"{'Abierto puerto serial'} {config.controller_connection.serial_device}, {config.controller_connection.serial_bauds} {'bauds'}")
        elif connection_type == "tcp":
            self.controller_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.controller_connection.connect(config.controller_connection.socket_host, config.controller_connection.socket_port)
            self.controller_connection.settimeout(1)
            print(f"{'Conectado a'} {config.controller_connection.socket_host}:{config.controller_connection.socket_port}")
        
        self.max_az = int(config.limits.max_azimuth)
        self.max_el = int(config.limits.max_elevation)

        self.min_az = int(config.limits.min_azimuth)
        self.min_el = int(config.limits.min_elevation)

        self.response_queue = queue.Queue()
        self.write_queue = queue.Queue()
        self.protocolo = Spid_rot2prog()
        self._stop = threading.Event()

        self._reader_thread = threading.Thread(target=self.serial_reader, daemon=True)
        self._reader_thread.start()
        self._writer_thread = threading.Thread(target=self.serial_writer, daemon=True)
        self._writer_thread.start()

        #Thread solo para enviar comandos "STATUS" al controlador cada
        #cierto tiempo (para obtener la posición actual de la antena)
        self._status_thread = threading.Thread(target=self.status_thread, daemon=True)
        self._status_thread.start()

    def eth_reader(self):
        while not self._stop.is_set():
            try:
                frame = self.close.recv(1024)
                az, el = self.protocolo.decode_command(frame)
                print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[STATUS]'} {'az: ' + str(az)}, {'el: ' + str(el)}")
            except socket.timeout:
                print("Error: socket timeout")
                traceback.print_exc()
            except OSError:
                traceback.print_exc()
            except ConnectionAbortedError:
                print("Conexión cerrada")
                traceback.print_exc()
            except Exception:
                traceback.print_exc()

    
    def eth_writer(self):
        while not self._stop.is_set():
            try:
                msg = self.write_queue.get()
                try:
                    self.controller_connection.sendall(msg)
                except Exception as e:
                    print("Error al enviar datos")
                    traceback.print_exc()
                    self._stop.is_set = True
            except queue.Empty:
                    sleep(0.1)

    def serial_reader(self):
        while not self._stop.is_set():
            # Block until we get a full frame
            header = self.controller_connection.read(1)
            if not header or header[0] != 0x57:
                continue  # resync: discard until we see START
            rest = self.controller_connection.read(11)
            #print(rest)
            if len(rest) == 11 and rest[10] == 0x20:
                frame = header + rest
                az, el = self.protocolo.decode_command(frame)
                print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[STATUS]'} {'az: ' + str(az)}, {'el: ' + str(el)}")
                #self.response_queue.put(frame)

    def serial_writer(self):
        while not self._stop.is_set():
            try:
                msg = self.write_queue.get()
                self.controller_connection.write(self.protocolo.encode_command(msg))
            except queue.Empty:
                sleep(0.1)

    def send_status(self):
        self.write_queue.put(self.protocolo.status_str)

    def set_position(self, az, el, calibration_active):
        #movement limits
        az = float(round(az, 1))
        el = float(round(el, 1))
        if az < self.min_az or az > self.max_az:
            if calibration_active:
                print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[IGNORADO] '} {az, el} {' (azimuth fuera de límites)'}\r\n")
            else:
                print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[IGNORADO] '} {az, el} {' (azimuth fuera de límites)'}")
        if el < self.min_el or el > self.max_el:
            if el < 0:
                if calibration_active:
                    print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[IGNORADO] '} {az, el} {' (objeto bajo el horizonte)'}\r\n")
                else:
                    print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[IGNORADO] '} {az, el} {' (objeto bajo el horizonte)'}")
            else:
                if calibration_active:
                    print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[IGNORADO] '} {az, el} {' (elevación fuera de límites)'}\r\n")
                else:
                    print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[IGNORADO] '} {az, el} {' (elevación fuera de límites)'}")
            return
        print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[MOVIENDO] -> '} {az, el}")
        #self.write_queue.put(self.protocolo.build_command(az, el))
    
    def stop(self):
        print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[Deteniendo]'}")
        self.write_queue.put(self.protocolo.stop_str)

    def close(self):
        self._stop.set()
        self.controller_connection.close()
    
    def status_thread(self):
        while not self._stop.is_set():
            self.send_status()
            sleep(5)