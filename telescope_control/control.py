import spid
import socket
import numpy as np
import threading
import sys
import time

movement_monitor = False
stop_threads = False
position = 0,0
stop_position = 0,0

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
                print(f"Current position -> EL: {position[1]} AZ: {position[0]}")

            else:
                print("Connection closed by the server.")
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

    while not stop_threads:
        message = input("").split(" ")
        
        if movement_monitor:
            msg = spid.encode_command(spid.status_str)
            if stop_position == position:
                movement_monitor = False

        if message[0] == "stop":
            msg = spid.encode_command(spid.stop_str)
            print("Stoping Telescope Movement")

        if message[0] == "status":
            msg = spid.encode_command(spid.status_str)
            print(f"Actual Position: ")

        if message[0] == "park":
            msg = spid.encode_command(spid.build_command(0,90))
            print("Moving to park position")

        if message[0] == "service":
            msg = spid.encode_command(spid.build_command(0,0))
            print("Moving to service position")

        if message[0] == "restart":
            msg = spid.encode_command(spid.restart_str)

        if message[0] == "move":
            if len(message) < 2:
                print("The command has missing arguments: move [move type] [position] ... ")
            elif message[1] == "elaz":
                if len(message) < 4:
                    print("Elevation and Azimuth movement needs the 2 position arguments")
                else:
                    msg = spid.encode_command(spid.build_command(str_to_f(message[3]),str_to_f(message[2])))
                    stop_pos = message[2], message[3]
                    print(f"Moving to El - Az {message[2]} - {message[3]}")
                    movement_monitor = True

            elif message[1] == "el":
                if len(message) < 3:
                    print("Elevation movement missing argument")
                else:
                    msg = spid.encode_command(spid.build_command(str_to_f(position[0]), str_to_f(message[2])))
                    print(f"Moving to El {message[2]}")
            elif message[1] == "az":
                if len(message) < 3:
                    print("Azimuth movement missing argument")
                else:
                    msg = spid.encode_command(spid.build_command(str_to_f(message[2]), str_to_f(position[1])))
                    print("Moving to Az {message[2]}")

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


def main():
    global stop_threads
    global position
    global stop_position

    # Define server address and port
    host = "10.17.89.223"  # or '127.0.0.1' or server IP address
    port = 23        # Ensure this port matches the server's port

    # Create a socket object
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Connect to the server
        sock.connect((host, port))
        print(f"Connected to server {host}:{port}")

        # Read the actual position of the antenna
        sock.sendall(spid.encode_command(spid.status_str))
        time.sleep(0.01)
        angles = spid.decode_command(sock.recv(1024))
        position = angles
        #angles = position
        print(f"Actual Position: Elevation: {position[1]} - Azimuth: {position[0]}")
    
    except Exception as e:
        print(f"Connection error: {str(e)}")
        return

    # Start the receiving thread
    receive_thread = threading.Thread(target=receive_messages, args=(sock,))
    receive_thread.start()

    # Start the sending thread (this is the main thread)
    send_messages(sock)

    # Wait for the receiving thread to finish (if connection closed)
    receive_thread.join()

    sys.exit()

if __name__ == "__main__":
    main()

