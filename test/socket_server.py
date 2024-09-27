import socket

starting_pos = "57303936380230393638022f20" 

def start_server(host='127.0.0.1', port=12345):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((host, port))
        server_socket.listen()
        print(f'Server listening on {host}:{port}...')

        while True:
            conn, addr = server_socket.accept()
            with conn:
                print(f'Connected by {addr}')
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    print(f'Received message: {data.hex()}')
                    # Echo the message back
                    conn.sendall(bytes.fromhex(starting_pos))

if __name__ == '__main__':
    start_server()
