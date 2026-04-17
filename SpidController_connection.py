import serial
import threading
import queue
import socket
import traceback
from time import sleep
from SpidProtocol_rot2prog import Spid_rot2prog
from datetime import datetime

class SpidController_serial:
    def __init__(self, serial_port, serial_baudrate, eth_port, eth_host):
        self.controller_connection = None

        if serial_port is not None:
            self.controller_connection = serial.Serial(serial_port, baudrate=serial_baudrate, timeout=2)
            print(f"{'Abierto puerto serial'} {serial_port}, {serial_baudrate} {'bauds'}")
        elif eth_host is not None:
            self.controller_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.controller_connection.connect()
            self.controller_connection.settimeout(1)
            print(f"{'Conectado a'} {eth_host}:{eth_port}")
            
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
                print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[Respuesta]'} {'az: ' + str(az)}, {'el: ' + str(el)}")
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
                    self._stop.is_set() = True
            except queue.Empty:
                    sleep(0.1)

    def serial_reader(self):
        while not self._stop.is_set():
            # Block until we get a full frame
            header = self.serial_device.read(1)
            if not header or header[0] != 0x57:
                continue  # resync: discard until we see START
            rest = self.serial_device.read(11)
            #print(rest)
            if len(rest) == 11 and rest[10] == 0x20:
                frame = header + rest
                az, el = self.protocolo.decode_command(frame)
                print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[Respuesta]'} {'az: ' + str(az)}, {'el: ' + str(el)}")
                #self.response_queue.put(frame)

    def serial_writer(self):
        while not self._stop.is_set():
            try:
                msg = self.write_queue.get()
                self.serial_device.write(self.protocolo.encode_command(msg))
            except queue.Empty:
                sleep(0.1)

    def send_status(self):
        self.write_queue.put(self.protocolo.status_str)

    def set_position(self, az, el):
        print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[Moviendo] ----> '} {az, el}")
        #self.write_queue.put(self.protocolo.build_command(az, el))
    
    def stop(self):
        print(f"{datetime.now().strftime("%H:%M:%S.%f")[:-3]} {'[Deteniendo]'}")
        self.write_queue.put(self.protocolo.stop_str)

    def close(self):
        self._stop.set()
        self.serial_device.close()
    
    def status_thread(self):
        while not self._stop.is_set():
            self.send_status()
            sleep(1)