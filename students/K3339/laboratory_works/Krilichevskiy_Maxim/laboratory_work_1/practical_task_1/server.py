import socket

HOST = "127.0.0.1"
PORT = 5000

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))

print(f"Server started on {HOST}:{PORT}")

data, client_address = server_socket.recvfrom(1024)
message = data.decode()

print(f"Client says: {message}")

response = "Hello, client!"
server_socket.sendto(response.encode(), client_address)
server_socket.close()